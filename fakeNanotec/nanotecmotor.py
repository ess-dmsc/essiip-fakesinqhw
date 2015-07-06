#--------------------------------------------------------------
# Fake Nanotec SMCI motor. I do not bother with acceleration and
# deacceleration, just run linearly. 
#
# The nanotecs have a huge command set. This implements only 
# that part which is necessary to run the thing 
#
# Mark Koennecke, July 2015
#-------------------------------------------------------------
import time
import math

class NanotecMotor(object):
    """
    Nanotec SMCI fake motor 
    """
    def __init__(self,motno,minref,maxref):
        self.speed = 1000
        self.motno = motno
        self.targetstep = 0
        self.currentstep = 0
        self.moving = False
        self.starttime = 0
        self.startstep  = 0
        self.mode =  'none'
        self.sign = 1
        self.minref = minref
        self.maxref = maxref
        self.refdir = 0


    def iterate(self):
        if self.moving:
            tdiff = time.time() - self.starttime
            stepsDone = tdiff * self.speed
            print('tdiff, stepsDone, startstep, targetstep, starttime: ' + str(tdiff) + ', ' + str(stepsDone) + ', ' +
                 str(self.startstep) + ', ' + str(self.targetstep) + ', ' + str(self.starttime) )
            if self.sign == 1:
                # moving positive
                curpos = self.startstep + stepsDone
                if curpos >= self.targetstep:
                    self.moving = False
                    self.currentstep = self.targetstep
                else:
                    self.currentstep = self.startstep + stepsDone
            else:
                # moving negative
                curpos = self.startstep - stepsDone 
                if curpos <= self.targetstep:
                    self.moving = False
                    self.currentstep = self.targetstep
                else:
                    self.currentstep = self.startstep - stepsDone

    def makeReturn(self,com,val):
        if val != 'none':
            return str(self.motno) + com + str(val)
        else :
            return str(self.motno) + com



    def doCommand(self,com, par):
        
        if com.startswith('C'):
            self.iterate()
            return self.makeReturn(com,self.currentstep)

        if com.startswith('p'):
            val = int(par)
            if val == 2:
                self.mode = 'abs'
            elif val == 4:
                self.mode = 'refrun'
            else:
                self.mode = 'none'
            return self.makeReturn(com,par)

        if com.startswith('o'):
            self.speed = int(par)
            return self.makeReturn(com,par)

        
        if com.startswith('s'):
            self.targetstep = int(par)
            if self.targetstep > self.currentstep:
                self.sign = 1
            else :
                self.sign = -1
            return self.makeReturn(com,par)

        if com.startswith('A'):
            self.startstep = self.currentstep
            if self.mode == 'abs':
                self.starttime = time.time()
                self.moving = True
            elif self.mode == 'refrun':
                if self.refdir == 0:
                    self.targetstep = self.minref
                else:
                    self.targetstep = self.maxref
                self.starttime = time.time()
                self.moving = True
            else:
                pass
            return self.makeReturn(com,'none')

        if com.startswith('$'):
            self.iterate()
            if self.moving:
                mask = '0'
            else:
                mask = '1'
            if self.currentstep == self.minref or self.currentstep == self.maxref:
                mask += '1'
            else:
                mask += '0'
            mask += '000101'
            return self.makeReturn(com,int(mask[::-1],2))
            
        if com.startswith('D'):
            if par == 'none':
                val = 0
            else:
                val = int(par)
            self.currentstep = val
            return self.makeReturn(com,val)

        if com.startswith('S'):
            self.iterate()
            self.moving = False
            return self.makeReturn(com,par)

        
        # -- not supported, but may be in the nanotec command set 
        return str(self.motno) + com + '?'

