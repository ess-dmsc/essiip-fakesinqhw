import time
import zmq
import sys
import numpy as np
import json
import threading

#from neventarray import *
def multiplyNEventArray(data,multiplier) :
    return np.tile(data,multiplier)

event_t = np.dtype([("ts",np.uint32),
                    ("data",np.uint32)])

class generatorReceiver :
    def __init__ (self, fulladdress) :
        self.fulladdress = fulladdress
        self.count = 0
        self.size = 0
        self.context = zmq.Context()
        self.socket = self.connect()
        self.run()


    def connect(self) :
        zmq_socket = self.context.socket(zmq.PULL)
        zmq_socket.connect(self.fulladdress)
        return zmq_socket

    def stats(self) :
        while True:
            time.sleep(10)
            print "Received",self.count,"events (",self.size/1.e6,"MB) @ ",self.size*self.count/(10.*1e6)," MB/s"
            self.count = 0

    def run(self) :
        pulseID = 0

        thread = threading.Thread(target=self.stats)
        thread.daemon = True
        thread.start()
        
        while(True):

            dataHeader = self.socket.recv_json()
            buf = self.socket.recv(copy=True)
            ne = dataHeader["ds"][1]
            
            if zmq.getsockopt(zmq.RECVMORE):
                data = np.frombuffer(buffer(buf),dtype=event_t)
            
                if data.size < ne:
                    print "pulse ",dataHeader["pid"]," incomplete"

                    for i in  data:
                        print i["ts"], (i["data"] & 0xfff), (i["data"] & 0xfff000) >> 12,(i["data"] & 0xf000000) >> 24,(i["data"] & 0x1000000) >> 28,(i["data"] & 0x2000000) >> 29 ,(i["data"] & 0x4000000) >> 30,(i["data"] & 0x8000000) >> 31
                
                
                    timestamp = dataHeader["st"]
                    if not int(dataHeader["pid"]) == (pulseID+1):
                        print "Lost pulse ",dataHeader["pid"]
                    pulseID = int(dataHeader["pid"])

                    self.size = data.size*event_t.itemsize+sys.getsizeof(dataHeader)
                    self.count = self.count+1


def main(argv):
    fulladdress = argv[1]
    generatorReceiver(fulladdress)


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print "Error, port required"
        sys.exit(2)

    main(sys.argv)
