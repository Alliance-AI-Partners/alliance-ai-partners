"""ap-mono: one-colour master silhouette with the interlace gaps of the flat originals (12, 11, 16).
Silhouette = Pathfinder Unite of the hero faces (exact); gaps = tapered cuts taken out of the letter
stroke behind the ribbon, along (a) the ribbon's top edge over the A's left leg and (b) the ribbon's outer
edge where it passes over the A's right leg and the P's stem/bowl; widths and taper from 12, scaled by
mark height. Pathfinder Minus Front, then the clean-path rebuild with the measured straight lines."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from build_hero import FACES, W, lines_dict, snap_lines
from fitcurve import rebuild, count_anchors, Line, resample
from pathops import vc_pathfinder

# measured on 12 (gaps12d.py): effective cut width ~5.7 px on a 371.1 px tall mark; constant over the
# first 40-60 % of the cut from its open end, then a straight taper to a point; lengths 87.9 / 192.3 px
H12 = 371.11
GAP12 = {'a': {'w': 5.7, 'len': 87.9, 'flat': 0.40}, 'b': {'w': 5.7, 'len': 192.3, 'flat': 0.60}}


def face_stack(geo, w=1024, h=1024):
    lab = np.full((h, w), -1, int)
    for i, n in enumerate(FACES):
        lab[kit.raster(geo[n], w, h) > 0.5] = i
    return lab


def outline(d, step=0.5):
    """closed outline polylines of a path (resampled), with outward normals (by the path's own fill)."""
    out = []
    own = kit.raster(d, 1024, 1024)
    for poly in kit.flatten(kit.parse_d(d), tol=0.05):
        p = resample(poly, step)
        t = np.roll(p, -2, 0) - np.roll(p, 2, 0)
        t /= np.maximum(np.hypot(*t.T), 1e-9)[:, None]
        n = np.stack([t[:, 1], -t[:, 0]], 1)
        q = p + 1.5 * n
        inside = own[np.clip(q[:, 1].astype(int), 0, 1023), np.clip(q[:, 0].astype(int), 0, 1023)] > 0.5
        if inside.mean() > 0.5:      # normals point inwards for this orientation: flip
            n = -n
        out.append((p, n))
    return out


def edge_run(geo, lab, face, neighbours, open_near, back_ext=10.0, step=0.5):
    """Longest run of `face`'s outline whose outward neighbour is one of `neighbours`, oriented to start
    at the end nearest `open_near` (the cut's open end) and extended backwards there by `back_ext` px of
    arc length (along the part that borders the background, so the cut opens cleanly)."""
    best = None
    for p, n in outline(geo[face], step):
        q = p + 1.5 * n
        nb = lab[np.clip(q[:, 1].astype(int), 0, 1023), np.clip(q[:, 0].astype(int), 0, 1023)]
        on = np.isin(nb, [FACES.index(m) for m in neighbours])
        N = len(p)
        if not on.any():
            continue
        start = int(np.argmin(on))
        i = 0
        while i < N:
            if on[(start + i) % N]:
                j = i
                while j + 1 < N and on[(start + j + 1) % N]:
                    j += 1
                if best is None or j - i > best[1] - best[0]:
                    best = (start + i, start + j, p, n)
                i = j + 1
            else:
                i += 1
    i0, i1, p, n = best
    N = len(p)
    ext = int(back_ext / step)
    if np.hypot(*(p[i1 % N] - open_near)) < np.hypot(*(p[i0 % N] - open_near)):
        idx = np.arange(i1 + ext, i0 - 1, -1) % N      # reversed: start at the i1 end
    else:
        idx = np.arange(i0 - ext, i1 + 1) % N
    return p[idx], n[idx], ext


def gap_polygon(p, n, ext, width, length, flat, out_ext=0.0):
    """tapered cut on the outward side of edge points p (normals n). Along the ribbon edge the cut's
    inner side is the edge itself; over the backward extension (which borders the background) it is
    eased 0.6 px further out so the silhouette there is not nicked."""
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    s = s - s[ext]
    avail = s[-1]
    length = min(length, avail)
    keep = s <= length
    p, n, s = p[keep], n[keep], s[keep]
    u = np.clip(s / length, 0, 1)
    w = np.where(u <= flat, 1.0, (1 - u) / (1 - flat)) * width
    e = out_ext * np.clip(-s / 1.5, 0, 1)
    inner = p + e[:, None] * n
    outer = p + np.maximum(w, e + 0.5)[:, None] * n
    return np.vstack([inner, outer[::-1]]), length, avail


def poly_d(P):
    return 'M' + ' L'.join('%.3f %.3f' % (x, y) for x, y in P) + ' Z'


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'hero_v4.json'
    tag = sys.argv[2] if len(sys.argv) > 2 else 'v1'
    geo = json.load(open(W / src))['geo']
    ln = lines_dict()
    H = ln['base'] - ln['top']
    k = H / H12
    lab = face_stack(geo)
    hero = json.load(open(W / src))
    sil = [hero['silhouette']] if 'silhouette' in hero else vc_pathfinder([(n, geo[n]) for n in FACES], 'unite', W / f'mono_{tag}_union.svg')
    gaps = {}
    pa, na, ea = edge_run(geo, lab, 'ribbon-front', ['a-left-outer', 'a-left-bevel'], open_near=np.array([222.0, 602.0]))
    pb, nb_, eb = edge_run(geo, lab, 'ribbon-back', ['a-right-inner', 'a-right-outer', 'p-bowl-under', 'p-bowl-lower'], open_near=np.array([505.0, 612.0]))
    info = {}
    for key, (p, n, e) in (('a', (pa, na, ea)), ('b', (pb, nb_, eb))):
        g = GAP12[key]
        P, used, avail = gap_polygon(p, n, e, g['w'] * k, g['len'] * k, g['flat'])
        # smooth the cut's outline with the same fitter (keeps the ribbon-side edge within 0.15 px)
        gaps[key] = rebuild(poly_d(P), lines=[], err=0.08, line_tol=0.08, sigma=0.0)
        info[key] = {'width_px': round(g['w'] * k, 3), 'length_px': round(used, 1), 'edge_available_px': round(avail, 1),
                     'start': np.round(p[e], 2).tolist(), 'end': np.round(P[len(P) // 2 - 1], 2).tolist()}
        print('gap', key, info[key])
    res = vc_pathfinder([('silhouette', ' '.join(sil))] + [(f'gap-{q}', gaps[q]) for q in 'ab'], 'minusFront', W / f'mono_{tag}_cut.svg')
    d_raw = ' '.join(res)
    lines = snap_lines(ln) + [Line.xy(ln[q]['a'], ln[q]['b'], q) for q in ('LL_inner', 'RL_inner', 'RL_outer')] + [Line.h(ln['base'], 'base')]
    # drop specks the cut can leave where it opens onto the background (|area| < 5 px^2)
    keep = []
    for sp in kit.parse_d(d_raw):
        poly = kit.flatten([sp], tol=0.05)[0]
        P = np.asarray(poly + [poly[0]])
        if abs(0.5 * (np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))) >= 5.0:
            keep.append(sp)
    d = kit.format_d(keep, 3)
    print('mono anchors', count_anchors(d), 'subpaths', len(keep), '(dropped', len(kit.parse_d(d_raw)) - len(keep), 'specks)')
    json.dump({'d': d, 'd_raw': d_raw, 'gaps': gaps, 'info': info}, open(W / f'mono_{tag}.json', 'w'), indent=1)
    (W / f'mono_{tag}.svg').write_text(kit.svg_doc(1024, 1024, f'<path id="ap-mono" d="{d}" fill="#000000" fill-rule="evenodd"/>'), encoding='utf-8')
