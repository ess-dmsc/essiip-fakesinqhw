# vim: ts=8 sts=4 sw=4 expandtab
# Fake Lakeshore Model 336 Temperature Controller
#
# Author: Douglas Clowes 2012, 2013
#
from LakeshoreDevice import LakeshoreDevice
import random
import re
import sys
import time

class Lakeshore336(LakeshoreDevice):
    """Lakeshore 336 temperature controller object - simulates the LS336"""

    def __init__(self):
        LakeshoreDevice.__init__(self)
        print Lakeshore336.__name__, "ctor"
        self.CONFIG_LOOPS = [1, 2, 3, 4]
        self.CONFIG_SNSRS = [1, 2, 3, 4]
        self.CONFIG_RAMPS = [1, 2]
        self.reset_powerup()

    def doCommand(self, command, params):
        print Lakeshore336.__name__, "Command:", command, params
        return LakeshoreDevice.doCommand(self, command, params)

    def doQuery(self, command, params):
        print Lakeshore336.__name__, "Query:", command, params
        return LakeshoreDevice.doQuery(self, command, params)

    def reset_powerup(self):
        print Lakeshore336.__name__, "reset_powerup"
        self.LAST_ITERATION = 0
        self.ALARM = {}
        self.ALARMST = {}
        for idx in self.CONFIG_SNSRS:
            self.ALARM[idx] = "0"
            self.ALARMST[idx] = "0"
        self.ANALOG = {1: "0,1,1,1,400.0,0.0,0.0", 2: "0,1,1,1,400.0,0.0,0.0"}
        self.AOUT = { 1: 0.0, 2: 0.0 }
        self.CFILT = {1: 1, 2: 1}
        self.CLIMI = 0.0
        self.CLIMIT = {1: "400.0,10,0,0", 2: "400.0,10,0,0"}
        self.CMODE = {}
        for idx in self.CONFIG_LOOPS:
            self.CMODE[idx] = 1
        self.CRVHDR = {}
        self.CRVHDR[1] = "DT-336-1       ,STANDARD  ,1,+500.000,1"
        self.CRVHDR[2] = "DT-336-2       ,STANDARD  ,2,+0.500,1"
        self.CRVHDR[3] = "DT-336-3       ,STANDARD  ,3,+2.000,2"
        self.CRVHDR[4] = "DT-336-4       ,STANDARD  ,4,+0.301,2"
        self.CRVPT = {}
        for i in range(1,21):
            self.CRVPT[i] = [(0.0, 0.0)]
        self.DOUT = 0
        self.FILTER = {1: "1,10,2"}
        self.FREQ = 2
        self.GUARD = 0
        self.HTR = {}
        for idx in self.CONFIG_LOOPS:
            self.HTR[idx] = 0.0
        self.HTRRNG = 0
        self.HTRST = 0
        self.IDN = "LSCI,MODEL336,123456/123456,1.0"
        self.IEEE = "0,0,4"
        self.INCRV = {}
        self.INTYPE = {}
        for idx in self.CONFIG_SNSRS:
            self.INCRV[idx] = "1"
            self.INTYPE[idx] = "1,0,1,0,1"
        self.KEYST = 1
        self.KRDG = {}
        for idx in self.CONFIG_SNSRS:
            self.KRDG[idx] = 300.0
        self.LOCK = "0,000"
        self.MDAT = {1: "0,0,1"} # Min,Max,Reset
        self.MOUT = {1: "0.0", 2: "0.0", 3: "0.0", 4: "0.0"}
        self.LOOPINPUT = {}
        self.OUTMODE = {}
        self.PID = {}
        for idx in self.CONFIG_LOOPS:
            self.PID[idx] = "+0150.0,+0005.0,+000.0"
            self.LOOPINPUT[idx] = idx
            if idx < 3:
                self.OUTMODE[idx] = "1,%d,0" % idx
            else:
                self.OUTMODE[idx] = "4,%d,0" % idx
        self.RAMP_ON = {}
        self.RAMP_RATE = {}
        self.RAMP_ST = {}
        for idx in self.CONFIG_RAMPS:
            self.RAMP_ON[idx] = 0
            self.RAMP_RATE[idx] = 0.000
            self.RAMP_ST[idx] = 0
        self.RAMP_TIME = 0.0
        self.RANGE = {}
        for idx in self.CONFIG_LOOPS:
            self.RANGE[idx] = "1"
        self.RDGST = {"A": 0, "B": 0, "C": 0, "D": 0}
        self.RELAY = {1: "1,A,0", 2: "2,A,0"}
        self.RELAYST = {1: "0", 2: "0"}
        self.SETP = {}
        self.TARGET = {}
        self.RAMP_START_TEMP = {}
        self.RAMP_START_TIME = {}
        for idx in self.CONFIG_LOOPS:
            self.SETP[idx] = 300.0
            self.TARGET[idx] = 300.0
            self.RAMP_START_TEMP[idx] = 300.0
            self.RAMP_START_TIME[idx] = 0.0
        self.STB = 0
        self.ESE = 0
        self.ESR = 0
        self.OPC = 0
        self.SRE = 0
        self.TST = 0
        self.RANDOM = 0.0

    def doIteration(self):
        delta_time = time.time() - self.LAST_ITERATION
        if delta_time < 1:
            return
        #print "DoIteration:", delta_time
        self.LAST_ITERATION = time.time()
        for idx in self.CONFIG_LOOPS:
            ndx = self.LOOPINPUT[idx]
            # progress ramping setpoints (SP)
            if idx in self.RAMP_ON and self.RAMP_ON[idx] and self.TARGET[idx] != self.SETP[idx]:
                delta_time = time.time() - self.RAMP_START_TIME[idx];
                delta_temp = self.RAMP_RATE[idx] * (delta_time / 60.0)
                if self.TARGET[idx] > self.RAMP_START_TEMP[idx]:
                    self.SETP[idx] = self.RAMP_START_TEMP[idx] + delta_temp
                    if self.SETP[idx] >= self.TARGET[idx]:
                        self.SETP[idx] = self.TARGET[idx]
                        self.RAMP_ST[idx] = 0
                else:
                    self.SETP[idx] = self.RAMP_START_TEMP[idx] - delta_temp
                    if self.SETP[idx] <= self.TARGET[idx]:
                        self.SETP[idx] = self.TARGET[idx]
                        self.RAMP_ST[idx] = 0

            # TODO - iterate Power Level
            if self.KRDG[ndx] <> self.SETP[idx]:
                self.HTR[idx] = self.SETP[idx] - self.KRDG[ndx]
                if self.HTR[idx] > 100.0:
                    self.HTR[idx] = 100.0
                elif self.HTR[idx] < -100.0:
                    self.HTR[idx] = -100.0

            # TODO - iterate Process Values (PV)
            self.KRDG[ndx] = (0.9 * self.KRDG[ndx] + 0.1 * self.SETP[idx])

    def doCommandCLS(self, cmd, args):
        print "Unimplemented Command: \"*CLS\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandESE(self, cmd, args):
        self.ESE = int(args[0]) & 0xFF
    def doQueryESE(self, cmd, args):
        self.write("%d" % self.ESE)
    def doQueryESR(self, cmd, args):
        self.write("%d" % self.ESR)
    def doQueryIDN(self, cmd, args):
        self.write(self.IDN)
    def doCommandOPC(self, cmd, args):
        self.OPC = 1
    def doQueryOPC(self, cmd, args):
        self.write("1")
    def doCommandRST(self, cmd, args):
        print "Unimplemented Command: \"*RST\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandSRE(self, cmd, args):
        self.SRE = int(args[0]) & 0xFF
    def doQuerySRE(self, cmd, args):
        self.write("%d" % self.SRE)
    def doQuerySTB(self, cmd, args):
        self.write("%d" % self.STB)
    def doQueryTST(self, cmd, args):
        self.write("%d" % self.TST)
    def doCommandWAI(self, cmd, args):
        print "Unimplemented Command: \"*WAI\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandALARM(self, cmd, args):
        if len(args) > 0:
            idx = ord(args[0]) - 64
            params = args[1:].join(",")
            if idx in self.ALARM:
                self.ALARM[idx] = params
    def doQueryALARM(self, cmd, args):
        if len(args) > 0:
            idx = ord(args[0]) - 64
        if idx in self.ALARM:
            self.write(self.ALARM[idx])
        else:
            self.write("0,1,500.0,0.0,0")
    def doQueryALARMST(self, cmd, args):
        if len(args) > 0:
            idx = ord(args[0]) - 64
            if idx in self.ALARMST:
                self.write(self.ALARMST[idx])
            else:
                self.write("0,0")
    def doCommandALMRST(self, cmd, args):
        for key in self.ALARMST.keys():
            self.ALARMST[key] = "0,0"
    def doCommandANALOG(self, cmd, args):
        key = args[0]
        if key < 1 or key > 2:
            key = 1
        self.ANALOG[key] = ",".join(args[1:])
        print "TODO implement Command: \"ANALOG\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryANALOG(self, cmd, args):
        key = args[0]
        if key < 1 or key > 2:
            key = 1
        self.write(self.ANALOG[key]) # TODO
        print "TODO implement Query: \"ANALOG?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryAOUT(self, cmd, args):
        key = args[0]
        if key < 1 or key > 2:
            key = 1
        self.write("%6.3f" % self.AOUT[key]) # TODO
        print "TODO implement Query: \"AOUT?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandBEEP(self, cmd, args):
        print "Unimplemented Command: \"BEEP\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryBEEP(self, cmd, args):
        print "Unimplemented Query: \"BEEP?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryBUSY(self, cmd, args):
        self.write("0")
    def doCommandCDISP(self, cmd, args):
        print "Unimplemented Command: \"CDISP\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryCDISP(self, cmd, args):
        print "Unimplemented Query: \"CDISP?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandCFILT(self, cmd, args):
        loop = int(args[0])
        if loop < 1:
            loop = 1
        if loop > 2:
            loop = 2
        self.CFILT[loop] = int(args[1])
    def doQueryCFILT(self, cmd, args):
        loop = int(args[0])
        if loop < 1:
            loop = 1
        if loop > 2:
            loop = 2
        self.write("%d" % self.CFILT[loop])
    def doCommandCLIMI(self, cmd, args):
        self.CLIMI = double(args[0])
    def doQueryCLIMI(self, cmd, args):
        self.write("%f" % self.CLIMI)
    def doCommandCLIMIT(self, cmd, args):
        loop = int(args[0])
        if loop < 1:
            loop = 1
        if loop > 2:
            loop = 2
        self.CLIMIT[loop] = ",".join(args[1:])
    def doQueryCLIMIT(self, cmd, args):
        loop = int(args[0])
        if loop < 1:
            loop = 1
        if loop > 2:
            loop = 2
        self.write("%s" % self.CLIMIT[loop])
    def doCommandCMODE(self, cmd, args):
        loop = int(args[0])
        if loop in self.CMODE:
            self.CMODE[loop] = int(args[1])
    def doQueryCMODE(self, cmd, args):
        loop = int(args[0])
        if loop in self.CMODE:
            self.write("%f" % self.CMODE[loop])
    def doCommandCOMM(self, cmd, args):
        self.COMM = ",".join(args)
    def doQueryCOMM(self, cmd, args):
        self.write("%f" % self.COMM)
    def doQueryCRDG(self, cmd, args):
        idx = ord(args[0]) - 64
        if idx in self.KRDG:
            if self.RANDOM > 0:
                self.write("%f" % (self.KRDG[idx] - 273.15 + random.uniform(-self.RANDOM, self.RANDOM)))
            else:
                self.write("%f" % (self.KRDG[idx] - 273.15))
        else:
            self.write("+000.0")
    def doCommandCRVDEL(self, cmd, args):
        print "Unimplemented Command: \"CRVDEL\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandCRVHDR(self, cmd, args):
        print "Unimplemented Command: \"CRVHDR\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryCRVHDR(self, cmd, args):
        key = int(args[0])
        if key in self.CRVHDR:
            self.write(self.CRVHDR[key])
        else:
            self.write("DT-336-1       ,STANDARD  ,1,+500.000,1") # TODO
        print "TODO implement Query: \"CRVHDR?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandCRVPT(self, cmd, args):
        key = int(args[0])
        if key < 1 or key > 20:
            key = 1
        idx = int(args[1])
        if idx < 1 or idx > 200:
            idx = 1
        # TODO set the Curve Point
        print "TODO implement Command: \"CRVPT\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryCRVPT(self, cmd, args):
        key = int(args[0])
        if key < 1 or key > 20:
            key = 1
        idx = int(args[1])
        if idx < 1 or idx > 200:
            idx = 1
        self.write("1.0E+01,1.0+E02") # TODO
        print "TODO implement Query: \"CRVPT?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandCRVSAV(self, cmd, args):
        pass
# CSET - see OUTMODE
    def doCommandDFLT(self, cmd, args):
        if args[0] == "99":
            print "Unimplemented Command: \"DFLT 99\" in \"" + cmd + " " + ",".join(args) + "\""
        else:
            print "Invalid Command: \"DFLT " + args[0] + "\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandDISPLAY(self, cmd, args):
        print "Unimplemented Command: \"DISPLAY\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryDISPLAY(self, cmd, args):
        print "Unimplemented Query: \"DISPLAY?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandDISPLOC(self, cmd, args):
        print "Unimplemented Command: \"DISPLOC\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryDISPLOC(self, cmd, args):
        print "Unimplemented Query: \"DISPLOC?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandDOUT(self, cmd, args):
        self.DOUT = int(args[0])
    def doQueryDOUT(self, cmd, args):
        self.write("%d" % self.DOUT)
    def doCommandFILTER(self, cmd, args):
        if len(args) > 0:
            if int(args[0]) in self.FILTER:
                keys = [int(args)]
            else:
                keys = self.FILTER.keys()
            params = args[1:].join(",")
            for key in keys:
                self.FILTER[key] = params
    def doQueryFILTER(self, cmd, args):
        idx = int(args[0])
        if idx in self.FILTER:
            self.write(self.FILTER[idx])
        else:
            raise IndexError
    def doQueryHTR(self, cmd, args):
        idx = int(args[0])
        if idx in self.HTR:
            self.write("%f" % self.HTR[idx])
        else:
            raise IndexError
    def doQueryHTRST(self, cmd, args):
        self.write("%d" % self.HTRST)
    def doQueryIEEE(self, cmd, args):
        self.write("%s" % self.IEEE)
    def doCommandIEEE(self, cmd, args):
        self.IEEE = args[0]
    def doQueryINCRV(self, cmd, args):
        idx = ord(args[0]) - 64
        if idx in self.INCRV:
            self.write(self.INCRV[idx])
        else:
            self.write("0")
    def doCommandINCRV(self, cmd, args):
        if len(args) > 1:
            idx = ord(args[0]) - 64
            if idx in self.INCRV:
                for key in keys:
                    self.INCRV[key] = args[1]
    def doQueryINTYPE(self, cmd, args):
        idx = ord(args[0]) - 64
        if idx in self.INTYPE:
            self.write(self.INTYPE[idx])
        else:
            self.write("0")
    def doCommandINTYPE(self, cmd, args):
        if len(args) > 1:
            idx = ord(args[0]) - 64
            if idx in self.INTYPE:
                for key in keys:
                    self.INTYPE[key] = ",".join(args[1:])
    def doQueryKEYST(self, cmd, args):
        self.write("%d" % self.KEYST)
        self.KEYST = 0
    def doQueryKRDG(self, cmd, args):
        idx = ord(args[0]) - 64
        if idx in self.KRDG:
            if self.RANDOM > 0:
                self.write("%f" % (self.KRDG[idx] + random.uniform(-self.RANDOM, self.RANDOM)))
            else:
                self.write("%f" % (self.KRDG[idx]))
        else:
            self.write("+000.0")
    def doQueryLDAT(self, cmd, args):
        self.write("3.000E+02") # TODO
        print "TODO implement Query: \"LDAT?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryLINEAR(self, cmd, args):
        self.write("1,1.0,1,3") # TODO
        print "TODO implement Query: \"LINEAR?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandLINEAR(self, cmd, args):
        print "Unimplemented Command: \"LINEAR\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryLOCK(self, cmd, args):
        self.write("%s" % self.LOCK)
    def doCommandLOCK(self, cmd, args):
        self.LOCK = args[0]
    def doQueryMDAT(self, cmd, args):
        response = "0"
        if len(args[0]) > 0:
            idx = int(args[0])
            if idx in self.MDAT:
                (minv, maxv, reset) = self.MDAT[idx].split(",")
                response = "%f,%f" % (float(minv), float(maxv))
        self.write(response)
    def doQueryMNMX(self, cmd, args):
        self.write("1") # TODO
        print "TODO implement Query: \"MNMX?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandMNMX(self, cmd, args):
        print "Unimplemented Command: \"MNMX\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandMNMXRST(self, cmd, args):
        print "Unimplemented Command: \"MNMXRST\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryMODE(self, cmd, args):
        print "Unimplemented Query: \"MODE?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandMODE(self, cmd, args):
        print "Unimplemented Command: \"MODE\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryMONITOR(self, cmd, args):
        print "Unimplemented Query: \"MONITOR?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandMONITOR(self, cmd, args):
        print "Unimplemented Command: \"MONITOR\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryMOUT(self, cmd, args):
        idx = int(args[0])
        self.write(self.MOUT[idx])
    def doCommandMOUT(self, cmd, args):
        print "Unimplemented Command: \"MOUT\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryOUTMODE(self, cmd, args):
        idx = int(args[0])
        if idx in self.OUTMODE:
            self.write(self.OUTMODE[idx])
        else:
            self.write(self.OUTMODE[1])
    def doCommandOUTMODE(self, cmd, args):
        idx = int(args[0])
        if idx in self.OUTMODE:
            newVal = self.mergeParams(3, self.OUTMODE[idx], ",".join(args[1:]))
            print "OUTMODE:", newVal
            self.OUTMODE[idx] = newVal
            self.LOOPINPUT[idx] = int(newVal.split(",")[1])
    def doQueryPID(self, cmd, args):
        idx = int(args[0])
        self.write(self.PID[idx])
    def doCommandPID(self, cmd, args):
        print "Unimplemented Command: \"PID\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryRANGE(self, cmd, args):
        idx = int(args[0])
        self.write(self.RANGE[idx])
    def doCommandRANGE(self, cmd, args):
        idx = int(args[0])
        val = int(args[1])
        self.RANGE[idx] = val
    def doQueryRAMP(self, cmd, args):
        idx = int(args[0])
        response = "%d,%f" % (self.RAMP_ON[idx], self.RAMP_RATE[idx])
        self.write(response)
    def doCommandRAMP(self, cmd, args):
        idx = int(args[0])
        ramp_on = int(args[1])
        if ramp_on == 0 or ramp_on == 1:
            self.RAMP_ON[idx] = ramp_on
            if ramp_on == 1:
                ramp_rate = float(args[2])
                if ramp_rate >= 0.001 and ramp_rate <= 100.0:
                    self.RAMP_RATE[idx] = ramp_rate
    def doQueryRAMPST(self, cmd, args):
        idx = int(args[0])
        response = "%d" % self.RAMP_ST[idx]
        self.write(response)
    def doQueryRDGPWR(self, cmd, args):
        self.write("1.000E-15") # TODO
        print "TODO implement Query: \"RDGPWR?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryRDGR(self, cmd, args):
        self.write("1.000E+03") # TODO
        print "TODO implement Query: \"RDGR?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryRDGRNG(self, cmd, args):
        self.write("1,1,19,0,0") # TODO
        print "TODO implement Query: \"RDGRNG?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandRDGRNG(self, cmd, args):
        print "Unimplemented Command: \"RDGRNG\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryRDGST(self, cmd, args):
        self.write("000")
        print "TODO implement Query: \"RDGST?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doQueryRELAY(self, cmd, args):
        idx = int(args[0])
        self.write(self.RELAY[idx])
    def doCommandRELAY(self, cmd, args):
        idx = int(args[0])
        if idx in self.RELAY:
            self.relay[idx] = ",".join(args[1:])
    def doQueryRELAYST(self, cmd, args):
        idx = int(args[0])
        self.write(self.RELAYST[idx])
    def doQuerySETP(self, cmd, args):
        idx = int(args[0])
        val = self.SETP[idx]
        self.write("%f" % val)
    def doCommandSETP(self, cmd, args):
        idx = int(args[0])
        val = float(args[1])
        if (val >= 0.0 and val <= 500.0):
            self.TARGET[idx] = val
            if self.RAMP_ON[idx] == 0:
                self.SETP[idx] = val
                self.RAMP_ST[idx] = 0
            else:
                self.RAMP_START_TEMP[idx] = self.SETP[idx]
                self.RAMP_START_TIME[idx] = time.time()
                self.RAMP_ST[idx] = 1
    def doQueryZONE(self, cmd, args):
        print "Unimplemented Query: \"ZONE?\" in \"" + cmd + " " + ",".join(args) + "\""
    def doCommandZONE(self, cmd, args):
        print "Unimplemented Command: \"ZONE\" in \"" + cmd + " " + ",".join(args) + "\""

if __name__ == '__main__':
    from LakeshoreProtocol import LakeshoreProtocol

    class TestFactory:
        def __init__(self):
            print self.__class__.__name__, "ctor"
            self.numProtocols = 0
        def write(self, data):
            print "test write:", data,
        def loseConnection(self):
            print "test lose connection"
    test_factory = TestFactory()
    test_device = Lakeshore336()
    test_protocol = LakeshoreProtocol(test_device, "\r\n")
    test_protocol.factory = test_factory
    test_protocol.transport = test_factory
    test_device.protocol = test_protocol
    test_device.protocol.connectionMade()
    test_device.protocol.dataReceived("*IDN?")
    test_device.protocol.dataReceived("*TST?")
    test_device.protocol.connectionLost("Dunno")
