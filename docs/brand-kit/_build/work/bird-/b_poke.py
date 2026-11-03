"""Exact check: does any extended facet cover area outside the union of the exact facets?"""
import numpy as np

def sub_inside(P, x0, y0, w, h, ss=8):
    xa = P[:, 0]; ya = P[:, 1]; xb = np.roll(xa, -1); yb = np.roll(ya, -1)
    H, Wd = h * ss, w * ss
    acc = np.zeros((H, Wd + 1), np.int32)
    for k in range(len(P)):
        if ya[k] == yb[k]:
            continue
        lo, hi = min(ya[k], yb[k]), max(ya[k], yb[k])
        m0 = max(int(np.ceil((lo - y0) * ss - 0.5)), 0); m1 = min(int(np.ceil((hi - y0) * ss - 0.5)), H)
        if m1 <= m0:
            continue
        yy = y0 + (np.arange(m0, m1) + 0.5) / ss
        xx = xa[k] + (yy - ya[k]) * (xb[k] - xa[k]) / (yb[k] - ya[k])
        col = np.clip(np.ceil((xx - x0) * ss - 0.5).astype(np.int64), 0, Wd)
        acc[np.arange(m0, m1), col] += 1 if yb[k] > ya[k] else -1
    return np.cumsum(acc[:, :-1], 1) != 0

def poke_report(exact, ext, box=(258, 217, 510, 391), ss=8):
    x0, y0, w, h = box
    UE = np.zeros((h * ss, w * ss), bool)
    for P in exact:
        UE |= sub_inside(P, x0, y0, w, h, ss)
    rep = []
    for i, P in enumerate(ext):
        p = sub_inside(P, x0, y0, w, h, ss) & ~UE
        if p.any():
            cov = p.reshape(h, ss, w, ss).mean((1, 3))
            ys, xs = np.nonzero(cov == cov.max())
            rep.append((i, float(cov.max()), int(p.sum()), (int(xs[0] + x0), int(ys[0] + y0))))
    return rep
