#!/usr/bin/python
# 
# fake Nanotec controller
#
# Any number of motors can be on a given controller channel. The Nanotecs 
# sit on a RS-485 bus. Thus this requires an initalisation file containing 
# the numbers of the motor and their min and maximum values. 
#
# Mark Koennecke, July 2015
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import time
from nanotecmotor import NanotecMotor
import sys
import string

initFile = None

class NanotecController(LineReceiver):
    def __init__(self):
        self.delimiter = '\r'
        self.motors = {}
        if initFile != None:
            self.loadConfig(initFile)

    def write(self, data):
        print "transmitted:", data
        if self.transport is not None: 
            self.transport.write(data)

    def splitCommand(self,data):
        idx = 1
        motno = ''
        while data[idx] in string.digits:
            motno += data[idx]
            idx = idx + 1

        com = data[idx]
        par = data[idx+1:]
        print(par)
        if len(par) <= 0:
            par = 'none'
        print('Received motno, com, par ' + motno + ', ' + com + ', ' + par)
        return motno,com,par

    def lineReceived(self, data):
        data = data.strip()
        print "lineReceived:", data

        if not data.startswith('#'):
            print('Ignoring invalid line ' + data)
            return

        motno,com,par = self.splitCommand(data)
        if motno in self.motors:
            result = self.motors[motno].doCommand(com,par)
            self.write(result + '\r')


    def loadConfig(self,filename):
        inf = open(filename,'r')
        for line in inf:
            if line.startswith('#'):
                continue
            l = line.split()
            if len(l) >= 3:
                self.motors[l[0]] = NanotecMotor(l[0],l[1],l[2])
            else:
                print('Mal formatted initialisation line ' + line)
        inf.close()
         

def main(argv):
    global initFile

    if len(argv) < 3:
        print('Usage\n\tnanotecController portno inifile\n')
        exit()

    port = int(argv[1])
    initFile = argv[2]

    factory = protocol.ServerFactory()
    factory.protocol = NanotecController
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)
