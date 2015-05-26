# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
# Fake Mercury Temperature Controller Protocol
#
# Author: Douglas Clowes 2014
#
from twisted.internet.protocol import Protocol

class MercuryProtocol(Protocol):
    """Protocol object used by the Twisted Infrastructure to handle connections"""

    def __init__(self, theDevice, theTerminator = "\r\n"):
        print MercuryProtocol.__name__, "ctor"
        self.device = theDevice
        self.response = ""
        self.term = theTerminator

    def write(self, response):
        self.response = self.response + response

    def connectionMade(self):
        self.pdu = ""
        self.response = ""
        self.device.protocol = self
        self.factory.numProtocols = self.factory.numProtocols + 1
        print "connectionMade:", self.factory.numProtocols
        if self.factory.numProtocols > 2:
            print "Too many connections - rejecting"
            self.transport.write("Too many connections, try later" + self.term)
            self.transport.loseConnection()
        else:
            self.transport.write(("Welcome connection %d" % self.factory.numProtocols) + self.term)

    def connectionLost(self, reason):
        print "connectionLost:", self.factory.numProtocols, reason
        self.factory.numProtocols = self.factory.numProtocols - 1

    def lineReceived(self, data):
        print "lineReceived - len:", len(data), data
        self.device.protocol = self
        self.device.dataReceived(data)

    def dataReceived(self, data):
        print "dataReceived - len:", len(data), data
        for c in data:
            if  c == "\r" or c == ";" or c == "\n":
                if len(self.pdu) > 0:
                    self.lineReceived(self.pdu)
                    self.pdu = ""
                if c == ";":
                    if len(self.response) > 0 and self.response[-1] != ";":
                        self.response = self.response + ";"
                else:
                    if len(self.response) > 0:
                        if self.response[-1] == ";":
                            self.response = self.response[:-1]
                    if len(self.response) > 0:
                        print "Protocol Response: %s" % self.response
                        self.transport.write(self.response + self.term)
                        self.response = ""
            else:
                self.pdu = self.pdu + c

if __name__ == '__main__':
    class TestDevice:
        def __init__(self):
            print self.__class__.__name__, "ctor"
        def dataReceived(self, pdu):
            print "test device data received:", pdu
            self.protocol.write("test device response")
    class TestFactory:
        def __init__(self):
            self.numProtocols = 0
        def write(self, data):
            print "test write:", data,
        def loseConnection(self):
            print "test lose connection"
            self.protocol.connectionLost("Factory")
    myTerm = "\r\n"
    test_device = TestDevice()
    test_factory = TestFactory()
    test_protocol = MercuryProtocol(test_device, myTerm)
    test_factory.protocol = test_protocol
    test_protocol.factory = test_factory
    test_protocol.transport = test_factory
    test_protocol.connectionMade()
    test_protocol.connectionMade()
    test_protocol.connectionMade()
    test_protocol.connectionLost("Dunno")
    test_protocol.dataReceived("READ:DEV:DB7.T1:TEMP:SIG:TEMP" + myTerm + "READ:DEV:DB7.T1:TEMP:NICK;READ")
    test_protocol.dataReceived(":DEV:DB7.T1:TEMP")
    test_protocol.dataReceived(":NICK" + myTerm)
    test_protocol.connectionLost("Dunno")
