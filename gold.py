#!/usr/bin/env python2.6
# experiments with gold sequences

class lfsr:
	def __init__(self, bits, poly, init=1):
		self.bits = bits
		self.poly = poly
		self.length = 2**bits - 1
		assert self.poly <= self.length
		self.init = init

	def __len__(self):
		return self.length

	def __iter__(self):
		self.state = self.init
		self.count = 0
		return self

	def next(self):
		self.count += 1
		if self.count > self.length:
			raise StopIteration()
		else:
			oldstate = self.state
			msb = self.state >> (self.bits - 1)
			self.state = (self.state << 1) & self.length
			if msb:
				self.state ^= self.poly
			return msb

	def __str__(self):
		ret = None
		poly = self.poly
		i = 0
		while poly:
			if poly&1:
				if i == 0: ret = "1"
				else:
					s = "2**" + str(i)
					if ret == None:	ret = s
					else: ret = s + " + " + ret
			poly >>= 1
			i += 1
		return ret

def rol(seq):
	return seq[1:] + seq[:1]

def ror(seq):
	return seq[-1:] + seq[:-1]

def corr(seq1, seq2=None):
	if seq2 == None: seq2 = seq1
	assert len(seq1) == len(seq2)
	return sum([(a1*2-1)*(a2*2-1) for a1, a2 in zip(seq1, seq2)])

def xor(seq1, seq2):
	return [a1^a2 for a1, a2 in zip(seq1, seq2)]

def cseq(seq1, seq2=None, f=corr):
	if seq2 == None: seq2 = seq1
	assert len(seq1) == len(seq2)
	res = []
	for i in seq2:
		res.append(f(seq1, seq2))
		seq2 = rol(seq2)
	return res

def gold(seq1, seq2):
	return cseq(seq1, seq2, xor)

def test():
	#n, p1, p2 = 3, 0b101, 0b011
	n, p1, p2 = 4, 0b0011, 0b1001
	
	l = 2**n - 1

	l1 = lfsr(n, p1)
	o1, s1 = zip(*[(o, l1.state) for o in l1])
	print "lfsr l1:", l1
	print "states s1:", s1
	print "output o1:", o1
	print "acf(o1):", cseq(o1)

	l2 = lfsr(n, p2)
	o2, s2 = zip(*[(o, l2.state) for o in l2])
	print "lfsr l2:", l2
	print "states s2:", s2
	print "output o2:", o2
	print "acf(o2):", cseq(o2)

	print "ccf:", cseq(o1, o2)
	print "ccf limit for gold code:", 2**((n+2)/2)

	g = gold(o1, o2)
	print "gold sequences:"
	for i in range(len(g)):
		print "g" + str(i) + ":", g[i]

	with open("gold.dot", "w") as f:
		print >>f, "graph gold {"
		for i1 in range(l):
			for i2 in range(l):
				if i2 < i1: continue
				ccf_gi1_gi2 = cseq(g[i1], g[i2])
				m = max(ccf_gi1_gi2)
				print "ccf_g%d_g%d:" % (i1, i2), "max:", m, ccf_gi1_gi2
				if i1 != i2:
					print >>f, "\tg%d -- g%d [label=%d, len=%d] ;" % (i1, i2, m, m - 2)
				#if m == 3:
					#print >>f, "\tg%d -- g%d [label=%d, len=3] ;" % (i1, i2, m)				
		print >>f, "}"

if __name__ == "__main__": test()

