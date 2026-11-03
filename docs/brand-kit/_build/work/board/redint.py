"""Scratch: per-channel integrals of thin red features -> width + color estimate (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
a = kit.load('02').astype(float)
BG = np.array([245.6, 249.8, 252.9])
LUM = np.array([0.299, 0.587, 0.114])

def prof(orient, pos, lo, hi, win=5):
    img = a if orient == 'h' else a.transpose(1, 0, 2)
    p0 = int(round(pos))
    band = img[p0 - win:p0 + win + 1, lo:hi]
    d = BG - band                       # (rows, n, 3)
    return d.mean(1)                    # mean profile per row (rows, 3)

def est(orient, pos, lo, hi, label, win=5):
    p = prof(orient, pos, lo, hi, win)
    integ = p.sum(0)                    # per channel
    pl = p @ LUM
    il = pl.sum()
    # width from luma: assume profile = box(w) sampled; w ~ integral / peak when peak pixel is fully covered
    peak = pl.max()
    w_est = il / peak
    for w in (w_est, 1.0, 1.5, 2.0):
        c = BG - integ / w
        print('%-20s w=%.2f color=%s %s  (integL=%.1f peakL=%.1f)' % (label, w, c.round(1), kit.rgbhex(c), il, peak))
    print('   luma profile', pl.round(1))

est('h', 505, 721, 728, 'dash h top (1 dash)')
est('h', 505, 731, 737, 'dash h top (dash2)')
est('v', 715.5, 515, 518, 'dash v left')
est('v', 715.5, 522, 527, 'dash v left 2')
est('v', 858, 515, 532, 'arrow shaft v')
est('h', 602, 722, 745, 'arrow shaft h')
