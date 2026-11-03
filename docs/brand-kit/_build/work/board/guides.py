"""Scratch: guide-line measurements on isolated segments + end scans (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
from lines import a, LUM

def seg(orient, pos, lo, hi, win=2):
    img = a if orient == 'h' else a.transpose(1, 0, 2)
    p0 = int(np.floor(pos))
    band = img[p0 - win:p0 + win + 2, lo:hi]
    bgs = np.concatenate([img[p0 - win - 3:p0 - win, lo:hi], img[p0 + win + 2:p0 + win + 5, lo:hi]], 0)
    bg = np.median(bgs, 0)
    d = bg[None] - band
    dl = d @ LUM
    integ = dl.sum(0)
    rows = np.arange(p0 - win, p0 + win + 2) + 0.5
    cen = (dl * rows[:, None]).sum(0) / np.where(np.abs(integ) < 1e-6, 1, integ)
    return np.median(cen), np.median(integ), np.median(d.sum(0), 0), integ, np.median(bg, 0)

def endscan(orient, pos, lo, hi, win=2):
    _, med, _, integ, _ = seg(orient, pos, lo, hi, win)
    on = integ > 0.5 * med
    idx = np.nonzero(on)[0]
    return lo + idx[0], lo + idx[-1] + 1, med

H = [(205.0, [(31, 62), (75, 170), (320, 400), (500, 650)]),
     (264.0, [(375, 400), (405, 515), (520, 535), (545, 650), (657, 680)]),
     (293.5, [(375, 398), (521, 535), (658, 680)]),
     (410.0, [(35, 60), (70, 395), (522, 535), (658, 680)])]
V = [(61.5, [(188, 200), (212, 335), (395, 435)]),
     (371.0, [(188, 330), (395, 435)]),
     (401.5, [(188, 200), (268, 290), (413, 435)]),
     (517.5, [(268, 290), (413, 435)]),
     (538.5, [(268, 290), (413, 435)]),
     (654.0, [(188, 200), (268, 290), (413, 435)])]
for o, L in (('h', H), ('v', V)):
    for pos, segs in L:
        for lo, hi in segs:
            c, m, ch, _, bg = seg(o, pos, lo, hi)
            print('%s %6.1f seg %3d..%3d center=%.2f integL=%5.1f chan=%s bg=%s' % (o, pos, lo, hi, c, m, ch.round(1), bg.round(1)))
# end scans
for o, pos, lo, hi in [('h', 205, 0, 120), ('h', 205, 600, 720), ('h', 410, 0, 120), ('h', 410, 600, 720),
                       ('h', 264, 340, 400), ('h', 264, 640, 720), ('h', 293.5, 340, 400), ('h', 293.5, 640, 720),
                       ('v', 61.5, 150, 230), ('v', 61.5, 400, 450), ('v', 371, 150, 230), ('v', 371, 400, 450),
                       ('v', 401.5, 150, 200), ('v', 654, 150, 200), ('v', 517.5, 240, 290), ('v', 538.5, 240, 290),
                       ('v', 517.5, 412, 450), ('v', 654, 412, 450)]:
    print('end', o, pos, lo, hi, endscan(o, pos, lo, hi))
