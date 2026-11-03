"""Fit one line to the edge points of a feature over given ranges; print residual bands.
usage: python diag_seg.py rows|cols LEFT RIGHT lo-hi[,lo-hi...] [band]"""
import sys
import numpy as np
from common import kit, W14
from seg14 import NAMES
from lines import row_edges, col_edges, fit_line

L = {n: k for k, n in enumerate(NAMES)}

if __name__ == '__main__':
    mode = sys.argv[1]
    a = [L[n] for n in sys.argv[2].split(',')]
    b = [L[n] for n in sys.argv[3].split(',')]
    rngs = [tuple(int(v) for v in r.split('-')) for r in sys.argv[4].split(',')]
    band = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    rgb = kit.load('14')
    lab = np.load(W14 / 'labels14.npy')
    pts = []
    for r in rngs:
        pts += row_edges(rgb, lab, a, b, r) if mode == 'rows' else col_edges(rgb, lab, a, b, r)
    pts = np.asarray(pts)
    k, c, rms, n, res = fit_line(pts, 'y' if mode == 'rows' else 'x')
    u = pts[:, 1] if mode == 'rows' else pts[:, 0]
    print('fit v = %.5f u + %.3f  rms %.3f  n %d/%d  angle %.3f deg' % (k, c, rms, n, len(pts), np.degrees(np.arctan(k))))
    for s in range(int(u.min()), int(u.max()) + 1, band):
        m = (u >= s) & (u < s + band)
        if m.any():
            print('  %4d-%4d n%2d resid %+.2f' % (s, s + band, m.sum(), res[m].mean()))
