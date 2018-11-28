#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys,time

import json
from pprint import pprint
import threading

from pykafka import KafkaClient

class EchoClient(LineReceiver):
    def __init__(self):
         self.delimiter = '\r'

    def connectionMade(self):
        with open('config') as data_file:
            data=json.load(data_file)
        pprint(data)
        client = KafkaClient(hosts="ess01.psi.ch:9092")
        topic = client.topics["AMOR.detector.command"]
        self.consumer = topic.get_simple_consumer()
        self.run()

    def lineReceived(self, line):
        print "receive:", line
        if line=="stop":
            self.transport.loseConnection()

    def sendMessage(self, line):
        self.sendLine(line)

    def run(self):
#        self.sendLine("Ciao")
#        self.sendLine("vecchio")
#        self.sendLine("pirata")
#        message = ""
#        self.sendLine(message)
#        

        while True:
            message = self.consumer.consume()
            print self.sendLine(message.value)
            time.sleep(1)
#        for message in self.consumer:


class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()

def main():
    factory = EchoClientFactory()
    reactor.connectTCP('localhost', 62000, factory)
    reactor.run()

if __name__ == '__main__':
    main()
