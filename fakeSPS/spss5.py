#!/usr/bin/python
# 
# fake SINQ SPS S5. This is a Siemens SPS S5 with a custom RS-232 interface and
# protocol as used at SINQ. The protocol is very simple. What is instrument
# specific is what happens when you set one of the digital inputs. Currently,
# only the AMOR case is implemented. 
#
#
# Mark Koennecke, August 2016
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import time
import sys

class SPSS5(LineReceiver):
    def __init__(self):
        self.b1 = 1
        self.b2 = 0
        self.b3 = 0
        self.b4 = 0
        self.b5 = 5
        self.b6 = 0
        self.b7 = 7
        self.b8 = 0
        self.b9 = 0
        self.b10 = 0
        self.b11 = 0
        self.b12 = 0
        self.b13 = 0
        self.b14 = 0
        self.b15 = 0
        self.b16 = 0
        self.a1 = 1
        self.a2 = 2
        self.a3 = 3
        self.a4 = 4
        self.a5 = 5
        self.a6 = 6
        self.a7 = 7
        self.a8 = 8
        
    def write(self, data):
        print "transmitted:", data
        if self.transport is not None: 
            self.transport.write(data+'\n')
    
    def lineReceived(self, data):
        print "lineReceived:", data
        data = data.lower().strip()

        if data.startswith('r'):
            self.write('R %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d %3.3d\r'
                       % (self.b1, self.b2,self.b3,self.b4,self.b5,self.b6,self.b7,self.b8,self.b9,self.b10,self.b11,
                          self.b12,self.b13,self.b14,self.b15,self.b16))
            return

        if data.startswith('a'):
            self.write('A %5.5d %5.5d %5.5d %5.5d %5.5d %5.5d %5.5d %5.5d\r'
                       % (self.a1, self.a2,self.a3,self.a4,self.a5,self.a6,self.a7,self.a8))
            return

        if data.startswith('s'):
            if len(data) < 5:
                self.write('?PAR\r')
                return
            byte = int(data[1:4])
            bit = int(data[4])
            self.doPush(byte,bit)
            self.write(data + '\r')
            return

    def doPush(self,byte,bit):
        # shutter
        if byte == 0 and bit == 0:
            if self.b5 == 5:
                self.b5 = 0
            else:
                self.b5 = 5
            return
        # laser light
        if byte == 0 and bit == 1:
            if self.b16 == 0:
                self.b16 = 129
            else:
                self.b16 = 0
            return
        # RF flipper
        if byte == 0 and bit == 7:
            if self.b13 == 0:
                self.b13 = 128
            else:
                self.b13 = 0
            return
        
                
def main(argv):
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 63000

    factory = protocol.ServerFactory()
    factory.protocol = SPSS5
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)
