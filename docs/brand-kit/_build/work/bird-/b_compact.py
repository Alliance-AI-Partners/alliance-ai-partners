import numpy as np
def compact(V, F):
    used = sorted({v for f in F for v in f})
    remap = {v: i for i, v in enumerate(used)}
    return np.asarray(V)[used].copy(), [[remap[v] for v in f] for f in F]
