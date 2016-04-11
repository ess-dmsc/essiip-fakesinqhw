import time
import zmq
import sys
import numpy as np
import json
import threading

from neventarray import *

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
            data = np.frombuffer(buffer(buf),dtype=event_t)
            for i in data:
                print i["ts"], i["sync"], i["x"], i["y"]

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

    print event_t.itemsize
    main(sys.argv)
