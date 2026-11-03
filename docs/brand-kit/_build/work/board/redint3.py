"""Scratch: full-period integrals of dashed lines vs continuous arrow shafts (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from redint import a, BG, LUM

def full(orient, pos, lo, hi, win=5):
    img = a if orient == 'h' else a.transpose(1, 0, 2)
    p0 = int(round(pos))
    band = img[p0 - win:p0 + win + 1, lo:hi]
    d = (BG - band)            # rows, n, 3
    per_col = d.sum(0)         # n, 3 (integral across line)
    lum = per_col @ LUM
    duty = (lum > 0.5 * np.percentile(lum, 90)).mean()
    m = per_col.mean(0)
    return m, duty, lum

for spec in [('h', 505, 720, 850), ('h', 505, 870, 985), ('h', 710, 720, 850), ('h', 710, 870, 985), ('v', 715, 512, 600), ('v', 988, 512, 600), ('v', 715, 610, 700)]:
    m, duty, lum = full(*spec)
    r = m / m[2]
    print(spec, 'mean integ', m.round(1), 'ratio', r.round(3), 'duty', round(duty, 3))
for spec in [('v', 858, 515, 532), ('h', 602, 722, 745), ('h', 602, 958, 980), ('v', 858, 680, 700)]:
    m, duty, lum = full(*spec)
    print('shaft', spec, 'mean integ', m.round(1), 'ratio', (m / m[2]).round(3))
