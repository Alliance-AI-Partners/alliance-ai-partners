"""Scratch: edge spread of the original (tile edges) -> blur sigma, tile edges and corners (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from math import erf, sqrt
a = kit.load('02').astype(float)
BG = np.array([245.2, 249.4, 252.6]); NAVY = np.array([18.0, 29.0, 48.5])
v = NAVY - BG


def alpha(p):
    return ((p - BG) @ v) / (v @ v)


def edge(orient, lo, hi, a0, a1, label):
    if orient == 'v':   # vertical edge: profile along x for rows lo..hi, x from a0..a1
        prof = alpha(a[lo:hi, a0:a1]).mean(0)
    else:
        prof = alpha(a[a0:a1, lo:hi]).mean(1)
    xs = np.arange(a0, a1) + 0.5
    best = None
    for s in np.linspace(0.2, 1.5, 27):
        for c in np.linspace(a0 + 1, a1 - 1, 400):
            f = np.array([0.5 * (1 + erf((x - c) / (s * sqrt(2)))) for x in xs])
            if prof[0] > prof[-1]:
                f = 1 - f
            A = np.stack([f, np.ones_like(f)], 1)
            coef, res, *_ = np.linalg.lstsq(A, prof, rcond=None)
            err = ((A @ coef - prof) ** 2).sum()
            if best is None or err < best[0]:
                best = (err, s, c, coef)
    print('%-22s sigma=%.2f edge=%.2f amp=%.3f off=%.3f  prof=%s' % (label, best[1], best[2], best[3][0], best[3][1], prof.round(2)))
    return best[2]


if __name__ == '__main__':
    edge('v', 300, 400, 396, 408, 'tile1 left')
    edge('v', 300, 400, 511, 523, 'tile1 right')
    edge('h', 410, 510, 288, 300, 'tile1 top')
    edge('h', 410, 510, 404, 416, 'tile1 bottom')
    edge('v', 300, 400, 533, 545, 'tile2 left')
    edge('v', 300, 400, 648, 660, 'tile2 right')
    edge('h', 545, 650, 288, 300, 'tile2 top')
    edge('h', 545, 650, 404, 416, 'tile2 bottom')
    for name, (cx, cy) in {'t1 TL': (401, 293), 't1 TR': (517, 293), 't1 BL': (401, 410), 't1 BR': (517, 410),
                           't2 TL': (538, 293), 't2 TR': (654, 293), 't2 BL': (538, 410), 't2 BR': (654, 410)}.items():
        print(name, np.round(alpha(a[cy - 1:cy + 3, cx - 1:cx + 3]), 2).tolist())
