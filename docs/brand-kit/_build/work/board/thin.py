"""Geometry + colour fitting of thin flat features of original 02 (rules, guides, rings, dashes, arrows, crosses).

A feature is a union of polygons built from a few parameters. For given parameters we rasterise it
(exact centre-sampled supersampling), push bg + coverage*(ink - bg) through the JPEG 4:2:0 chroma model
of the original and solve the ink in closed form (least squares); Nelder-Mead searches the geometry.
That way thin features get their true colour back instead of the chroma-diluted one (board agent)."""
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import jpegsim as J
import textfit as tf

IMG = kit.load('02').astype(float)
BG = tf.BG


def cover_polys(polys, box, ss=4):
    """Union coverage of polygons (lists of (x, y) in image px) over box=(x0,y0,x1,y1)."""
    x0, y0, x1, y1 = box
    W, H = (x1 - x0) * ss, (y1 - y0) * ss
    acc = np.zeros((H, W), bool)
    for p in polys:
        q = (np.asarray(p, float) - [x0, y0]) * ss
        acc |= tf.fill_evenodd([q], W, H)
    return acc.reshape(H // ss, ss, W // ss, ss).mean((1, 3))


def rect(xa, ya, xb, yb):
    return [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]


def rect_cov(xa, ya, xb, yb, box):
    """Exact (analytic) coverage of an axis-aligned rectangle over box."""
    x0, y0, x1, y1 = box
    px = np.arange(x0, x1)
    py = np.arange(y0, y1)
    cx = np.clip(np.minimum(px + 1, xb) - np.maximum(px, xa), 0, 1)
    cy = np.clip(np.minimum(py + 1, yb) - np.maximum(py, ya), 0, 1)
    return cy[:, None] * cx[None, :]


def seg_poly(ax, ay, bx, by, w):
    """Butt-capped stroke of width w from a to b as a quad."""
    d = np.array([bx - ax, by - ay], float)
    n = np.array([-d[1], d[0]]) / max(1e-9, np.hypot(*d)) * w / 2
    return [tuple(np.array([ax, ay]) + n), tuple(np.array([bx, by]) + n), tuple(np.array([bx, by]) - n), tuple(np.array([ax, ay]) - n)]


def ring_poly(cx, cy, r_out, r_in, n=360):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    outer = np.column_stack([cx + r_out * np.cos(t), cy + r_out * np.sin(t)])
    inner = np.column_stack([cx + r_in * np.cos(t), cy + r_in * np.sin(t)])[::-1]
    return outer, inner


def ls_ink(cov, box, bg=BG, mask=None):
    x0, y0, x1, y1 = box
    orig = IMG[y0:y1, x0:x1]
    base = J.jpeg420(np.broadcast_to(bg, cov.shape + (3,)), x0, y0, clip=False)
    B = []
    for k in range(3):
        e = np.zeros(3); e[k] = 1.0
        B.append(J.jpeg420(bg + cov[..., None] * e, x0, y0, clip=False) - base)
    m = np.ones(cov.shape, bool) if mask is None else mask
    w = np.repeat(m[..., None], 3, -1)
    for _ in range(3):
        A = np.stack([b[w] for b in B], 1)
        d, *_ = np.linalg.lstsq(A, (orig - base)[w], rcond=None)
        pred = base + sum(d[k] * B[k] for k in range(3))
        w = np.repeat(m[..., None], 3, -1) & ~(((pred > 255) & (orig >= 254)) | ((pred < 0) & (orig <= 1)))
    pred = base + sum(d[k] * B[k] for k in range(3))
    res = float(np.sqrt(((pred - orig)[np.repeat(m[..., None], 3, -1)] ** 2).mean()))
    return bg + d, res


def fit(build, p0, steps, box, bg=BG, mask=None, iters=150, ink_bounds=True, ss=12, covfn=None):
    """Nelder-Mead over geometry parameters; ink solved by least squares inside. Returns (p, ink, rms).
    covfn(p) may supply coverage directly (e.g. analytic rectangles); otherwise build(p) polygons are filled."""
    cv = covfn or (lambda p: cover_polys(build(p), box, ss))

    def f(p):
        ink, r = ls_ink(cv(p), box, bg, mask)
        pen = 0.0
        if ink_bounds:   # keep the solved ink a real colour
            pen = float(np.clip(-ink, 0, None).sum() + np.clip(ink - 255, 0, None).sum()) * 0.05
        return r + pen
    p, v = tf.nelder_mead(f, np.asarray(p0, float), steps, iters)
    p, v = tf.nelder_mead(f, p, [s * 0.25 for s in steps], iters // 2)
    ink, r = ls_ink(cv(p), box, bg, mask)
    return p, ink, r
