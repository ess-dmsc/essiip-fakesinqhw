from nexus2event import *
from neventarray import *

import sys, os, getopt
import errno
import numpy
import time
import threading
import psutil

import zmq
import twisted
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

def usage() :
    print ""
    print "Usage:"
    print "\tpython",sys.argv[0],"[-h -m -r] <nexus file> <port> (<multiplier>)"
    print ""
    print "-h: this help"
    print "-m: use fake data"
    print "-r: don't wait for external signal to start send data"
    print ""


class generatorSource(LineReceiver):

    def __init__(self):
        self.status = False
        
    def connectionMade(self):
        self.sendLine("Type run to start counter")
        self.sendLine("Type pause to stop counter")
        
    def connectionLost(self, reason):
        print "Disconnetting controller"
        
    def lineReceived(self, line):
        print line
        if line == "run" :
            self.status = True
            self.factory.run()
        if line == "pause" :
            self.status = False
            self.factory.pause()
        self.sendLine(str(self.factory.count))



class generatorSourceFactory(Factory):
    protocol = generatorSource

    def __init__ (self,source,port,multiplier,mock=False,status=False):
        self.source = source
        self.port = port

        self.multiplier = multiplier
        self.status = status
        self.data = self.load(mock)

        self.context = zmq.Context()
#        mem = psutil.virtual_memory().available
#
#        print self.data.size*event_t.itemsize/(1024.*1024.),"MB/message"
#        print mem/(1024.*1024.),"MB"
#        prin

        self.socket = self.connect()

        self.count = 0
        if (self.status == True):
            self.status = False
            self.run()


    def load(self,mock):
        if not mock:
            data = loadNeXus2event(self.source)
        else:
            data = self.dummy()

        if self.multiplier > 1:
            data = multiplyNEventArray(data,int(self.multiplier))

        print "ready to run"
        return data

    def dummy(self):
        data = np.empty(shape=1,dtype=event_t)
        data["ts"]=1234
        data["x"] = 23
        data["y"] = 4
        return data

    def connect(self):
        zmq_socket = self.context.socket(zmq.PUSH)
        zmq_socket.bind("tcp://127.0.0.1:"+self.port)
        return zmq_socket

    def run(self) :
        if (self.status == False) :
            print "started counting"
            self.status = True
            thread = threading.Thread(target=self.start)
            thread.daemon = True
            thread.start()
        else :
            print "Nothing to do, I'm already counting!"
            
    def pause(self) :
        if (self.status == True) :
            print "paused counting"
            self.status = False
        else :
            print "Nothing to do, I'm already in pause!"

    def start(self):
        data = self.data
        ctime=time.time()
        pulseID=0
        
        while True:
            itime = time.time()
            dataHeader=header(pulseID,itime)
            
            def send_data(socket,head):
                socket.send_json(head,zmq.SNDMORE)
                socket.send(self.data)
                self.count += 1

            if (self.status == True):
                send_data(self.socket,dataHeader)

            elapsed = time.time() - itime
            remaining = 1./14-elapsed

            if remaining > 0:
                time.sleep (remaining)

            pulseID += 1

            if time.time()-ctime > 10 :
                size = (data.size*event_t.itemsize+
                        sys.getsizeof(dataHeader))

                print "Sent ",self.count," events @ ",size*self.count/(10.*1e6)," MB/s"
                self.count = 0
                ctime = time.time()




def main(argv,mock=False,status=False):
    source = argv[0]
    port = argv[1]

    multiplier = 1
    if len(argv) > 2:
        multiplier = argv[2]

    reactor.listenTCP(8123, generatorSourceFactory(source,port,multiplier,mock,status))
    reactor.run()

if __name__ == "__main__":
    try:
        opts,args = getopt.getopt(sys.argv[1:], "hmr",["help","mock","run"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    if len(args) < 2:
        usage()
        exit(2)
    
    mock = False
    run = False
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit()
        if o in ("-m","--mock"):
            mock = True
        if o in ("-r","--run"):
            run = True
            
    main(args,mock,run)

