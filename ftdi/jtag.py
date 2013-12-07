#!/usr/bin/env python2.6
# Christian Unhold, DICE GmbH & Co KG
"""
JTAG interface.
"""

import ftdi, tap, svf

def get_state_change_command(fromState, toState):
    edges = tap.find_shortest_edges(tap.STATES, fromState, toState)
    assert len(edges) <= 7
    return ftdi.ShiftTms(edges)

class Jtag:
    def __init__(self, mpsse):
        mpsse.lsbFirst = True
        self.mpsse = mpsse
        self.ir_end_state = "IDLE"
        self.dr_end_state = "IDLE"
        self.run_state = "IDLE"
        self.end_state = "IDLE"
        self.mpsse.execute(ftdi.ShiftTms([1]*5))
        self.state = "RESET"

    def execute(self, svfCommand):
        print(svfCommand)
        svfCommand.execute(self)

    def execute_list(self, svfCommandList):
        for svfCommand in svfCommandList:
            self.execute(svfCommand)
    
    def set_state(self, state):
        if state != self.state:
            shiftTms = get_state_change_command(self.state, state)
            self.mpsse.execute(shiftTms)
            self.state = state

    def shift_ir(self, length, data):
        commandList = (get_state_change_command(self.state, "IRSHIFT"),
            ftdi.ShiftInOut(length, data),
            get_state_change_command("IRSHIFT", self.ir_end_state),)
        self.mpsse.executeList(commandList)
        self.state = self.ir_end_state
        return commandList[1].result

    def shift_dr(self, length, data):
        commandList = (get_state_change_command(self.state, "DRSHIFT"),
            ftdi.ShiftInOut(length, data),
            get_state_change_command("DRSHIFT", self.dr_end_state),)
        self.mpsse.executeList(commandList)
        self.state = self.dr_end_state
        return commandList[1].result

    def run(self, cycles):
        self.set_state(self.run_state)
        self.mpsse.execute(ftdi.Clock(cycles))
        self.set_state(self.end_state)

def readIdCode():
    with ftdi.open() as mpsse:
        jtag = Jtag(mpsse)
        

def test1():
    with ftdi.open() as mpsse:
        mpsse.lsbFirst = True
        mpsse.execute(ftdi.SetClockFrequency(100e3))
        def pause(): raw_input()
        print("mpsse.execute(ShiftOut(4, \"\\x05\")")
        mpsse.execute(ftdi.ShiftOut(4, "\x05"))
        pause()
        print("mpsse.execute(ShiftOut(4, \"\\x0A\")")
        mpsse.execute(ftdi.ShiftOut(4, "\x0A"))
        pause()
        print("jtag = Jtag(mpsse)")
        jtag = Jtag(mpsse)
        pause()
        print("jtag.set_state(\"IDLE\")")
        jtag.set_state("IDLE")
        print("jtag.state =", jtag.state)
        pause()
        print("jtag.shift_ir(4, \"\\x05\")")
        jtag.shift_ir(4, "\x05")
        print("jtag.state =", jtag.state)
        pause()
        print("jtag.shift_dr(6, \"\\x2A\")")
        jtag.shift_dr(6, "\x2A")
        print("jtag.state =", jtag.state)
        pause()
        print("jtag.shift_dr(8, \"\\x2A\")")
        jtag.shift_dr(8, "\x2A")
        print("jtag.shift_dr(8, \"\\x2A\")")
        jtag.shift_dr(8, "\x2A")
        print("jtag.state =", jtag.state)
        pause()
        assert mpsse.checkReadBufferEmpty()

def test2():
    commandList = None
    with open("svf.svf") as file:
        commandList = svf.parse(file)
    with ftdi.open() as mpsse:
        Jtag(mpsse).execute_list(commandList)
        assert mpsse.checkReadBufferEmpty()

if __name__ == "__main__":
    test1()