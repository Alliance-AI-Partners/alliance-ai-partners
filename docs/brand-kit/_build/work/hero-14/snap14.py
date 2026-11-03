"""Known straight lines of 14 for the path rebuild. 14's leg edges have an upper and a lower line that run
within a pixel of each other, so every line only snaps contour points inside its own span
(work/ap-/fitcurve.py's line_runs is wrapped with that test; the rest of its rebuild is reused as is)."""
import numpy as np
import common  # noqa: F401  (puts kit and the 06 pipeline on the path)
import fitcurve
from fitcurve import Line

_line_runs = fitcurve.line_runs


class SLine(Line):
    def __init__(self, n, d, name='', axis=1, lo=-1e9, hi=1e9):
        super().__init__(n, d, name)
        self.axis, self.lo, self.hi = axis, lo, hi

    def inspan(self, p):
        v = np.asarray(p)[:, self.axis]
        return (v >= self.lo) & (v <= self.hi)


def span_line_runs(p, lines, step, dtol=0.8, atol=5.0, min_len=10.0):
    out = []
    for L in lines:
        if not isinstance(L, SLine):
            out += _line_runs(p, [L], step, dtol, atol, min_len)
            continue
        # evaluate on a copy of p where out-of-span points are pushed far from the line
        q = np.array(p, float)
        far = ~L.inspan(q)
        q[far] += L.n * 1e6
        out += [(i0, i1, L) for i0, i1, _ in _line_runs(q, [L], step, dtol, atol, min_len)]
    return out


fitcurve.line_runs = span_line_runs


def make(ln, names):
    """SLine objects for the named lines of lines14.json"""
    out = []
    for n in names:
        l = ln[n]
        k = l['kind']
        lo, hi = l.get('span', (-1e9, 1e9))
        if k == 'xy':      # x = a y + b, span in y
            out.append(SLine((1, -l['a']), l['b'], n, axis=1, lo=lo, hi=hi))
        elif k == 'h':     # y = c, span in x
            out.append(SLine((0, 1), l['c'], n, axis=0, lo=lo, hi=hi))
        elif k == 'v':     # x = c, span in y
            out.append(SLine((1, 0), l['c'], n, axis=1, lo=lo, hi=hi))
        elif k == 'pd':    # through p along d, span in x
            p, d = np.asarray(l['p']), np.asarray(l['d'])
            nn = np.array([-d[1], d[0]])
            lo, hi = l.get('span', (p[0] - 40, p[0] + 40))
            out.append(SLine(nn, float(nn @ p), n, axis=0, lo=lo, hi=hi))
        elif k == 'cut_h':
            out.append(SLine((0, 1), l['c'], n, axis=0, lo=lo, hi=hi))
        elif k == 'cut_v':
            out.append(SLine((1, 0), l['c'], n, axis=1, lo=lo, hi=hi))
    return out


if __name__ == '__main__':
    # self-check: a point run on the upper line but outside its span must not snap to it
    L1 = SLine((1, -0.5), 300.0, 'u', axis=1, lo=300, hi=420)
    ys = np.arange(300, 520, 0.5)
    p = np.stack([0.5 * ys + 300.0, ys], 1)
    runs = span_line_runs(p, [L1], 0.5)
    assert runs and all(p[i1, 1] <= 420.5 and p[i0, 1] >= 299.5 for i0, i1, _ in runs), runs
    print('ok', [(p[i0, 1], p[i1, 1]) for i0, i1, _ in runs])
