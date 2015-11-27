#!/usr/bin/env python
# vim: ft=python ts=8 sts=4 sw=4 expandtab autoindent smartindent nocindent
# Classes for device simulation using: First Order Plus Delay Time (FOPDT)
#
# Author: Unknown
# Finder: Douglas Clowes
"""
The class fopdt is a container for one or more fopdt_sink objects.

I am guessing that an fopdt_sink is a FOPDT source such as a heater element
or FOPDT sink such as a heat leak to the environment.

TODO:
* look into the isinstance block in getAbsolute
  because there doesn't seem to be a 'current_value' anywhere
"""
from math import exp

class fopdt_sink:
    def __init__(self, value, Kp, Tp, Td, absolute=False):
        self.value = value
        self.absolute = absolute
        self.Kp = Kp
        self.Tp = Tp
        self.Td = Td
        self.vmap = dict()

    def getAbsolute(self):
        if isinstance(self.value, fopdt):
            result = self.value.current_value
        else:
            result = self.value
        return result

    def getValue(self, tm, current):
        result = self.getAbsolute()

        # Do the timeshifting implied by Td
        t2 = round(tm)
        t1 = round(tm - self.Td)
        if not t2 in self.vmap:
            self.vmap[t2] = result
        for key in sorted(self.vmap.keys()):
            if key < t1:
                del self.vmap[key]
            else:
                break
        if t1 in self.vmap:
            result = self.vmap[t1]
        else:
            result = self.vmap[sorted(self.vmap.keys())[0]]

        # TODO should this go before timeshifting?
        if not self.absolute:
            result = result - current

        return result

    def getDelta(self, tm, current):
        value = self.getValue(tm, current)
        return (1 - exp(-1.0/self.Tp)) * self.Kp * value

class fopdt:

    def __init__(self, pv):
        self.pv = pv
        self.sources = []
        self.sinks = []

    def AddSource(self, source):
        self.sources.append(source)

    def RemSource(self, source):
        if source in self.sources:
            self.sources.remove(source)

    def AddSink(self, sink):
        self.sinks.append(sink)

    def RemSink(self, sink):
        if sink in self.sinks:
            self.sinks.remove(sink)

    def iterate(self, tm):
        self.source_delta = 0.0
        self.sink_delta = 0.0
        for sink in self.sources:
            self.source_delta = self.source_delta + sink.getDelta(tm, self.pv)
        for sink in self.sinks:
            self.sink_delta = self.sink_delta + sink.getDelta(tm, self.pv)
        self.old_value = self.pv
        self.new_value = self.pv + self.source_delta + self.sink_delta
        self.pv = self.new_value

if __name__ == "__main__":
    dev = fopdt(20)
    source = fopdt_sink(20, 2, 13, 10, False)
    dev.AddSource(source)
    dev.AddSource(source)
    dev.AddSource(source)
    dev.AddSource(source)
    sink = fopdt_sink(20, 1, 30, 1, False)
    dev.AddSink(sink)
    dev.AddSink(sink)
    min = max = dev.pv
    fd = open("test.csv", "w")
    fd.write("Time,value,source,source_v,sink,sink_v\n")
    for i in range(0,300+ 1):
        if i == 15:
            source.value = 30
        elif i == 45:
            source.value = 10
        dev.iterate(i)
        current = dev.pv
        if current > max:
            max = current
        if current < min:
            min = current
        #print "%3d: %6.3f = %6.3f + %6.3f + %6.3f" % ( i, current, prev, delta_in, delta_out )
        line = "%d,%.3f,%.3f,%.3f,%.3f,%.3f" % (i, current, source.value, dev.source_delta, sink.value, dev.sink_delta)
        fd.write(line + "\n")
    fd.close()
    print "Now: %6.3f, Min: %6.3f, Max: %6.3f" % (current, min, max)
