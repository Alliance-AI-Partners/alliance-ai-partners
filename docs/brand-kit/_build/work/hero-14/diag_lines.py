"""Print the sub-pixel edge points of one feature (binned) to judge straightness and ranges.
usage: python diag_lines.py rows|cols LEFT_LABELS RIGHT_LABELS lo hi [step]"""
import sys
import numpy as np
from common import kit, W14
from seg14 import NAMES
from lines import row_edges, col_edges

L = {n: k for k, n in enumerate(NAMES)}

if __name__ == '__main__':
    mode = sys.argv[1]
    a = [L[n] for n in sys.argv[2].split(',')]
    b = [L[n] for n in sys.argv[3].split(',')]
    lo, hi = int(sys.argv[4]), int(sys.argv[5])
    step = int(sys.argv[6]) if len(sys.argv) > 6 else 4
    rgb = kit.load('14')
    lab = np.load(W14 / 'labels14.npy')
    pts = np.asarray(row_edges(rgb, lab, a, b, (lo, hi)) if mode == 'rows' else col_edges(rgb, lab, a, b, (lo, hi)))
    u = pts[:, 1] if mode == 'rows' else pts[:, 0]
    v = pts[:, 0] if mode == 'rows' else pts[:, 1]
    A = np.stack([u, np.ones_like(u)], 1)
    (k, c), *_ = np.linalg.lstsq(A, v, rcond=None)
    print('global fit v = %.5f u + %.3f' % (k, c))
    for s in range(lo, hi, step):
        m = (u >= s) & (u < s + step)
        if m.any():
            print('%4d-%4d  n%2d  v %.2f  resid %+.2f' % (s, s + step, m.sum(), v[m].mean(), (v[m] - (k * u[m] + c)).mean()))
