"""Soft (sub-pixel) face memberships for a label map: boundary pixels are split between their own
label and the dominant neighbouring label by 2-colour unmixing against local interior colours."""
import numpy as np


def box(a, r):
    """Box sum over a (2r+1)^2 window (zero padded), any trailing dims."""
    H, W = a.shape[:2]
    p = np.pad(a, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (a.ndim - 2))
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    return c[k:k + H, k:k + W] - c[:H, k:k + W] - c[k:k + H, :W] + c[:H, :W]


def shift(a, dy, dx, fill):
    out = np.full_like(a, fill)
    H, W = a.shape[:2]
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = a[ys, xs]
    return out


def memberships(rgb, lab, n, r=4, cmin=10.0, cfull=30.0):
    """rgb float (H,W,3), lab int (H,W) in 0..n-1 -> M float (n,H,W), summing to 1 per pixel."""
    H, W = lab.shape
    rgb = np.asarray(rgb, float)
    # interior = pixel whose 3x3 neighbourhood has one label
    same = np.ones((H, W), bool)
    nb_counts = np.zeros((n, H, W), np.int16)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            s = shift(lab, dy, dx, -1)
            same &= (s == lab) | (s < 0)
            for k in range(n):
                nb_counts[k] += (s == k)
    # local interior mean colour per label
    means = np.zeros((n, H, W, 3))
    have = np.zeros((n, H, W), bool)
    for k in range(n):
        m = ((lab == k) & same).astype(float)
        cnt = box(m, r)
        sm = box(rgb * m[..., None], r)
        have[k] = cnt > 2
        means[k] = sm / np.maximum(cnt, 1)[..., None]
    M = np.zeros((n, H, W))
    for k in range(n):
        M[k][lab == k] = 1.0
    bnd = ~same
    ys, xs = np.nonzero(bnd)
    own = lab[ys, xs]
    cnts = nb_counts[:, ys, xs].astype(int)
    cnts[own, np.arange(len(own))] = -1
    other = cnts.argmax(0)
    ok = have[own, ys, xs] & have[other, ys, xs]
    ca = means[own, ys, xs]
    cb = means[other, ys, xs]
    d = ca - cb
    dd = (d * d).sum(1)
    t = np.clip(((rgb[ys, xs] - cb) * d).sum(1) / np.maximum(dd, 1e-6), 0, 1)
    w = np.clip((np.sqrt(dd) - cmin) / (cfull - cmin), 0, 1) * ok
    t = w * t + (1 - w) * 1.0
    M[own, ys, xs] = t
    M[other, ys, xs] += 1 - t
    return M
