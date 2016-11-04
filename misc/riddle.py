#!/usr/bin/python
# -*- coding: latin1 -*-

# the riddle of:
# http://www.geocaching.com/seek/cache_details.aspx?wp=GC1VT71

# a,b in 1..999

# P <= a * b
# S <= a + b
# D <= a - b

pairs0 = set()
for a in range(1, 1001):
	for b in range(1, a+1):
		pairs0.add((a, b,))

print len(pairs0), "Möglichkeiten."
	
print "1: P: Ich kenne die Zahlen nicht."

p_map = {}
for a, b in pairs0:
	p = a*b
	if p in p_map:
		p_map[p] += 1
	else:
		p_map[p] = 1

pairs1 = set()
for a, b in pairs0:
	if p_map[a*b] > 1:
		  	pairs1.add((a,b,))

print len(pairs0) - len(pairs1), "Paare entfallen."
print len(pairs1), "Möglichkeiten."

print "2: S: Das brauchst Du mir nicht zu sagen, denn das wusste ich schon."

s_set = set()

for s in range(2, 1999):
	e = False
	for h in range(1, s/2 + 1):
		b = h
		a = s-b
		if a > 999 or b > 999:
			continue
		p = a*b
		if p_map[p] == 1:
			e = True
			break
	if e == False:
		s_set.add(s)

pairs2 = set()
for s in s_set:
	for h in range(1, s/2 + 1):
		b = h
		a = s-b
		if a > 999 or b > 999:
			continue
		pairs2.add((a,b,))

assert (73, 64) in pairs2

pairs2 = pairs1 & pairs2

print len(pairs1) - len(pairs2), "Paare entfallen."
print len(pairs2), "Möglichkeiten."

print "3 P: Dann kenne ich die Zahlen jetzt."

p_map = {}
for a, b in pairs2:
	p = a*b
	if p in p_map:
		p_map[p] += 1
	else:
		p_map[p] = 1

pairs3 = set()
for a, b in pairs2:
	if p_map[a*b] == 1:
		  	pairs3.add((a,b,))

print len(pairs2) - len(pairs3), "Paare entfallen."
print len(pairs3), "Möglichkeiten."

print "4 S: Ich kenne sie jetzt auch."

s_map = {}
for a, b in pairs3:
	s = a+b
	if s in s_map:
		s_map[s] += 1
	else:
		s_map[s] = 1

pairs4 = set()
for a, b in pairs3:
	if s_map[a+b] == 1:
		  	pairs4.add((a,b,))

print len(pairs3) - len(pairs4), "Paare entfallen."
print len(pairs4), "Möglichkeiten."
 
print "5a D: Ich kenne die beiden Zahlen noch nicht."
 
d_map = {}
for a, b in pairs4:
	d = a-b
	if d in d_map:
		d_map[d] += 1
	else:
		d_map[d] = 1

pairs5 = set()
for a, b in pairs4:
	if d_map[a-b] > 1:
		  	pairs5.add((a,b,))

print len(pairs4) - len(pairs5), "Paare entfallen."
print len(pairs5), "Möglichkeiten."

print "5b D: Ich kann nur eine Zahl vermuten, die wahrscheinlich dabei ist, aber sicher weiß ich's nicht."

d_map = {}
for a, b in pairs5:
	d = a-b
	if d in d_map:
		d_map[d] += 1
	else:
		d_map[d] = 1

for d in d_map:
	print d, ":",
	for a, b in pairs5:
		if a-b == d:
			print a, b,
	print

# Bei Differenz 9 kommen als Einzige Zahlen mehrmals vor
pairs5 = [(a, b,) for a, b in pairs5 if a-b == 9]

print "6: P: Ich weiß, welche Zahl Du vermutest, aber die ist falsch."

pairs6 = []
for a, b in pairs5:
	if a != 32 and b != 32:
		pairs6.append((a,b,))

print len(pairs5) - len(pairs6), "Paare entfallen."
print len(pairs6), "Möglichkeiten."

print "7: D: OK, dann kenne ich jetzt auch beide Zahlen."

d_map = {}
for a, b in pairs6:
	d = a-b
	if d in d_map:
		d_map[d] += 1
	else:
		d_map[d] = 1

pairs7 = set()
for a, b in pairs6:
	if d_map[a-b] == 1:
		  	pairs7.add((a,b,))

print len(pairs6) - len(pairs7), "Paare entfallen."
print len(pairs7), "Möglichkeiten."

print pairs7

