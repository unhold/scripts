#!/usr/bin/env python2
# iRobot Roomba Serial Command Interface

import serial, struct, time

def bytes(values):
	return ''.join([chr(i) for i in values])

class StateError(Exception):
	def __init__(self, command, state):
		self.command = command
		self.state = state
	def __str__(self):
		return "command %s not allowed in state %s" % (
			self.command.__class__.__name__, self.state)

class Command:
	def getWriteData(self):
		return bytes((self.opcode,))
	def getReadCount(self):
		return 0

class Start(Command):
	opcode = 128
	states = ('undefined', 'passive', 'safe', 'full',)
	nstate = 'passive'

class Baud(Command):
	opcode = 129
	states = ('passive', 'safe', 'full',)
	nstate = 'passive'
	baudTable = {
		  300:  0,
		  600:  1,
		 1200:  2,
		 2400:  3,
		 4800:  4,
		 9600:  5,
		14400:  6,
		19200:  7,
		28800:  8,
		38400:  9,
		57600: 10,
	}
	def __init__(self, baudrate):
		self.baudrate = baudrate
	def getWriteData(self):
		baudcode = self.baudTable[self.baudrate]
		return bytes((self.opcode, baudcode,))

class Control(Command):
	opcode = 130
	states = ('passive',)
	nstate = 'safe'

class Safe(Command):
	opcode = 131
	states = ('full',)
	nstate = 'safe'

class Full(Command):
	opcode = 132
	states = ('safe',)
	nstate = 'full'

class Power(Command):
	opcode = 133
	states = ('safe', 'full',)
	nstate = 'off'

class Spot(Command):
	opcode = 134
	states = ('safe', 'full',)
	nstate = 'passive'

class Clean(Command):
	opcode = 135
	states = ('safe', 'full',)
	nstate = 'passive'

class Max(Command):
	opcode = 136
	states = ('safe', 'full',)
	nstate = 'passive'

class Drive(Command):
	opcode = 137
	states = ('safe', 'full',)
	nstate = 'undefined'
	STRAIGHT = -32768 # why not 0?
	TURN_LEFT = 1 # in place
	TURN_RIGHT = -1 # in place
	def __init__(self, speed_mmPs=0, radius_mm=STRAIGHT):
		if speed_mmPs != 0 and abs(speed_mmPs) < 11:
			raise ValueError("abs(speed_mmPs) too small")
		self.speed_mmPs = speed_mmPs
		self.radius_mm = radius_mm
	def getWriteData(self):
		speed = struct.pack('>h', self.speed_mmPs)
		radius = struct.pack('>h', self.radius_mm)
		return bytes((self.opcode,)) + speed + radius

class Motors(Command):
	opcode = 138
	states = ('safe', 'full',)
	nstate = 'unchanged'
	def __init__(self, mainBrushOn=0, vacuumOn=0, sideBrushOn=0):
		self.mainBrushOn = mainBrushOn
		self.vacuumOn = vacuumOn
		self.sideBrushOn = sideBrushOn
	def getWriteData(self):
		motorState = 0
		if self.mainBrushOn: motorState |= 1<<2
		if self.vacuumOn:    motorState |= 1<<1
		if self.sideBrushOn: motorState |= 1<<0
		return bytes((self.opcode, motorState,))

class Leds(Command):
	opcode = 139
	states = ('safe', 'full',)
	nstate = 'unchanged'
	statusLedValueTable = {
		'off':   0, 0 : 0,
		'red':   1, 1 : 1,
		'green': 2, 2 : 2,
		'amber': 3, 3 : 3,}
	def __init__(self,
			statusLedValue='off',
			spotLedOn=0,
			cleanLedOn=0,
			maxLedOn=0,
			dirtDetectLedOn=0,
			powerLedColor=0,
			powerLedIntensity=0):
		self.statusLedValue = statusLedValue
		self.spotLedOn = spotLedOn
		self.cleanLedOn = cleanLedOn
		self.maxLedOn = maxLedOn
		self.dirtDetectLedOn = dirtDetectLedOn
		self.powerLedColor = powerLedColor
		self.powerLedIntensity = powerLedIntensity
	def getWriteData(self):
		ledState = 0
		ledState |= self.statusLedValueTable[self.statusLedValue]<<4
		if self.spotLedOn:       ledState |= 1<<3
		if self.cleanLedOn:      ledState |= 1<<2
		if self.maxLedOn:        ledState |= 1<<1
		if self.dirtDetectLedOn: ledState |= 1<<0
		return bytes((self.opcode, ledState, self.powerLedColor,
				self.powerLedIntensity,))

class Song(Command):
	opcode = 140
	states = ('passive', 'safe', 'full',)
	nstate = 'unchanged'
	noteOffsetTable = {
		'C'  :  0,	'C#' :  1,	'D'  :  2,	'D#' :  3,
		'E'  :  4,	'F'  :  5,	'F#' :  6,	'G'  :  7,
		'G#' :  8,	'A'  :  9,	'A#' : 10,	'B'  : 11,}
	def __init__(self, songNumber, notesAndDurations):
		assert songNumber >= 0 and songNumber < 16
		assert len(notesAndDurations) <= 16
		self.songNumber = songNumber
		self.notesAndDurations = notesAndDurations
	def getWriteData(self):
		songData = ''.join(self.nadToString(nad) for
					nad in self.notesAndDurations)
		songLength = len(self.notesAndDurations)
		return bytes((self.opcode, self.songNumber, songLength,)
				) + songData
	def noteToByte(self, note):
		#print 'noteToByte(%s)' % (note,)
		assert len(note) in (2, 3,)
		noteOffset = note[:-1]
		oktave = ord(note[-1]) - ord('0')
		#print 'noteToByte(%s): noteOffset=%s, oktave=%d' % (note, noteOffset, oktave)
		assert oktave in range(1, 10)
		number = 36 + 12 * (oktave-2) + self.noteOffsetTable[noteOffset]
		#print 'noteToByte(%s) : %d' % (note, number,)
		assert number in range(31, 128)
		return chr(number)
	def durationToByte(self, duration):
		code = int(duration * 64)
		assert code < 256
		return chr(code)
	def nadToString(self, nad):
		note, duration = nad
		return self.noteToByte(note) + self.durationToByte(duration)

class Play(Command):
	opcode = 141
	states = ('safe', 'full',)
	nstate = 'unchanged'
	def __init__(self, songNumber):
		assert songNumber >= 0 and songNumber < 16
		self.songNumber = songNumber
	def getWriteData(self):
		return bytes((self.opcode, self.songNumber,))

class Sensors(Command):
	opcode = 142
	states = ('passive', 'safe', 'full',)
	nstate = 'unchanged'
	packetLengthTable = {
		0: 26,
		1: 10,
		2:  6,
		3: 10,}
	def __init__(self, packetCode):
		assert packetCode >= 0 and packetCode < 4
		self.packetCode = packetCode
	def getWriteData(self):
		return bytes((self.opcode, self.packetCode,))
	def getReadCount(self):
		return packetLengthTable[self.packetCode]
	def setReadData(self, readData):
		assert len(readData) == self.getReadCount()
		def getNextValue(format, length):
			global readData
			value = struct.unpack(format, readData[:length])
			readData = readData[length:]
			return value
		def getNextChar():
			return getNextValue('c', 1) # uchar
		def getNextShort():
			return getNextValue('>h', 1) # sshort
		if self.packetCode in (0, 1,):
			self.bumpsWheeldrops = getNextChar()
			self.wall = getNextChar()
			self.cliffLeft = getNextChar()
			self.cliffFrontLeft = getNextChar()
			self.cliffFrontRight = getNextChar()
			self.cliffRight = getNextChar()
			self.virtualWall = getNextChar()
			self.motorOvercurrents = getNextChar()
			self.dirtDetectorLeft = getNextChar()
			self.dirtDetectorRight = getNextChar()
		if self.packetCode in (0, 2,):
			self.remoteControlCommand = getNextChar()
			self.buttons = getNextChar()
			self.distance_mm = getNextShort()
			self.angle_mm = getNextShort()
		if self.packetCode in (0, 3,):
			self.chargingState = getNextChar()
			self.voltage_mV = getNextValue('>H', 2) # ushort
			self.current_mA = getNextShort()
			self.temperature_C = getNextValue('b', 1) # schar
			self.charge_mAh = getNextValue('>H', 2) # ushort
			self.capacity_mAh = getNextValue('>H', 2) # ushort
		assert len(readData) == 0 # readData consumed by getNext*()

class ForceSeekingDock(Command):
	opcode = 143
	states = ('passive', 'safe', 'full',)
	nstate = 'unchanged'

class Roomba:
	def __init__(self, serialPortName, baudrate):
		self.serialPort = serial.Serial(serialPortName, baudrate)
		self.state = 'undefined'
	def __call__(self, command):
		self.execute(command)
	def __lshift__(self, value):
		"""Overload left-shift operator to execute Commands and set
		states. Not very pythonic but it saves a lot of typing."""
		if isinstance(value, str):
			self.setState(value)
		else:
			self.execute(value)
		return self
	def execute(self, command):
		if not self.state in command.states:
			raise StateError(command, self.state)
		writeData = command.getWriteData()
		self.serialPort.write(writeData)
		readCount = command.getReadCount()
		if readCount:
			readData = self.serialPort.read(readCount)
			command.setReadData(readData)
		if command.nstate != 'unchanged':
			self.state = command.nstate
			time.sleep(0.020)
	def setState(self, state, force=False):
		if force:
			self.state = 'undefined'
		if state == self.state:
			pass
		elif state == 'unchanged':
			pass
		elif state == 'undefined':
			self.state = 'undefined'
		elif state == 'passive':
			self << Start()
		elif state == 'safe':
			if self.state == 'full':
				self << Safe()
			else:
				self.setState('passive')
				self << Control()
		elif state == 'full':
			self.setState('safe')
			self << Full()
		else:
			raise ValueError('unknown state value %s' % (state,))
		assert self.state == state
	def songCleanup(self):
		"Reset song pointers to beginning of songs."
		for i in range(16):
			self << Song(i, 0, ()),
			self << Play(i),
	def drive(self, speed_mmPs=0, radius_mm=Drive.STRAIGHT, time=1.0):
		oldstate = self.state
		try:
			self << Drive(speed_mmPs, radius_mm)
			time.sleep(time)
		finally:
			self.setState(oldstate)

"Dance of the Sugar Plum Fairy, part 0"
DOTSPF0 = (
	('G5',  1.0/8),
	('E5',  1.0/8),
	('G5',  1.0/4),
	('F#5', 1.0/4),
	('D#5', 1.0/4),
	('E5',  1.0/4),
	('D5',  1.0/8),
	('D5',  1.0/8),
	('D5',  1.0/4),
	('C#5', 1.0/8),
	('C#5', 1.0/8),
	('C#5', 1.0/4),
	('C5',  1.0/8),
	('C5',  1.0/8),
	('C5',  1.0/4),
	('B4',  1.0/8),)
"Dance of the Sugar Plum Fairy, part 1"
DOTSPF1 = (
	('E5',  1.0/8),
	('C5',  1.0/8),
	('E5',  1.0/8),
	('B4',  1.0/4),
	('E3',  1.0/16),
	('D3',  1.0/16),
	('C3',  1.0/16),
	('B2',  1.0/16),
	('A#2', 1.0/4),
	('G4',  1.0/8),
	('E4',  1.0/8),
	('G4',  1.0/4),
	('F#4', 1.0/4),
	('C5',  1.0/4),
	('B4',  1.0/4),
	('G5',  1.0/8),)
"Dance of the Sugar Plum Fairy, part 2"
DOTSPF2 = (
	('G5',  1.0/8),
	('G5',  1.0/4),
	('F#5', 1.0/8),
	('F#5', 1.0/8),
	('F#5', 1.0/4),
	('E5',  1.0/8),
	('E5',  1.0/8),
	('E5',  1.0/4),
	('D#5', 1.0/8),
	('F#5', 1.0/8),
	('E5',  1.0/8),
	('F#5', 1.0/8),
	('D#5', 1.0/4),)

def durationOfSong(song):
	return sum([duration for note, duration in song]) + 0.02

def changeSong(song, nadFunctor):
	return [nadFunctor(nad) for nad in song]

def nadStretchDuration(nad, factor):
	note, duration = nad
	return (note, duration * factor,)

def nadOffsetNote(nad, offset):
	note, duration = nad
	octave = ord(note[-1]) + offset
	note = note[:-1] + chr(octave)
	return (note, duration,)

def nadTruncateNote(nad):
	note, duration = nad
	octave = ord(note[-1]) - ord('0')
	if octave < 2:
		octave += 1
	note = note[:-1] + chr(ord('0') + octave)
	return (note, duration,)

if __name__ == '__main__':
	def nadFunctor(nad):
		nad = nadStretchDuration(nad, 1.75)
		nad = nadOffsetNote(nad, -1)
		nad = nadTruncateNote(nad)
		return nad
	song0 = changeSong(DOTSPF0, nadFunctor)
	song1 = changeSong(DOTSPF1, nadFunctor)
	song2 = changeSong(DOTSPF2, nadFunctor)
	roomba = Roomba('/dev/ttyUSB0', 115200)
	commandList = [
		'safe',
		Song(0, song0),
		Song(1, song1),
		Song(2, song2),
		Play(0), durationOfSong(song0),
		Play(1), durationOfSong(song1),
		Play(2), durationOfSong(song2),
		Leds('red'  , 1, 0, 1, 0,   0,  86), 1,
		Leds('amber', 1, 1, 1, 1, 127, 171), 1,
		Leds('green', 0, 1, 0, 1, 255, 255), 1,
		Leds(), 1,
		Motors(sideBrushOn=True), 3,
		Motors(mainBrushOn=True), 3,
		Motors(vacuumOn=True), 3, Motors(),
		Drive(50, Drive.TURN_LEFT), 0.5, "safe", Drive(), "safe",
		Drive(50, Drive.TURN_RIGHT), 0.5, "safe", Drive(), "safe",
		Drive(50, Drive.STRAIGHT), 0.5, "safe", Drive(), "safe",
		Drive(-50, Drive.STRAIGHT), 0.5, "safe", Drive(), "safe",
		Spot(), 5, Power(),
		Clean(), 1, Power(),
		Max(), 1, Power(),
		Drive(10), 1, Drive(), 2,
		Motors(1, 1, 1), 5, Motors(), 1,
		ForceSeekingDock(), 1,
	]
	try:
		for command in commandList:
			if isinstance(command, Command):
				roomba.execute(command)
			elif isinstance(command, str):
				roomba.setState(command)
			else:
				time.sleep(command)
	finally:
		roomba.setState('passive')

