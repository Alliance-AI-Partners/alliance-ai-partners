"""Scratch: dash geometry of the clear-space dashed lines (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
a = kit.load('02').astype(float)
BG = np.array([245.6, 249.8, 252.9])
LUM = np.array([0.299, 0.587, 0.114])

def along(orient, pos, lo, hi, win=3):
    img = a if orient == 'h' else a.transpose(1, 0, 2)
    p0 = int(round(pos))
    band = img[p0 - win:p0 + win + 1, lo:hi]
    dl = (BG - band) @ LUM
    integ = dl.sum(0)
    rows = np.arange(p0 - win, p0 + win + 1) + 0.5
    cen = (dl * rows[:, None]).sum(0) / np.maximum(integ, 1e-6)
    return integ, cen

def segments(integ, lo, thr):
    on = integ > thr
    segs = []
    i = 0
    n = len(integ)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            # sub-pixel crossings
            s = i - (integ[i] - thr) / (integ[i] - integ[i - 1]) if i > 0 else i
            e = j + (integ[j - 1] - thr) / (integ[j - 1] - integ[j]) if j < n else j
            segs.append((lo + s, lo + e))
            i = j
        else:
            i += 1
    return segs

if __name__ == '__main__':
    specs = [('h', 505, 705, 1000), ('h', 543, 705, 1000), ('h', 672, 705, 1000), ('h', 710, 705, 1000),
             ('v', 715.5, 495, 720), ('v', 752, 495, 720), ('v', 950, 495, 720), ('v', 988, 495, 720)]
    for o, p, lo, hi in specs:
        integ, cen = along(o, p, lo, hi)
        thr = 0.5 * np.percentile(integ, 90)
        segs = segments(integ, lo, thr)
        ok = [s for s in segs if 2 < s[1] - s[0] < 12]
        L = [round(e - s, 2) for s, e in ok]
        starts = np.array([s for s, e in ok])
        per = np.diff(starts)
        c = np.median(cen[integ > thr])
        print('%s %.1f: center=%.2f  n=%d  first=%.2f last_end=%.2f  dash len med=%.2f  period med=%.2f' % (o, p, c, len(ok), ok[0][0], ok[-1][1], np.median(L), np.median(per)))
        print('   segs:', ' '.join('%.1f-%.1f' % s for s in segs))
