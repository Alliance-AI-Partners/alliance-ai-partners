# Measure every frame boundary of original 17 with sub-pixel edge refinement on both halves,
# mirror the right half onto the left about the symmetry axis, and fit clean curves.
# Output: edges.json (polynomial coefficients + residuals) used by build_shield.py.
import json
from meas import *

AX = 687.6


def robust_polyfit(u, v, deg, iters=4, k=2.5):
    keep = np.ones(len(u), bool)
    for _ in range(iters):
        c = np.polyfit(u[keep], v[keep], deg)
        r = v - np.polyval(c, u)
        s = max(1.4826 * np.median(np.abs(r[keep])), 0.05)
        keep = np.abs(r) < k * s + 0.15
    c = np.polyfit(u[keep], v[keep], deg)
    r = v[keep] - np.polyval(c, u[keep])
    return c, float(np.sqrt((r ** 2).mean())), float(np.abs(r).max()), int(keep.sum()), len(u)


def refine_x_of_y(c0, ys, side, w=3.0, gap=1.4):
    """Boundary given roughly as x = polyval(c0, y) on the LEFT half. Refine on the given side
    ('L' or 'R'); returns mirrored-to-left points (x, y)."""
    pts = []
    for y in ys:
        x = np.polyval(c0, y)
        dxdy = np.polyval(np.polyder(c0), y)
        n = np.array([1.0, -dxdy]); n /= np.linalg.norm(n)  # left half: from outside (left) to inside
        if side == 'R':
            p, nn = np.array([2 * AX - x, y]), np.array([-n[0], n[1]])
        else:
            p, nn = np.array([x, y]), n
        q, A, B = edge_pos(p, nn, w=w, gap=gap)
        if q is None:
            continue
        if side == 'R':
            q = np.array([2 * AX - q[0], q[1]])
        pts.append(q)
    return np.array(pts)


def refine_y_of_x(c0, xs, side, w=3.0, gap=1.4, down=True):
    """Boundary roughly y = polyval(c0, x) on the left half; normal points down (+y) if down."""
    pts = []
    for x in xs:
        y = np.polyval(c0, x)
        dydx = np.polyval(np.polyder(c0), x)
        n = np.array([-dydx, 1.0]); n /= np.linalg.norm(n)
        if not down:
            n = -n
        if side == 'R':
            p, nn = np.array([2 * AX - x, y]), np.array([-n[0], n[1]])
        else:
            p, nn = np.array([x, y]), n
        q, A, B = edge_pos(p, nn, w=w, gap=gap)
        if q is None:
            continue
        if side == 'R':
            q = np.array([2 * AX - q[0], q[1]])
        pts.append(q)
    return np.array(pts)


def fit_side(name, rough_pts, ranges, deg=3, **kw):
    """rough_pts: [(y, x)] left-half rough positions. ranges: {'L': [(y0,y1)...], 'R': [...]}"""
    rp = np.array(rough_pts, float)
    c0 = np.polyfit(rp[:, 0], rp[:, 1], min(deg, len(rp) - 1))
    allp = []
    for side, rr in ranges.items():
        for (y0, y1) in rr:
            P = refine_x_of_y(c0, np.arange(y0, y1 + 1e-9, 1.0), side, **kw)
            if len(P):
                allp.append(np.c_[P, np.full(len(P), 0 if side == 'L' else 1)])
    P = np.vstack(allp)
    c, rms, mx, nk, n = robust_polyfit(P[:, 1], P[:, 0], deg)
    # per-side mean residual (asymmetry check)
    r = P[:, 0] - np.polyval(c, P[:, 1])
    asym = {s: round(float(r[P[:, 2] == i].mean()), 3) for i, s in enumerate('LR') if (P[:, 2] == i).any()}
    print(f'{name:10s} deg{deg} rms {rms:.3f} max {mx:.3f} kept {nk}/{n} side-mean-resid {asym}')
    return {'kind': 'x_of_y', 'coef': c.tolist(), 'rms': rms, 'max': mx, 'n': nk, 'side_resid': asym}, P


def fit_lowcurve(name, rough_pts, ranges, deg=3, down=True, **kw):
    rp = np.array(rough_pts, float)  # [(x, y)]
    c0 = np.polyfit(rp[:, 0], rp[:, 1], min(deg, len(rp) - 1))
    allp = []
    for side, rr in ranges.items():
        for (x0, x1) in rr:
            P = refine_y_of_x(c0, np.arange(x0, x1 + 1e-9, 1.0), side, down=down, **kw)
            if len(P):
                allp.append(np.c_[P, np.full(len(P), 0 if side == 'L' else 1)])
    P = np.vstack(allp)
    c, rms, mx, nk, n = robust_polyfit(P[:, 0], P[:, 1], deg)
    r = P[:, 1] - np.polyval(c, P[:, 0])
    asym = {s: round(float(r[P[:, 2] == i].mean()), 3) for i, s in enumerate('LR') if (P[:, 2] == i).any()}
    print(f'{name:10s} deg{deg} rms {rms:.3f} max {mx:.3f} kept {nk}/{n} side-mean-resid {asym}')
    return {'kind': 'y_of_x', 'coef': c.tolist(), 'rms': rms, 'max': mx, 'n': nk, 'side_resid': asym}, P
