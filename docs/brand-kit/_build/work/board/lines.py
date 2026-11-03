"""Scratch: measure straight lines (center, darkness integral, extent) in original 02 (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

a = kit.load('02').astype(float)
LUM = np.array([0.299, 0.587, 0.114])


def measure(orient, pos, lo, hi, win=4, show_runs=True, thr=0.5):
    """orient 'h': line near row `pos` scanned over columns lo..hi; 'v': near column `pos` over rows lo..hi."""
    img = a if orient == 'h' else a.transpose(1, 0, 2)
    p0 = int(round(pos))
    band = img[p0 - win:p0 + win + 1, lo:hi]                    # (2win+1, n, 3)
    bgs = np.concatenate([img[p0 - win - 3:p0 - win, lo:hi], img[p0 + win + 1:p0 + win + 4, lo:hi]], 0)
    bg = np.median(bgs, 0)                                       # (n, 3)
    d = (bg[None] - band)                                        # darkness per channel
    dl = d @ LUM                                                 # (2win+1, n)
    integ = dl.sum(0)
    rows = np.arange(p0 - win, p0 + win + 1) + 0.5
    cen = (dl * rows[:, None]).sum(0) / np.where(np.abs(integ) < 1e-6, 1, integ)
    med = np.median(integ[integ > 0.3 * integ.max()])
    on = integ > thr * med
    # runs
    runs, s = [], None
    for i, v in enumerate(on):
        if v and s is None:
            s = i
        if not v and s is not None:
            runs.append((lo + s, lo + i)); s = None
    if s is not None:
        runs.append((lo + s, lo + len(on)))
    sel = on & (integ > 0.8 * med) & (integ < 1.2 * med)
    chan = d.sum(0)[sel].mean(0) if sel.any() else d.sum(0).mean(0)
    print('%s pos~%s range %d..%d: center=%.2f integL=%.1f chan=%s' % (orient, pos, lo, hi, np.median(cen[sel]) if sel.any() else -1, med, chan.round(1)))
    if show_runs:
        print('   runs:', [(r0, r1) for r0, r1 in runs if r1 - r0 >= 3])
    return np.median(cen[sel]), med, chan, runs, integ


if __name__ == '__main__':
    o, pos, lo, hi = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    win = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    measure(o, pos, lo, hi, win)
