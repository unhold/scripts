#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
I2C master.
Correct flags for MPSSE commands:
[FLAG.BIT_MODE]|FLAG.WRITE_TDI|FLAG.READ_TDO|FLAG.WRITE_NEGEDGE, not FLAG.READ_NEGEDGE.
"""

import ftdi

class I2C:
    def __init__(self, mpsse, address=0):
        assert mpsse.deviceInfo["type"] in ftdi.HIGHSPEED_DEVICES
        mpsse.execute(ftdi.SetClockDivisor(119))
        mpsse.execute(ftdi.ThreePhaseClocking(True))
        self.address = address
        self.mpsse = mpsse

    COUNT = 40

    START = \
        tuple([ftdi.SetIo(ftdi.MASK.I2C_O, ftdi.MASK.I2C_O) for i in range(COUNT)]) + \
        tuple([ftdi.SetIo(ftdi.PIN.SK, ftdi.MASK.I2C_O) for i in range(COUNT)]) + \
        tuple([ftdi.SetIo(0, ftdi.MASK.I2C_O) for i in range(COUNT)])

    STOP = \
        tuple([ftdi.SetIo(0, ftdi.MASK.I2C_O) for i in range(COUNT)]) + \
        tuple([ftdi.SetIo(ftdi.PIN.SK, ftdi.MASK.I2C_O) for i in range(COUNT)]) + \
        tuple([ftdi.SetIo(ftdi.MASK.I2C_O, ftdi.MASK.I2C_O) for i in range(COUNT)])

    def _address(self, readWrite):
        byte = self.address&0xFE
        if readWrite:
            byte |= 1
        ack_command = ftdi.ShiftInOutBit(1, chr(1))
        address_command = self.START + (ftdi.ShiftOutByte(chr(byte)), ack_command)
        self.mpsse.executeList(address_command)
        ack = ord(ack_command.result)
        return ack == 0

    def read(self, length):
        data = ""
        if not self._address(True):
            self.mpsse.executeList(self.STOP)
            return None
        for i in range(length):
            ack = 1 if i == length-1 else 0
            read_byte = (ftdi.ShiftInOutByte("\xFF"), ftdi.ShiftOutBit(1, chr(ack)))
            self.mpsse.executeList(read_byte)
            byte = read_byte[0].result
            data += byte
        self.mpsse.executeList(self.STOP)
        return data

    def write(self, data):
        i = 0
        if not self._address(False):
            self.mpsse.executeList(self.STOP)
            return None
        for byte in data:
            if isinstance(byte, int):
                byte = chr(byte)
            write_byte = (ftdi.ShiftOutByte(byte), ftdi.ShiftInOutBit(1, chr(1)))
            self.mpsse.executeList(write_byte)
            ack = ord(write_byte[1].result)
            if ack != 0:
                break
            i += 1
        self.mpsse.executeList(self.STOP)
        return i

def open(address = 0xE8):
    mpsse = ftdi.open(ftdi.MASK.I2C_O, ftdi.MASK.I2C_O)
    i2c = I2C(mpsse, address)
    return i2c

def test():
    i2c = open(0xE8)
    print "i2c.read(1)", [hex(ord(i)) for i in i2c.read(1)]
    print "i2c.read(2)", [hex(ord(i)) for i in i2c.read(2)]
    for i in range(100):
        print "i2c.write(\"\\x05\")", i2c.write("\x05")
    print "i2c.write(\"\\x05\\x03\")", i2c.write("\x05\x03")

if __name__ == "__main__":
    test()