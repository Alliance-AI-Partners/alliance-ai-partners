"""Per-facet colour fitting on a mesh, palette snapping, supporting-tone clustering."""
import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from b_fit import cover
from b_export import fit_gradient, fit_gradient_k

SOLID_DE = 2.0     # 2-stop gradient whose stops are closer than this (dE2000) -> solid fill
THREE_GAIN = 0.85  # use a middle stop only when it cuts the facet's rms by >15 % ...
THREE_ABS = 1.0    # ... and by more than 1 RGB unit


def interior_samples(poly, img, ss=4, erode=1, xform=None, valid=None):
    """Pixel centres fully inside `poly` (eroded by `erode` px) and their RGB in `img`.
    xform: optional f(x, y) -> (X, Y) mapping master coords to img coords (bilinear sampling);
    then `poly` is in master coords and the samples are taken on the master pixel grid."""
    x0 = int(np.floor(poly[:, 0].min())) - 2; x1 = int(np.ceil(poly[:, 0].max())) + 3
    y0 = int(np.floor(poly[:, 1].min())) - 2; y1 = int(np.ceil(poly[:, 1].max())) + 3
    c = cover(poly, x0, y0, x1 - x0, y1 - y0, ss)
    m = c >= 0.999
    for _ in range(erode):
        mm = m.copy()
        mm[1:] &= m[:-1]; mm[:-1] &= m[1:]; mm[:, 1:] &= m[:, :-1]; mm[:, :-1] &= m[:, 1:]
        if mm.sum() >= 8:
            m = mm
    ys, xs = np.nonzero(m)
    px, py = xs + x0 + 0.5, ys + y0 + 0.5
    if xform is None:
        rgb = img[ys + y0, xs + x0].astype(float)
    else:
        X, Y = xform(px, py)
        X = np.clip(X - 0.5, 0, img.shape[1] - 1.001); Y = np.clip(Y - 0.5, 0, img.shape[0] - 1.001)
        x0i, y0i = np.floor(X).astype(int), np.floor(Y).astype(int)
        fx, fy = (X - x0i)[:, None], (Y - y0i)[:, None]
        I = img.astype(float)
        rgb = (I[y0i, x0i] * (1 - fx) * (1 - fy) + I[y0i, x0i + 1] * fx * (1 - fy)
               + I[y0i + 1, x0i] * (1 - fx) * fy + I[y0i + 1, x0i + 1] * fx * fy)
        if valid is not None:   # drop samples that land on the target's background (geometry mismatch)
            ok = valid[np.clip(np.round(Y).astype(int), 0, img.shape[0] - 1), np.clip(np.round(X).astype(int), 0, img.shape[1] - 1)]
            px, py, rgb = px[ok], py[ok], rgb[ok]
    return px, py, rgb


def robust_weights(px, py, rgb, poly, iters=4):
    """IRLS (Cauchy) weights: samples that belong to a misaligned neighbour stop pulling the fit."""
    w = np.ones(len(px))
    for _ in range(iters):
        g = fit_gradient(px, py, rgb, poly, w)
        pred = g['coef'][0] + ((px - g['center'][0]) * np.cos(g['th']) + (py - g['center'][1]) * np.sin(g['th']))[:, None] * g['coef'][1]
        r = np.sqrt(((pred - rgb) ** 2).mean(1))
        c = max(2.5 * np.median(r), 3.0)
        w = 1.0 / (1.0 + (r / c) ** 2)
    return w


def fit_facets(V, F, img, xform=None, allow_three=True, force_solid=False, erode=1, robust=False, valid=None, min_samples=8):
    """One fill per facet: {'kind': solid|linear, 'stops': [(offset, rgb)], 'p1', 'p2', 'rms', ...}."""
    fills = []
    for f in F:
        poly = V[f]
        px, py, rgb = interior_samples(poly, img, xform=xform, erode=erode, valid=valid)
        if len(px) < min_samples:   # nothing reliable to sample: borrow a neighbour's fill below
            fills.append(None)
            continue
        wts = robust_weights(px, py, rgb, poly) if robust else None
        g2 = fit_gradient(px, py, rgb, poly, wts)
        stop_de = float(kit.de2000(kit.srgb_to_lab(np.clip(g2['c1'], 0, 255)), kit.srgb_to_lab(np.clip(g2['c2'], 0, 255))))
        out = dict(n=len(px), rms_solid=float(g2['rms_solid']), rms2=float(g2['rms']), stop_de=stop_de,
                   mean=np.clip(g2['mean'], 0, 255))
        if force_solid or stop_de < SOLID_DE:
            out.update(kind='solid', stops=[(0.0, out['mean'])], rms=out['rms_solid'])
        else:
            out.update(kind='linear', p1=g2['p1'], p2=g2['p2'], rms=float(g2['rms']),
                       stops=[(0.0, np.clip(g2['c1'], 0, 255)), (1.0, np.clip(g2['c2'], 0, 255))])
            if allow_three and len(px) >= 30:
                g3 = fit_gradient_k(px, py, rgb, poly, 3, th0=g2['th'], w=wts)
                out['rms3'] = float(g3['rms'])
                if g3['rms'] < THREE_GAIN * g2['rms'] and g2['rms'] - g3['rms'] > THREE_ABS:
                    out.update(p1=g3['p1'], p2=g3['p2'], rms=float(g3['rms']),
                               stops=list(zip(g3['offsets'], g3['colors'])))
        # keep every stop inside the colours actually seen in the facet (no overshoot / clipping artefacts)
        lo, hi = rgb.min(0), rgb.max(0)
        out['stops'] = [(o, np.clip(col, lo, hi)) for o, col in out['stops']]
        fills.append(out)
    # facets without samples take the fill of the neighbour they share the longest edge with
    for i, g in enumerate(fills):
        if g is not None:
            continue
        best = None
        for j, h in enumerate(fills):
            if h is None or j == i:
                continue
            shared = 0.0
            for k in range(len(F[i])):
                a, b = F[i][k], F[i][(k + 1) % len(F[i])]
                if a in F[j] and b in F[j]:
                    shared += float(np.hypot(*(V[a] - V[b])))
            if shared > 0 and (best is None or shared > best[0]):
                best = (shared, j)
        src = fills[best[1]] if best else next(h for h in fills if h is not None)
        fills[i] = dict(src, borrowed_from=best[1] if best else None, n=0)
    return fills


def snap(rgb):
    name, hx, de = kit.nearest_palette(np.clip(rgb, 0, 255))
    return (hx, name, de) if de <= 4.0 else (kit.rgbhex(rgb), None, de)


def family(lab):
    """Readable family name from CIE Lab (used to name supporting tones)."""
    L, a, b = lab
    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a)) % 360
    if C < 30:
        return 'Navy' if L < 25 else 'Slate'
    if L < 30:
        return 'Deep Blue'
    if h >= 285:
        return 'Blue'
    if h >= 260:
        return 'Azure'
    if h >= 225:
        return 'Sky'
    if h >= 185:
        return 'Cyan'
    return 'Aqua'


def cluster_tones(colors, thresh=3.0):
    """Agglomerative merge (average colour in sRGB, distance dE2000 between cluster means) until no two
    clusters are within `thresh`. Returns (labels, centers_rgb)."""
    cols = np.array(colors, float)
    groups = [[i] for i in range(len(cols))]
    while True:
        cs = [kit.srgb_to_lab(cols[g].mean(0)) for g in groups]
        best = None
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                d = float(kit.de2000(cs[i], cs[j]))
                if d <= thresh and (best is None or d < best[0]):
                    best = (d, i, j)
        if best is None:
            break
        _, i, j = best
        groups[i] += groups[j]; groups.pop(j)
    labels = np.zeros(len(cols), int)
    centers = []
    for k, g in enumerate(groups):
        labels[g] = k
        centers.append(cols[g].mean(0))
    return labels, centers
