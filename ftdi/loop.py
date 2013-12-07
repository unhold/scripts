#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
Electrical connection test for reverse-engineering of Olimex ARM-USB-TINY-H.
"""
from ftdi import *

def getIo(mpsse):
	return mpsse.execute(GetIo(BYTE.HIGH))<<8 | mpsse.execute(GetIo(BYTE.LOW))

def setIo(mpsse, value, direction):
	mpsse.execute(SetIo(value&0xFF, direction&0xFF, BYTE.LOW))
	mpsse.execute(SetIo((value>>8)&0xFF, (direction>>8)&0xFF, BYTE.HIGH))

#with open(lowByteValue=0, lowByteDirection=0) as mpsse:
with Mpsse(d2xx.open(1), lowByteValue=0, lowByteDirection=0) as mpsse:
	idleValue = getIo(mpsse)
	print "idle: 0x%04X" % (idleValue,)
	for bit in range(16):
		setIo(mpsse, 0<<bit, 1<<bit)
		clearValue = getIo(mpsse)
		setIo(mpsse, 1<<bit, 1<<bit)
		setValue = getIo(mpsse)
		print "bit %2d clear: 0x%04X, set: 0x%04X" % (bit, clearValue, setValue,)
		changedValue = clearValue ^ setValue
		if changedValue & ~(1<<bit):
			print "bit %2d changed bits: 0x%04X" % (bit, changedValue,)
			print "              normal: 0x%04X" % (changedValue & setValue,)
			print "            inverted: 0x%04X" % (changedValue & clearValue,)