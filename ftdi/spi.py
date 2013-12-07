#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
SPI master.
Correct flags for MPSSE commands:
[FLAG.BIT_MODE]|FLAG.WRITE_TDI|FLAG.READ_TDO|FLAG.WRITE_NEGEDGE, not FLAG.READ_NEGEDGE.
"""

import ftdi

class SPI:
    def __init__(self, mpsse):
        mpsse.execute(ftdi.SetClockDivisor(59))
        #mpsse.execute(ftdi.ThreePhaseClocking(False))
        self.mpsse = mpsse

    def __del__(self):
        self.mpsse.__del__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.mpsse.__exit__(exc_type, exc_value, traceback)

    COUNT = 20

    CS_LOW = tuple([ftdi.SetIo(ftdi.MASK.SPI_S&~ftdi.PIN.CS, ftdi.MASK.SPI_O) for i in range(COUNT)])
    CS_HIGH = tuple([ftdi.SetIo(ftdi.MASK.SPI_S, ftdi.MASK.SPI_O) for i in range(COUNT)])

    def readWrite(self, word):
        byte = chr(word)
        shift = ftdi.ShiftInOutByte(byte)
        commandList = self.CS_HIGH + self.CS_LOW + (shift,) + self.CS_LOW + self.CS_HIGH
        self.mpsse.executeList(commandList)
        return ord(shift.result)

def open():
    mpsse = ftdi.open(ftdi.MASK.SPI_S, ftdi.MASK.SPI_O)
    spi = SPI(mpsse)
    return spi

def test():
    with open() as spi:
        print "spi.readWrite(0)",
        version = spi.readWrite(0)
        print version
        print "spi.readWrite(2)", spi.readWrite(3)
        for i in range(1000):
            v = spi.readWrite(0x07)
            assert v == version

if __name__ == "__main__":
    test()
