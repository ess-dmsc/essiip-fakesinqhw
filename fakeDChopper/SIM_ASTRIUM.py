#!/usr/bin/python
# vim: ft=python ts=8 sts=4 sw=4 et autoindent smartindent nocindent
# author: Douglas Clowes (douglas.clowes@ansto.gov.au) 2014
#
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
users = {"Bilby":"RwN"}

class Astrium_Chopper(LineReceiver):
    def __init__(self):
        print dir(self)
        print dir(self.transport)
        self.delimiter = '\r'
        self.state = 0
        # TODO

    def write(self, data):
        print "transmitted:", data
        self.transport.write(data)

    def lineReceived(self, data):
        print "lineReceived:", data
        if self.state == 1: # expecting user:
            if data.startswith("user:"):
                uid = data.split(':', 1)[1]
                if uid in users:
                    self.state = 2
                    self.uid = uid
                    self.write("#SES#Fill in your password")
                    return
            self.write("#SES#Fill in your user ID")
        if self.state == 2: # expecting password:
            if data.startswith("password:"):
                pwd = data.split(':', 1)[1]
                if pwd == users[self.uid]:
                    self.state = 3
                    self.write("#SES#Hello")
                    return
        if self.state == 3: # expecting command
            if data.startswith("#SOS#STATE "):
                unit = data.split(' ', 1)[1]
                print "Unit:", repr(unit)
                if unit.isdigit():
                    unit = int(unit)
                    if not (1 <= unit <= 4):
                        self.write("#SOS#NCCEPT CH NO "\
                                + str(unit)\
                                + ": NOT VALID")
                        return
                self.write(\
                        "#SOS#ACCEPT CH= "\
                        + str(unit)\
                        + "# State= Synchron."\
                        + "#ASPEED= 0"\
                        + "#RSPEED= 0"\
                        + "#APHASE= -0.7" + str(unit)\
                        + "#RPHASE= 0"\
                        + "#AVETO = 0"\
                        + "#DIR   =  CW"\
                        + "#MONIT = ok"\
                        + "#FLOWR = 3.7"\
                        + "#WTEMP = 14.2"\
                        + "#MTEMP = 18.1"\
                        + "#MVIBR = 0.0"\
                        + "#MVACU = 0.0022"\
                        + "#DATE  = "\
                        + "9/10/2009"\
                        + "#TIME  = "\
                        + "4:48:36 PM"\
                        + "#")
                return
            if data.startswith("#SOS#"):
                self.write(\
                        "#SOS#NCCEPT "\
                        + "garbag"\
                        + ": UNKOWN CMD")
    def rawDataReceived(self, data):
        print "rawDataReceived:", data

    def connectionMade(self):
        print "connectionMade"
        self.write("#SES#Fill in your user ID")
        self.state = 1

def main():
    factory = protocol.ServerFactory()
    factory.protocol = Astrium_Chopper
    reactor.listenTCP(60000, factory)
    reactor.run()

if __name__ == "__main__":
    main()
