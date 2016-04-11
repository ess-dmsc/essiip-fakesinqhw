import sys
import os
import errno

import numpy as np

import nxs
import neventarray


def loadAMOR(source) :
    f = nxs.open(source,'r')

    f.openpath("entry1/AMOR/area_detector/data")
    dim,datatype= f.getinfo()
    size = np.prod(dim)
    data = f.getdata()
    f.close()

    f = nxs.open(source,'r')
    f.openpath("entry1/AMOR/area_detector/time_binning")
    tof = f.getdata()
    f.close()

    nEvents = np.sum(data)
    signal = np.empty(nEvents,dtype=neventarray.event_t)

    nEv = 0
    detID = 0
    for row in range(dim[0]):
        for col in range(dim[1]):
            for it in range(dim[2]):
                events = data[row][col][it]
                if events > 0:
                    signal[nEv:nEv+events]["ts"] = round(tof[it]/10.)
                    signal[nEv:nEv+events]["x"] = row
                    signal[nEv:nEv+events]["y"] = col
                    nEv = nEv+events

    if not signal.shape[0] == nEv:
        raise Exception("Error in reading NeXus data: wrong number of events",nEv)

    return signal






############################
def loadFOCUS(source) :
    f = nxs.open(source,'r')

    f.openpath("entry1/FOCUS/merged/counts")
    dim,datatype= f.getinfo()
    size = np.prod(dim)
    data = f.getdata()
    f.close()

    f = nxs.open(source,'r')
    f.openpath("entry1/FOCUS/merged/time_binning")
    tof = f.getdata()
    f.close()

    nEvents = np.sum(data)
    signal = np.empty(nEvents,dtype=neventarray.event_t)

    nEv = 0
    detID = 0
    for row in range(dim[0]):
        for it in range(dim[1]):
            events = data[row][it]
            if events > 0:
                signal[nEv:nEv+events]["x"] = row
                signal[nEv:nEv+events]["y"] = it
                nEv = nEv+events

    if not signal.shape[0] == nEv:
        raise Exception("Error in reading NeXus data: wrong number of events",nEv)

    return signal
##########################


def loadRITA2(source) :

    f = nxs.open(source,'r')

    f.openpath("entry1/RITA-2/detector/counts")
    dim,datatype= f.getinfo()
    size = np.prod(dim)
    data = f.getdata()
    f.close()

    np.random.seed(1234)
    timestamp = np.sort(np.random.randint(2**32-1,size=dim[0]))

    nEvents = np.sum(data)
    signal = np.empty(nEvents,dtype=neventarray.event_t)

    nEv = 0
    detID = 0

    row = np.uint16
    col = np.uint16

    for row in range(dim[1]):
        for col in range(dim[2]):
            for it in range(dim[0]):
                events = data[it][row][col]
                if events > 0:
                    signal[nEv:nEv+events]["ts"] = timestamp[it]
                    signal[nEv:nEv+events]["sync"] = 0 
                    signal[nEv:nEv+events]["x"] = row
                    signal[nEv:nEv+events]["y"] = col
                    nEv = nEv+events

    return signal


def header(pulseID=1234,st=1457097133,nevents=1):
    dataHeader = {
        "htype":"sinq-1.0",
        "mode":"pos",
        "pid":pulseID,
        "hws":{"error":0,"overflow":0,"abc":432,"state1":1092,"state2":1092},
        "st":st,
        "ts":123456789,
        "tr":10000,
        "ne":nevents,
        "ds":[{"ts":32,"cnt":1,"rok":1,"bsy":1,"sev":1,"pad":12,"x":16,"y":16},296]}
    return dataHeader


def loadNeXus2event(source):

    if not os.path.isfile(source) :
        raise IOError

    print "Loading from file " + source
    if "amor" in source:
        return loadAMOR(source)
    if "rita" in source:
        return loadRITA2(source)

    raise NotImplementedError("Detector not implemented")
