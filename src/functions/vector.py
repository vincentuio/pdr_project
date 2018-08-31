import numpy as np

def norm(v):
    return np.sqrt(np.sum(np.power(v, 2)))

def normalise(v):
    if norm(v) != 0:
        return v / norm(v)
    else:
        return 0