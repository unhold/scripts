#!/usr/bin/env python2
# roman numbers

def roman(number):
	"convert number to roman representation"
	if number > 3888:
		raise ValueError('number too big for roman representation')
	table = {
		 100: ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM'),
		  10: ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC'),
		   1: ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX')}
	thousands = number/1000
	hundrets = number%1000/100
	tens = number%100/10
	ones = number%10
	return (''.join(['M' for m in range(thousands)]) +
		table[100][hundrets] +
		table[10][tens] +
		table[1][ones])
	
def roman_test(do_print = False):
	numbers = (
		(1000, True),
		(2000, True),
		(1000, True),
		(1984, True),
		(3889, False),
		(3890, False),
		(3900, False),
		(4000, False))
	for n, f in numbers:
		try:
			r = roman(n)
			if do_print: print "%d: %s" % (n, r)
			assert f
		except ValueError as e:
			if do_print: print "%d: %s" % (n, e)
			assert not f

def roman_time(hours, minutes, seconds = None, maxhours = 24, seperator = ' '):
	assert hours in range(0, 24)
	hours %= maxhours
	# there's no 0 in roman numbers
	if hours == 0: hours = maxhours
	assert minutes in range(0, 60)
	time = roman(hours) + seperator + roman(minutes)
	if seconds != None:
		assert seconds < 60
		time += seperator + roman(seconds)
	return time

def roman_time_test():
	for h in range(24):
		for m in range(60):
			for s in range(60):
				roman_time(h, m, s)

if __name__ == '__main__':
	#roman_test()
	#roman_time_test()
	import time
	t = time.localtime()
	h, m, s = t.tm_hour, t.tm_min, t.tm_sec
	print roman_time(h, m, s)

