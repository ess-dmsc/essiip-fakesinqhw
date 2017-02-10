#!/usr/bin/python
# 
# fake SINQ EL737 counter box
#
# I am using 1000cts/sec for m1, 500 for m2, 300 for m3 and 2000 for m4
#
# Mark Koennecke, July 2015
#----------------------------------------------------------------------
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver

import zmq

import time
import sys,os
from datetime import datetime
import threading
import json

from nexus2event import *
from neventarray import *

class EL737Controller(LineReceiver):
    def __init__(self):
        self.remotestate = 0
        self.delimiter = '\r'
        self.mode = 'timer'
        self.preset = .0
        self.starttime = time.time()
        self.endtime = time.time()
        self.counting = False
        self.mypaused = True
        self.pausestart = 0
        self.pausedTime = 0.
        self.threshold = 0
        self.thresholdcounter = 1

        self.context = zmq.Context()
        self.socket = []
        self.source = []
        self.size = 0
        self.count = 0
        self.dtype = event_t
        self.Stop = False
        self.of = []

    def write(self, data):
        print "transmitted:", data
        if self.transport is not None: 
            self.transport.write(data)
    
    def calculateCountStatus(self):
        if self.counting and not self.mypaused :
            runtime = time.time() - self.starttime - self.pausedTime
            print(str(runtime) + ' versus ' + str(self.preset))
            if self.mode == 'timer':
                if runtime >= self.preset:
                    self.counting = False
                    self.endtime = self.starttime + self.preset
                    self.pausedTime = 0
            else:
                if runtime*1000 >= self.preset:
                    self.counting = False
                    self.endtime = self.starttime + self.preset/1000
        print('count flag after calculateCountStatus ' + str(self.counting))


    def lineReceived(self, data):
        print "lineReceived:", data

        if self.remotestate == 0:
            if data.startswith('init'):
                """Enbles the event reader. Syntax:

                >>> init <address>:<port>
                
                Args:
                port       (int):  tcp/ip address to listen for
                port       (int):  the port to use for zmq communications
                
                It does not start the reader, simply sets up the
                environment. To run the reader use >>> run
                
                >>> init tcp://127.0.0.1:1234

                """
                self.socket = self.context.socket(zmq.PULL)
                self.socket.connect(data.split(" ")[1])
                self.write("zmq connected to "+data.split(" ")[1])
                self.write("\r")
                self.remotestate = 1
            return

        data = data.lower().strip()

        if self.remotestate == 0:
            if data.startswith('rmt 1'):
                self.remotestate = 1
                self.write("\r")
            else:
                self.write("?loc\r")
            return

        if self.remotestate == 1:
            if data.startswith('echo 2'):
                self.remotestate = 2
                self.write("\r")
            else:
                if data.startswith("run"):
                    """Runs the event reader. Syntax:

                    >>> run
                    Args:
                    
                    Reads data from :NeXus file:, eventually applies
                    :multiplier: and start sending data. Every 10s return
                    statistics.
                    
                    >>> run

                    """
                    self.counting = True
                    self.mypaused = False

                    self.remotestate = 2
                    thread = threading.Thread(target=self.start)
                    thread.daemon = True
                    thread.start()
                else:
                    if data.startswith("debug"):
                        """Runs the event generator in debug mode. Syntax:

                        >>> debug

                        """
                        self.counting = True
                        self.mypaused = False
                        self.dtype = debug_t
                        self.of = open("dump_"+datetime.now().strftime("%Y-%m-%dT%H:%M:%S")+".txt","w")
                        self.remotestate = 2
                        thread = threading.Thread(target=self.start)
                        thread.daemon = True
                        thread.start()
                    else:
                        self.write("?loc\r")
            return
            

        if self.remotestate == 2:

           if data.startswith('rmt 1') or data.startswith('echo'):
               self.write('\r')
               return

           if data.startswith('mp'):
               l = data.split()
               self.mode = 'monitor'
               self.preset = float(l[1])
               self.starttime = time.time()
               self.mypaused = False
               self.pausedTime = 0.
               self.counting = True
               self.write('\r')
               return
               
           if data.startswith('tp'):
               l = data.split()
               self.mode = 'timer'
               self.preset = float(l[1])
               self.starttime = time.time()
               self.mypaused = False
               self.pausedTime = 0.
               self.counting = True
               self.write('\r')
               return
               
           if data.startswith('s'):
               self.counting = False
               self.endtime = time.time()
               self.write('\r')
               return

           if data.startswith('ps'):
               self.counting = True
               self.mypaused = True
               self.pausestart = time.time()
               self.write('\r')
               return

           if data.startswith('co'):
               if not self.mypaused:
                   pass
               else:
                   self.mypaused = False
                   self.pausedTime  += time.time() - self.pausestart
               self.write('\r')
               return

           if data.startswith('dl'):
               l = data.split()
               if len(l) >= 3:
                   self.threshold = float(l[2])
                   self.write('\r')
               else:
                   self.write(str(self.threshold) + '\r')

           if data.startswith('dr'):
               l = data.split()
               if len(l) >= 2:
                   self.thresholdcounter = int(l[1])
                   self.write('\r')
               else:
                   self.write(str(self.thresholdcounter) + '\r')

           if data.startswith('rs'):
               self.calculateCountStatus()
               if self.counting:
                   if self.mypaused:
                       if self.mode == 'timer':
                           self.write('9\r')
                       else:
                           self.write('10\r')
                   else:
                       if self.mode == 'timer':
                           self.write('1\r')
                       else:
                           self.write('2\r')
               else:
                   self.write('0\r')
               return

           if data.startswith('ra'):
               self.calculateCountStatus()
               if self.counting:
                   if self.mypaused:
                       pausetime = time.time() - self.pausestart
                   else:
                       pausetime = self.pausedTime
                   diff = time.time() - self.starttime - pausetime
               else:
                   diff = self.endtime - self.starttime
               rlist = []
               rlist.append(str(diff))
               rlist.append(str(int(diff*1000)))
               rlist.append(str(int(diff*1500)))
               rlist.append(str(int(diff*500)))
               rlist.append(str(int(diff*300)))
               rlist.append(str(int(diff*2000)))
               rlist.append('0')
               rlist.append('0')
               rlist.append('0')
               rastring = ' '.join(rlist)
               self.write(rastring +'\r')
               return

           if data.startswith('id'):
               self.write('EL737 Neutron Counter V8.02\r')
               return

           self.write('?2\r')


    def stats(self) :
        while not self.Stop:

            time.sleep(10)
            print "Received",self.count,"events (",self.size/1.e6,"MB) @ ",self.size*self.count/(10.*1e6)," MB/s"
            self.count = 0


    def start(self):

        pulseID=0
        
        thread = threading.Thread(target=self.stats)
        thread.daemon = True
        thread.start()
        
        while not self.Stop:

            if not self.mypaused:
                dataHeader = self.socket.recv_json()
                buf = self.socket.recv(copy=True)
                data = np.frombuffer(buffer(buf),dtype=event_t)
                if self.dtype == debug_t:
                    self.of.write(json.dumps(dataHeader))
                    for i in data:
                        self.of.write(str(i)+"\n")
                    self.of.flush()
                    os.fsync(self.of.fileno())
                self.count += 1
                self.size = (data.size*event_t.itemsize+
                        sys.getsizeof(dataHeader))

                if dataHeader["ts"] > pulseID:
                    while not int(dataHeader["ts"]) == (pulseID+1):
                        print "Lost pulse ",pulseID
                        pulseID += 1
                if dataHeader["ts"] < pulseID:
                        pulseID = dataHeader["ts"]

            pulseID += 1
        print "execution stopped"
        thread.stop()

def main(argv):
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 62000

    factory = protocol.ServerFactory()
    factory.protocol = EL737Controller
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)
