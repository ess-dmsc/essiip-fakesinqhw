import numpy as np

event_t = np.dtype([("ts",np.uint32),
                    ("data",np.uint32)])

def multiplyNEventArray(data,multiplier) :
    return np.tile(data,multiplier)
