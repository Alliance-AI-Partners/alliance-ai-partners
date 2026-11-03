"""Similarity fit (scale, rotation, translation) of the master bird silhouette onto another original by mask IoU."""
import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit


def cover_loops(loops, x0, y0, w, h, ss=2):
    """Even-odd coverage of several closed loops (list of (n,2) arrays)."""
    H, Wd = h * ss, w * ss
    acc = np.zeros((H, Wd + 1), np.int32)
    for poly in loops:
        xa = poly[:, 0]; ya = poly[:, 1]
        xb = np.roll(xa, -1); yb = np.roll(ya, -1)
        for k in range(len(poly)):
            if ya[k] == yb[k]:
                continue
            lo, hi = (ya[k], yb[k]) if ya[k] < yb[k] else (yb[k], ya[k])
            m0 = max(int(np.ceil((lo - y0) * ss - 0.5)), 0)
            m1 = min(int(np.ceil((hi - y0) * ss - 0.5)), H)
            if m1 <= m0:
                continue
            yy = y0 + (np.arange(m0, m1) + 0.5) / ss
            xx = xa[k] + (yy - ya[k]) * (xb[k] - xa[k]) / (yb[k] - ya[k])
            col = np.clip(np.ceil((xx - x0) * ss - 0.5).astype(np.int64), 0, Wd)
            acc[np.arange(m0, m1), col] += 1
    inside = (np.cumsum(acc[:, :-1], axis=1) % 2) == 1
    return inside.reshape(h, ss, w, ss).mean((1, 3))


def similarity(params, center):
    s, th, tx, ty = params
    c, si = np.cos(th), np.sin(th)
    A = s * np.array([[c, -si], [si, c]])
    t = np.array([tx, ty]) - A @ np.asarray(center)
    return A, t   # X = A @ p + t


def apply(A, t, pts):
    return pts @ A.T + t


def nelder_mead(f, x0, steps, iters=300, tol=1e-7):
    n = len(x0)
    pts = [np.array(x0, float)] + [np.array(x0, float) + np.eye(n)[i] * steps[i] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = np.argsort(vals); pts = [pts[i] for i in order]; vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol:
            break
        c = np.mean(pts[:-1], 0)
        xr = c + (c - pts[-1]); fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


def fit_placement(loops_master, target_mask, region):
    """region: (x0, y0, x1, y1) in target px containing the bird. Returns params, IoU, (A, t)."""
    x0, y0, x1, y1 = region
    tm = target_mask[y0:y1, x0:x1]
    ys, xs = np.nonzero(tm)
    allm = np.concatenate(loops_master)
    mc = 0.5 * (allm.min(0) + allm.max(0))
    mw = allm[:, 0].max() - allm[:, 0].min()
    s0 = (xs.max() - xs.min() + 1) / mw
    p0 = [s0, 0.0, x0 + 0.5 * (xs.min() + xs.max() + 1), y0 + 0.5 * (ys.min() + ys.max() + 1)]

    def neg_iou(p):
        A, t = similarity(p, mc)
        cov = cover_loops([apply(A, t, L) for L in loops_master], x0, y0, x1 - x0, y1 - y0, 2)
        m = cov >= 0.5
        return -float((m & tm).sum() / max(1, (m | tm).sum()))

    best, val = nelder_mead(neg_iou, p0, [0.02 * s0, 0.01, 2.0, 2.0], iters=400)
    best, val = nelder_mead(neg_iou, best, [0.004 * s0, 0.003, 0.5, 0.5], iters=300)
    return best, -val, similarity(best, mc), mc
