#!/usr/bin/python
# 
# fake SINQ EL734 controller
#
# There are some interesting features here:
#
#  The initialisation via the global variable is a hack. It is necessary 
#  because twisted makes a complete new EL734controller object per 
#  connection. This also means that I cannot simulate errors by sending 
#  a code from another connection.  
#
# Mark Koennecke, June 2015
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import time
from el734motor import EL734Motor
import sys

initFile = None

class EL734Controller(LineReceiver):
    def __init__(self):
        self.remotestate = 0
        self.delimiter = '\r'
        self.motors = {}
        for i in range(1,13):
            no = "%d" % i
            self.motors[no] = EL734Motor()
        if initFile != None:
            self.loadConfig(initFile)

    def write(self, data):
        print "transmitted:", data
        if self.transport is not None: 
            self.transport.write(data)

    def lineReceived(self, data):
        print "lineReceived:", data
        data = data.lower().strip()

        if self.remotestate == 0:
            if data.startswith('rmt 1'):
                self.remotestate = 1
                self.write("\r")
            else:
                self.write("?loc\r")
            return

        if self.remotestate == 1:
            if data.startswith('echo 0'):
                self.remotestate = 2
                self.write("\r")
            else:
                self.write("?loc\r")
            return

        if self.remotestate == 2:
           if data.startswith('id'):
               self.write('STPMC EL734 V0.0.0\r')
               return

           if data.startswith('rmt 1') or data.startswith('echo'):
               self.write('\r')
               return

           tlist = data.split()
           if len(tlist) < 2:
               self.write('?adr\r')
               return
           key = tlist[0]
           motno = tlist[1]
           if not motno in self.motors.keys():
               self.write('?adr\r')
               return

           if data.startswith('h'):
               print('Processing limits')
               if len(tlist) > 2:
                   txt = self.motors[tlist[1]].setlimits(float(tlist[2]),float(tlist[3]))
                   self.write('\r')
               else:
                   lims = self.motors[tlist[1]].getlimits()
                   self.write(str(lims[0]) + ' ' + str(lims[1]) + '\r')
               return

           
           if len(tlist) > 2:
               arg = ' '.join(tlist[2:])
               txt = self.motors[motno].setpar(key,arg)
           else:
               txt = self.motors[motno].getpar(key)
           self.write(txt + '\r')
           return

    def loadConfig(self,filename):
        self.remotestate = 2
        inf = open(filename,'r')
        for line in inf:
            print(line)
            self.lineReceived(line)
        inf.close()
        self.remotestate = 0
         

def main(argv):
    global initFile
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 61000

    if len(argv) > 2:
        initFile = argv[2]

    factory = protocol.ServerFactory()
    factory.protocol = EL734Controller
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)
