#!/usr/bin/env python
#
# This is a simulator for the SANS velocity selector as used at SINQ
# It is from Astrium, is operated by that Turbo Pascal software and is
# as all Astrium devices, a one of a kind.
#
# We simulate 3 minutes for each velocity selector change....
#
# Mark Koennecke, March 2020
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import time

class Astrium_NVS(LineReceiver):
    def __init__(self):
        self.delimiter = b'\r\n'
        self.speed = 0
        self.target = 0
        self.oldspeed = 0
        self.speedchange = time.time() - 200

        # Number of seconds for a state change
        self.time_compression = 40.0


    def write(self, data):
        print("transmitted:", data)
        self.transport.write(data.encode())

    def calculatespeed(self):
        if time.time() < self.speedchange + self.time_compression:
            diff = time.time() - self.speedchange
            frac = diff / self.time_compression
            self.speed = int(self.oldspeed + frac*(self.target - self.oldspeed))
        else:
            self.speed = self.target
            self.oldspeed = self.speed        

    def lineReceived(self, data):
        print("lineReceived:", data)
        if data.startswith(b'???'):
            self.calculatespeed()
            time.sleep(0.2)
            self.write('???                                              \Status:REG/S_DREH: %d/I_DREH: %d/P_VERL:' \
            '0/STROM:  0.0/T_ROT: 17/T_VOR: 18/T_RUECK: 18/DURCHFL:2.4/VAKUUM:0.14984/BESCHL: 0.1/BCU: 0.0/Hz:' \
            '38/KOM: ENABLED/DATE: 29.4.2015/TIME: 12.34.35/\r\n' %(self.speed, self.speed))
            return
        if data.startswith(b'SST'):
            self.target = 3000
            self.speedchange = time.time() 
            self.oldspeed = self.speed
            self.write('')
            return
        if data.startswith(b'HAL'):
            self.target = 0
            self.speedchange = time.time() 
            self.oldspeed = self.speed
            self.write('')
            return
        if data.startswith(b'SDR'):
            par = data.split()
            if len(par) > 1:
                self.target = int(par[1])
                self.speedchange = time.time() 
                self.oldspeed = self.speed
                self.write('')
            return

    def rawDataReceived(self, data):
        print("rawDataReceived:", data)

    def connectionMade(self):
        print("connectionMade")

def main():
    factory = protocol.ServerFactory()
    factory.protocol = Astrium_NVS
    reactor.listenTCP(5050, factory)
    reactor.run()

if __name__ == "__main__":
    main()
