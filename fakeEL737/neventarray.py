import numpy as np

event_t = np.dtype([("ts",np.uint32),
                    ("sync",np.uint16),
                    ("x",np.uint16),
                    ("y",np.uint16)])

debug_t = np.dtype([("ts",np.uint32),
                    ("sync",np.uint16),
                    ("channel",(np.void,4)),
                    ("pso",(np.void,12))])

def multiplyNEventArray(data,multiplier) :
#    return NEventArray(np.tile(data[0],multiplier), 
#                       np.tile(data[1],multiplier))
    return np.tile(data,multiplier)
