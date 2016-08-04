#-------------------------------------------------------------
# A simulation of a single Magnet for the Magnet simulation
#
# Mark Koennecke, July 2016
#-------------------------------------------------------------

class Magnet(object):
    """
        PSI fake Magnet
    """

    def __init__(self,lowlim,hilim):
        self._set = .0
        self._cur = .0
        self._onoff = 0
        self.lowlim = lowlim
        self.hilim = hilim
        self._err = 0
        self._errText = 'NO'

    @property
    def set(self):
        return self._set

    @property
    def cur(self):
        return self._cur

    @property
    def onoff(self):
        return self._onoff

    @property
    def err(self):
        return self._err

    @property
    def errText(self):
        return self._errText
    
    @property
    def hl(self):
        return self.hilim

    @property
    def ll(self):
        return self.lowlim

    @onoff.setter
    def onoff(self,value):
        if value == 0 or value == 1:
            self._onoff = value
            return 'OK'
        else:
            return 'ERROR: invalid value'

    def setcur(self,value):
        print('cur.setter called with ' +str(value))
        if value >= self.lowlim and value <= self.hilim:
            print(' limit check ok')
            if self._onoff ==  1:
                self._set = value
                self._cur = value
                return 'OK'
            else:
                return 'OK'
        else:
            return 'ERROR: out of range %f - %f' % (self.hilim,self.lowlim)


        
            
