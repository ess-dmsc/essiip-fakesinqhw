#!/usr/bin/python
# An acceptable state reply looks like this,
# reply = 'N#SOS#ACCEPT#STATE = BRAKING       #RSPEED= 25476#ASPEED=     0#SSPEED=  0.3#AVETO = nok#PLOSS = 290.2#SPLOS = 25422#TTANG = 0.000#RTEMP = 23.9#WFLOW =  0.1#WINLT = 20.3#WOUTT = 21.0#VACUM = 0.1922#WVALV = clos#VVALV = open#VIBRT = 0.08#BCUUN =  0.0#SDATE = 24.04.2013#STIME = 13:53:10#'

from twisted.internet import reactor, protocol


class NVS_Prot(protocol.Protocol):
    def __init__(self):
        self.fields = [
            'state' , 'rspeed', 'aspeed', 'sspeed', 'aveto' , 'ploss' , 'sploss',
            'ttang' , 'rtemp' , 'wflow' , 'winlt' , 'woutt' , 'vacum' , 'wvalv' ,
            'vvalv' , 'vibrt' , 'bcuun' , 'sdate' , 'stime'
            ]
        self.state = {
            'state' : {'fname': '#STATE ', 'fval':'BRAKING'},
            'rspeed': {'fname': '#RSPEED', 'fval': 25476},
            'aspeed': {'fname': '#ASPEED', 'fval':     0},
            'sspeed': {'fname': '#SSPEED', 'fval':  0.3},
            'aveto' : {'fname': '#AVETO ', 'fval': 'nok'},
            'ploss' : {'fname': '#PLOSS ', 'fval': 290.2},
            'sploss': {'fname': '#SPLOS ', 'fval': 25422},
            'ttang' : {'fname': '#TTANG ', 'fval': 0.000},
            'rtemp' : {'fname': '#RTEMP ', 'fval': 23.9},
            'wflow' : {'fname': '#WFLOW ', 'fval': 0.1},
            'winlt' : {'fname': '#WINLT ', 'fval': 20.3},
            'woutt' : {'fname': '#WOUTT ', 'fval': 21.0},
            'vacum' : {'fname': '#VACUM ', 'fval': 0.1922},
            'wvalv' : {'fname': '#WVALV ', 'fval': ' clos'},
            'vvalv' : {'fname': '#VVALV ', 'fval': ' open'},
            'vibrt' : {'fname': '#VIBRT ', 'fval': 0.08},
            'bcuun' : {'fname': '#BCUUN ', 'fval': 0.0},
            'sdate' : {'fname': '#SDATE ', 'fval': '24.04.2013'},
            'stime' : {'fname': '#STIME ', 'fval': '13:53:10'}
            }

    def dataReceived(self, data):
        print "RECEIVED ", data
        reply = 'N#SOS#ACCEPT'
        for k in self.fields:
            reply += self.state[k]['fname'] + '= ' + str(self.state[k]['fval'])
        reply += '#'
        print "REPLY ", reply
        self.transport.write(reply)

def main():
    factory = protocol.ServerFactory()
    factory.protocol = NVS_Prot
    reactor.listenTCP(60001,factory)
    reactor.run()

if __name__ == '__main__':
    main()
