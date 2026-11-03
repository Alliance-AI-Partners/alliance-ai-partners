# Scratch measurement helpers for the shield frame (original 17). Imported by fit scripts in this folder.
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

IMG = kit.load('17').astype(float)
LAB = kit.srgb_to_lab(IMG)
H, W = IMG.shape[:2]


def sample(arr, xs, ys):
    """Bilinear sample arr (H, W, C) at float coords."""
    xs = np.clip(np.asarray(xs, float), 0, W - 1.001)
    ys = np.clip(np.asarray(ys, float), 0, H - 1.001)
    x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = (xs - x0)[..., None], (ys - y0)[..., None]
    return (arr[y0, x0] * (1 - fx) * (1 - fy) + arr[y0, x0 + 1] * fx * (1 - fy)
            + arr[y0 + 1, x0] * (1 - fx) * fy + arr[y0 + 1, x0 + 1] * fx * fy)


def transitions(p0, p1, step=0.25, thresh=6.0):
    """Strong color transitions along p0->p1: list of (distance, point, dE-per-px)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    d = (p1 - p0) / L
    s = np.arange(0, L + 1e-9, step)
    lab = sample(LAB, p0[0] + s * d[0], p0[1] + s * d[1])
    k = int(round(0.5 / step))
    g = np.zeros(len(s))
    g[k:-k] = kit.de2000(lab[:-2 * k], lab[2 * k:])
    out = []
    for i in range(1, len(s) - 1):
        if g[i] >= thresh and g[i] >= g[i - 1] and g[i] > g[i + 1]:
            a, b, c = g[i - 1], g[i], g[i + 1]
            den = a - 2 * b + c
            off = 0.5 * (a - c) / den if den != 0 else 0
            si = s[i] + off * step
            out.append((round(si, 2), tuple(np.round(p0 + si * d, 2)), round(b, 1)))
    return out


def edge_pos(p, n, w=5.0, gap=1.75, step=0.125):
    """Refine a boundary point: p approx on the edge, n unit normal from side A to side B.
    Returns (refined point, A color, B color). Uses the 50% crossing of the RGB projection
    between the plateau medians on each side."""
    p, n = np.asarray(p, float), np.asarray(n, float) / np.linalg.norm(n)
    s = np.arange(-w, w + 1e-9, step)
    rgb = sample(IMG, p[0] + s * n[0], p[1] + s * n[1])
    A = np.median(rgb[s <= -gap], 0)
    B = np.median(rgb[s >= gap], 0)
    v = B - A
    t = (rgb - A) @ v / max(v @ v, 1e-9)
    # nearest crossing of 0.5 to s=0
    best = None
    for i in range(len(s) - 1):
        if (t[i] - 0.5) * (t[i + 1] - 0.5) <= 0 and t[i] != t[i + 1]:
            si = s[i] + (0.5 - t[i]) / (t[i + 1] - t[i]) * step
            if best is None or abs(si) < abs(best):
                best = si
    if best is None:
        return None, A, B
    return p + best * n, A, B
