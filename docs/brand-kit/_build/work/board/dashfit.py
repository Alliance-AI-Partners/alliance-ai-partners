"""Scratch: regular dash-pattern fit per dashed line (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
from dashes import along, segments

def fit(o, p, lo, hi, thr, excl=()):
    integ, cen = along(o, p, lo, hi)
    segs = segments(integ, lo, thr)
    good = [s for s in segs if 4.5 < s[1] - s[0] < 8.5 and not any(e0 <= s[0] <= e1 for e0, e1 in excl)]
    st = np.array([s for s, e in good]); en = np.array([e for s, e in good])
    # assign integer index k by rounding with a provisional period
    P0 = np.median(np.diff(st)[np.diff(st) < 11])
    k = np.round((st - st[0]) / P0)
    A = np.stack([np.ones_like(k), k], 1)
    (s0, P), *_ = np.linalg.lstsq(A, st, rcond=None)
    (e0, P2), *_ = np.linalg.lstsq(A, en, rcond=None)
    res = st - (s0 + k * P)
    c = np.median(cen[integ > thr])
    print('%s %6.1f center=%.2f n=%2d s0=%.2f P=%.3f (end-fit P=%.3f) D=%.2f  res_rms=%.2f  k_last=%d  lines: first seg %.1f-%.1f last seg %.1f-%.1f' % (
        o, p, c, len(good), s0, P, P2, e0 - s0, np.sqrt((res ** 2).mean()), k[-1], segs[0][0], segs[0][1], segs[-1][0], segs[-1][1]))
    return s0, P, e0 - s0, c

for o, p in [('h', 505), ('h', 709.6), ('v', 716), ('v', 752.7), ('v', 950), ('v', 987)]:
    fit(o, p, 705, 1000, 60) if o == 'h' else fit(o, p, 495, 720, 60)
# middle lines: only measure outside the mark
for o, p in [('h', 543.5), ('h', 671.5)]:
    fit(o, p, 705, 1000, 60)
