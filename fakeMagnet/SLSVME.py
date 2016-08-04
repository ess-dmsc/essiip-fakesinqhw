#!/usr/bin/python
"""
  This is a simulator for a very special PSI Magnet interface. It uses the PSI DSP magnets from SLS. This is
  interfaced via a special communications card and VME to a MEN-A12 VME computer. There runs a little program
  which reads commands from stdin, does things to the magnets and responds on stdout. This little program
  is then networked through inetd.

  Mark Koennecke, July 2016
"""
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
from Magnet import Magnet
import sys

class SLSVME(LineReceiver):
    def __init__(self):
        self.magnets = {}
        """
          This is the configuration for AMOR. As this is so special, it is hardcoded.
          But the thing can take up to 6 magnets if pushed. Change this to another
          configuration scheme if this is used any where else then AMOR
        """
        self.magnets['1'] = Magnet(-40.,40.)
        self.magnets['2'] = Magnet(-100.,100.)
        self.magnets['3'] = Magnet(-40.,40.)
        self.magnets['4'] = Magnet(0.,0.)
        self.magnets['5'] = Magnet(0.,0.)
        self.magnets['6'] = Magnet(0.,0.)
     
 
    def write(self, data):
        print "transmitted:", data
        if self.transport is not None: 
            self.transport.write(data + '\n')

    def doRead(self,magnet, comlist):
        if len(comlist) < 3:
            self.write('ERROR: no parameter to read found')
            return
        if comlist[2] == 'cur':
            value = magnet.cur
        elif comlist[2] == 'err':
            value = magnet.err
        elif comlist[2] == 'errtext':
            value = magnet.errText
        elif comlist[2] == 'onoff':
            value = magnet.onoff
            if value == 1:
                value = 'on'
            else:
                value = 'off'
        elif comlist[2] == 'hl':
            value = magnet.hl
        elif comlist[2] == 'll':
            value = magnet.ll
        else:
            self.write('ERROR: parameter ' + comlist[2] + ' unknown')
            return
        self.write(comlist[1] + ' ' + comlist[2] + ' ' + str(value))
        return    
    
    def doWrite(self,magnet, comlist):
       if comlist[2] == 'on':
           magnet.onoff = 1
           self.write('OK')
           return
       elif comlist [2] == 'off':
           magnet.onoff = 0
           self.write('OK')
           return
       else:
           pass
           
       if len(comlist) < 4:
            self.write('ERROR: no value to set found')
            return
       if comlist[2] == 'cur':
            stat = magnet.setcur(float(comlist[3]))
            self.write(stat)
            return
       else:                
            self.write('ERROR: no parameter to write recognized')
            return
                       
    def lineReceived(self, data):
        print "lineReceived:", data
        data = data.lower().strip()

        comlist = data.split()
        
        if not comlist[1] in self.magnets:
            self.write('ERROR: power supply number out of range, 1-6 allowed')
            return

        magnet = self.magnets[comlist[1]]

        if comlist[0] == 'r':
            self.doRead(magnet,comlist)
            return
        elif comlist[0] == 'w':
            self.doWrite(magnet, comlist)
            return
        else:
            self.write('ERROR: command not understood')
            return    
                

         

def main(argv):
    global initFile
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 6666

    factory = protocol.ServerFactory()
    factory.protocol = SLSVME
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)

