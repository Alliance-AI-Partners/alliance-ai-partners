"""Inks pass 2 for board-02 (original 02): re-measure every element's ink on the original, apply the recreation
colour rule, write the colours back into the SVGs in place (ids and structure kept), and verify.

    python inks_v2.py measure   -> inks_v2.json        per-element measurements on the original
    python inks_v2.py assign    (prints the colour each element gets and why)
    python inks_v2.py apply     -> components/board-02.svg, components/rec/slot-tile-{twotone,flat}.svg, fit/board-02.json
    python inks_v2.py verify    -> verify/board-02_inks.png, inks_v2_verify.json, board-02_inks_{before,after}.png
                                   (build.compose(build.rec_layers('02')) rendered 1x; before = inks_v2_before/ swapped in)

Measurement (geometry = the SVGs as they stand):
  text runs   coverage = exact nonzero fill of the run's outlines (8x8 samples / px); stroke width w = 2 * area / perimeter.
              One ink per typographic setting (the fit's groups: the 5 labels, 6 swatch names, 5 hex codes and 5 specimen
              lines are each one setting), measured over all its runs at once.
              w >= 3 px: median of the original over the eroded interior (coverage >= 0.5 eroded 1 px, 2 px when w >= 5).
              w <  3 px: coverage unmixing, least squares of bg + cov * (ink - bg) through the JPEG 4:2:0 chroma model
              (jpegsim; as thin.ls_ink), local background, pixels near other elements masked. Where the 4:2:0 chroma
              solve is not determined (it disagrees with plain unmixing by > dE 3: the 1 px hex codes) plain unmixing;
              where even that leaves the gamut (outlines lighter than the original's strokes) the eroded-core median.
  rules       width + ink through the 4:2:0 model, centre fixed (the row rule's 3 segments and col1's 2 share one);
              guides: one ink for the group at the drawn width over their visible stretches.
  swatches    disc interiors (eroded 4 px); outline rings: width + ink through the model over the swatch fill.
  tiles       tile interior away from the mark; background: flat background median; clear space: all red elements
              jointly at the drawn geometry; right tile mark: eroded interior; left tile mark: per face, the gradient
              stops re-fitted (ridge least squares on the visible face interior toward the pre-pass stops shifted by the
              face's median Lab difference; stop offsets may be squeezed toward one end when that cuts the residual 20%).
Rule: palette colour when the measured ink is within dE2000 2 of kit.PALETTE, else the measured ink; inks within
dE2000 2 of each other are merged (agglomerative complete linkage, area-weighted mean; an existing fill within 2 of the
mean and of every member is kept). Strokes whose ink moves keep their fitted luma integral (width rescaled).
Left mark under-glyph shadow: dark copies of the face silhouette (offset or spread, group opacity) are tried with
VectorCraft and kept only if the tile's mean dE drops by >= 0.05.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
from PIL import Image, ImageDraw
import kit
import jpegsim as J
import textfit as tf
import thin

WB = kit.WORK / 'board'
SVG = kit.COMP / 'board-02.svg'
TWO = kit.COMP / 'rec' / 'slot-tile-twotone.svg'
FLAT = kit.COMP / 'rec' / 'slot-tile-flat.svg'
MEAS = WB / 'inks_v2.json'
BEFORE_DIR = WB / 'inks_v2_before'          # the three SVGs (and the fit JSON) as they were before this pass
IMG = thin.IMG                              # original 02, float RGB
H_, W_ = IMG.shape[:2]
SS = 8
LUM = np.array([0.299, 0.587, 0.114])
TWO_BOX = (414, 322, 506, 382)              # left tile mark (+ margin)
FLAT_BOX = (551, 322, 642, 382)             # right tile mark (+ margin)


# ------------------------------------------------------------------ colour
def lab(c):
    return kit.srgb_to_lab(np.clip(np.asarray(c, float), 0, 255))


def de(c1, c2):
    return float(kit.de2000(lab(c1), lab(c2)))


def lab_to_srgb(L):
    L = np.asarray(L, float)
    fy = (L[..., 0] + 16) / 116
    f = np.stack([fy + L[..., 1] / 500, fy, fy - L[..., 2] / 200], -1)
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * np.array([0.95047, 1.0, 1.08883])
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    lin = np.clip(xyz @ np.linalg.inv(m).T, 0, None)
    return np.clip(np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055) * 255, 0, 255)


def hx(c):
    return kit.rgbhex(np.clip(c, 0, 255))


# ------------------------------------------------------------------ coverage
def poly_area(p):
    return 0.5 * float(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


def path_cov(d, box, ss=SS):
    """Nonzero-winding coverage of SVG path data over box=(x0, y0, x1, y1) -> (cov, area_px, perimeter_px)."""
    x0, y0, x1, y1 = box
    W, H = (x1 - x0) * ss, (y1 - y0) * ss
    wind = np.zeros((H, W), np.int16)
    per = 0.0
    for poly in kit.flatten(kit.parse_d(d), tol=0.02):
        p = np.asarray(poly, float)
        if len(p) < 3:
            continue
        per += float(np.hypot(*np.diff(np.vstack([p, p[:1]]), axis=0).T).sum())
        wind += np.int16(np.sign(poly_area(p))) * tf.fill_evenodd([(p - [x0, y0]) * ss], W, H).astype(np.int16)
    cov = (wind != 0).reshape(H // ss, ss, W // ss, ss).mean((1, 3))
    return cov, float(cov.sum()), per


def polys_cov(polys, box, ss=SS):
    """Union coverage of simple polygons [(n, 2) arrays]."""
    x0, y0, x1, y1 = box
    W, H = (x1 - x0) * ss, (y1 - y0) * ss
    acc = np.zeros((H, W), bool)
    for p in polys:
        acc |= tf.fill_evenodd([(np.asarray(p, float) - [x0, y0]) * ss], W, H)
    return acc.reshape(H // ss, ss, W // ss, ss).mean((1, 3))


def circle_poly(cx, cy, r, n=720):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.column_stack([cx + r * np.cos(t), cy + r * np.sin(t)])


def ring_cov(cx, cy, r, w, box):
    return np.clip(polys_cov([circle_poly(cx, cy, r + w / 2)], box) - polys_cov([circle_poly(cx, cy, r - w / 2)], box), 0, 1)


def dash_rects(orient, c, a, b, w, dash=None):
    """Butt-capped (dashed) straight stroke from a to b at centre c -> rectangles (xa, ya, xb, yb)."""
    segs = [(a, b)]
    if dash:
        D, G = dash
        segs, s = [], a
        while s < b:
            segs.append((s, min(b, s + D)))
            s += D + G
    return [(u, c - w / 2, v, c + w / 2) if orient == 'h' else (c - w / 2, u, c + w / 2, v) for u, v in segs]


def rects_cov(rects, box):
    cov = np.zeros((box[3] - box[1], box[2] - box[0]))
    for r in rects:
        cov = np.maximum(cov, thin.rect_cov(*r, box))   # ponytail: max, not union; these rects never overlap
    return cov


def bbox_box(pts, pad=4):
    pts = np.asarray(pts, float)
    return (max(0, int(np.floor(pts[:, 0].min())) - pad), max(0, int(np.floor(pts[:, 1].min())) - pad),
            min(W_, int(np.ceil(pts[:, 0].max())) + pad + 1), min(H_, int(np.ceil(pts[:, 1].max())) + pad + 1))


def d_points(d):
    return np.concatenate([np.asarray(p, float) for p in kit.flatten(kit.parse_d(d), tol=0.5)])


# ------------------------------------------------------------------ SVG
def attrs(tag):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))


def set_attr(svg, eid, name, value):
    """Set attribute `name` on the element with id `eid` (added after the id when absent)."""
    m = re.search(r'<\w+\b[^>]*\bid="%s"[^>]*>' % re.escape(eid), svg)
    tag = m.group(0)
    if re.search(r'\s%s="[^"]*"' % re.escape(name), tag):
        new = re.sub(r'(\s%s=")[^"]*(")' % re.escape(name), lambda q: q.group(1) + value + q.group(2), tag, count=1)
    else:
        new = tag.replace('id="%s"' % eid, 'id="%s" %s="%s"' % (eid, name, value), 1)
    return svg[:m.start()] + new + svg[m.end():]


def elements(svg_text):
    """Every painted element of the board: id -> {kind, paint, color, group, box, cov (box-local), ...}."""
    E, group, gattr = {}, None, {}
    for m in re.finditer(r'<(/?)(g|path|circle|rect)\b([^>]*?)/?>', svg_text):
        close, tag, a = m.group(1), m.group(2), attrs(m.group(3))
        if tag == 'g':
            if close:
                group, gattr = None, {}
            elif a.get('id') != 'clear-space-diagram':
                group, gattr = a.get('id'), a
            continue
        eid = a.get('id')
        if group == 'slots' or eid is None:
            continue
        sw = float(a.get('stroke-width', gattr.get('stroke-width', 0)))
        e = {'group': group, 'tag': tag}
        if tag == 'rect' and eid == 'background':
            e.update(kind='background', paint='fill', color=a['fill'], box=(0, 0, W_, H_), cov=np.ones((H_, W_)))
        elif tag == 'rect':
            x, y, w, h = (float(a[k]) for k in ('x', 'y', 'width', 'height'))
            box = (int(np.floor(x)) - 2, int(np.floor(y)) - 2, int(np.ceil(x + w)) + 3, int(np.ceil(y + h)) + 3)
            e.update(kind='tile', paint='fill', color=a.get('fill', gattr.get('fill')), box=box,
                     cov=thin.rect_cov(x, y, x + w, y + h, box), rect=(x, y, x + w, y + h))
        elif tag == 'circle':
            cx, cy, r = float(a['cx']), float(a['cy']), float(a['r'])
            if 'url(' in a.get('fill', ''):
                continue                                   # the cyan glow follows the cyan swatch
            stroke = a.get('stroke')
            R = r + (sw / 2 if stroke else 0)
            box = (int(cx - R) - 5, int(cy - R) - 5, int(cx + R) + 6, int(cy + R) + 6)
            e.update(kind='swatch', paint='fill', color=a['fill'], box=box, cx=cx, cy=cy, r=r,
                     cov=polys_cov([circle_poly(cx, cy, R)], box))
            E[eid] = e
            if stroke:
                E[eid + ':ring'] = {'group': group, 'tag': tag, 'kind': 'ring', 'paint': 'stroke', 'color': stroke, 'box': box,
                                    'cx': cx, 'cy': cy, 'r': r, 'width': sw, 'fill': a['fill'], 'cov': ring_cov(cx, cy, r, sw, box)}
            continue
        else:
            d = a['d']
            if group in ('layout-guides', 'dividers', 'clear-space-grid'):
                mm = re.match(r'M([\d.]+) ([\d.]+) ([HV])([\d.]+)', d)
                x, y, o, t = float(mm.group(1)), float(mm.group(2)), mm.group(3), float(mm.group(4))
                orient, c, lo, hi = ('h', y, x, t) if o == 'H' else ('v', x, y, t)
                da = a.get('stroke-dasharray')
                dash = tuple(float(v) for v in da.split()) if da else None
                rects = dash_rects(orient, c, lo, hi, sw, dash)
                box = bbox_box([(r[0], r[1]) for r in rects] + [(r[2], r[3]) for r in rects], 5)
                e.update(kind={'layout-guides': 'guide', 'dividers': 'rule', 'clear-space-grid': 'cs'}[group], paint='stroke',
                         color=a.get('stroke', gattr.get('stroke')), orient=orient, c=c, lo=lo, hi=hi, width=sw, dash=dash,
                         box=box, cov=rects_cov(rects, box))
            elif group == 'clear-space-crosses':
                pts = [float(v) for v in re.findall(r'[\d.]+', d)]
                polys = [thin.seg_poly(*pts[0:4], sw), thin.seg_poly(*pts[4:8], sw)]
                box = bbox_box(np.concatenate([np.array(p) for p in polys]), 4)
                e.update(kind='cs', paint='stroke', color=a.get('stroke', gattr.get('stroke')), box=box, cov=polys_cov(polys, box))
            else:
                box = bbox_box(d_points(d), 4)
                cov, area, per = path_cov(d, box)
                kind = 'cs' if group in ('clear-space-arrows', 'text-clear-space') else 'text'
                e.update(kind=kind, paint='fill', color=a.get('fill', gattr.get('fill')), box=box, cov=cov,
                         stroke_w=2 * area / max(per, 1e-9))
        E[eid] = e
    return E


def slot_mask(svg_text, pad=3):
    m = np.zeros((H_, W_), bool)
    g = re.search(r'<g id="slots".*?</g>', svg_text, re.S).group(0)
    for r in re.finditer(r'<rect[^>]*/>', g):
        a = attrs(r.group(0))
        x, y, w, h = (float(a[k]) for k in ('x', 'y', 'width', 'height'))
        m[max(0, int(y) - pad):int(np.ceil(y + h)) + pad, max(0, int(x) - pad):int(np.ceil(x + w)) + pad] = True
    return m


def canvas(e, thr=0.02):
    m = np.zeros((H_, W_), bool)
    x0, y0, x1, y1 = e['box']
    m[y0:y1, x0:x1] = e['cov'] > thr
    return m


def others_near(E, eid, r=2):
    """Pixels within r px of any other element (background and swatch fills are backdrops)."""
    acc = np.zeros((H_, W_), bool)
    for k, e in E.items():
        if k.split(':')[0] == eid or e['kind'] in ('background', 'swatch'):
            continue
        acc |= canvas(e)
    return kit.dilate(acc, r)


def local_bg(box, busy, pad=6):
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W_, x1 + pad), min(H_, y1 + pad)
    return np.median(IMG[Y0:Y1, X0:X1][~busy[Y0:Y1, X0:X1]], 0)


# ------------------------------------------------------------------ ink estimators
def unmix(cov, box, bg, mask, jpeg=True):
    """Least-squares ink for pixel = bg + cov * (ink - bg), optionally through the JPEG 4:2:0 model.
    Returns (unbounded ink, rms)."""
    return unmix_parts([(cov, box, bg, mask)], jpeg)


def unmix_parts(parts, jpeg=True):
    """One ink shared by several (cov, box, bg, mask) regions (each with its own background)."""
    As, ys = [], []
    for cov, box, bg, mask in parts:
        x0, y0, x1, y1 = box
        orig = IMG[y0:y1, x0:x1]
        if jpeg:
            base = J.jpeg420(np.broadcast_to(bg, cov.shape + (3,)), x0, y0, clip=False)
            cols = [J.jpeg420(bg + cov[..., None] * u, x0, y0, clip=False) - base for u in np.eye(3)]
        else:
            base = np.broadcast_to(bg, cov.shape + (3,))
            cols = [cov[..., None] * u for u in np.eye(3)]
        w = np.repeat(mask[..., None], 3, -1)
        A = np.stack([c[w] for c in cols], 1)
        As.append(A)
        ys.append((orig - base)[w] + A @ np.asarray(bg, float))     # = A @ ink
    A, y = np.concatenate(As), np.concatenate(ys)
    ink, *_ = np.linalg.lstsq(A, y, rcond=None)
    return ink, float(np.sqrt(((A @ ink - y) ** 2).mean()))


def interior(cov, box, w, mask):
    core = kit.erode(cov >= 0.5, 2 if w >= 5 else 1) & mask
    x0, y0, x1, y1 = box
    px = IMG[y0:y1, x0:x1][core]
    return (np.median(px, 0) if len(px) else np.full(3, np.nan)), int(len(px))


def in_gamut(c, tol=1.0):
    return bool(np.all(c > -tol) and np.all(c < 255 + tol))


def thin_ink(parts, core, n_core):
    jls, r1 = unmix_parts(parts, True)
    pls, r2 = unmix_parts(parts, False)
    if in_gamut(jls) and de(jls, pls) <= 3.0:
        return np.clip(jls, 0, 255), 'unmix through the JPEG 4:2:0 model', jls, pls
    if in_gamut(pls):
        return pls, 'plain unmix (4:2:0 chroma solve undetermined: dE %.1f from plain)' % de(jls, pls), jls, pls
    if n_core >= 20:
        return core, 'eroded-core median (unmix leaves the gamut: outlines lighter than the original strokes)', jls, pls
    return np.clip(pls, 0, 255), 'plain unmix, clipped to the gamut', jls, pls


RULE_SETS = {'divider-row': ['divider-row-left', 'divider-row-mid', 'divider-row-right'],   # one rule cut by the column gaps
             'divider-col1': ['divider-col1-top', 'divider-col1-bottom']}                   # one rule cut by the row rule


def fit_rule(es, bgs, masks):
    """Width + ink of straight rules (centres fixed; one shared width and ink) through the JPEG model; ink in closed
    form per width."""
    w0 = float(np.mean([e['width'] for e in es]))
    best = None
    for w in np.arange(max(0.6, w0 - 0.9), w0 + 0.9, 0.01):
        parts = [(thin.rect_cov(*dash_rects(e['orient'], e['c'], e['lo'], e['hi'], w)[0], e['box']), e['box'], bg, m)
                 for e, bg, m in zip(es, bgs, masks)]
        ink, rms = unmix_parts(parts, True)
        if in_gamut(ink, 2) and (best is None or rms < best[2]):
            best = (float(w), ink, rms)
    return best


def ring_ls(e, w, fill, dfill=None):
    """Ring over the swatch fill (pixel = fill / bg base, ring on top) through the JPEG model -> (ink, rms)."""
    box = e['box']
    x0, y0, x1, y1 = box
    BG = tf.BG
    dfill = polys_cov([circle_poly(e['cx'], e['cy'], e['r'])], box) if dfill is None else dfill
    base = BG + dfill[..., None] * (fill - BG)
    ring = ring_cov(e['cx'], e['cy'], e['r'], w, box)
    J0 = J.jpeg420(base * (1 - ring[..., None]), x0, y0, clip=False)
    zero = J.jpeg420(np.zeros(base.shape), x0, y0, clip=False)
    B = [J.jpeg420(ring[..., None] * u, x0, y0, clip=False) - zero for u in np.eye(3)]
    orig = IMG[y0:y1, x0:x1]
    A = np.stack([b.reshape(-1) for b in B], 1)
    ink, *_ = np.linalg.lstsq(A, (orig - J0).reshape(-1), rcond=None)
    pred = J0 + sum(ink[k] * B[k] for k in range(3))
    return ink, float(np.sqrt(((np.clip(pred, 0, 255) - orig) ** 2).mean()))


# ------------------------------------------------------------------ tile marks
def gradients(svg_text):
    G = {}
    for m in re.finditer(r'<linearGradient\b([^>]*)>(.*?)</linearGradient>', svg_text, re.S):
        a = attrs(m.group(1))
        stops = [(float(attrs(s)['offset']), kit.hexrgb(attrs(s)['stop-color'])) for s in re.findall(r'<stop\b[^>]*/>', m.group(2))]
        G[a['id']] = {'p1': np.array([float(a['x1']), float(a['y1'])]), 'p2': np.array([float(a['x2']), float(a['y2'])]),
                      'stops': stops}
    return G


def faces(svg_text):
    """Painted faces of a mark SVG in paint order: [(id, d, fill)] (the shadow group is not a face)."""
    out = []
    for m in re.finditer(r'<path\b[^>]*/>', svg_text):
        a = attrs(m.group(0))
        if not a.get('id', '').startswith('shadow'):
            out.append((a['id'], a['d'], a.get('fill')))
    return out


def stop_weights(t, offs):
    """Hat-function weight of each stop at gradient parameter t (SVG pad: clamped to the end stops)."""
    t = np.clip(t, offs[0], offs[-1])
    W = np.zeros((len(t), len(offs)))
    for k in range(len(offs) - 1):
        a, b = offs[k], offs[k + 1]
        sel = (t >= a) & ((t <= b) if k == len(offs) - 2 else (t < b))
        u = (t[sel] - a) / max(b - a, 1e-9)
        W[sel, k] += 1 - u
        W[sel, k + 1] += u
    return W


def fit_twotone(lam=3.0):
    """Per face of the left tile mark: visible interior pixels, the current gradient's colour there, and stops
    re-fitted to the original (ridge toward the stops shifted by the face's median Lab difference). Starts from the
    pre-pass stops when that copy exists (so a re-run reproduces the same fit), else from the file as it stands."""
    pre = BEFORE_DIR / TWO.name
    t = (pre if pre.exists() else TWO).read_text(encoding='utf-8')
    G = gradients(t)
    F = faces(t)
    x0, y0, x1, y1 = TWO_BOX
    covs = [path_cov(d, TWO_BOX)[0] for _, d, _ in F]
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    out = {}
    for i, (fid, d, fill) in enumerate(F):
        gid = re.match(r'url\(#([^)]+)\)', fill).group(1)
        g = G[gid]
        vis = covs[i].copy()
        for c in covs[i + 1:]:
            vis *= 1 - c
        core = kit.erode(vis >= 0.999, 1)
        if core.sum() < 8:
            core = vis >= 0.999
        P = np.column_stack([xx[core], yy[core]])
        v = g['p2'] - g['p1']
        tt = ((P - g['p1']) @ v) / (v @ v)
        offs0 = [o for o, _ in g['stops']]
        C0 = np.array([c for _, c in g['stops']])
        orig = IMG[y0:y1, x0:x1][core]
        cur = stop_weights(tt, offs0) @ C0
        prior = lab_to_srgb(lab(C0) + np.median(lab(orig), 0) - np.median(lab(cur), 0))
        fits = []
        for s in (1.0, 0.75, 0.5, 0.35, 0.25):     # stop offsets as drawn, or squeezed toward either end
            for offs in ([o * s for o in offs0], [1 - (1 - o) * s for o in offs0]):
                Wt = stop_weights(tt, offs)
                C = ridge_stops(Wt, orig, prior, lam)
                fits.append((float(((Wt @ C - orig) ** 2).sum()), offs, C, Wt))
                if s == 1.0:
                    break
        base = fits[0]
        best = min(fits, key=lambda f: f[0])
        sse, offs, C, Wt = best if best[0] <= 0.8 * base[0] else base
        out[fid] = {'gradient': gid, 'n': int(core.sum()), 'stops_before': [hx(c) for c in C0],
                    'stops_after': [hx(c) for c in C], 'offsets_before': offs0, 'offsets': [round(o, 4) for o in offs],
                    'orig_median': hx(np.median(orig, 0)), 'model_median_before': hx(np.median(cur, 0)),
                    'model_median_after': hx(np.median(Wt @ np.round(C), 0)),
                    'dE_before': de(np.median(orig, 0), np.median(cur, 0)),
                    'dE_after': de(np.median(orig, 0), np.median(Wt @ np.round(C), 0))}
    return out


def ridge_stops(Wt, orig, prior, lam):
    """Stop colours: ridge least squares per channel toward `prior`; stops that leave 0..255 are pinned, the rest re-solved."""
    n = Wt.shape[1]
    C = np.zeros((n, 3))
    for ch in range(3):
        fixed = {}
        for _ in range(n):
            free = [k for k in range(n) if k not in fixed]
            rhs = orig[:, ch] - sum(Wt[:, k] * v for k, v in fixed.items())
            Wf = Wt[:, free]
            sol = np.linalg.solve(Wf.T @ Wf + lam * np.eye(len(free)), Wf.T @ rhs + lam * prior[free, ch])
            bad = {k: float(np.clip(v, 0, 255)) for k, v in zip(free, sol) if v < 0 or v > 255}
            if not bad:
                break
            fixed.update(bad)
        for k, v in fixed.items():
            C[k, ch] = v
        for k, v in zip(free, sol):
            C[k, ch] = v
    return C


def measure_flat():
    t = FLAT.read_text(encoding='utf-8')
    (fid, d, fill), = faces(t)
    cov, area, per = path_cov(d, FLAT_BOX)
    w = 2 * area / per
    ink, n = interior(cov, FLAT_BOX, w, np.ones(cov.shape, bool))
    return {'kind': 'mark', 'paint': 'fill', 'color': fill, 'ink': ink.tolist(), 'n': n, 'stroke_w': round(w, 2),
            'weight': area, 'method': 'eroded interior median of the flat mark', 'file': 'rec/slot-tile-flat.svg', 'id': fid}


# ------------------------------------------------------------------ measure
def measure():
    svg = SVG.read_text(encoding='utf-8')
    E = elements(svg)
    slots = slot_mask(svg)
    busy = np.zeros((H_, W_), bool)
    for k, e in E.items():
        if e['kind'] != 'background':
            busy |= canvas(e, 0.0)
    busy = kit.dilate(busy, 2) | slots
    out, text_parts, rule_parts = {}, {}, {}
    flat = ~busy & ~kit.dilate(kit.bg_mask(IMG.astype(np.uint8), '#F5F9FC', 6.0), 3)
    out['background'] = {'kind': 'background', 'paint': 'fill', 'color': E['background']['color'], 'weight': float(flat.sum()),
                         'ink': np.median(IMG[flat], 0).tolist(), 'method': 'median of the flat background'}
    for eid, e in E.items():
        k = e['kind']
        if k == 'background':
            continue
        box = e['box']
        x0, y0, x1, y1 = box
        near = others_near(E, eid)[y0:y1, x0:x1] | slots[y0:y1, x0:x1]
        rec = {'kind': k, 'group': e['group'], 'paint': e['paint'], 'color': e['color']}
        if k == 'text':
            w = e['stroke_w']
            core = kit.erode(e['cov'] >= 0.5, 2 if w >= 5 else 1) & ~near
            px = IMG[y0:y1, x0:x1][core]
            text_parts[eid] = {'w': w, 'area': float(e['cov'].sum()), 'core_px': px,
                               'part': (e['cov'], box, local_bg(box, busy), ~near)}
            rec.update(stroke_w=round(w, 2), interior=(np.median(px, 0) if len(px) else np.full(3, np.nan)).tolist(),
                       interior_n=int(len(px)), weight=float(e['cov'].sum()))
        elif k == 'tile':
            mark = kit.dilate(slots[y0:y1, x0:x1], 6)
            inside = kit.erode(e['cov'] >= 0.999, 3) & ~mark
            rec.update(ink=np.median(IMG[y0:y1, x0:x1][inside], 0).tolist(), method='tile interior away from the mark',
                       weight=float(inside.sum()))
        elif k == 'swatch':
            yy, xx = np.mgrid[y0:y1, x0:x1]
            inside = np.hypot(xx + 0.5 - e['cx'], yy + 0.5 - e['cy']) < e['r'] - 4
            rec.update(ink=np.median(IMG[y0:y1, x0:x1][inside], 0).tolist(), method='disc interior (eroded 4 px)',
                       weight=float(np.pi * e['r'] ** 2))
        elif k == 'ring':
            fill = kit.hexrgb(e['fill'])
            dfill = polys_cov([circle_poly(e['cx'], e['cy'], e['r'])], box)
            best = None
            for w in np.arange(0.8, 2.4, 0.01):
                ink, rms = ring_ls(e, w, fill, dfill)
                if best is None or rms < best[2]:
                    best = (float(w), ink, rms)
            w, ink, rms = best
            rec.update(ink=ink.tolist(), width_fit=w, rms=rms, drawn_width=e['width'], weight=2 * np.pi * e['r'] * w,
                       method='ring width + ink through the JPEG model over the swatch fill')
        elif k == 'rule':
            rule_parts[eid] = (local_bg(box, busy), ~near)
        elif k == 'guide':
            continue                 # solved jointly below
        out[eid] = rec
    # rules: width + ink, the segments of one rule together
    sets = dict(RULE_SETS)
    for k in rule_parts:
        if not any(k in v for v in sets.values()):
            sets[k] = [k]
    for name, ids in sets.items():
        w, ink, rms = fit_rule([E[i] for i in ids], [rule_parts[i][0] for i in ids], [rule_parts[i][1] for i in ids])
        for i in ids:
            out[i].update(ink=ink.tolist(), width_fit=w, rms=rms, bg=rule_parts[i][0].tolist(), drawn_width=E[i]['width'],
                          weight=w * (E[i]['hi'] - E[i]['lo']),
                          method='width + ink through the JPEG model (centre fixed)' +
                                 (', one width and ink for the %d segments of %s' % (len(ids), name) if len(ids) > 1 else ''))
    # text: one ink per typographic setting (the fit's run groups: labels, names, hex codes, specimen lines share one)
    groups = {}
    for rid, t in json.loads((kit.FIT / 'board-02.json').read_text(encoding='utf-8'))['text_runs'].items():
        for eid in ('txt-' + rid, 'txt-%s-ai' % rid):
            if eid in text_parts:
                groups.setdefault(t['group'] + ('-ai' if eid.endswith('-ai') else ''), []).append(eid)
    for g, ids in groups.items():
        P = [text_parts[i] for i in ids]
        area = np.array([p['area'] for p in P])
        w = float((area * np.array([p['w'] for p in P])).sum() / area.sum())
        px = np.concatenate([p['core_px'] for p in P])
        core = np.median(px, 0) if len(px) else np.full(3, np.nan)
        joint = (' jointly over the %d runs of the "%s" setting' % (len(ids), g)) if len(ids) > 1 else ''
        if w >= 3:
            ink, how, extra = core, 'eroded interior median' + joint + ' (w %.2f px)' % w, {}
        else:
            ink, how, jls, pls = thin_ink([p['part'] for p in P], core, len(px))
            how += joint + ' (w %.2f px)' % w
            extra = {'unmix_420': jls.tolist(), 'unmix_plain': pls.tolist()}
            for i, p in zip(ids, P):    # per-run unmix, recorded for reference
                out[i]['unmix_420_this_run'] = unmix_parts([p['part']], True)[0].tolist()
        for i in ids:
            out[i].update(ink=np.asarray(ink).tolist(), method=how, setting=g, **extra)
    # layout guides: one stroke style on their group, so one ink, solved over every guide's visible stretch
    gd = [k for k, e in E.items() if e['kind'] == 'guide']
    cov = np.zeros((H_, W_))
    vis = np.zeros((H_, W_), bool)
    for k in gd:
        x0, y0, x1, y1 = E[k]['box']
        cov[y0:y1, x0:x1] = np.maximum(cov[y0:y1, x0:x1], E[k]['cov'])
        free = ~(others_near({j: v for j, v in E.items() if j not in gd or j == k}, k)[y0:y1, x0:x1] | slots[y0:y1, x0:x1])
        vis[y0:y1, x0:x1] |= free
    ys, xs = np.nonzero(cov > 0)
    box = (xs.min() - 5, ys.min() - 5, xs.max() + 6, ys.max() + 6)
    X0, Y0, X1, Y1 = box
    bg = local_bg(box, busy, 0)
    ink, rms = unmix(cov[Y0:Y1, X0:X1], box, bg, vis[Y0:Y1, X0:X1], True)
    for k in gd:
        per, _ = unmix(E[k]['cov'], E[k]['box'], bg, vis[E[k]['box'][1]:E[k]['box'][3], E[k]['box'][0]:E[k]['box'][2]], True)
        out[k] = {'kind': 'guide', 'group': E[k]['group'], 'paint': 'stroke', 'color': E[k]['color'], 'ink': ink.tolist(),
                  'rms': rms, 'bg': bg.tolist(), 'drawn_width': E[k]['width'], 'ink_this_guide_alone': per.tolist(),
                  'weight': float((E[k]['cov'] * vis[E[k]['box'][1]:E[k]['box'][3], E[k]['box'][0]:E[k]['box'][2]]).sum()),
                  'method': 'one ink for all guides at the drawn width, JPEG model, visible stretches only'}
    # clear space: one ink for every red element, solved jointly at the drawn geometry
    cs = [k for k, e in E.items() if e['kind'] == 'cs']
    box = (min(E[k]['box'][0] for k in cs), min(E[k]['box'][1] for k in cs),
           max(E[k]['box'][2] for k in cs), max(E[k]['box'][3] for k in cs))
    X0, Y0, X1, Y1 = box
    cov = np.zeros((Y1 - Y0, X1 - X0))
    for k in cs:
        x0, y0, x1, y1 = E[k]['box']
        cov[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = np.maximum(cov[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0], E[k]['cov'])
    bg = local_bg(box, busy)
    ink, rms = unmix(cov, box, bg, ~slots[Y0:Y1, X0:X1], True)
    for k in cs:
        out[k] = {'kind': 'cs', 'group': E[k]['group'], 'paint': E[k]['paint'], 'color': E[k]['color'], 'ink': ink.tolist(),
                  'rms': rms, 'bg': bg.tolist(), 'weight': float(E[k]['cov'].sum()),
                  'method': 'all clear-space elements jointly at the drawn geometry (JPEG model)'}
    out['mark-flat'] = measure_flat()
    out['_twotone'] = fit_twotone()
    return out


# ------------------------------------------------------------------ the colour rule
def assign(M):
    """eid -> final colour. Palette colour within dE2000 2 of the measurement; the other measurements merged by
    agglomerative complete linkage at dE2000 2, each cluster painted with its area-weighted mean (or with a member's
    current fill when that is within dE 2 of the mean and of every member's measurement: no churn)."""
    items = {k: r for k, r in M.items() if not k.startswith('_')}
    ink = {k: np.clip(r['ink'], 0, 255) for k, r in items.items()}
    out, rest = {}, []
    for k in items:
        nm, ph, d = kit.nearest_palette(ink[k])
        if d <= 2.0:
            out[k] = {'hex': ph, 'tone': nm, 'palette': True}
        else:
            rest.append(k)
    # agglomerative, complete linkage: repeatedly merge the two closest clusters while every pair stays within 2
    L = lab(np.array([ink[k] for k in rest]))
    D = kit.de2000(L[:, None], L[None, :])
    clusters = [[i] for i in range(len(rest))]
    while True:
        best = None
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                d = D[np.ix_(clusters[a], clusters[b])].max()
                if d <= 2.0 and (best is None or d < best[0]):
                    best = (d, a, b)
        if best is None:
            break
        _, a, b = best
        clusters[a] += clusters.pop(b)
    for cl in clusters:
        cl = [rest[i] for i in cl]
        w = np.array([items[j]['weight'] for j in cl])
        mean = (w[:, None] * np.array([ink[j] for j in cl])).sum(0) / w.sum()
        rep = kit.hexrgb(hx(mean))
        for cur in sorted({items[j]['color'] for j in cl}):      # an existing fill that already satisfies the rule stays
            c = kit.hexrgb(cur)
            if de(c, mean) <= 2.0 and all(de(c, ink[j]) <= 2.0 for j in cl) and kit.nearest_palette(c)[2] > 2.0:
                rep = c
                break
        for j in cl:
            out[j] = {'hex': hx(rep), 'tone': None, 'palette': False}
    for k, v in out.items():
        v['measured'] = hx(ink[k])
        v['dE_to_measured'] = round(de(kit.hexrgb(v['hex']), ink[k]), 2)
        v['was'] = items[k]['color']
    bad = {k: v['dE_to_measured'] for k, v in out.items() if v['dE_to_measured'] > 2.0}
    assert not bad, 'colour rule broken (final colour > dE2000 2 from the measurement): %s' % bad
    taken = set()                      # tone names (Illustrator swatch names come from these, see build.tone_names)
    for h_ in sorted({v['hex'] for v in out.values() if not v['palette']}, key=lambda h_: tone_rank(out, h_)):
        mem = {j for j in out if out[j]['hex'] == h_}
        name = next((n for key, n in TONE_KEYS if key in mem and n not in taken), 'Board Tone ' + h_[1:])
        taken.add(name)
        for j in mem:
            out[j]['tone'] = name
    return out


# a non-palette ink is named after the first of these elements it paints
TONE_KEYS = [('txt-title', 'Ink Navy'), ('txt-spec-1', 'Ink Navy Deep'), ('txt-label-01', 'Label Black'),
             ('txt-hex-blue', 'Hex Black'), ('txt-body', 'Text Black'), ('txt-horiz-line2', 'Lockup Ink'),
             ('txt-headline-note', 'Note Ink'), ('txt-hero-tagline', 'Tagline Ink'), ('divider-row-left', 'Divider Ink'),
             ('divider-col2', 'Column Rule Ink'), ('divider-header', 'Header Rule Black'), ('divider-col1-top', 'Divider Slate'),
             ('swatch-pure-white:ring', 'Swatch Outline Navy'), ('swatch-off-white:ring', 'Swatch Outline Grey'),
             ('swatch-bright-cyan', 'Board Cyan'), ('txt-title-ai', 'Board Cyan'), ('mark-flat', 'Board Cyan'),
             ('txt-hero-wordmark-ai', 'Royal Blue'), ('guide-h-205', 'Guide Grey'), ('cs-arrow-top', 'Clear-space Red'),
             ('txt-subtitle', 'Subtitle Ink'), ('txt-subheader', 'Subheader Ink'), ('txt-hero-wordmark', 'Lockup Navy')]


def tone_rank(out, h_):
    mem = {j for j in out if out[j]['hex'] == h_}
    return min((i for i, (key, _) in enumerate(TONE_KEYS) if key in mem), default=len(TONE_KEYS))


# ------------------------------------------------------------------ apply
def luma(c):
    return float(np.asarray(c, float) @ LUM)


def stroke_width(r, final_hex):
    """Width that keeps the fitted luma integral when the stroke is painted final_hex instead of the fitted ink."""
    bg = np.asarray(r.get('bg', tf.BG), float)
    return r['width_fit'] * (luma(bg) - luma(np.clip(r['ink'], 0, 255))) / (luma(bg) - luma(kit.hexrgb(final_hex)))


def shadow_group(faces_, fill, opacity, dx, dy, spread):
    st = (' stroke="%s" stroke-width="%.2f" stroke-linejoin="round"' % (fill, spread)) if spread else ''
    body = ''.join('<path id="shadow-%s" d="%s"/>' % (fid, d) for fid, d, _ in faces_)
    tr = (' transform="translate(%.2f %.2f)"' % (dx, dy)) if (dx or dy) else ''
    return '<g id="shadow" fill="%s" opacity="%.2f"%s%s>%s</g>\n' % (fill, opacity, st, tr, body)


def with_shadow(two_text, grp):
    t = re.sub(r'<g id="shadow".*?</g>\n?', '', two_text, flags=re.S)
    i = t.index('</defs>') + len('</defs>\n')
    return t[:i] + grp + t[i:] if grp else t


def tile_trial(two_text, tile_hex, region=(398, 290, 521, 414)):
    """VectorCraft render of the left tile (board tile rect + mark) over its region -> mean / p95 dE vs the original."""
    x0, y0, x1, y1 = region
    inner = two_text[two_text.index('>', two_text.index('<svg')) + 1:two_text.rindex('</svg>')]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%d %d %d %d">'
           '<rect x="0" y="0" width="1376" height="768" fill="#F4F7FB"/>'
           '<rect x="401.41" y="293.49" width="116.13" height="116.65" fill="%s"/>%s</svg>' % (
               x1 - x0, y1 - y0, x0, y0, x1 - x0, y1 - y0, tile_hex, inner))
    ren = kit.over(kit.render_svg(svg), '#FFFFFF')
    d = kit.de2000(kit.srgb_to_lab(IMG[y0:y1, x0:x1]), kit.srgb_to_lab(ren))
    m = np.zeros(d.shape, bool)
    m[293 - y0 + 2:410 - y0 - 1, 401 - x0 + 2:517 - x0 - 1] = True      # tile interior
    return float(d[m].mean()), float(np.percentile(d[m], 95))


def choose_shadow(two_text, tile_hex):
    """Try dark copies of the silhouette under the faces; keep the best only if it lowers the tile's mean dE by 0.05."""
    F = faces(two_text)
    base = tile_trial(with_shadow(two_text, ''), tile_hex)
    trials = []
    for fill in ('#000000', '#010B1A'):
        for op in (0.25, 0.4, 0.55, 0.7):
            for dx, dy, sp in ((0, 1.0, 0), (0, 1.5, 0), (0.5, 1.5, 0), (0, 2.0, 0), (0, 0, 2.0), (0, 0, 3.0), (0, 0.5, 3.0),
                               (0, 0, 4.0), (0, 0.5, 4.0)):
                g = shadow_group(F, fill, op, dx, dy, sp)
                mean, p95 = tile_trial(with_shadow(two_text, g), tile_hex)
                trials.append({'fill': fill, 'opacity': op, 'dx': dx, 'dy': dy, 'spread': sp, 'de_mean': round(mean, 3),
                               'de_p95': round(p95, 2)})
    best = min(trials, key=lambda t: t['de_mean'])
    keep = best['de_mean'] <= base[0] - 0.05
    return {'without': {'de_mean': round(base[0], 3), 'de_p95': round(base[1], 2)}, 'best': best, 'kept': keep,
            'trials': sorted(trials, key=lambda t: t['de_mean'])[:12]}


def apply(M, A):
    svg = SVG.read_text(encoding='utf-8')
    E = elements(svg)
    rec = {}
    # text, swatch fills, tiles, background, clear-space text: their own fill attribute
    for k, e in E.items():
        a = A.get(k)
        if a is None or k == 'background':
            continue
        if e['kind'] in ('text', 'swatch') or (e['kind'] == 'cs' and e['tag'] == 'path' and e['group'] == 'text-clear-space'):
            svg = set_attr(svg, k, 'fill', a['hex'])
    # strokes / group paints
    for gid, kind, paint in (('dividers', 'rule', 'stroke'), ('layout-guides', 'guide', 'stroke'),
                             ('logo-variation-tiles', 'tile', 'fill'), ('clear-space-grid', 'cs', 'stroke'),
                             ('clear-space-arrows', 'cs', 'fill'), ('clear-space-crosses', 'cs', 'stroke')):
        ids = [k for k, e in E.items() if e['group'] == gid]
        hexes = [A[k]['hex'] for k in ids]
        common = max(set(hexes), key=hexes.count)
        svg = set_attr(svg, gid, paint, common)
        for k in ids:
            if A[k]['hex'] != common:
                svg = set_attr(svg, k, paint, A[k]['hex'])
            elif re.search(r'id="%s"[^>]*\s%s="' % (re.escape(k), paint), svg):
                svg = re.sub(r'(id="%s"[^>]*?)\s%s="[^"]*"' % (re.escape(k), paint), r'\1', svg, count=1)
            if kind == 'rule' and A[k]['hex'] != E[k]['color']:
                w = stroke_width(M[k], A[k]['hex'])
                svg = set_attr(svg, k, 'stroke-width', '%.2f' % w)
                rec[k] = {'stroke': A[k]['hex'], 'width': round(w, 3), 'width_fit': M[k]['width_fit'], 'ink_fit': hx(M[k]['ink'])}
    # swatch outline rings: colour, width kept at the fitted luma integral, outer edge where it was
    for k in ('swatch-pure-white:ring', 'swatch-off-white:ring'):
        cid = k.split(':')[0]
        if A[k]['hex'] != E[k]['color']:
            w = stroke_width(M[k], A[k]['hex'])
            outer = E[k]['r'] + E[k]['width'] / 2
            svg = set_attr(svg, cid, 'stroke', A[k]['hex'])
            svg = set_attr(svg, cid, 'stroke-width', '%.2f' % w)
            svg = set_attr(svg, cid, 'r', '%.2f' % (outer - w / 2))
            rec[k] = {'stroke': A[k]['hex'], 'width': round(w, 3), 'r': round(outer - w / 2, 3), 'width_fit': M[k]['width_fit'],
                      'ink_fit': hx(M[k]['ink'])}
    # the cyan swatch's glow follows the swatch
    cy = A['swatch-bright-cyan']['hex']
    svg = re.sub(r'(<radialGradient id="swatch-bright-cyan-glow-gradient".*?</radialGradient>)',
                 lambda m: re.sub(r'stop-color="#[0-9A-Fa-f]{6}"', 'stop-color="%s"' % cy, m.group(1)), svg, flags=re.S)
    SVG.write_text(svg, encoding='utf-8')
    # tile marks
    t = FLAT.read_text(encoding='utf-8')
    fid = M['mark-flat']['id']
    FLAT.write_text(set_attr(t, fid, 'fill', A['mark-flat']['hex']), encoding='utf-8')
    t = TWO.read_text(encoding='utf-8')
    for f, v in M['_twotone'].items():
        def put(m, v=v):
            stops = iter(zip(v['offsets'], v['stops_after']))
            return re.sub(r'<stop offset="[^"]*" stop-color="#[0-9A-Fa-f]{6}"/>',
                          lambda q: '<stop offset="%.4f" stop-color="%s"/>' % next(stops), m.group(0))
        t = re.sub(r'<linearGradient id="%s".*?</linearGradient>' % re.escape(v['gradient']), put, t, flags=re.S)
    sh = choose_shadow(t, A['tile-two-tone']['hex'])
    b = sh['best']
    t = with_shadow(t, shadow_group(faces(t), b['fill'], b['opacity'], b['dx'], b['dy'], b['spread']) if sh['kept'] else '')
    TWO.write_text(t, encoding='utf-8')
    return rec, sh


def update_fit(M, A, strokes, shadow):
    """fit/board-02.json: fills of the text runs, the strokes that moved, the tone list (build.tone_names reads it)."""
    p = kit.FIT / 'board-02.json'
    fj = json.loads(p.read_text(encoding='utf-8'))
    for rid, t in fj['text_runs'].items():
        t['fill'] = A['txt-' + rid]['hex']
        t['fill_name'] = A['txt-' + rid]['tone']
        if t.get('ai_fill'):
            t['ai_fill'] = A['txt-%s-ai' % rid]['hex']
    sh = fj['shapes']
    for k, v in strokes.items():
        if k in sh['dividers']:
            sh['dividers'][k].update(stroke=v['stroke'], width=v['width'], width_at_fitted_ink=v['width_fit'], fitted_ink=v['ink_fit'])
    pw = strokes.get('swatch-pure-white:ring')
    if pw:
        sh['swatches']['pure_white'].update(stroke=pw['stroke'], stroke_width=pw['width'], r_stroke=pw['r'])
    sh['guides']['_style']['stroke'] = A['guide-h-205']['hex']
    sh['clear_space']['color'] = A['cs-arrow-top']['hex']
    tones = {}
    for k, v in A.items():
        if not v['palette']:
            tones.setdefault(v['hex'], {'hex': v['hex'], 'palette': None, 'name': v['tone'], 'members': []})['members'].append(k)
    for v in tones.values():
        mem = v['members']
        w = np.array([M[j]['weight'] for j in mem])
        v['measured'] = hx((w[:, None] * np.array([np.clip(M[j]['ink'], 0, 255) for j in mem])).sum(0) / w.sum())
        nm, ph, d = kit.nearest_palette(kit.hexrgb(v['hex']))
        v.update(nearest_palette=nm, dE_to_palette=round(d, 2),
                 dE_to_members_max=round(max(A[j]['dE_to_measured'] for j in mem), 2), used_for=', '.join(mem))
        del v['members']
    fj['colors']['supporting_tones'] = {v['name']: v for v in sorted(tones.values(), key=lambda v: v['name'])}
    ks = sorted(fj['colors']['supporting_tones'])
    fj['colors']['supporting_tone_pairwise_dE2000'] = {
        '%s / %s' % (a, b): round(de(kit.hexrgb(fj['colors']['supporting_tones'][a]['hex']),
                                     kit.hexrgb(fj['colors']['supporting_tones'][b]['hex'])), 2)
        for i, a in enumerate(ks) for b in ks[i + 1:]}
    fj['colors']['inks_v2'] = {
        'rule': 'palette colour when the measured ink is within dE2000 2 of kit.PALETTE, else the measured ink; '
                'inks within dE2000 2 merged (complete linkage, area-weighted mean)',
        'method': 'work/board/inks_v2.py (measurements in work/board/inks_v2.json)',
        'elements': {k: {'hex': v['hex'], 'tone': v['tone'], 'measured': v['measured'], 'dE_to_measured': v['dE_to_measured'],
                         'method': M[k]['method']} for k, v in sorted(A.items())},
        'tile_marks': {'rec/slot-tile-flat.svg': A['mark-flat']['hex'],
                       'rec/slot-tile-twotone.svg': {'faces': M['_twotone'], 'under_glyph_shadow': {
                           k: v for k, v in shadow.items() if k != 'trials'}}}}
    p.write_text(json.dumps(fj, indent=1, default=float), encoding='utf-8')


# ------------------------------------------------------------------ verify
def fidelity(c):
    nm, ph, d = kit.nearest_palette(kit.hexrgb(hx(c)))
    return ph if d <= 2.0 else hx(c)


def render_composed(before=False):
    """1x VectorCraft render of the board exactly as build.compose(build.rec_layers('02')) composes it, over the
    background the build gives recreation 02 (fidelity of the original's 6 px border median). before=True swaps in
    the pre-pass copies of the three SVGs this pass edits (work/board/inks_v2_before/)."""
    import importlib.util
    import os
    cwd = os.getcwd()
    os.chdir(kit.BUILD)
    try:   # the brand-kit build.py (work/board/build.py shadows the name); only compose / rec_layers are called
        spec = importlib.util.spec_from_file_location('aap_build', kit.BUILD / 'build.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        layers = build.rec_layers('02')
        if before:
            sub = {p.resolve(): BEFORE_DIR / p.name for p in (SVG, TWO, FLAT)}
            layers = [(k, sub.get(Path(src).resolve(), src) if not str(src).lstrip().startswith('<') else src, *rest)
                      for k, src, *rest in layers]
        svg = build.compose(1376, 768, layers)
    finally:
        os.chdir(cwd)
    rgb = kit.load('02').astype(float)
    m = np.ones(rgb.shape[:2], bool)
    m[6:-6, 6:-6] = False
    return kit.over(kit.render_svg(svg), fidelity(np.median(rgb[m], 0)))


def regions(E):
    R = {}
    for g in ('text-header', 'text-section-labels', 'text-logo-variations', 'text-color-palette', 'text-typography',
              'text-clear-space'):
        m = np.zeros((H_, W_), bool)
        for k, e in E.items():
            if e['group'] == g:
                m |= canvas(e)
        R[g] = kit.dilate(m, 1)
    tiles = np.zeros((H_, W_), bool)
    for k in ('tile-two-tone', 'tile-flat'):
        R[k] = canvas(E[k], 0.5)
        tiles |= R[k]
    for name, kinds in (('dividers', ('rule',)), ('layout-guides', ('guide',)), ('swatches', ('swatch', 'ring')),
                        ('clear-space', ('cs',))):
        m = np.zeros((H_, W_), bool)
        for k, e in E.items():
            if e['kind'] in kinds:
                m |= canvas(e)
        R[name] = kit.dilate(m, 1) & ~kit.dilate(tiles, 1)
    R['board'] = np.ones((H_, W_), bool)
    return R


def run_stats(E, o, r):
    """Audit-style: dE between the medians of the original and of the render over each run's eroded interior."""
    out = {}
    for k, e in E.items():
        if e['kind'] != 'text' and not k.startswith('txt-cs'):
            continue
        x0, y0, x1, y1 = e['box']
        core = kit.erode(e['cov'] >= 0.5, 2 if e.get('stroke_w', 0) >= 5 else 1)
        if core.sum() < 3:
            core = e['cov'] >= 0.9
        mo, mr = np.median(o[y0:y1, x0:x1][core], 0), np.median(r[y0:y1, x0:x1][core], 0)
        out[k] = (hx(mo), hx(mr), round(de(mo, mr), 2))
    return out


def rule_stats(E, o, r):
    out = {}
    for k, e in E.items():
        if e['kind'] != 'rule':
            continue
        a, b = e['lo'] + 25, e['hi'] - 25
        img_o = o if e['orient'] == 'h' else o.transpose(1, 0, 2)
        img_r = r if e['orient'] == 'h' else r.transpose(1, 0, 2)
        c = int(np.floor(e['c']))
        res = []
        for im in (img_o, img_r):
            band = im[c - 4:c + 5, int(a):int(b)]
            bg = np.median(np.concatenate([im[c - 9:c - 5, int(a):int(b)], im[c + 6:c + 10, int(a):int(b)]]).reshape(-1, 3), 0)
            dark = (bg - band) @ LUM
            res.append((np.median(dark.sum(0)), np.median(band[np.argmax(dark.mean(1))], 0)))
        out[k] = {'integral_orig': round(float(res[0][0]), 1), 'integral_render': round(float(res[1][0]), 1),
                  'ratio': round(float(res[1][0] / res[0][0]), 3), 'core_orig': hx(res[0][1]), 'core_render': hx(res[1][1]),
                  'core_dE': round(de(res[0][1], res[1][1]), 2)}
    return out


def mark_stats(o, r):
    x0, y0, x1, y1 = TWO_BOX
    t = TWO.read_text(encoding='utf-8')
    covs = [path_cov(d, TWO_BOX)[0] for _, d, _ in faces(t)]
    u = np.zeros(covs[0].shape)
    for c in covs:
        u = 1 - (1 - u) * (1 - c)
    oo, rr = o[y0:y1, x0:x1], r[y0:y1, x0:x1]
    light = (kit.srgb_to_lab(oo)[..., 0] > 60) & (u > 0.5)
    core = kit.erode(u >= 0.999, 1)
    shell = kit.dilate(u > 0.02, 3) & ~(u > 0.02)
    res = {'light_px_median': [hx(np.median(oo[light], 0)), hx(np.median(rr[light], 0))],
           'mean_L_interior': [round(float(kit.srgb_to_lab(oo[core])[:, 0].mean()), 2), round(float(kit.srgb_to_lab(rr[core])[:, 0].mean()), 2)],
           'outside_3px_median': [hx(np.median(oo[shell], 0)), hx(np.median(rr[shell], 0))]}
    union = {'A (upper half)': np.zeros(u.shape), 'P': np.zeros(u.shape)}
    for i, (fid, d, _) in enumerate(faces(t)):
        vis = covs[i].copy()
        for c in covs[i + 1:]:
            vis *= 1 - c
        cm = kit.erode(vis >= 0.999, 1)
        if cm.sum() < 8:
            cm = vis >= 0.999
        mo, mr = np.median(oo[cm], 0), np.median(rr[cm], 0)
        res[fid] = [hx(mo), hx(mr), round(de(mo, mr), 2)]
        if fid.startswith('face-a-'):
            union['A (upper half)'] = np.maximum(union['A (upper half)'], vis)
        elif fid.startswith('face-p-'):
            union['P'] = np.maximum(union['P'], vis)
    union['A (upper half)'][351 - y0:] = 0
    for k, v in union.items():      # audit-style: medians over the eroded letter
        cm = kit.erode(v >= 0.999, 1)
        mo, mr = np.median(oo[cm], 0), np.median(rr[cm], 0)
        res[k] = [hx(mo), hx(mr), round(de(mo, mr), 2)]
    x0, y0, x1, y1 = FLAT_BOX
    (fid, d, _), = faces(FLAT.read_text(encoding='utf-8'))
    cov = path_cov(d, FLAT_BOX)[0]
    core = kit.erode(cov >= 0.5, 2)
    mo, mr = np.median(o[y0:y1, x0:x1][core], 0), np.median(r[y0:y1, x0:x1][core], 0)
    res['flat-mark-interior'] = [hx(mo), hx(mr), round(de(mo, mr), 2)]
    return res


def sheet(o, before, after, A, out):
    crops = [('header', (360, 34, 1016, 126), 1.4), ('section label 01', (52, 156, 300, 184), 3.0),
             ('section label 02', (722, 156, 948, 184), 3.0), ('logo panel: lockups + tiles', (40, 196, 680, 444), 1.3),
             ('lockup wordmark + tagline', (56, 338, 380, 392), 2.5), ('left tile mark', (408, 316, 510, 386), 6.0),
             ('right tile mark', (545, 316, 647, 386), 6.0), ('palette names + hex (left)', (740, 318, 1030, 394), 2.8),
             ('palette names + hex (right)', (1030, 318, 1320, 394), 2.8), ('specimen', (52, 500, 420, 720), 2.2),
             ('typography notes', (444, 500, 656, 722), 3.0), ('header rule x col divider', (640, 136, 740, 186), 6.0),
             ('row rules x col divider', (650, 420, 730, 470), 7.0), ('pure-white swatch outline', (1094, 214, 1200, 322), 6.0)]
    rows = []
    for title, (x0, y0, x1, y1), s in crops:
        w, h = int((x1 - x0) * s), int((y1 - y0) * s)
        panels = []
        for lab_, im in (('original', o), ('before', before), ('after', after)):
            p = Image.fromarray(np.clip(im[y0:y1, x0:x1], 0, 255).astype(np.uint8)).resize((w, h), Image.NEAREST if s > 2 else Image.LANCZOS)
            c = Image.new('RGB', (w, h + 18), 'white')
            c.paste(p, (0, 18))
            ImageDraw.Draw(c).text((4, 3), '%s - %s' % (title, lab_), fill=(180, 0, 0))
            panels.append(c)
        row = Image.new('RGB', (sum(p.width for p in panels) + 20, h + 18), (140, 140, 140))
        x = 0
        for p in panels:
            row.paste(p, (x, 0))
            x += p.width + 10
        rows.append(row)
    # legend: every colour the board now uses
    tones = {}
    for k, v in A.items():
        tones.setdefault(v['hex'], []).append(k)
    leg_h = 22 * (len(tones) + 1) + 10
    W = max(r.width for r in rows)
    legend = Image.new('RGB', (W, leg_h), 'white')
    d = ImageDraw.Draw(legend)
    d.text((6, 4), 'inks after this pass (swatch, hex, tone, max dE2000 to the members\' measurements, members)', fill='black')
    for i, (h_, mem) in enumerate(sorted(tones.items(), key=lambda kv: -len(kv[1]))):
        y = 26 + 22 * i
        d.rectangle([6, y, 40, y + 16], fill=h_, outline='black')
        a0 = A[mem[0]]
        txt = '%s  %-22s  max dE %.1f  %s' % (h_, a0['tone'], max(A[j]['dE_to_measured'] for j in mem),
                                               ', '.join(m.replace('txt-', '') for m in mem))
        d.text((48, y + 2), txt[:260], fill='black')
    H = sum(r.height + 8 for r in rows) + leg_h
    sh = Image.new('RGB', (W, H), (140, 140, 140))
    y = 0
    for r in rows:
        sh.paste(r, (0, y))
        y += r.height + 8
    sh.paste(legend, (0, y))
    out.parent.mkdir(parents=True, exist_ok=True)
    sh.save(out)


def verify(M, A):
    o = IMG
    before, after = render_composed(before=True), render_composed()
    for nm, im in (('before', before), ('after', after)):
        Image.fromarray(np.clip(np.round(im), 0, 255).astype(np.uint8)).save(WB / ('board-02_inks_%s.png' % nm))
    E = elements(SVG.read_text(encoding='utf-8'))
    R = regions(E)
    lo = kit.srgb_to_lab(o)
    db, da = kit.de2000(lo, kit.srgb_to_lab(before)), kit.de2000(lo, kit.srgb_to_lab(after))
    reg = {k: {'pixels': int(m.sum()), 'before': [round(float(db[m].mean()), 2), round(float(np.percentile(db[m], 95)), 2)],
               'after': [round(float(da[m].mean()), 2), round(float(np.percentile(da[m], 95)), 2)]} for k, m in R.items()}
    rb, ra = run_stats(E, o, before), run_stats(E, o, after)
    runs = {k: {'orig': rb[k][0], 'before': rb[k][1], 'after': ra[k][1], 'dE_before': rb[k][2], 'dE_after': ra[k][2]} for k in ra}
    rules_b, rules_a = rule_stats(E, o, before), rule_stats(E, o, after)
    rules = {k: {'before': rules_b[k], 'after': rules_a[k]} for k in rules_a}
    marks = {'before': mark_stats(o, before), 'after': mark_stats(o, after)}
    res = {'regions_mean_p95': reg, 'text_run_interiors': runs, 'rules': rules, 'tile_marks': marks}
    (WB / 'inks_v2_verify.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    sheet(o, before, after, A, kit.VERIFY / 'board-02_inks.png')
    return res


def load_assign():
    M = json.loads(MEAS.read_text(encoding='utf-8'))
    return M, assign(M)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'measure'
    if cmd == 'measure':
        M = measure()
        MEAS.write_text(json.dumps(M, indent=1), encoding='utf-8')
        for k, r in M.items():
            if k == '_twotone':
                for f, v in r.items():
                    print('%-24s n=%3d orig=%s model %s -> %s  dE %.1f -> %.1f  stops %s -> %s' % (
                        f, v['n'], v['orig_median'], v['model_median_before'], v['model_median_after'], v['dE_before'],
                        v['dE_after'], ' '.join(v['stops_before']), ' '.join(v['stops_after'])))
                continue
            ink = np.clip(r['ink'], 0, 255)
            nm, ph, dp = kit.nearest_palette(ink)
            print('%-26s %-6s now=%s meas=%s dE(now)=%4.1f  %-12s %4.1f  %s' % (
                k, r['kind'], r['color'], hx(ink), de(kit.hexrgb(r['color']), ink), nm, dp, r['method']))
    elif cmd == 'assign':
        M, A = load_assign()
        by = {}
        for k, v in A.items():
            by.setdefault(v['hex'], []).append(k)
        for h_, mem in sorted(by.items(), key=lambda kv: -len(kv[1])):
            a0 = A[mem[0]]
            print('%s %-20s palette=%-5s max dE to members %.2f  was {%s}  members: %s' % (
                h_, a0['tone'], a0['palette'], max(A[j]['dE_to_measured'] for j in mem),
                ','.join(sorted({A[j]['was'] for j in mem})), ' '.join(m.replace('txt-', '') for m in mem)))
    elif cmd == 'apply':
        M, A = load_assign()
        strokes, shadow = apply(M, A)
        update_fit(M, A, strokes, shadow)
        print(json.dumps(strokes, indent=1))
        print(json.dumps({k: v for k, v in shadow.items() if k != 'trials'}, indent=1))
        for t in shadow['trials'][:6]:
            print(t)
    elif cmd == 'verify':
        M, A = load_assign()
        res = verify(M, A)
        for k, v in res['regions_mean_p95'].items():
            print('%-22s px=%6d  mean %5.2f -> %5.2f   p95 %5.2f -> %5.2f' % (k, v['pixels'], v['before'][0], v['after'][0],
                                                                         v['before'][1], v['after'][1]))
