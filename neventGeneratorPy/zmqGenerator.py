from nexus2event import *
from neventarray import *

import sys, os, getopt
import errno
import numpy
import time
import binascii

import zmq
import twisted
from twisted.internet.defer import inlineCallbacks

import ritaHeader as rh

def usage() :
    print ""
    print "Usage:"
    print "\tpython",sys.argv[0],"[-h] <nexus file> <port> (<multiplier>)"
    print ""
    print "-h: this help"
    print ""



class generatorSource:

    def __init__ (self,source,port,multiplier):
        print rh.header()
        self.source = source
        self.port = port
        self.context = zmq.Context()
        self.socket = self.connect()
#        self.data = self.load(multiplier)
        self.count = 0
        self.run(self.load(multiplier))

    def connect(self):
        zmq_socket = self.context.socket(zmq.PUSH)
        zmq_socket.bind("tcp://*:"+self.port)
        zmq_socket.setsockopt(zmq.SNDHWM, 100)
        return zmq_socket

    def load(self,multiplier):
        data = loadNeXus2event(self.source)
        if multiplier > 1:
            data = multiplyNEventArray(data,int(multiplier))
        return data

    def mutation(self,ctl,d):
        o = d
        if (ctl['mutation'] == 'nev') or (ctl['mutation'] == 'all'):
            if  np.random.rand() > .99 :
                o = np.delete(o,np.random.rand(o.size))
                print "Error: missing value"

        if (ctl['mutation'] == 'ts') or (ctl['mutation'] == 'all'):
            if  np.random.rand() > .99 :
                o[1]['ts'] = -1
                print "Error: wrong timestamp"

        if (ctl['mutation'] == 'pos') or (ctl['mutation'] == 'all'):
            if  np.random.rand() > .99 :
                x=np.random.randint(o.size,size=np.random.randint(5)) 
                o[1]["data"] = o[1]["data"] & 0xff000fff | 16773120
                print "Error: wrong position"
            if  np.random.rand() > .99 :
                x=np.random.randint(o.size,size=np.random.randint(5)) 
                o[2]["data"] = o[2]["data"] & 0xfffff000 | 4095
                print "Error: wrong position"

        return o

    
    def run(self,data):

        ctl = rh.control()

        ctime=time.time()
        pulseID=0

        s = 1e-6*(data.nbytes+len(rh.header(pulseID,ctime,12345678,data.shape[0])))
        print "size = ",s, "MB; expected bw = ",s * ctl["rate"], "MB/s"

        while(ctl["run"] != "stop"):
            stream_frequency = 1./ctl["rate"]

            itime = time.time()
            if ctl["run"] != "pause":
                dataHeader=rh.header(pulseID,itime,12345678,data.shape[0])
            else:
                dataHeader=rh.header(pulseID,itime,12345678,0)

#            data = rh.set_ds(data,ctl)

            def send_data(socket,head):
                if ctl["run"] == "run": 
                    socket.send(head,zmq.SNDMORE)
                    socket.send(self.mutation(ctl,data))
#                    socket.send(data)
                    self.count += 1
                else:
                    socket.send(head)
                    self.count += 1

            send_data(self.socket,dataHeader)

            elapsed = time.time() - itime
            remaining = stream_frequency-elapsed

            if remaining > 0:
                time.sleep (remaining)

            pulseID += 1
            ctl = rh.control()
            if time.time()-ctime > 10 :
                size = (data.size*data.dtype.itemsize+
                        sys.getsizeof(dataHeader))

                print "Sent ",self.count," events @ ",size*self.count/(10.*1e6)," MB/s"
                self.count = 0
                ctime = time.time()







def main(argv):

    source = argv[0]
    port = argv[1]

    multiplier = 1
    if len(argv) > 2:
        multiplier = argv[2]

    generatorSource(source,port,multiplier)
    


if __name__ == "__main__":
    try:
        opts,args = getopt.getopt(sys.argv[1:], "h",["help"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)
        
    if len(args) < 2:
        usage()
        exit(2)
        
    for o,a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit()

    main(args)

