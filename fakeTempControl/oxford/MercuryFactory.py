# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
# Fake Mercury Temperature Controller Factory
#
# Author: Douglas Clowes 2014
#
from twisted.internet.protocol import ServerFactory

class MercuryFactory(ServerFactory):
    """Factory object used by the Twisted Infrastructure to create a Protocol
       object for incomming connections"""

    protocol = None

    def __init__(self, theProtocol, theDevice, theTerminator = "\r\n"):
        print MercuryFactory.__name__, "ctor"
        self.protocol = theProtocol
        self.device = theDevice
        self.term = theTerminator
        self.numProtocols = 0

    def buildProtocol(self, addr):
        p = self.protocol(self.device, self.term)
        p.factory = self
        return p

if __name__ == '__main__':
    class TestProtocol:
        def __init__(self, theDevice, theTerm = "\r\n"):
            self.device = theDevice
            self.response = ""
            self.term = theTerm

    class TestDevice:
        def __init__(self):
            pass

    new_factory = MercuryFactory(TestProtocol, TestDevice, "\r\n");
    new_protocol = new_factory.buildProtocol("address")
    print "Factory:   ", new_factory
    print "  .protocol", new_factory.protocol
    print "  .device  ", new_factory.device
    print "  .num_prot", new_factory.numProtocols
    print "  .term    ", new_factory.term
    print "Protocol:  ", new_protocol
    print "  .device  ", new_protocol.device
    print "  .response", new_protocol.response
    print "  .term    ", new_protocol.term
