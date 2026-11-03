"""Least-squares fitting of SVG linear gradients (direction + K uniformly spaced stops, sRGB
interpolation like SVG/Illustrator) to the pixels of a region."""
import numpy as np
import kit


def hat(s, K):
    """Piecewise-linear basis (n, K) for positions s in [0, 1] with K uniform stops."""
    t = np.clip(s, 0, 1) * (K - 1)
    i = np.clip(np.floor(t).astype(int), 0, K - 2)
    f = t - i
    Bm = np.zeros((len(s), K))
    Bm[np.arange(len(s)), i] = 1 - f
    Bm[np.arange(len(s)), i + 1] = f
    return Bm


def fit_dir(xy, rgb, ang, K, lo_q=0.0, hi_q=1.0, ridge=1e-3):
    u = np.array([np.cos(ang), np.sin(ang)])
    s = xy @ u
    s0, s1 = np.quantile(s, lo_q), np.quantile(s, hi_q)
    sn = (s - s0) / max(s1 - s0, 1e-6)
    Bm = hat(sn, K)
    # small smoothness ridge on second differences keeps stops well behaved where data is thin
    D = np.diff(np.eye(K), 2, axis=0) * np.sqrt(ridge * len(s))
    A = np.vstack([Bm, D])
    stops = np.stack([np.linalg.lstsq(A, np.r_[rgb[:, c], np.zeros(len(D))], rcond=None)[0] for c in range(3)], -1)
    stops = np.clip(stops, 0, 255)
    pred = Bm @ stops
    return stops, pred, (xy[0] * 0 + s0 * u, s1 * u, u)


def fit_gradient(xy, rgb, K=8, angles=None):
    """xy: (n,2) pixel centers; rgb: (n,3) sRGB 0..255. Returns dict with vector p0->p1, stops, mean/p95 dE."""
    if angles is None:
        angles = np.radians(np.arange(-90, 90, 3))
    lab = kit.srgb_to_lab(rgb)
    best = None
    for a in angles:
        stops, pred, (_, _, u) = fit_dir(xy, rgb, a, K)
        err = float(((pred - rgb) ** 2).sum(1).mean())
        if best is None or err < best[0]:
            best = (err, a)
    # refine angle
    a0 = best[1]
    for a in a0 + np.radians(np.linspace(-3, 3, 13)):
        stops, pred, _ = fit_dir(xy, rgb, a, K)
        err = float(((pred - rgb) ** 2).sum(1).mean())
        if err < best[0]:
            best = (err, a)
    a = best[1]
    u = np.array([np.cos(a), np.sin(a)])
    s = xy @ u
    s0, s1 = s.min(), s.max()
    stops, pred, _ = fit_dir(xy, rgb, a, K)
    # gradient vector endpoints: project the region centroid onto the line through s0..s1
    c = xy.mean(0)
    cperp = c - (c @ u) * u
    p0, p1 = cperp + s0 * u, cperp + s1 * u
    de = kit.de2000(lab, kit.srgb_to_lab(pred))
    return {"p0": p0, "p1": p1, "stops": stops, "angle_deg": float(np.degrees(a)),
            "de_mean": float(de.mean()), "de_p95": float(np.percentile(de, 95))}
