"""Linear-gradient fit for one face: colour = piecewise-linear (hat basis, padded ends) function of the
projection on a direction; stop colours by least squares in sRGB. Unlike gradfit.fit's grid search, the
direction and the stop positions are refined continuously (coordinate descent with shrinking steps) from
the best grid starts. Constraints as gradfit: stops only inside the face's visible pixels (0.5..99.5 %
projection quantiles), stop colours inside the observed range, optional flat ('pad') zone over seam points."""
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\ap-')
from gradfit import hat_basis, solve, unit


def _mse(xy, c, ang, knots, lo, hi, cmin, cmax, sp_pad, pad_end):
    k = np.asarray(knots, float)
    if k[0] < lo - 1e-9 or k[-1] > hi + 1e-9 or np.any(np.diff(k) < 1.5):
        return np.inf, None
    u = unit(ang)
    if sp_pad is not None:
        s_p = sp_pad(u)
        if pad_end == 0 and s_p.max() > k[0] + 0.5:
            return np.inf, None
        if pad_end == 1 and s_p.min() < k[-1] - 0.5:
            return np.inf, None
    B = hat_basis(xy @ u, k)
    X, *_ = np.linalg.lstsq(B, c, rcond=None)
    if np.any(X < cmin) or np.any(X > cmax):
        return np.inf, None
    r = c - B @ X
    return float((r * r).sum(1).mean()), X


def fit(xy, c, Kmax=5, angles=None, improve=0.9, pad=None, nsub=2000, seed=7, angle_bounds=None):
    """-> dict(K, angle, u, knots, colors, mse) like gradfit.fit. angle_bounds=(lo, hi) keeps the direction
    inside that range (e.g. a face between two horizontal cuts must stay vertical to meet both seamlessly)."""
    xy = np.asarray(xy, float); c = np.asarray(c, float)
    rng = np.random.default_rng(seed)
    idx = np.arange(len(xy)) if len(xy) <= nsub else np.sort(rng.choice(len(xy), nsub, replace=False))
    xs, cs = xy[idx], c[idx]
    cmin, cmax = c.min(0) - 12.0, c.max(0) + 12.0
    angles = np.arange(0, 180, 4.0) if angles is None else np.asarray(angles, float)
    pad = None if pad is None or len(pad) == 0 else np.asarray(pad, float)

    def bounds(ang):
        s = xy @ unit(ang)
        lo, hi = np.quantile(s, [0.005, 0.995])
        pad_end = None
        if pad is not None:
            sp = pad @ unit(ang)
            pad_end = 0 if abs(sp.mean() - lo) < abs(sp.mean() - hi) else 1
        return lo, hi, pad_end

    sp_pad = None if pad is None else (lambda u: pad @ u)

    def evaluate(ang, knots):
        if angle_bounds is not None and not (angle_bounds[0] <= ang <= angle_bounds[1]):
            return np.inf
        lo, hi, pe = bounds(ang)
        return _mse(xs, cs, ang, knots, lo, hi, cmin, cmax, sp_pad, pe)[0]

    def start_knots(ang, K):
        lo, hi, pe = bounds(ang)
        if pad is not None:
            sp = pad @ unit(ang)
            if pe == 0:
                lo = max(lo, sp.max() + 0.6)
            else:
                hi = min(hi, sp.min() - 0.6)
        if hi - lo < 2 * (K - 1):
            return None
        s = np.clip(xy @ unit(ang), lo, hi)
        return np.quantile(s, np.linspace(0, 1, K)) if K > 2 else np.array([lo, hi])

    def descend(ang, knots):
        best = evaluate(ang, knots)
        span = max(4.0, (knots[-1] - knots[0]) / 8)
        for st_a, st_k in ((2.0, span), (1.0, span / 2), (0.5, span / 4), (0.25, 1.0), (0.1, 0.4)):
            improved = True
            while improved:
                improved = False
                for da in (st_a, -st_a):
                    v = evaluate(ang + da, knots)
                    if v < best - 1e-9:
                        best, ang, improved = v, ang + da, True
                for j in range(len(knots)):
                    for dk in (st_k, -st_k):
                        k2 = knots.copy(); k2[j] += dk
                        v = evaluate(ang, k2)
                        if v < best - 1e-9:
                            best, knots, improved = v, k2, True
        return best, ang, knots

    out, prev = None, None
    for K in range(2, Kmax + 1):
        starts = []
        for a in angles:
            k0 = start_knots(a, K)
            if k0 is not None:
                starts.append((evaluate(a, k0), a, k0))
        starts = sorted([s for s in starts if np.isfinite(s[0])], key=lambda s: s[0])[:3]
        if prev is not None:     # also grow the best (K-1) solution by one stop in each gap
            k = prev['knots']
            starts += [(0, prev['angle'], np.insert(k, j + 1, (k[j] + k[j + 1]) / 2)) for j in range(len(k) - 1)]
        best = None
        for _, a, k0 in starts:
            v, a2, k2 = descend(a, np.asarray(k0, float))
            if np.isfinite(v) and (best is None or v < best[0]):
                best = (v, a2, k2)
        if best is None:
            continue
        prev = g = {'K': K, 'angle': float(best[1]), 'u': unit(best[1]), 'knots': best[2], 'mse': best[0]}
        if out is None or g['mse'] < improve * out['mse']:   # a stop more must earn a 10 % lower error
            out = g
    out['colors'], out['mse'] = solve(hat_basis(xy @ out['u'], out['knots']), c)
    return out


if __name__ == '__main__':
    # self-check: recover a known 3-stop gradient at 30 deg from noisy samples
    rng = np.random.default_rng(1)
    xy = rng.uniform(0, 100, (3000, 2))
    u = unit(30.0)
    s = xy @ u
    kn = np.array([20.0, 60.0, 110.0])
    cols = np.array([[20, 80, 200], [10, 220, 240], [60, 80, 120.0]])
    c = hat_basis(s, kn) @ cols + rng.normal(0, 2, (3000, 3))
    g = fit(xy, c, Kmax=4)
    assert g['K'] == 3 and abs(g['angle'] - 30) < 1.0, g
    assert np.abs(g['knots'] - kn).max() < 2.5 and np.abs(g['colors'] - cols).max() < 4, g
    print('ok', g['K'], round(g['angle'], 2), np.round(g['knots'], 1))
