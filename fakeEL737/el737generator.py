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
import time
import sys

import zmq
from nexus2event import *
from neventarray import *
import threading

class EL737Controller(LineReceiver):
    def __init__(self):
        self.remotestate = 0
        self.delimiter = '\r'
        self.mode = 'timer'
        self.preset = .0
        self.starttime = time.time()
        self.endtime = time.time()
        self.counting = False
        self.mypaused = False
        self.pausestart = 0
        self.pausedTime = 0.
        self.threshold = 0
        self.thresholdcounter = 1

        self.context = zmq.Context()
        self.socket = []
        self.source = []
        self.multiplier = 1
        self.Stop = False
        self.dtype = event_t

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
                """Enbles the event generator. Syntax:

                >>> init <NeXus file> <port> (<multiplier>)
                
                Args:
                NeXus file (str):  the NeXus file from which extract data
                port       (int):  the port to use for zmq communications
                multiplier (int):  allows to produce replicas of raw data to mimic a larger message
                
                It does not start the generation, simply sets up the
                environment. To run the event generation use >>> run
                
                >>> init ../neventGenerator/rita22012n006190.hdf 1234 100

                """
                self.socket = self.context.socket(zmq.PUSH)
                self.socket.bind("tcp://127.0.0.1:"+data.split(" ")[2])
                self.write("zmq connected on port "+data.split(" ")[2])
                self.write("\r")
                self.source = data.split(" ")[1]
                if len(data.split(" ")) > 3:
                    self.multiplier = int(data.split(" ")[3])
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
                    """Runs the event generator. Syntax:

                    >>> run
                    Args:
                    
                    Reads data from :NeXus file:, eventually applies
                    :multiplier: and start sending data. Every 10s return
                    statistics.
                    
                    >>> run

                    """
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


    def start(self):
        print "generator started"
        data = loadNeXus2event(self.source)

        if self.multiplier > 1:
            data = multiplyNEventArray(data,int(self.multiplier))

        ctime=time.time()
        pulseID=0
        count = 0
        
        while not self.Stop:
            itime = time.time()
            dataHeader=header(pulseID,itime)
            
            def send_data(data,socket,head):
                socket.send_json(head,zmq.SNDMORE)
                socket.send(data)

            if self.mypaused == False:
                send_data(data,self.socket,dataHeader)
                count += 1

            elapsed = time.time() - itime
            remaining = 1./14-elapsed

            if remaining > 0:
                time.sleep (remaining)

            pulseID += 1

            if time.time()-ctime > 10 :
                size = (data.size*self.dtype.itemsize+
                        sys.getsizeof(dataHeader))

                print "Sent ",count," events @ ",size*count/(10.*1e6)," MB/s"
                count = 0
                ctime = time.time()




def main(argv):
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 62001

    factory = protocol.ServerFactory()
    factory.protocol = EL737Controller
    reactor.listenTCP(port, factory)
    reactor.run()

if __name__ == "__main__":
    main(sys.argv)
