from nexus2event import *
from neventarray import *

import sys, os, getopt
import errno
import numpy
import time

import zmq
import twisted
from twisted.internet.defer import inlineCallbacks


def usage() :
    print ""
    print "Usage:"
    print "\tpython",sys.argv[0],"[-h -m -r] <nexus file> <port> (<multiplier>)"
    print ""
    print "-h: this help"
    print "-m: use fake data"
    print ""



class generatorSource:

    def __init__ (self,source,port,multiplier,mock=False):
        self.source = source
        self.port = port
        self.multiplier = multiplier
        self.context = zmq.Context()
        self.data = self.load(mock)
        self.socket = self.connect()
        self.count = 0
        self.run()

    def load(self,mock):
        if not mock:
            data = loadNeXus2event(self.source)
        else:
            data = self.dummy()

        if self.multiplier > 1:
            data = multiplyNEventArray(data,int(self.multiplier))

        for i in data[0:100]:
            print i["ts"], i["sync"], i["x"], i["y"]

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
        zmq_socket.setsockopt(zmq.SNDHWM, 100)
        return zmq_socket

    def run(self):
        data = self.data
        ctime=time.time()
        pulseID=0

        print sys.getsizeof(data)
        print data.size*event_t.itemsize/(1024.*1024.),"MB"

        while(True):
            itime = time.time()
            dataHeader=header(pulseID,itime,data.shape[0])
            
            def send_data(socket,head):
                socket.send_json(head)
                socket.send(self.data)
                self.count += 1
                
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




def main(argv,mock=False):

    source = argv[0]
    port = argv[1]

    multiplier = 1
    if len(argv) > 2:
        multiplier = argv[2]

    generatorSource(source,port,multiplier)
    


if __name__ == "__main__":
    try:
        opts,args = getopt.getopt(sys.argv[1:], "hm",["help","mock"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    if len(args) < 2:
        usage()
        exit(2)
    
    mock = False
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit()
        if o in ("-m","--mock"):
            mock = True
            
    main(args,mock)
