#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
Abstraction layer for FTDI USB interface chips.
Uses PyUSB, the Python/FTDI-USB module from http://bleyer.org/pyusb/.
Performs a basic test program when executed directly.
"""

import d2xx # PyUSB

class BIT_MODE:
    """
    Bit modes for the FT2232 and other compatible FTDI devices.
    (FTDI AN2232-02)
    """
    RESET = 0x00
    ASYNC = 0x01
    MPSSE = 0x02
    SYNC  = 0x04
    MCU   = 0x08
    OPTO  = 0x10
    UNDEF = 0xFF

class BYTE:
    "Name the I/O port of an FTDI device."
    LOW  = 0
    HIGH = 1

class PIN:
    "Pin masks for the I/O pins. (FTDI FT2232H DS)"
    ADBUS0 = BDBUS0 = TCK = SK = 1<<0
    ADBUS1 = BDBUS1 = TDI = DO = 1<<1
    ADBUS2 = BDBUS2 = TDO = DI = 1<<2
    ADBUS3 = BDBUS3 = TMS = CS = 1<<3
    ADBUS4 = BDBUS4 = GPIOL0 = 1<<4
    ADBUS5 = BDBUS5 = GPIOL1 = 1<<5
    ADBUS6 = BDBUS6 = GPIOL2 = 1<<6
    ADBUS7 = BDBUS7 = GPIOL3 = 1<<7
    ACBUS0 = BCBUS0 = GPIOH0 = 1<<8
    ACBUS1 = BCBUS1 = GPIOH1 = 1<<9
    ACBUS2 = BCBUS2 = GPIOH2 = 1<<10
    ACBUS3 = BCBUS3 = GPIOH3 = 1<<11
    ACBUS4 = BCBUS4 = GPIOH4 = 1<<12
    ACBUS5 = BCBUS5 = GPIOH5 = 1<<13
    ACBUS6 = BCBUS6 = GPIOH6 = 1<<14
    ACBUS7 = BCBUS7 = GPIOH7 = 1<<15

class MASK:
    "Combined pin masks for the I/O pins."
    JTAG_I = SPI_I = I2C_I = PIN.TDO
    JTAG_O = SPI_O = PIN.TCK|PIN.TDI|PIN.TMS
    I2C_O = PIN.SK|PIN.DO
    JTAG_IO = SPI_IO = JTAG_I|JTAG_O
    JTAG_S = SPI_S = PIN.TMS

class FLAG:
    "Flags for MPSSE mode."
    WRITE_NEGEDGE = 0x01
    BIT_MODE      = 0x02
    READ_NEGEDGE  = 0x04
    LSB_FIRST     = 0x08
    WRITE_TDI     = 0x10
    READ_TDO      = 0x20
    WRITE_TMS     = 0x40

class EDGE:
    "Name the polarity of an edge."
    POS = 0
    NEG = 1

EXTENDED_DEVICES = (
    d2xx.DEVICE_232R,
    d2xx.DEVICE_2232C,
    d2xx.DEVICE_2232H,
    d2xx.DEVICE_4232H)

MPSSE_DEVICES = (
    d2xx.DEVICE_2232C,
    d2xx.DEVICE_2232H,
    d2xx.DEVICE_4232H)

HIGHSPEED_DEVICES = (
    d2xx.DEVICE_2232H,
    d2xx.DEVICE_4232H)

class Ftdi:
    "Basic interface for an FTDI device."
    def __init__(self, handle, lowByteDirection = 0):
        self.handle = handle
        self.lowByteDirection = lowByteDirection
        self.bitMode = BIT_MODE.RESET
        self.readTimeout = 1000 # ms
        self.writeTimeout = 1000 # ms
        self.receiveBufferTimeout = 16 # ms
        self.deviceInfo = self.handle.getDeviceInfo()
        self.reset()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

    def __del__(self):
        try:
            self.handle.resetDevice()
            self.handle.close()
            del self.handle
        except AttributeError:
            pass

    def reset(self):
        "Reset the device."
        h = self.handle
        h.resetDevice()
        h.purge()
        if self.deviceInfo["type"] in EXTENDED_DEVICES:
            h.setLatencyTimer(self.receiveBufferTimeout)
        h.setTimeouts(self.readTimeout, self.writeTimeout)
        h.setBitMode(self.lowByteDirection, self.bitMode)
        h.resetDevice()
        h.purge()

    def execute(self, command):
        "Execute a command on the device."
        assert self.bitMode in command.bitModes
        if isinstance(command, ClockDivideByFive):
            assert self.deviceInfo["type"] in HIGHSPEED_DEVICES
        writeData = command.getWriteData(self)
        readCount = command.getReadCount(self)
        if not writeData:
            assert readCount == 0
            return
        writeCount = self.handle.write(writeData)
        assert writeCount == len(writeData)
        if readCount != 0:
            readData = self.handle.read(readCount)
            assert readCount == len(readData)
            command.setReadData(self, readData)
            return command.result

    def executeListSimple(self, commandList):
        "Execute a list of commands. Simple and inefficient."
        for command in commandList:
            self.execute(command)

    def executeList(self, commandList):
        "Execute a list of commands."
        writeData = []
        readCount = 0
        for command in commandList:
            assert self.bitMode in command.bitModes
            if isinstance(command, ClockDivideByFive):
                assert self.deviceInfo["type"] in HIGHSPEED_DEVICES
            writeData.append(command.getWriteData(self))
            readCount += command.getReadCount(self)
        writeData = "".join(writeData)
        if not writeData:
            assert readCount == 0
            return
        writeCount = self.handle.write(writeData)
        if readCount != 0:
            readData = self.handle.read(readCount)
            assert readCount == len(readData)
            readIndex = 0
            for command in commandList:
                subReadCount = command.getReadCount(self)
                if subReadCount != 0:
                    begin = readIndex
                    end = readIndex + subReadCount
                    subReadData = readData[begin:end]
                    command.setReadData(self, subReadData)
                    readIndex += subReadCount
            assert readIndex == readCount

    def checkReadBufferEmpty(self):
        readData = self.handle.read(0x100)
        if readData == "":
            return True
        else:
            print "Ftdi.checkReadBuffer:", readData.encode("hex")
            return False

class Mpsse(Ftdi):

    def __init__(self, handle, lowByteValue = MASK.SPI_S,
                 lowByteDirection = MASK.SPI_O):
        self.lsbFirst = False
        self.handle = handle
        self.resetLowByteValue = lowByteValue
        self.lowByteDirection = lowByteDirection
        self.bitMode = BIT_MODE.MPSSE
        self.readTimeout = 1000 # ms
        self.writeTimeout = 1000 # ms
        self.receiveBufferTimeout = 16 # ms
        self.deviceInfo = self.handle.getDeviceInfo()
        assert self.deviceInfo["type"] in MPSSE_DEVICES
        self.reset()

        __enter__ = Ftdi.__enter__
        __exit__ = Ftdi.__exit__
        __del__ = Ftdi.__del__

    def reset(self, lowByteValue = MASK.SPI_S, lowByteDirection = MASK.SPI_O):
        "Reset the device and setup for MPSSE mode."
        Ftdi.reset(self)
        # clear the MPSSE buffers
        sendImmediate = SendImmediate()
        commandList = []
        for i in range(0, 65537):
            commandList.append(sendImmediate)
        self.executeList(commandList)
        self.handle.resetDevice()
        self.handle.purge()
        commandList = None
        if self.deviceInfo["type"] in HIGHSPEED_DEVICES:
            commandList = (
                Loopback(False),
                ClockDivideByFive(True), # compatible with low-speed by default
                SetIo(self.resetLowByteValue, self.lowByteDirection, BYTE.LOW))
        else:
            commandList = (
                Loopback(False),
                SetIo(self.resetLowByteValue, self.lowByteDirection, BYTE.LOW))
        self.executeList(commandList)

class Command:
    def getReadCount(self, ftdi):
        return 0

class CommandContainer(Command):
    def __init__(self):
        self.subCommands = []

    def getWriteData(self, ftdi):
        return "".join([command.getWriteData(ftdi) for command in self.subCommands])

    def getReadCount(self, ftdi):
        return sum([command.getReadCount(ftdi) for command in self.subCommands])

    def setReadData(self, ftdi, readData):
        assert len(readData) == self.getReadCount(ftdi)
        self.result = readData

class Loopback(Command):
    "Enable/disable internal connection between TDI/DO and TDO/DI."
    def __init__(self, enableLoopback):
        self.enableLoopback = enableLoopback
        self.bitModes = (BIT_MODE.MPSSE,)

    def getWriteData(self, mpsse):
        if self.enableLoopback:
            return "\x84"
        else:
            return "\x85"

class ClockDivideByFive(Command):
    """
    Only for FT2232H, FT4232H!
    Enable/disable divide by 5 from the 60 MHz clock in the FTDI device.
    """
    def __init__(self, enableClockDivideByFive):
        self.enableClockDivideByFive = enableClockDivideByFive
        self.bitModes = (BIT_MODE.MPSSE,)

    def getWriteData(self, mpsse):
        if self.enableClockDivideByFive:
            return "\x8B"
        else:
            return "\x8A"

class ThreePhaseClocking(Command):
    """
    Only for FT2232H, FT4232H!
    Enable/disable three phase data clocking:
    Data setup, pulse clock, data hold.
    """
    def __init__(self, enableThreePhaseClocking):
        self.enableThreePhaseClocking = enableThreePhaseClocking
        self.bitModes = (BIT_MODE.MPSSE,)

    def getWriteData(self, mpsse):
        if self.enableThreePhaseClocking:
            return "\x8C"
        else:
            return "\x8D"

class SetClockDivisor(Command):
    """
    Set the clock divisor. The TCK/SK always has a duty cycle of 50%,
    except between commands where it will remain in its initial state.
    F(TCK/SK) = F(FTDI) / (( 1 + clockDivisorValue) * 2)
    with F(FTDI) = 12MHz or 60MHz for high-speed devices with clock divider off.
    """
    def __init__(self, clockDivisorValue):
        assert clockDivisorValue <= 0xFFFF
        self.clockDivisor = clockDivisorValue
        self.bitModes = (BIT_MODE.MPSSE,)

    def getWriteData(self, mpsse):
        return ("\x86" + chr(self.clockDivisor & 0xFF) +
            chr(self.clockDivisor >> 8))

class SetClockFrequency(Command):
    """
    Set the clock frequency by using SetClockDivisor
    and ClockDivideByFive for high-speed devices.
    """
    def __init__(self, clockFrequency):
        self.clockFrequency = clockFrequency
        self.bitModes = (BIT_MODE.MPSSE,)

    def getWriteData(self, mpsse):
        minFrequency = 6e6 / 0x1000
        assert self.clockFrequency >= minFrequency
        if mpsse.deviceInfo["type"] in HIGHSPEED_DEVICES:
            minHsFrequency = 30e6 / 0x1000
            divide = False
            divisor = 30e6 / self.clockFrequency - 1
            if self.clockFrequency < minHsFrequency:
                divide = True
                divisor = 6e6 / self.clockFrequency - 1
            divint = int(round(divisor))
            return (ClockDivideByFive(divide).getWriteData(mpsse) +
                SetClockDivisor(divint).getWriteData(mpsse))
        else:
            divisor = 6e6 / self.clockFrequency - 1
            divint = int(round(divisor))
            return SetClockDivisor(divint).getWriteData(mpsse)

class SendImmediate(Command):
    "Make the FTDI flush its buffer back to the PC."
    def __init__(self):
        self.bitModes = (BIT_MODE.MPSSE, BIT_MODE.MCU)

    def getWriteData(self, ftdi):
        return "\x87"

class SetIo(Command):
    """
    Setup the direction of the I/O lines and
    force a value on the bits that are set as output.
    """
    def __init__(self, value, direction = MASK.JTAG_O, lowHighByte = BYTE.LOW):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert lowHighByte in (BYTE.LOW, BYTE.HIGH)
        self.lowHighByte = lowHighByte
        self.value = value
        self.direction = direction

    def getWriteData(self, ftdi):
        if self.lowHighByte == BYTE.LOW:
            opcode = "\x80"
        elif self.lowHighByte == BYTE.HIGH:
            opcode = "\x82"
        return opcode + chr(self.value) + chr(self.direction)

class GetIo:
    "Read the current state of the I/O lines."
    def __init__(self, lowHighByte):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert lowHighByte in (BYTE.LOW, BYTE.HIGH)
        self.lowHighByte = lowHighByte

    def getWriteData(self, mpsse):
        if self.lowHighByte == BYTE.LOW:
            return "\x81"
        elif self.lowHighByte == BYTE.HIGH:
            return "\x83"

    def getReadCount(self, mpsse):
        return 1

    def setReadData(self, mpsse, readData):
        assert len(readData) == 1
        self.result = ord(readData)

class WaitOnIo(Command):
    """
    Wait until GPIOL1 (MPSSE mode) or I/O1 (MCU mode)
    is in a certain state then process the next instruction.
    The only way out of this is to disable the FTDI
    if the I/O never goes into the state.
    """
    def __init__(self, stateToWaitFor):
        self.bitModes = (BIT_MODE.MPSSE, BIT_MODE.MCU)
        self.stateToWaitFor = stateToWaitFor

    def getWriteData(self, mpsse):
        if self.stateToWaitFor:
            return "\x88"
        else:
            return "\x89"

class ShiftInBit(Command):
    def __init__(self, bitCount):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert bitCount >= 1
        assert bitCount <= 8
        self.bitCount = bitCount
        self.opcode = FLAG.READ_TDO|FLAG.BIT_MODE

    def getWriteData(self, mpsse):
        opcode = self.opcode
        if mpsse.lsbFirst: opcode |= FLAG.LSB_FIRST
        return chr(opcode) + chr(self.bitCount-1)

    def getReadCount(self, mpsse):
        return 1

    def setReadData(self, mpsse, readData):
        assert len(readData) == 1
        maskedData = ord(readData) & self.getMask()
        self.result = chr(maskedData)

    def getMask(self):
        return (1 << self.bitCount) - 1

class ShiftOutBit(Command):
    def __init__(self, bitCount, writeData):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert bitCount > 0
        assert bitCount <= 8
        self.bitCount = bitCount
        assert len(writeData) == 1
        self.writeData = writeData
        self.opcode = FLAG.WRITE_TDI|FLAG.BIT_MODE|FLAG.WRITE_NEGEDGE

    def getWriteData(self, mpsse):
        opcode = self.opcode
        data = ord(self.writeData)
        if mpsse.lsbFirst:
            opcode |= FLAG.LSB_FIRST
        else:
            if self.bitCount != 8:
                data &= self.getMask()
                addTrail = data & 1
                data <<= 8 - self.bitCount
                if addTrail:
                    data |= 1 << (8 - self.bitCount - 1)
        return chr(opcode) + chr(self.bitCount - 1) + chr(data)

    def getMask(self):
        return (1 << self.bitCount) - 1

class ShiftInOutBit(ShiftOutBit, ShiftInBit):
    def __init__(self, bitCount, writeData):
        ShiftInBit.__init__(self, bitCount)
        ShiftOutBit.__init__(self, bitCount, writeData)
        self.opcode = (FLAG.WRITE_TDI|FLAG.READ_TDO|FLAG.BIT_MODE|
            FLAG.WRITE_NEGEDGE)

    def getReadCount(self, mpsse):
        return 1

class ShiftInByte(Command):
    def __init__(self, byteCount):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert byteCount > 0
        assert byteCount <= 0x1000
        self.byteCount = byteCount
        self.resultReceiver = None
        self.opcode = FLAG.READ_TDO

    def getWriteData(self, mpsse):
        count = self.byteCount - 1
        opcode = self.opcode
        if mpsse.lsbFirst:
            opcode |= FLAG.LSB_FIRST
        return chr(opcode) + chr(count&0xff) + chr(count>>8)

    def getReadCount(self, mpsse):
        return self.byteCount

    def setReadData(self, mpsse, readData):
        assert len(readData) == self.getReadCount(mpsse)
        self.result = readData
        if self.resultReceiver:
            self.resultReceiver.result = readData

class ShiftOutByte(Command):
    def __init__(self, writeData):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert len(writeData) <= 0x1000
        self.writeData = writeData
        self.opcode = FLAG.WRITE_TDI|FLAG.WRITE_NEGEDGE

    def getWriteData(self, mpsse):
        count = len(self.writeData) - 1
        opcode = self.opcode
        if mpsse.lsbFirst:
            opcode |= FLAG.LSB_FIRST
        return (chr(opcode) + chr(count&0xff) + chr(count>>8) +
            self.writeData)

class ShiftInOutByte(ShiftOutByte, ShiftInByte):
    def __init__(self, writeData):
        ShiftInByte.__init__(self, len(writeData))
        ShiftOutByte.__init__(self, writeData)
        self.opcode = (FLAG.WRITE_TDI|FLAG.READ_TDO|FLAG.WRITE_NEGEDGE)

    def getReadCount(self, mpsse):
        return self.byteCount

class ShiftOut(CommandContainer):
    def __init__(self, bitCount, writeData):
        CommandContainer.__init__(self)
        self.bitModes = (BIT_MODE.MPSSE,)
        self.bitCount = bitCount
        self.writeData = writeData
        bits = bitCount%8
        bytes = bitCount/8
        offset = 0
        if bits:
            self.subCommands.append(
                ShiftOutBit(bits, self.writeData[0]))
            offset = 1
        if bytes:
            self.subCommands.append(
                ShiftOutByte(self.writeData[offset:]))

class ShiftIn(CommandContainer):
    def __init__(self, bitCount):
        CommandContainer.__init__(self)
        self.bitModes = (BIT_MODE.MPSSE,)
        self.bitCount = bitCount
        bits = bitCount%8
        bytes = bitCount/8
        if bits:
            self.subCommands.append(ShiftInBit(bits))
        if bytes:
            self.subCommands.append(ShiftInByte(bytes))

class ShiftInOut(CommandContainer):
    def __init__(self, bitCount, writeData):
        CommandContainer.__init__(self)
        self.bitModes = (BIT_MODE.MPSSE,)
        self.bitCount = bitCount
        self.writeData = writeData
        bits = bitCount%8
        bytes = bitCount/8
        offset = 0
        if bits:
            self.subCommands.append(
                ShiftInOutBit(bits, self.writeData[0]))
            offset = 1
        if bytes:
            self.subCommands.append(
                ShiftInOutByte(self.writeData[offset:]))

class ShiftTms(Command):
    "Clock data to TMS pin."
    def __init__(self, data):
        self.bitModes = (BIT_MODE.MPSSE,)
        assert len(data) <= 7
        self.data = data

    def getWriteData(self, mpsse):
        length = len(self.data)
        byte = 0
        for i in range(length):
            if self.data[-i] in (1, "1", "H"):
                byte |= 1<<i
        return "\x4A" + chr(length-1) + chr(byte)

class Clock(Command):
    "Clock without data transfer."
    def __init__(self, count):
        self.bitModes = (BIT_MODE.MPSSE,)
        self.count = count

    def getWriteData(self, mpsse):
        result = ""
        byteCount = self.count/8
        bitCount = self.count%8
        if bitCount:
            result += "\x8E" + chr(bitCount)
        if byteCount:
            result += "\x8F" + chr(byteCount&0xFF) + chr(byteCount>>8)
        return result

def openBySerialNumber(serialNumber,
		lowByteValue = MASK.SPI_S,
		lowByteDirection = MASK.SPI_O):
    return Mpsse(d2xx.openEx(serialNumber, d2xx.OPEN_BY_SERIAL_NUMBER),
		lowByteValue, lowByteDirection)

def open(lowByteValue = MASK.SPI_S, lowByteDirection = MASK.SPI_O):
    return Mpsse(d2xx.open(0), lowByteValue, lowByteDirection)

def ioTest(mpsse):
    """
    Basic test of the I/O functions of an MPSSE.
    This sets ports to output,
    so don't execute with JTAG/SPI peripheral attached!
    """
    ioCommandList = (
        SetIo(0x3C, 0x0F, BYTE.LOW),
        SetIo(0xC3, 0xF0, BYTE.HIGH),
        GetIo(BYTE.LOW),
        GetIo(BYTE.HIGH),
        SendImmediate())
    mpsse.executeList(ioCommandList)
    low = ioCommandList[2].result
    high = ioCommandList[3].result
    assert low & 0x0F == 0x0C
    assert high & 0xF0 == 0xC0
    mpsse.executeList((
        SetIo(0, 0, BYTE.LOW),
        SetIo(0, 0, BYTE.HIGH)))

def shiftTest(mpsse):
    """
    Basic test of the shift functions of an MPSSE.
    This sets ports to output,
    so don't execute with JTAG/SPI peripheral attached!
    """
    mpsse.execute(Loopback(True))
    s = ShiftOutBit(5, "\x5C")
    mpsse.execute(s)
    s = ShiftInBit(4)
    mpsse.execute(s)
    shiftList = []
    for l in range(1, 9):
        for d in range(0, 1 << l):
            s = ShiftInOutBit(l, chr(d))
            s.expectedResult = chr(d)
            shiftList.append(s)
            if True:
                mpsse.execute(s)
                if s.result != s.expectedResult:
                    print "Error:\nbitCount=%d\nresult=0x%X\nexpected=0x%X" % (
                        s.bitCount,
                        ord(s.result),
                        ord(s.expectedResult))
                    assert mpsse.checkReadBufferEmpty()
    mpsse.executeList(shiftList)
    for s in shiftList:
        if s.result != s.expectedResult:
            print "Error:\nbitCount=%d\nresult=0x%X\nexpected=0x%X" % (
                s.bitCount,
                ord(s.result),
                ord(s.expectedResult))
        assert s.result == s.expectedResult
    data = "\x01\x02\x03\xF0\xF1\xF2"
    s = ShiftInByte(6)
    mpsse.execute(s)
    s = ShiftOutByte(data)
    mpsse.execute(s)
    s = ShiftInOutByte(data)
    mpsse.execute(s)
    assert s.result == data
    mpsse.execute(Loopback(False))

def test():
    "Basic module self-test."
    print "Module 'ftdi' self test:"
    with open(0, MASK.SPI_O) as mpsse:
        mpsse.readTimeout = 100
        mpsse.reset()
        mpsse.execute(SetClockDivisor(0))
        mpsse.lsbFirst = True
        shiftTest(mpsse)
        print "shiftTest successfull"
        assert mpsse.checkReadBufferEmpty()

if __name__ == "__main__":
    test()