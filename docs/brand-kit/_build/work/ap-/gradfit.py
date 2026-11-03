"""Least-squares linear-gradient fit in sRGB: colour = piecewise-linear function of the projection of
the pixel position on a direction, with K stops (hat basis, padded at both ends, as SVG/Illustrator do).
Stops are only placed where the face has visible pixels and never outside the observed colour range,
so hidden parts of a face cannot pull a stop to an invented colour."""
import itertools
import numpy as np


def hat_basis(s, knots):
    """s (N,), knots (K,) increasing -> (N, K) piecewise-linear interpolation weights, clamped."""
    knots = np.asarray(knots, float)
    s = np.clip(s, knots[0], knots[-1])
    K = len(knots)
    B = np.zeros((len(s), K))
    idx = np.clip(np.searchsorted(knots, s, side='right') - 1, 0, K - 2)
    t = (s - knots[idx]) / np.maximum(knots[idx + 1] - knots[idx], 1e-9)
    B[np.arange(len(s)), idx] = 1 - t
    B[np.arange(len(s)), idx + 1] += t
    return B


def solve(B, c, extra=None):
    """LSQ for stop colours; extra = (rows (M,K), targets (M,3)) appended as weighted constraints."""
    if extra is not None:
        B2 = np.vstack([B, extra[0]]); c2 = np.vstack([c, extra[1]])
    else:
        B2, c2 = B, c
    X, *_ = np.linalg.lstsq(B2, c2, rcond=None)
    r = c - B @ X
    return X, float((r * r).sum(1).mean())


def unit(ang):
    return np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])


def supported(s, k, n_min=40, w=1.5):
    return int((np.abs(s - k) < w).sum()) >= n_min


def in_range(X, c, margin=12.0):
    lo, hi = c.min(0) - margin, c.max(0) + margin
    return bool(((X >= lo) & (X <= hi)).all())


def fit(xy, c, Kmax=4, angles=None, improve=0.8, n_min=None, n_cand=12, pad=None):
    """xy (N,2), c (N,3) sRGB 0..255 -> dict(K, angle, u, knots, colors, mse).
    Every K gets its own direction search; K>2 uses end knots at the 0.5/99.5% projection quantiles
    and middle knots on data-supported positions; stops must stay inside the observed colour range."""
    xy = np.asarray(xy, float); c = np.asarray(c, float)
    N = len(xy)
    n_min = n_min if n_min is not None else max(10, N // 400)
    if angles is None:
        angles = np.arange(0, 180, 3.0)
    angles = np.asarray(angles, float)
    pad = None if pad is None else np.asarray(pad, float)

    def pad_ok(s_pad, a, b):
        """the gradient is flat (padded) over the `pad` points: all their projections beyond one end"""
        return s_pad is None or s_pad.max() <= a + 0.5 or s_pad.min() >= b - 0.5

    def best_k2(angs, grid):
        best = None
        for ang in angs:
            u = unit(ang)
            s = xy @ u
            sp = None if pad is None else pad @ u
            qs = np.quantile(s, np.linspace(0, 1, grid + 1))
            if sp is not None:
                qs = np.unique(np.concatenate([qs, [sp.min(), sp.max()]]))
            for a in qs[:max(2, len(qs) // 2 + 1)]:
                for b in qs[len(qs) // 2 - 1:]:
                    if b - a < 2 or not pad_ok(sp, a, b):
                        continue
                    X, mse = solve(hat_basis(s, [a, b]), c)
                    if best is None or mse < best['mse']:
                        best = {'K': 2, 'angle': float(ang), 'u': u, 'knots': np.array([a, b]), 'colors': X, 'mse': mse}
        return best

    def best_k(K, angs):
        best = None
        for ang in angs:
            u = unit(ang)
            s = xy @ u
            a, b = np.quantile(s, [0.005, 0.995])
            if pad is not None:
                sp = pad @ u
                if abs(sp.mean() - a) < abs(sp.mean() - b):
                    a = max(a, sp.max())
                else:
                    b = min(b, sp.min())
                if b - a < 8:
                    continue
            cand = [k for k in np.linspace(a, b, n_cand + 2)[1:-1] if supported(s, k, n_min)]
            for mids in itertools.combinations(cand, K - 2):
                knots = np.array((a,) + mids + (b,))
                X, mse = solve(hat_basis(s, knots), c)
                if not in_range(X, c):
                    continue
                if best is None or mse < best['mse']:
                    best = {'K': K, 'angle': float(ang), 'u': u, 'knots': knots, 'colors': X, 'mse': mse}
        return best

    step = angles[1] - angles[0] if len(angles) > 1 else 1.0
    g = best_k2(angles, 8)
    g = best_k2(g['angle'] + np.arange(-step, step + 0.01, 0.5), 16)
    out = g
    for K in range(3, Kmax + 1):
        gk = best_k(K, angles)
        if gk is None:
            continue
        gk = best_k(K, gk['angle'] + np.arange(-step, step + 0.01, 1.0)) or gk
        if gk['mse'] < out['mse'] * improve:
            out = gk
    return out


def predict(g, xy):
    if g['K'] == 1:
        return np.repeat(g['colors'], len(xy), 0)
    s = np.asarray(xy, float) @ g['u']
    return hat_basis(s, g['knots']) @ g['colors']


def joint(faces, seams, lam=3.0):
    """Re-solve the stop colours of several faces together so their colours agree along seams.
    faces: {name: (xy, c, g)}; seams: [(nameA, nameB, pts (M,2))]. Directions/knots are kept.
    Returns {name: colors}."""
    names = list(faces)
    off = {}
    k0 = 0
    for n in names:
        off[n] = k0; k0 += faces[n][2]['K']
    rows, tg = [], []
    for n in names:
        xy, c, g = faces[n]
        B = hat_basis(xy @ g['u'], g['knots'])
        R = np.zeros((len(xy), k0)); R[:, off[n]:off[n] + g['K']] = B
        rows.append(R / np.sqrt(len(xy))); tg.append(c / np.sqrt(len(xy)))
    for A, Bn, pts in seams:
        gA, gB = faces[A][2], faces[Bn][2]
        R = np.zeros((len(pts), k0))
        R[:, off[A]:off[A] + gA['K']] = hat_basis(pts @ gA['u'], gA['knots'])
        R[:, off[Bn]:off[Bn] + gB['K']] -= hat_basis(pts @ gB['u'], gB['knots'])
        rows.append(lam * R / np.sqrt(len(pts))); tg.append(np.zeros((len(pts), 3)))
    X, *_ = np.linalg.lstsq(np.vstack(rows), np.vstack(tg), rcond=None)
    return {n: X[off[n]:off[n] + faces[n][2]['K']] for n in names}


def svg_vector(g, center):
    """Gradient line endpoints through `center` and stop offsets for an SVG linearGradient."""
    u = g['u']; k = np.asarray(g['knots'], float)
    c0 = np.asarray(center, float)
    base = c0 - (c0 @ u) * u
    p1 = base + k[0] * u
    p2 = base + k[-1] * u
    offs = (k - k[0]) / (k[-1] - k[0])
    return p1, p2, offs
