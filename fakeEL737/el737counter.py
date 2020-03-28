#!/usr/bin/python
#
# fake SINQ EL737 counter box
#
# I am using 1000cts/sec for m1, 500 for m2, 300 for m3 and 2000 for m4
#
# Mark Koennecke, July 2015
# Michele Brambilla    2016
# Nikhil Byiani        2017
# ----------------------------------------------------------------------
import os
import sys
import time
import logging

import generator
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver


class EL737Controller(LineReceiver):

    def __init__(self):
        self.remotestate = 0
        self.delimiter = '\r'
        self.mode = 'timer'
        self.preset = .0
        self.starttime = time.time()
        self.endtime = time.time()
        self.counting = False
        self.mypaused = False
        self.pausestart = 0
        self.pausedTime = 0.
        self.threshold = 0
        self.thresholdcounter = 1
        self.startFailure = False
        self.runFailure = False
        self.atRunFailure = False
        self.readFailure = False
        self.recover = False
        self.proc = MyPIPE()
        self.generator = generator.Generator()
        self.generator_path = None

    def set_path(self, path):
        self.generator_path = path

    def write(self, data):
        logging.info("transmitted: %s", data)
        if self.transport is not None:
            self.transport.write(data)

    def to_process(self, data):
        logging.info("transmitted to process:", data)
        try:
            if self.transport is not None:
                self.proc.transport.write(data.encode())
        except Exception as e:
            logging.error(e, exc_info=True)

    def calculateCountStatus(self):
        if self.counting and not self.mypaused:
            runtime = time.time() - self.starttime - self.pausedTime
            print(str(runtime) + ' versus ' + str(self.preset))
            if self.mode == 'timer':
                if runtime >= self.preset:
                    self.counting = False
                    self.endtime = self.starttime + self.preset
                    self.pausedTime = 0
                    self.to_process('pause\r')
                elif self.runFailure and not self.recover and runtime >= self.preset * 0.2:
                    self.atRunFailure = True
            else:
                if runtime * 1000 >= self.preset:
                    self.counting = False
                    self.endtime = self.starttime + self.preset / 1000
                    self.to_process('pause\r')
                elif self.runFailure and not self.recover and runtime * 1000 >= self.preset * 0.2:
                    self.atRunFailure = True

        if self.atRunFailure:
            self.write('?92\r')
            self.counting = False
            self.endtime = time.time()

        logging.debug('count flag after calculateCountStatus %s' + str(self.counting))

    def calculateFailureStatus(self):
        if not self.recover:
            if self.startFailure:
                self.write('?91\r')
                return True
            elif self.atRunFailure:
                self.write('?92\r')
                return True
            elif self.readFailure:
                self.write('?93\r')
                return True
        else:
            self.startFailure = False
            self.runFailure = False
            self.atRunFailure = False
            self.readFailure = False
            self.recover = False
            return False

    def lineReceived(self, data):
        logging.info("lineReceived: %s", data)

        orig = data.strip()
        data = data.lower().strip()
        g = self.generator

        if self.remotestate == 0:
            if data.startswith('rmt 1'):
                self.remotestate = 1
                self.write("\r")
            else:
                self.write("?OF\r")
            return

        if self.remotestate == 1:
            if data.startswith('echo 2'):

                try:
                    g.find(self.generator_path)
                    reactor.spawnProcess(self.proc, g.exe, args=orig.split()[2:], env=os.environ)
                except Exception as what:
                    logging.error(what, exc_info=True)
                    self.remotestate = 0

                self.remotestate = 2
                self.write("\r")
            else:
                self.write("?OF\r")
            return

        if self.remotestate == 2:

            if data.startswith('rmt 1') or data.startswith('echo'):
                self.write('\r')
                return
            arguments = data.split()

            if data.startswith('mp'):

                if self.startFailure and not self.recover:
                    self.write('?91\r')
                    return
                if len(arguments) < 2:
                    self.write("argument required\r")
                    return
                self.mode = 'monitor'
                self.preset = float(arguments[1])
                self.starttime = time.time()
                self.mypaused = False
                self.pausedTime = 0.
                self.counting = True
                self.write('\r')
                self.to_process('run\r')
                return

            if data.startswith('tp'):
                if self.startFailure and not self.recover:
                    self.write('?91\r')
                    return
                self.mode = 'timer'
                if len(arguments) < 2:
                    self.write("argument required\r")
                    return
                self.preset = float(arguments[1])
                self.starttime = time.time()
                self.mypaused = False
                self.pausedTime = 0.
                self.counting = True
                self.write('\r')
                self.to_process('run\r')
                return

            if data.startswith('st'):
                self.counting = False
                self.endtime = time.time()
                self.write('\r')
                self.to_process('stop\r')
                return

            if data.startswith('ps'):
                self.counting = True
                self.mypaused = True
                self.pausestart = time.time()
                self.write('\r')
                self.to_process('pause\r')
                return

            if data.startswith('rt'):
                if len(arguments) < 2:
                    self.write("argument required\r")
                    return
                self.to_process('rate\r')
                self.to_process(arguments[1])
                return

            if data.startswith('co'):
                if not self.mypaused:
                    pass
                else:
                    self.mypaused = False
                    self.pausedTime += time.time() - self.pausestart
                self.to_process('run\r')
                self.write('\r')
                return

            if data.startswith('dl'):
                # if len(arguments) < 2:
                #     self.write("argument required\r")
                #     return
                if len(arguments) >= 3:
                    self.threshold = float(arguments[2])
                    self.write('\r')
                else:
                    self.write(str(self.threshold) + '\r')

            if data.startswith('dr'):
                if len(arguments) >= 2:
                    self.thresholdcounter = int(arguments[1])
                    self.write('\r')
                else:
                    self.write(str(self.thresholdcounter) + '\r')

            if data.startswith('rs'):
                if self.calculateFailureStatus():
                    return
                self.calculateCountStatus()
                if self.counting:
                    if self.mypaused:
                        if self.mode == 'timer':
                            self.write('9\r')
                        else:
                            self.write('10\r')
                    else:
                        if self.mode == 'timer':
                            self.write('1\r')
                        else:
                            self.write('2\r')
                else:
                    self.write('0\r')
                return

            if data.startswith('ra'):
                if self.calculateFailureStatus():
                    return
                self.calculateCountStatus()
                if self.counting:
                    if self.mypaused:
                        pausetime = time.time() - self.pausestart
                    else:
                        pausetime = self.pausedTime
                    diff = time.time() - self.starttime - pausetime
                else:
                    diff = self.endtime - self.starttime
                rlist = []
                rlist.append(str(diff))
                rlist.append(str(int(diff * 1000)))
                rlist.append(str(int(diff * 1500)))
                rlist.append(str(int(diff * 500)))
                rlist.append(str(int(diff * 300)))
                rlist.append(str(int(diff * 2000)))
                rlist.append('0')
                rlist.append('0')
                rlist.append('0')
                rastring = ' '.join(rlist)
                self.write(rastring + '\r')
                return

            if data.startswith('xs'):
                self.startFailure = True
                self.write("Start failure activated\r")
                return

            if data.startswith('xr'):
                self.runFailure = True
                self.write("Run failure activated\r")
                return

            if data.startswith('xd'):
                self.readFailure = True
                self.write("Read failure activated\r")
                return

            if data.startswith('rc'):
                self.recover = True
                self.write("Recover activated\r")
                return

            if data.startswith('id'):
                self.write('EL737 Neutron Counter V8.02\r')
                return

            self.write('?2\r')

    def connectionLost(self, reason):
        self.to_process('exit\r')
        time.sleep(1)
        self.proc.transport.signalProcess('KILL')
        logging.info("Goodbye... %s",reason)


class MyPIPE(protocol.ProcessProtocol):

    def connectionMade(self):
        logging.info("  Connection made")

    def childDataReceived(self, childFD, data):
        print("Message from %s", childFD, ":")
        print(data)

    def connectionLost(self, reason):
        logging.info("Goodbye...")

    def outReceived(self, data):
        print("out : ", data)

    def errReceived(self, data):
        print("err : ", data)

    def processExited(self, reason):
        if reason.value.exitCode != 0:
            print("exit : ", reason.value)
        else:
            print("exit")

    def processEnded(self, reason):
        logging.info("process ended : ", reason.value)


def main(argv):
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 62000

    factory = protocol.ServerFactory()
    factory.protocol = EL737Controller
    if len(argv) > 2:
        factory.protocol.generator_path = argv[2]

    reactor.listenTCP(port, factory)
    reactor.run()


if __name__ == "__main__":
    main(sys.argv)
