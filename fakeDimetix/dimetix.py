#!/usr/bin/python
# 
# This is a simulation for a Dimetix laser distance measuring device.
# Basically you switch on a laser and then measure. A manual of the device
# is available in the very directory where this source file resides. In addition
# to the dimetix command set, there is a command which allows to set the readback
# value from the outside. This is there in order to support a simulation of the real
# device which delivers distances depending on the position of a motor.
#
# At AMOR this dimetix device is used to measure the position of various beamline
# components on the optical bench. To this purpose each component carries a little mirror
# attached at a height unique to each component. Thus, by moving the dimetix distance
# measuring device with a motor, we can determine the position of all beamline
# components with sufficient accuracy. 
#
# Mark Koennecke, August 2016
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import time
import sys

laseron = False
Readback = 22

class Dimetix(LineReceiver):
    def __init__(self):
        pass
        
    def write(self, data):
        print "transmitted:", data
        if self.transport is not None: 
            self.transport.write(data+'\r\n')
    
    def lineReceived(self, data):
        global laseron, Readback
        print "lineReceived:", data
        data = data.lower().strip()

        if data.startswith('s0o'):
            laseron = True
            self.write('g0?')
            return
            
        if data.startswith('s0p'):
            laseron = False
            self.write('g0?')
            return

        if data.startswith('s0g'):
            if laseron:
                self.write('g0g+' + str(Readback))
            else:
                self.write('g0@E213')
            return

        if data.startswith('setval'):
            l = data.split()
            Readback = int(l[1])
            self.write('g0?')
            return
            

        self.write('g0@E203')
        return
        
                
def main(argv):
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 64000

    factory = protocol.ServerFactory()
    factory.protocol = Dimetix
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)
