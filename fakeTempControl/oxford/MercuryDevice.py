# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
#
# Generic Mercury Temperature Controller Device
#
# Author: Douglas Clowes (2014)
#
import inspect
import traceback

class MercuryDevice(object):

    def __init__(self):
        print MercuryDevice.__name__, "ctor"
        #print "Methods:", inspect.getmembers(self, inspect.ismethod)
        methods = inspect.getmembers(self, inspect.ismethod)
        self.myMethods = {}
        for method in methods:
            self.myMethods[method[0]] = method[1:]
        #for method in sorted(self.myMethods):
        #    print "Method:", method, self.myMethods[method], type(method), type(self.myMethods[method])

    def reset_powerup(self):
        print MercuryDevice.__name__, "reset_powerup"

    def write(self, response):
        print "Device Response: %s" % response
        self.protocol.write(response)

    def doCommand(self, command, params):
        print MercuryDevice.__name__, "Command:", command, params
        method = "doCommand%s" % command
        if method in self.myMethods:
            action = "response = self.%s(command, params)" % method
            print "Action:", action
            exec action
            if response:
                return response
        else:
            print "Unimplemented Command:", command, params
        return False

    def doQuery(self, command, params):
        print MercuryDevice.__name__, "Query:", command, params
        method = "doQuery%s" % command
        if method in self.myMethods:
            action = "response = self.%s(command, params)" % method
            print "Action:", action
            exec action
            if response:
                return response
        else:
            print "Unimplemented Query:", command, params
            self.write("Unimplemented Query: %s" % command)
        return False

    def doQueryRANDOM(self, command, params):
        self.write("%f" % self.RANDOM)

    def doCommandRANDOM(self, command, params):
        self.RANDOM = float(params[0])

    def mergeParams(self, count, theOld, theNew):
        oldParams = theOld.split(",")
        if len(oldParams) != count:
            raise IndexError
        newParams = theNew.split(",")
        if len(newParams) > count:
            raise IndexError
        mergedParams = []
        for idx in range(count):
            if oldParams[idx] == '':
                raise ValueError
            if idx >= len(newParams) or newParams[idx] == '':
                mergedParams.append(oldParams[idx])
            else:
                mergedParams.append(newParams[idx])
        if len(mergedParams) != count:
            raise IndexError
        return ",".join(mergedParams)

    def dataReceived(self, data):
        print MercuryDevice.__name__, "PDU: \"" + data + "\""
        command = data.split(":")[0]
        params = data[len(command)+1:].strip().split(":")
        if command[0] == "*":
            command = command[1:]
        try:
            if command in ('READ'):
                self.doQuery(command, params)
            else:
                self.doCommand(command, params)
        except:
            traceback.print_exc()

if __name__ == '__main__':
    class TestProtocol:
        def __init__(self):
            print self.__class__.__name__, "ctor"
            self.numProtocols = 0
        def write(self, data):
            print "test write:", data
        def loseConnection(self):
            print "test lose connection"
    test_protocol = TestProtocol()
    test_device = MercuryDevice()
    test_device.protocol = test_protocol
    test_device.dataReceived("READ:DEV:DB7.T1:TEMP:SIG:TEMP")
    test_device.dataReceived("READ:DEV:DB7.T1:TEMP:NICK")
    test_device.dataReceived("SET:DEV:DB8.T1:TEMP:LOOP:TSET:273")
    test_device.dataReceived("READ:DEV:DB8.T1:TEMP:LOOP:TSET")
