#!/usr/bin/env python
# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
# Author: Douglas Clowes (dcl@ansto.gov.au) 2013-06-03

from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.python import log, usage

from MercurySCPI import MercurySCPI as MYBASE
from MercuryFactory import MercuryFactory
from MercuryProtocol import MercuryProtocol
import os
import sys

sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),"../../util"))))
from displayscreen import Screen

class MyOptions(usage.Options):
    optFlags = [
            ["window", "w", "Create a display window"],
            ]
    optParameters = [
            ["logfile", "l", None, "output logfile name"],
            ["port", "p", None, "port number to listen on"],
            ]
    def __init__(self):
        usage.Options.__init__(self)
        self['files'] = []

    def parseArgs(self, *args):
        for arg in args:
            self['files'].append(arg)

class MyScreen(Screen):
    def __init__(self, stdscr):
        Screen.__init__(self, stdscr)

    def sendLine(self, txt):
        global myDev
        myDev.protocol = self
        myDev.dataReceived(txt)

    def write(self, txt):
        try:
            newLine = self.lines[-1] + " => " + txt
            del self.lines[-1]
            self.addLine(newLine)
        except:
            pass

class MYDEV(MYBASE):
    def __init__(self):
        MYBASE.__init__(self)
        print MYDEV.__name__, "ctor"

def device_display():
    global screen, myDev, myOpts, myPort, myFactory
    try:
        myDev.doIteration();
    except:
        raise

    if not myOpts["window"]:
        return

    try:
        rows, cols = screen.stdscr.getmaxyx()
        screen.stdscr.addstr(0, 0, "Lnks:%2d" % myFactory.numProtocols)
        screen.stdscr.addstr(0, 10, "Rnd:%6.3f" % myDev.RANDOM)
        screen.stdscr.addstr(0, 22, "Identity : %s (%d)" % (myDev.IDN, myPort))
        screen.stdscr.addstr(1, 0, "Valve: %8.4f%%" % myDev.valve_open)
        screen.stdscr.addstr(1, 20, "Helium: %8.4f%%" % myDev.hlev)
        screen.stdscr.addstr(1, 40, "Nitrogen: %8.4f%%" % myDev.nlev)
        base = 1
        screen.stdscr.addstr(base + 1, 0, "Sensor   :")
        screen.stdscr.addstr(base + 2, 0, "PV       :")
        screen.stdscr.addstr(base + 3, 0, "Setpoint :")
        screen.stdscr.addstr(base + 4, 0, "T Delta  :")
        screen.stdscr.addstr(base + 5, 0, "PV Delta :")
        for idx in myDev.CONFIG_SNSRS:
            if 12 + (idx - 1) * 12 > cols - 1:
                break
            screen.stdscr.addstr(base + 1, 12 + (idx - 1) * 12, "%8.3f" % myDev.Loops[idx].sensor)
        for idx in myDev.CONFIG_LOOPS:
            if 12 + (idx - 1) * 12 > cols - 1:
                break
            screen.stdscr.addstr(base + 2, 12 + (idx - 1) * 12, "%8.3f" % myDev.Loops[idx].pv)
            screen.stdscr.addstr(base + 3, 12 + (idx - 1) * 12, "%8.3f" % myDev.Loops[idx].setpoint)
            screen.stdscr.addstr(base + 4, 12 + (idx - 1) * 12, "%8.3f" % (myDev.Loops[idx].setpoint - myDev.Loops[idx].sensor))
            screen.stdscr.addstr(base + 5, 12 + (idx - 1) * 12, "%8.3f" % (myDev.Loops[idx].setpoint - myDev.Loops[idx].pid_delta))
    except:
        pass
    finally:
        try:
            screen.stdscr.refresh()
        except:
            pass

if __name__ == "__main__":
    global screen, myDev, myOpts, myPort, myFactory

    myOpts = MyOptions()
    try:
        myOpts.parseOptions()
    except usage.UsageError, errortext:
        print '%s: %s' % (sys.argv[0], errortext)
        print '%s: Try --help for usage details.' % (sys.argv[0])
        raise SystemExit, 1

    myDev = MYDEV()
    default_port = 7020
    myPort = default_port
    logfile = None

    if myOpts["port"]:
        myPort = int(myOpts["port"])
        if myPort < 1025 or myPort > 65535:
            myPort = default_port

    if myOpts["window"]:
        logfile = "/tmp/Fake_Mercury_%d.log" % (myPort)

    if myOpts["logfile"]:
        logfile = myOpts["logfile"]

    if logfile:
        log.startLogging(open(logfile, "w"))
    else:
        log.startLogging(sys.stdout)
        #log.startLogging(sys.stderr)

    if myOpts["window"]:
        import curses

        stdscr = curses.initscr()
        screen = MyScreen(stdscr)
        # add screen object as a reader to the reactor
        reactor.addReader(screen)

    myFactory = MercuryFactory(MercuryProtocol, myDev, "\r")
    lc = LoopingCall(device_display)
    lc.start(0.250)
    reactor.listenTCP(myPort, myFactory) # server
    reactor.run()
