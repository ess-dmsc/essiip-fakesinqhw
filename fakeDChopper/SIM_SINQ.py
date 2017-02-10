#!/usr/bin/python
# vim: ft=python ts=8 sts=4 sw=4 et autoindent smartindent nocindent
# author: Douglas Clowes (douglas.clowes@ansto.gov.au) 2014
#
# modified for SINQ chopper, Mark Koennecke (mark.koennecke@psi.ch)
# We simulate 3 minutes for each chopper change.... 
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import time

class Astrium_Chopper(LineReceiver):
    def __init__(self):
        print dir(self)
        print dir(self.transport)
        self.delimiter = '\r\n'
        self.speed = 4
        self.target = 4
        self.oldspeed = 4
        self.speed2 = 4
        self.target2 = 4
        self.oldspeed2 = 4
        self.speedchange = time.time() - 200
        self.ratio = 1
        self.phase = 12.8
        self.oldphase = 12.8
        self.targetphase = 12.8
        self.phasechange = self.speedchange
        self.dphas = .0

        # Number of seconds for a state change
        self.time_compression = 40.0


    def write(self, data):
        print "transmitted:", data
        self.transport.write(data)

    def calculatespeed(self):
        if time.time() < self.speedchange + self.time_compression:
            diff = time.time() - self.speedchange
            frac = diff / self.time_compression
            self.speed = int(self.oldspeed + frac*(self.target - self.oldspeed))
            self.speed2 = int(self.oldspeed + frac*(self.target2 - self.oldspeed2))
        else:
            self.speed = self.target
            self.speed2 = self.target2
            self.oldspeed = self.speed
            self.oldspeed2 = self.speed2

    def calculatephase(self):
        fr = (time.time() - self.phasechange) / self.time_compression
        print('fr: {:.4f}'.format(fr))
        if fr < 0:
            # should not happen except in rare leap second cases
            pass
        elif fr < 1:
            self.dphas = (1-fr) * self.oldphase + fr * self.targetphase
        else:
            self.dphas = self.targetphase
            self.oldphase = self.dphas
        

    def lineReceived(self, data):
        print "lineReceived:", data
        if data.startswith("asyst 1"):
            self.calculatespeed()
            self.calculatephase()
            self.write('asyst 1         ......valid\r\n')
            time.sleep(0.1)
            self.write(\
                'chopp_1;state async;amode Regel;nspee  ' \
                    + str(self.target) + \
                    ';aspee  ' +\
                    str(self.speed) +\
                    ';nphas   0.0;dphas  0.0;averl 5.2;spver  1996;'+\
                    'ratio 1;no_action   ;monit_1;vibra  0.2;'+\
                    't_cho   0.0;durch  0.0;vakum  0.0010;valve 0;sumsi 0;\r\n')
            time.sleep(0.1)
            self.write(\
                'chopp_2;state synch;amode Kalib;nspee  ' +\
                    str(self.target2) +\
                    ';aspee  ' +\
                    str(self.speed2) +\
                    ';nphas' + '%7.2f' % (self.targetphase) +
                    ';dphas' + '%7.2f' % (self.dphas) +
                    ';averl 4.0;spver  1996;ratio '+\
                    str(self.ratio) + ';no_action   ;monit_2;vibra  0.2;t_cho   0.0;' +\
                    'durch  0.0;vakum  0.0010;valve 0;sumsi 0;\r\n')
            return
        if data.startswith("nspee"):
            par = data.split()
            if len(par) < 3:
                self.write('not valid\r\n')
                return
            if par[1].isdigit():
                idx = int(par[1])
                if idx < 1 or idx > 2:
                    self.write('not valid\r\n')
                    return
                if par[2].isdigit():
                    val = int(par[2])
                else:
                    self.write('not valid\r\n')
                    return
                if idx == 1:
                    self.oldspeed = self.speed
                    self.target = val
                    self.oldspeed2 = self.speed2
                    self.target2 = int(val/self.ratio)
                else :
                    self.oldspeed2 = self.speed2
                    self.target2 = val
                self.write('valid\r\n')
                self.speedchange = time.time()
            else:
                self.write('not valid\r\n')
            return
        if data.startswith("ratio 2"):
            par = data.split()
            if len(par) < 3:
                print(len(par), par)
                self.write('not valid\r\n')
                return
            if par[2].isdigit():
                r = int(par[2])
                if r < 0 or r > 5:
                    self.write('not valid\r\n')
                    return
                self.ratio = r
                self.target2 = self.target/r
                self.speedchange = time.time()
                self.write('valid\r\n')
            else:
                print(par[2])
                self.write('not valid\r\n')
                return
        if data.startswith("nphas 2"):
            par = data.split()
            if len(par) < 3:
                print(len(par), par)
                self.write('not valid\r\n')
                return

            ph = float(par[2])
            if ph < 0 or ph > 360.:
                self.write('not valid\r\n')
                return
            self.oldphase = self.targetphase
            self.targetphase = ph
            self.phasechange = time.time()
            self.write('valid\r\n')

    def rawDataReceived(self, data):
        print "rawDataReceived:", data

    def connectionMade(self):
        print "connectionMade"

def main():
    factory = protocol.ServerFactory()
    factory.protocol = Astrium_Chopper
    reactor.listenTCP(60000, factory)
    reactor.run()

if __name__ == "__main__":
    main()
