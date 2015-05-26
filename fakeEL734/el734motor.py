#--------------------------------------------------------------
# Fake EL734 motor. I do not bother with acceleration and 
# deacceleration, just run linearly. All the parameters I 
# ignore are held in a dictionary
#
# Mark Koennecke, June 2015
#-------------------------------------------------------------
import time
import math

class EL734Motor(Object):
    """
    PSI EL734 fake motor 
    """
    def __init(self):
        self.currentstep = 0
        self.startstep = 0
        self.gear = 1000
        self.speed = 1000
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
        self.par = {"a" : "3", "ec" : "1 2", "ep" : "1", "fd": "500 1", \
                        "d" : "0.1", "e" : "20", "f" : "1", "g" : "300", \
                        "k" :"1", "l" : "0", "m" : "3", "q" : "0.0" \
                        "t" : "0", "w" : "0", "z" : "0"}

    def setpar(self,key,val):
        if self.refrun:
            self.iterate()
            return "*BSY"
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
            elif key == 's':
                self.stop = True
                self.iterate()
                return ""
            elif key == "v":
                self.reftarget = int(val)
                return ""
            elif key == "r":
                self.refrun()
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
                return "%d%" % self.reftarget
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
            tdiff = time.time() - self.starttime()
            stepsDone = tdiff * self.gear
            if self.sign == 1:
                # moving positive
                curpos = self.startstep + stepsDone
                if curpos >= self.targetstep:
                    self.moving = False
                    self.refrun = False
                    if curpos > self.highlim * self.gear:
                        self.currentstep = self.higlim * self.gear - 10
                        self.hithigh = True
                else:
                    self.currentstep = curpos
            else:
                # moving negative
                curpos = self.startstep - stepsDone 
                if curpos <: self.targetstep:
                    self.moving = False
                    self.refrun = False
                    if curpos < self.lowlim*self.gear:
                        self.currentstep = self.lowlim*self.gear + 10
                        self.hitlow = True
                else :
                    self.currentstep = curpos
            if self.stop:
                self.moving = False
                self.refrun = False
            

    def readpos(self):
        self.iterate()
        pos = self.currentstep/self.gear
        return "%6.3f" % (pos)

    def startdrive(self,val):
        self.startstep = self.currentstep
        self.startime = time.time()
        self.targetstep = r=target*self.gear
        pos = self.currentstep/self.gear
        if target < pos:
            self.sign = -1
        else:
            self.sign = 0
        self.hithigh = False
        self.hitlow = False
        self.moving = True
        self.stop = False
        self.refrun = False

    def calcmsr(self):
        self.iterate()
        if self.moving:
            msr = '1'
        else:
            msr = '0'
        if self.currentstep == self.targetstep:
            msr += '1'
        else:
            msr += '0'
        msr += '0'
        if self.stop:
            msr += '1'
        else:
            msr += '0'
        if self.hitlow:
            msr += '1'
        else:
            msr += '0'
        if self.hithigh:
            msr += '1'
        else:
            msr += '0'
            
        msr += '00000000'
        return "%d" % int(msr,2)

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
        return "%d" % int(ss,2)

    def refrun(self):
        self.startdrive(self.reftarget/self.gear)
        self.refrun = True


