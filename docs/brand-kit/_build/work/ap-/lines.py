"""Subpixel straight-edge fits for the A legs and the flat top / baseline of the hero mark (06).
Edge position per scanline by the area method on the 2-color unmixing profile; robust LSQ line fit."""
import sys
import json
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from seg import NAMES

W = kit.WORK / 'ap-'
L = {n: k for k, n in enumerate(NAMES)}


def edge_pos(prof, half=5):
    """prof: (n, 3) colors across an edge, edge near the middle. Returns the subpixel position of the
    step (continuous coords, 0 = start of first sample) and the contrast."""
    n = len(prof)
    ca = np.median(prof[:3], 0)
    cb = np.median(prof[-3:], 0)
    d = cb - ca
    dd = float(d @ d)
    if dd < 1e-6:
        return None, 0.0
    s = np.clip((prof - ca) @ d / dd, 0, 1)
    return n - s.sum(), np.sqrt(dd)


def fit_line(pts, axis='y'):
    """pts (N,2) of (x, y); fits x = a*y + b (axis 'y') or y = a*x + b (axis 'x'), robust."""
    p = np.asarray(pts, float)
    u, v = (p[:, 1], p[:, 0]) if axis == 'y' else (p[:, 0], p[:, 1])
    keep = np.ones(len(p), bool)
    for _ in range(4):
        A = np.stack([u[keep], np.ones(keep.sum())], 1)
        (a, b), *_ = np.linalg.lstsq(A, v[keep], rcond=None)
        r = v - (a * u + b)
        sd = max(0.05, 1.4826 * np.median(np.abs(r[keep])))
        keep = np.abs(r) < 3 * sd
    return float(a), float(b), float(np.sqrt(np.mean(r[keep] ** 2))), int(keep.sum()), r


def row_edges(rgb, lab, left, right, yrange, half=6):
    pts = []
    for y in range(*yrange):
        row = lab[y]
        xs = np.nonzero(np.isin(row[:-1], left) & np.isin(row[1:], right))[0]
        if len(xs) != 1:
            continue
        x0 = xs[0] + 1  # first pixel of the right label
        prof = rgb[y, x0 - half:x0 + half].astype(float)
        pos, c = edge_pos(prof)
        if pos is None or c < 8:
            continue
        pts.append((x0 - half + pos, y + 0.5))
    return pts


def col_edges(rgb, lab, top, bottom, xrange, half=6):
    pts = []
    for x in range(*xrange):
        col = lab[:, x]
        ys = np.nonzero(np.isin(col[:-1], top) & np.isin(col[1:], bottom))[0]
        if len(ys) != 1:
            continue
        y0 = ys[0] + 1
        prof = rgb[y0 - half:y0 + half, x].astype(float)
        pos, c = edge_pos(prof)
        if pos is None or c < 8:
            continue
        pts.append((x + 0.5, y0 - half + pos))
    return pts


if __name__ == '__main__':
    rgb = kit.load('06')
    lab = np.load(W / 'labels06.npy')
    bg = [L['bg']]
    lo, lb, ri, ro = L['a-left-outer'], L['a-left-bevel'], L['a-right-inner'], L['a-right-outer']
    specs = {
        'LL_outer': [(bg, [lo], (318, 545)), (bg, [lo], (668, 706))],
        'LL_crease': [([lo], [lb], (318, 540)), ([lo], [lb], (652, 706))],
        'LL_inner': [([lb], bg, (416, 548)), ([lb], [ri, ro], (318, 402)), ([lb], bg, (640, 706))],
        'RL_inner': [(bg, [ri], (416, 534)), (bg, [ri], (618, 706))],
        'RL_internal': [([ri], [ro], (372, 505)), ([ri], [ro], (600, 706))],
        'RL_outer': [([ro], bg, (318, 450)), ([ro], [bg[0], L['p-stem']], (590, 706))],
    }
    out = {}
    for name, parts in specs.items():
        pts = []
        for left, right, yr in parts:
            pts += row_edges(rgb, lab, left, right, yr)
        a, b, rms, n, r = fit_line(pts, 'y')
        out[name] = {'a': a, 'b': b, 'rms': rms, 'n': n, 'N': len(pts)}
        # residual trend: mean residual by y band, to see curvature
        p = np.asarray(pts)
        bands = [(int(y0), round(float(np.mean(r[(p[:, 1] >= y0) & (p[:, 1] < y0 + 50)])), 2))
                 for y0 in range(310, 710, 50) if ((p[:, 1] >= y0) & (p[:, 1] < y0 + 50)).any()]
        print(f'{name:12s} x = {a:.5f}*y + {b:.3f}  rms={rms:.3f} n={n}/{len(pts)}  x@312={a*312+b:.2f} x@710={a*710+b:.2f}  bands={bands}')
    allf = [lo, lb, ri, ro]
    tops = {'A_top': col_edges(rgb, lab, bg, [lo, lb], (366, 446)),
            'P_top': col_edges(rgb, lab, bg, [L['ribbon-upper']], (546, 700)),
            'L_base': col_edges(rgb, lab, [lo, lb], bg, (180, 262)),
            'R_base': col_edges(rgb, lab, [ri, ro], bg, (566, 644))}
    for name, pts in tops.items():
        a, b, rms, n, r = fit_line(pts, 'x')
        out[name] = {'a': a, 'b': b, 'rms': rms, 'n': n}
        print(f'{name:8s} y = {a:.5f}*x + {b:.3f} rms={rms:.3f} n={n}/{len(pts)}  y@mid={a*np.mean(np.asarray(pts)[:,0])+b:.3f}')
    json.dump(out, open(W / 'lines06.json', 'w'), indent=1)
