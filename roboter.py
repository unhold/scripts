#!/usr/bin/env python2.6
# -*- coding: latin-1 -*-
# decode the text in http://static.nichtlustig.de/toondb/100422.html

def textToBin(text):
	result = ""
	for character in text:
		number = ord(character)
		binary = bin(number)[2:]
		while len(binary) < 8:
			binary = "0" + binary
		if result != "": result += " "
		result += binary
	return result

def binToText(bins):
	result = ""
	bins = bins.split()
	for bin in bins:
		result += chr(int(bin, 2))
	return result

print binToText(
"""
00001010 01001000 01100001 01101100 01101100 01101111 00100000 01010011 01100011 01101000 01110111 01100101 01110011 01110100 01100101 01110010 00100000 01110101 01101110 01100100 00100000 01010011 01100011 01101000 01110111 01100001 01100111 01100101 01110010 00100001 00001010 01000100 01100101 01110010 00100000 01001010 01101111 01110011 01100011 01101000 01100001 00100000 01101001 01110011 01110100 00100000 01100100 01101111 01100011 01101000 00100000 01101011 01101100 11000011 10111100 01100111 01100101 01110010 00100000 01100001 01101100 01110011 00100000 01100101 01110010 00100000 01100001 01110101 01110011 01110011 01101001 01100101 01101000 01110100 00111010
""")
	
print '\nSCHLECHTE NACHRICHTEN, HERR ' + textToBin('ROBOTER') + '.\nAUF DIESEM RÖNTENBILD SIEHT MAN GANZ DEUTLICH: SIE SIND EIN ROBOTER.\n'

print 'Also wie man im Programm sieht heißt "'+ textToBin('ROBOTER') + '" ROBOTER.\n'

print binToText(
"""
01001100 01101001 01100101 01100010 01100101 00100000 01000111 01110010 11000011 10111100 11000011 10011111 01100101 00101100 00001010 01000111 01101001 01100111 01101001 00101101 01000101 01101110 01110100 01100101
""")

try:
	print "\nZum Beenden ENTER drücken >>",
	input()
except:
	pass
print '\nAuf Wiedersehen!'
import time
time.sleep(2)
