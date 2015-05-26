#!/usr/bin/python
# vim: ft=python ts=8 sts=4 sw=4 et autoindent smartindent nocindent
# author: Douglas Clowes (douglas.clowes@ansto.gov.au) 2014
#
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet.task import LoopingCall

import os
import sys
import curses
sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),"../../util"))))
from displayscreen import Screen

devices = []

class Channel(object):
    def __init__(self):
        self.voltage = 0
        self.current = 0
        self.setpoint = 0
        self.ramp_speed = 255
        self.current_trip = 0
        self.voltage_limit = 100
        self.current_limit = 100
        self.status_word = "MAN"
        self.module = 0
        self.auto_start = 8
        self.polarity = "+"

    def iterate(self):
        if self.voltage < self.setpoint:
            self.voltage += min(self.ramp_speed, self.setpoint - self.voltage)
        elif self.voltage > self.setpoint:
            self.voltage -= min(self.ramp_speed, self.voltage - self.setpoint)

    def set(self, data):
        if data[0] == "D":
            self.setpoint = int(data[3:])
        if data[0] == "V":
            self.ramp_speed = int(data[3:])
        if data[0] == "L":
            self.current_trip = int(data[3:])
        if data[0] == "A":
            self.auto_start = int(data[3:])

    def get(self, data):
        if data[0] == "U":
            return "%s%04d" % (self.polarity, self.voltage)
        if data[0] == "I":
            return "%04d-6" % self.current
        if data[0] == "M":
            return "%03d" % self.voltage_limit
        if data[0] == "D":
            return "%04d" % self.setpoint
        if data[0] == "V":
            return "%03d" % self.ramp_speed
        if data[0] == "G":
            return "S%s=%s" % (data[1], self.status_word)
        if data[0] == "L":
            return "%04d" % self.current_trip
        if data[0] == "S":
            return "%s" % self.status_word
        if data[0] == "T":
            return "%03d" % self.module
        if data[0] == "A":
            return "%d" % self.auto_start

class NHQ_200(LineReceiver):
    def __init__(self):
        self.delimiter = '\r\n'
        self.channels = {}
        self.channels["1"] = Channel()
        self.channels["2"] = Channel()
        self.channels["2"].polarity = "-"
        self.setRawMode()
        self.line = ""

    def iterate(self):
        for idx in self.channels.keys():
            self.channels[idx].iterate()

    def write(self, data):
        sent = data
        print "transmitted:", repr(sent)
        self.transport.write(sent)

    def lineReceived(self, data):
        print "lineReceived:", data
        if data == "#":
            self.write("123456;3.14;6000;1000uA");
            self.write(self.delimiter);
            return
        if data == "W":
            self.write("000")
            self.write(self.delimiter);
            return
        if data[1] not in self.channels:
            return
        if len(data) > 2 and data[2] == "=":
            if data[0] in "DVLA":
                self.channels[data[1]].set(data)
                self.write(self.delimiter);
            return
        if data[0] in "UIMDVGLSTA":
            result = self.channels[data[1]].get(data)
            self.write(result)
            self.write(self.delimiter);
            return
        print "Unimplemented command for: '%s'" % data
        return

    def rawDataReceived(self, data):
        #print "rawDataReceived:", repr(data)
        self.transport.write(data)
        self.line += data
        if self.line.endswith(self.delimiter):
            self.line = self.line[:-len(self.delimiter)]
            self.lineReceived(self.line)
            self.line = ""

    def connectionMade(self):
        print "connectionMade"
        devices.append(self)

    def connectionLost(self, reason):
        print "connectionLost"
        devices.remove(self)

def device_iterator():
    global devices
    for dev in devices:
        dev.iterate()

def display_iterator():
    global screen, devices

    try:
        rows, cols = screen.stdscr.getmaxyx()
        screen.stdscr.clear()
        col = 0
        for base in [0, 12]:
            screen.stdscr.addstr(base +  1, 0, "Voltage : ")
            screen.stdscr.addstr(base +  2, 0, "Current : ")
            screen.stdscr.addstr(base +  3, 0, "Setpoint: ")
            screen.stdscr.addstr(base +  4, 0, "Ramp    : ")
        for dev in devices:
            col += 1
            screen.stdscr.addstr(0, 12 * col, "Top TODO")
            for chan, base in [("1", 0), ("2", 12)]:
                try:
                    if dev.channels[chan].polarity == "-":
                        voltage = - dev.channels[chan].voltage
                    else:
                        voltage = + dev.channels[chan].voltage
                    screen.stdscr.addstr(base + 1, 12 * col, "%6d" % voltage)
                    screen.stdscr.addstr(base + 2, 12 * col, "%6d" % dev.channels[chan].current)
                    screen.stdscr.addstr(base + 3, 12 * col, "%6d" % dev.channels[chan].setpoint)
                    screen.stdscr.addstr(base + 4, 12 * col, "%6d" % dev.channels[chan].ramp_speed)
                except:
                    pass
    except:
        raise
    finally:
        try:
            screen.stdscr.refresh()
        except:
            pass

class MyScreen(Screen):
    def __init__(self, stdscr):
        Screen.__init__(self, stdscr)

    def sendLine(self, txt):
        global devices

    def write(self, txt):
        try:
            newLine = self.lines[-1] + " => " + txt
            del self.lines[-1]
            self.addLine(newLine)
        except:
            pass

def main():
    global screen
    import argparse
    parser = argparse.ArgumentParser(description="Fake NHQ-20x device")
    parser.add_argument('instrument', help='The instrument name', nargs='*')
    parser.add_argument('-p', '--port',\
            help='Port on which to listen',\
            type=int, default=60000)
    parser.add_argument('-v', '--verbose',\
            help='Print lots of stuff',\
            action='store_true', default=False)
    parser.add_argument('-w', '--window',\
            help='Create a display window',\
            action='store_true', default=False)
    args = parser.parse_args()
    log.startLogging(open(("/tmp/Fake_NHQ.log"), "w"))
    if args.verbose:
        print "Args:", args
        Verbose = True

    if (args.window):
        stdscr = curses.initscr()
        screen = MyScreen(stdscr)
        reactor.addReader(screen)
        disp_iter = LoopingCall(display_iterator)
        disp_iter.start(0.5)

    dev_iter = LoopingCall(device_iterator)
    dev_iter.start(1.0)
    factory = protocol.ServerFactory()
    factory.protocol = NHQ_200
    reactor.listenTCP(args.port, factory)
    reactor.run()

if __name__ == "__main__":
    main()
