#--------------------------------------------------------------
# Fake EL734 motor. I do not bother with acceleration and 
# deacceleration, just run linearly. All the parameters I 
# ignore are held in a dictionary
#
# Mark Koennecke, June 2015
#-------------------------------------------------------------
import time
import math

class EL734Motor(object):
    """
    PSI EL734 fake motor 
    """
    def __init__(self):
        self.currentstep = 0
        self.startstep = 0
        self.gear = 1000
        self.speed = 100
        self.targetstep = 0
        self.starttime = time.time()
        self.moving = False
        self.stop = False
        self.sign = 1;
        self.lowlim = -180.
        self.hitlow = False
        self.highlim = 360.
        self.hithigh = False
        self.refrun = False
        self.reftarget = self.highlim * self.gear
        self.target = .0
        self.stopping = False
        self.acfail = False
        self.runfail = False
        self.posfail = False
        self.par = {"a" : "3", "ec" : "1 2", "ep" : "1", "fd": "500 1", \
                        "d" : "0.1", "e" : "20", "f" : "1", "g" : "300", \
                        "k" :"1", "l" : "0", "m" : "3", "q" : "0.0", \
                        "t" : "0", "w" : "0", "z" : "0", 'mn' : 'xyz'}

    def setpar(self,key,val):
        if self.refrun:
            self.iterate()
            return '*BSY'
        if key in self.par.keys():
            self.par[key] = val
            return ""
        else:
            if key == "j":
                self.speed = int(val)
                return ""
            elif key == "fm":
                l = val.split()
                self.gear = int(l[1])
                return ""
            elif key == "u":
                pos = float(val)
                self.currentstep = pos*self.gear
                return ""
            elif key == "p":
                self.startdrive(float(val))
                return ""
            elif key == "v":
                self.reftarget = int(val)
                return ""
            elif key == "r":
                self.refrun()
                return ""
            elif key == 's':
                self.stop = True
                self.iterate()
                return ""
            else:
                return "?CMD"

    def getpar(self,key):
        if self.refrun:
            self.iterate()
            return "*BSY"
        if key in self.par.keys():
            return self.par[key]
        else:
            if key == "j":
                return str(self.speed)
            elif key == "fm":
                return "%d 1" % self.gear
            elif key == "u":
                return self.readpos()
            elif key == "msr":
                return self.calcmsr()
            elif key == "ss":
                return self.calcss()
            elif key == "v":
                return "%d" % self.reftarget
            elif key == 's':
                self.stop = True
                self.iterate()
                return ""
            elif key == 'xa':
                self.acfail = True
                return ""
            elif key == 'xp':
                self.posfail = True
                return ""
            elif key == 'xr':
                self.runfail = True
                return ""
            else :
                return "?CMD"

    def setlimits(self,l,h):
        if self.refrun:
            return "*BSY"
        self.highlim = h
        self.lowlim = l
        return ""

    def getlimits(self):
        if self.refrun:
            return "*BSY"
        return (self.lowlim,self.highlim)

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
                    self.refrun = False
                    if self.target  > self.highlim:
                        self.currentstep = self.highlim * self.gear - 10
                        self.hithigh = True
                    else:
                        self.currentstep = self.target*self.gear

                    self.stopping = True
                else:
                    self.currentstep = self.startstep + stepsDone
                    if self.runfail or self.acfail:
                        self.moving = False
                        self.stopping = True
            else:
                # moving negative
                curpos = self.startstep - stepsDone 
                if curpos <= self.targetstep:
                    self.moving = False
                    self.refrun = False
                    if self.target < self.lowlim:
                        self.currentstep = self.lowlim*self.gear + 10
                        self.hitlow = True
                    else :
                        self.currentstep = self.target*self.gear
                    self.stopping = True
                else:
                    self.currentstep = self.startstep - stepsDone
                    if self.runfail or self.acfail:
                        self.moving = False
                        self.stopping = True
                    
            if self.stop:
                self.moving = False
                self.refrun = False
            

    def readpos(self):
        self.iterate()
        pos = self.currentstep/self.gear
        return "%6.3f" % (pos)

    def startdrive(self,target):
        self.startstep = self.currentstep
        self.starttime = time.time()
        self.targetstep = target*self.gear
        pos = self.currentstep/self.gear
        if target < pos:
            self.sign = -1
        else:
            self.sign = 1
        self.hithigh = False
        self.hitlow = False
        self.moving = True
        self.stop = False
        self.refrun = False
        self.target = target
        self.stopping = False
        self.acfail = False
        self.posfail = False
        self.runfail = False

    def calcmsr(self):
        self.iterate()
        if self.moving:
            msr = '1'
        else:
            msr = '0'
        if self.stopping and self.currentstep == self.targetstep:
            msr += '1'
            self.stopping = False
        else:
            msr += '0'
        msr += '0'
        if self.stop:
            msr += '1'
            self.stop = False
        else:
            msr += '0'
        if self.hitlow:
            msr += '1'
            self.hitlow = False
        else:
            msr += '0'
        if self.hithigh:
            msr += '1'
            self.hithigh = False
        else:
            msr += '0'
        msr += '0'

        if self.runfail:
            msr += '1'
            self.runfail = False
        else:
            msr += '0'
        msr += '0'

        if self.posfail:
            msr += '1'
            self.posfail = False
        else:
            msr += '0'
        msr += '0'
        msr += '0'
        
        if self.acfail:
            msr += '1'
            self.acfail = False
        else:
            msr += '0'
            
        msr += '0'

        print('raw msr ' + msr[::-1])
        return "%d" % int(msr[::-1],2)

    def calcss(self):
        self.iterate()
        ss = '00'
        if self.stop:
            ss += '1'
        else:
            ss += '0'
        if self.hitlow:
            ss += '1'
        else :
            ss += '0'
        if self.hithigh:
            ss += '1'
        else :
            ss += '0'
        ss += '0'
        return "%d" % int(ss[::-1],2)

    def refrun(self):
        self.startdrive(self.reftarget/self.gear)
        self.refrun = True


