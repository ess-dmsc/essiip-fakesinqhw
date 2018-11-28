import sys
import os
import errno
import time
import json
import numpy as np

def header(pid=1234,st=time.time(),ts=np.random.randint(3200000000),ne=0):
    with open("header.in") as i:
        h = json.load(i)
    i.close()

    h["pid"]   = pid
    h["st"]    = st
    h["ts"]    = ts
    h["ds"][1] = ne
    
    return json.dumps(h)
    

def control():
    with open("control.in") as i:
        ctl = json.load(i)
    i.close()
    return ctl

def set_ds(d,ctl):
    for i in d:
        i["data"] = (i["data"] & 0xffffff) | (ctl["bsy"] << 31 | ctl["cnt"] << 30 | ctl["rok"] << 29 | ctl["gat"] << 28 | ctl["evt"] << 24)
    return d
