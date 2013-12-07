#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
Serial Vector Format (SVF) parser and utilities.
"""

from pyparsing import *
import tap

COMMANDS = ("ENDDR", "ENDIR", "FREQUENCY", "HDR", "HIR", "PIO", "PIOMAP", "RUNTEST", "SDR", "SIR", "STATE", "TDR", "TIR", "TRST",)
TRST_MODES = ("ON", "OFF", "Z", "ABSENT",)

def intToStr(i, minLength=0):
    s = ""
    while i != 0 or minLength > 0:
        s = chr(i&0xFF) + s
        i >>= 8
        minLength -= 1
    return s

class Command:
    def interpret(self, args):
        self.args = tuple(args)
        self._interpret(args)
    def execute(self, jtag):
        #print(self.name(), "not implemented")
        pass
    def name(self):
        return self.__class__.__name__.upper()
    def has(self, var):
        return var in vars(self)
    def __str__(self):
        v = vars(self)
        if "args" in v: del v["args"]
        return self.name() + "(" + str(v) + ")"

class Enddr(Command):
    def _interpret(self, args):
        assert len(args) == 1
        self.stable_state = args[0]
    def execute(self, jtag):
        jtag.dr_end_state = self.stable_state

class Endir(Command):
    def _interpret(self, args):
        assert len(args) == 1
        self.stable_state = args[0]
    def execute(self, jtag):
        jtag.ir_end_state = self.stable_state

class Frequency(Command):
    def _interpret(self, args):
        assert len(args) in (0, 2)
        if len(args) == 2: self.cycles = float(args[0])
        else: self.cycles = 0.0 # Unrestricted.

class DrIr(Command):
    def _interpret(self, args):
        assert len(args) in (1, 3, 5, 7, 9)
        self.length = int(args[0])
        for i in range(1, len(args), 2):
            name, value = args[i], args[i+1]
            name = name.upper()
            if name == "TDI":
                assert not self.has("tdi")
                self.tdi = int(value, 16)
            elif name == "TDO":
                assert not self.has("tdo")
                self.tdo = int(value, 16)
            elif name == "MASK":
                assert not self.has("mask")
                self.mask = int(value, 16)
            elif name == "SMASK":
                assert not self.has("smask")
                self.smask = int(value, 16)

class Hdr(DrIr): pass

class Hir(DrIr): pass

class Pio(Command):
    def _interpret(self, args):
        assert len(args) == 1
        self.vector_string = args[0]

class Piomap(Command):
    def _interpret(self, args):
        assert len(args) >= 2 and len(args) % 2 == 0
        self.piomap = []
        for i in range(0, len(args), 2):
            direction, logical_name = args[i], args[i+1]
            self.piomap.append((logical_name, direction,))

class Runtest(Command):
    def _interpret(self, args):
        assert len(args) in range(2, 10)
        if args[0] in tap.STABLE_STATES:
            self.run_state = args[0]
            args = args[1:]
        if args[1] == "SEC":
            self.min_time = int(args[0])
            args = args[2:]
        else:
            self.run_count = int(args[0])
            self.run_clk = args[1]
            args = args[2:]
            if args and args[0] != "MAXIMUM":
                self.min_time = int(args[0])
                assert args[1] == "SEC"
                args = args[2:]
        if args and args[0] == "MAXIMUM":
            self.max_time = int(args[1])
            assert args[2] == "SEC"
            args = args[3:]
        if args and args[0] == "ENDSTATE":
            self.end_state = args[1]
            args = args[2:]
        assert not args
    def execute(self, jtag):
        if self.has("run_state"):
            jtag.run_state = self.run_state
            jtag.end_state = self.run_state
        if self.has("end_state"):
            jtag.end_state = self.end_state
        # TODO: other variants
        # run_count, run_clk
        assert self.run_clk == "TCK"
        jtag.run(self.run_count)

class Sdr(DrIr):
    def execute(self, jtag):
        bytes = self.length/8
        if self.length%8: bytes += 1
        jtag.shift_dr(self.length, intToStr(self.tdi, bytes))

class Sir(DrIr):
    def execute(self, jtag):
        bytes = self.length/8
        if self.length%8: bytes += 1
        jtag.shift_ir(self.length, intToStr(self.tdi, bytes))

class State(Command):
    def _interpret(self, args):
        assert len(args) >= 1
        self.states = args

class Tdr(DrIr): pass

class Tir(DrIr): pass

class Trst(Command):
    def _interpret(self, args):
        assert len(args) == 1
        self.trst_mode = args[0]

def parse(file):
    bracket = lambda expr: Combine(Literal("(").suppress() + expr + Literal(")").suppress())
    identifierExp = Word(alphas+"_", alphanums+"_")
    posRealExp = Combine(Word(nums) + Optional("." + Word(nums)) + Optional("E" + Optional(Word("+-")) + Word(nums)))
    statesExp = oneOf(tuple(tap.STATES))
    stableStatesExp = oneOf(tap.STABLE_STATES)
    dataExp = bracket(Word(nums+srange("[A-F]")))
    DrIrExp = Word(nums) + ZeroOrMore(oneOf("TDI TDO MASK SMASK") + dataExp)
    commands = {
        "ENDDR"     : stableStatesExp,
        "ENDIR"     : stableStatesExp,
        "FREQUENCY" : Optional(posRealExp + "HZ"),
        "HDR"       : DrIrExp,
        "HIR"       : DrIrExp,
        "PIO"       : bracket(Word("HLZUDX")),
        "PIOMAP"    : OneOrMore(oneOf("IN OUT") + identifierExp),
            # Second form - mapping between column and logical name - is deprecated, not implemented.
        "RUNTEST"   : Optional(stableStatesExp) + Word(nums) + oneOf("SEC TCK SCK") + Optional(posRealExp + "SEC" + Optional("MAXIMUM" + posRealExp + "SEC")) + Optional("ENDSTATE" + stableStatesExp),
        "SDR"       : DrIrExp,
        "SIR"       : DrIrExp,
        "STATE"     : stableStatesExp | (ZeroOrMore(statesExp) + stableStatesExp),
        "TDR"       : DrIrExp,
        "TIR"       : DrIrExp,
        "TRST"      : oneOf(TRST_MODES),
    }
    commentLiterals = Literal("!") | "//"
    commentExpression = commentLiterals + SkipTo(LineEnd()) + LineEnd()
    commandExpression = oneOf(tuple(commands)) + SkipTo(";", failOn=commentLiterals) + Literal(";").suppress()
    expression = commentExpression.suppress() | Group(commandExpression)
    fileExpression = LineStart() + ZeroOrMore(expression) + LineEnd().suppress()
    commandList = fileExpression.parseFile(file)
    classList = []
    for cmd, args in commandList:
        exp = LineStart() + commands[cmd] + LineEnd().suppress()
        res = exp.parseString(args.upper())
        commandClass = None
        commandClass = eval(cmd.title())
        commandInst = commandClass()
        commandInst.interpret(res)
        classList.append(commandInst)
    return classList

def test():
    global commandList
    commandList = []
    with open("svf.svf") as file:
        commandList = parse(file)
    assert(len(commandList) == 1892)

    #[print(cmd) for cmd in commandList]
    noneCount = len([None for cmd in commandList if cmd == None])
    print("Unresolved commands:", noneCount)

    commandsUsed = set([cmd.name() for cmd in commandList if cmd])
    commandsUnused = set(COMMANDS) - commandsUsed
    print("Unused commands:", commandsUnused)

if __name__ == "__main__":
    test()