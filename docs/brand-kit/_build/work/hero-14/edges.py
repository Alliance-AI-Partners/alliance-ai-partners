"""Sub-pixel edge sampling along the normal of an approximate segment or polyline (bilinear profiles,
area method on the two-colour unmixing profile, as work/ap-/lines.py does per scanline)."""
import numpy as np


def bilinear(rgb, x, y):
    """rgb (H,W,3) float, sample at pixel-centre coordinates (x, y are continuous, pixel (i,j) centre = (j+.5, i+.5))."""
    H, W = rgb.shape[:2]
    fx, fy = np.asarray(x, float) - 0.5, np.asarray(y, float) - 0.5
    x0 = np.clip(np.floor(fx).astype(int), 0, W - 2); y0 = np.clip(np.floor(fy).astype(int), 0, H - 2)
    tx = np.clip(fx - x0, 0, 1)[..., None]; ty = np.clip(fy - y0, 0, 1)[..., None]
    return ((1 - tx) * (1 - ty) * rgb[y0, x0] + tx * (1 - ty) * rgb[y0, x0 + 1]
            + (1 - tx) * ty * rgb[y0 + 1, x0] + tx * ty * rgb[y0 + 1, x0 + 1])


def step_pos(prof, k=3):
    """prof (n,3) along a line through a step; returns (length of the first colour in samples, contrast):
    the area method, so the edge sits that many sample cells after the start of the first cell."""
    ca = np.median(prof[:k], 0)
    cb = np.median(prof[-k:], 0)
    d = cb - ca
    dd = float(d @ d)
    if dd < 1e-6:
        return None, 0.0
    s = np.clip((prof - ca) @ d / dd, 0, 1)
    return len(prof) - s.sum(), np.sqrt(dd)


def normal_edges(rgb, pts, half=5.0, step=0.25, cmin=8.0, k=None):
    """pts (N,2) points near an edge with unit normals estimated from the polyline; returns the
    sub-pixel edge point found along each normal, and the contrast."""
    pts = np.asarray(pts, float)
    tang = np.gradient(pts, axis=0)
    tang /= np.maximum(np.hypot(*tang.T), 1e-9)[:, None]
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    ts = np.arange(-half, half + 1e-9, step)
    kk = k or max(3, int(round(1.0 / step)))
    out, con = [], []
    for p, n in zip(pts, nrm):
        q = p[None] + ts[:, None] * n[None]
        prof = bilinear(rgb, q[:, 0], q[:, 1])
        pos, c = step_pos(prof, kk)
        if pos is None or c < cmin:
            out.append((np.nan, np.nan)); con.append(c); continue
        t = -half - step / 2 + pos * step  # samples are centres of cells of width `step`
        out.append(tuple(p + t * n)); con.append(c)
    return np.asarray(out), np.asarray(con)


def seg_points(p0, p1, spacing=1.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    n = max(2, int(np.hypot(*(p1 - p0)) / spacing) + 1)
    t = np.linspace(0, 1, n)[:, None]
    return p0 + t * (p1 - p0)


def fit_line_tls(pts):
    """total least squares line through pts: returns (point, unit direction, rms of normal residuals)."""
    p = np.asarray(pts, float)
    p = p[np.isfinite(p).all(1)]
    c = p.mean(0)
    u, s, vt = np.linalg.svd(p - c)
    d = vt[0]
    r = (p - c) @ np.array([-d[1], d[0]])
    return c, d, float(np.sqrt(np.mean(r ** 2))), r
