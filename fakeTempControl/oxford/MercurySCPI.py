# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
# Fake Mercury Temperature Controller
#
# Author: Douglas Clowes 2014
#
from MercuryDevice import MercuryDevice
import random
import re
import os
import sys
import time

sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),"../../util"))))
from fopdt import fopdt, fopdt_sink
from pid import PID

class Loop(fopdt):
    def __init__(self, the_temp, the_nick):
        fopdt.__init__(self, the_temp)
        self.setpoint = the_temp
        self.sensor = the_temp
        # P, I, D
        self.pid = PID(0.05, 0.02, 1.2)
        self.pid.setPoint(the_temp)
        # Value, Kp, Tp, Td, Absolute
        self.AddSource(fopdt_sink(0, 2, 13, 10, True))
        self.AddSink(fopdt_sink(the_temp, 1, 30, 1, False))
        self.power = 0
        self.nick = the_nick
        self.count = 0

    def Setpoint(self, the_sp):
        self.setpoint = the_sp
        self.pid.setPoint(the_sp)

    def doIteration(self):
        self.pid_delta = self.pid.update(self.pv)
        self.sources[0].value = self.pid_delta
        if self.sources[0].value > 100.0:
            self.sources[0].value = 100.0
        if self.sources[0].value < 0.0:
            self.sources[0].value = 0.0
        self.count += 1
        self.iterate(self.count)
        self.sensor = 0.9 * self.sensor + 0.1 * self.setpoint

class MercurySCPI(MercuryDevice):
    """Mercury SCPI temperature controller object - simulates the device"""

    def __init__(self):
        MercuryDevice.__init__(self)
        print MercurySCPI.__name__, "ctor"
        self.RANDOM = 0.0
        self.IDN = "Simulated Mercury SCPI"
        self.CONFIG_LOOPS = [1, 2, 3, 4]
        self.CONFIG_SNSRS = [1, 2, 3, 4]
        self.Loops = {}
        self.Loops[1] = self.Loops['MB0'] = self.Loops['MB1'] = Loop(270, "VTI_STD")
        self.Loops[2] = self.Loops['DB1'] = self.Loops['DB6'] = Loop(270, "Sample_1")
        self.Loops[3] = self.Loops['DB2'] = self.Loops['DB7'] = Loop(270, "Sample_2")
        self.Loops[4] = self.Loops['DB3'] = self.Loops['DB8'] = Loop(270, "VTI")
        self.valve_open = 0.0
        self.hlev = 92.0
        self.nlev = 87.6
        self.reset_powerup()

    def doCommand(self, command, params):
        print MercurySCPI.__name__, "Command:", command, params
        return MercuryDevice.doCommand(self, command, params)

    def doQuery(self, command, params):
        print MercurySCPI.__name__, "Query:", command, params
        return MercuryDevice.doQuery(self, command, params)

    def reset_powerup(self):
        print MercurySCPI.__name__, "reset_powerup"
        self.LAST_ITERATION = 0

    def doIteration(self):
        delta_time = time.time() - self.LAST_ITERATION
        if delta_time < 1:
            return
        #print "DoIteration:", delta_time
        self.LAST_ITERATION = time.time()
        for idx in self.CONFIG_LOOPS:
            self.Loops[idx].doIteration()

    def doCommandSET(self, cmd, args):
        if args[0] != "DEV":
            return
        key = args[1].split(".")[0]
        if key == "DB4":
            # Valve
            self.valve_open = float(args[5])
            self.write("STAT:SET:" + ":".join(args) + ":VALID")
            return
        if key in self.Loops:
            if args[4] == "TSET":
                self.Loops[key].Setpoint(float(args[5]))
            self.write("STAT:SET:" + ":".join(args) + ":VALID")
            return
        self.write("STAT:SET:"  + ":".join(args) + ":INVALID")

    def doQueryREAD(self, cmd, args):
        if args[0] != "DEV":
            return
        key = args[1].split(".")[0]
        if key == "DB4":
            # Valve
            self.write("STAT:DEV:DB4.G1:AUX:SIG:OPEN:%7.4f%%" % self.valve_open)
            return
        if key == "DB5":
            # Level
            if args[4] == "HEL":
                self.write("STAT:DEV:DB5.L1:LVL:SIG:HEL:LEV:%7.4f%%" % self.hlev)
                return
            if args[4] == "NIT":
                self.write("STAT:DEV:DB5.L1:LVL:SIG:NIT:LEV:%7.4f%%" % self.nlev)
                return
            return
        if key in self.Loops:
            if args[3] == "NICK":
                self.write("STAT:DEV:"+args[1]+":TEMP:NICK:%s" % self.Loops[key].nick)
                return
            if args[4] == "TSET":
                self.write("STAT:DEV:"+args[1]+":TEMP:LOOP:TSET:%g" % self.Loops[key].setpoint)
                return
            if args[4] == "TEMP":
                self.write("STAT:DEV:"+args[1]+":TEMP:SIG:TEMP:%7.4fK" % self.Loops[key].sensor)
                return
            if args[4] == "POWR":
                self.write("STAT:DEV:"+args[1]+":HTR:SIG:POWR:%.4fW" % self.Loops[key].power)
                return
        self.write("STAT:"  + ":".join(args) + ":INVALID")
        print "TODO implement Query: \"READ\" in \"" + cmd + ":" + ":".join(args) + "\""

if __name__ == '__main__':
    from MercuryProtocol import MercuryProtocol

    class TestFactory:
        def __init__(self):
            print self.__class__.__name__, "ctor"
            self.numProtocols = 0
        def write(self, data):
            print "test write:", data,
        def loseConnection(self):
            print "test lose connection"
    test_factory = TestFactory()
    test_device = MercurySCPI()
    test_protocol = MercuryProtocol(test_device, "\r\n")
    test_protocol.factory = test_factory
    test_protocol.transport = test_factory
    test_device.protocol = test_protocol
    test_device.protocol.connectionMade()
    commands = ["READ:DEV:MB1.T1:TEMP:SIG:TEMP",
        "READ:DEV:MB1.T1:TEMP:NICK",
        "SET:DEV:MB1.T1:TEMP:LOOP:TSET:274",
        "READ:DEV:MB1.T1:TEMP:LOOP:TSET",
        "READ:DEV:MB0.H1:HTR:SIG:POWR"]
    for cmd in commands:
        test_device.protocol.dataReceived(cmd)
        test_device.protocol.dataReceived(test_protocol.term)
    test_device.protocol.connectionLost("Dunno")
