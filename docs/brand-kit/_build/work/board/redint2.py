"""Scratch: red color estimate from dash interiors (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from redint import a, BG, LUM

def dash_cols(row, lo, hi):
    """columns where row is dark (dash interiors), excluding 1px at each dash end."""
    d = (BG - a[row - 1:row + 2, lo:hi]).sum(0) @ LUM
    on = d > 0.6 * np.percentile(d, 95)
    keep = on & np.roll(on, 1) & np.roll(on, -1)
    return lo + np.nonzero(keep)[0]

def est_cols(orient, pos, idxs, label, win=5):
    img = a if orient == 'h' else a.transpose(1, 0, 2)
    p0 = int(round(pos))
    band = img[p0 - win:p0 + win + 1][:, idxs]
    p = (BG - band).mean(1)
    integ = p.sum(0); pl = p @ LUM
    w = pl.sum() / pl.max()
    out = []
    for ww in (w, 1.6, 1.8):
        c = BG - integ / ww
        out.append('w=%.2f %s' % (ww, kit.rgbhex(c)))
    print('%-22s n=%3d integ=%s  %s' % (label, len(idxs), integ.round(1), ' | '.join(out)))
    return integ, w

# horizontal dashed lines: rows ~505, 543, 672, 710 ; vertical ~715, 752, 950, 988
for row, lo, hi in [(505, 720, 850), (505, 870, 985), (543, 720, 745), (543, 760, 800), (710, 720, 850), (710, 870, 985)]:
    cols = dash_cols(row, lo, hi)
    est_cols('h', row, cols, 'dash h %d %d..%d' % (row, lo, hi))
at = a.transpose(1, 0, 2)
def dash_rows(col, lo, hi):
    d = (BG - at[col - 1:col + 2, lo:hi]).sum(0) @ LUM
    on = d > 0.6 * np.percentile(d, 95)
    keep = on & np.roll(on, 1) & np.roll(on, -1)
    return lo + np.nonzero(keep)[0]
for col, lo, hi in [(715, 512, 600), (715, 610, 705), (752, 550, 590), (988, 512, 600), (950, 550, 590)]:
    rows = dash_rows(col, lo, hi)
    est_cols('v', col, rows, 'dash v %d %d..%d' % (col, lo, hi))
