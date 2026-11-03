"""ap-hero, stage 1: soft face masks from original 06 -> traced raw outlines (legs: exact polygons from
fitted lines). Writes work/ap-/F_faces.npy and geo_raw.json. Stage 2 is make_hero.py."""
import json
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from seg import NAMES
from soft import memberships
from fitcurve import Line

W = kit.WORK / 'ap-'
L = {n: k for k, n in enumerate(NAMES)}
H = Wd = 1024
DELTA = 2.5   # px a lower face reaches under the face stacked above it

# faces bottom -> top
FACES = ['p-bowl-lower', 'p-bowl-under', 'a-right-outer', 'a-right-inner', 'a-left-bevel', 'a-left-outer',
         'p-bowl-top', 'p-bowl-fold', 'ribbon-front-stem', 'ribbon-front', 'ribbon-back']
POLY = {'a-right-outer', 'a-right-inner', 'a-left-bevel', 'a-left-outer'}

# measured on 06 (lines.py and the column/row edge fits): straight edges of the P and the seams
G = {'top': 313.38, 'base': 710.64, 'P_left': 541.4, 'stem_right': 622.2, 'fold_top': 352.5,
     'counter_top': 391.66, 'counter_bottom': 498.55, 'crease': 538.23, 'bowl_bottom': 577.15,
     'seam_stem': 480.0, 'under_end': 760.0, 'top_split_x': 640.0,
     'crossbar_top': 554.2, 'crossbar_bottom': 632.12}


def lines_dict():
    ln = json.load(open(W / 'lines06.json'))
    ln.update(G)
    return ln


def snap_lines(ln):
    return [Line.h(ln['top'], 'top'), Line.h(ln['fold_top'], 'fold_top'), Line.h(ln['counter_top'], 'counter_top'),
            Line.h(ln['counter_bottom'], 'counter_bottom'), Line.h(ln['crease'], 'crease'),
            Line.h(ln['bowl_bottom'], 'bowl_bottom'), Line.h(ln['seam_stem'], 'seam_stem'),
            Line.v(ln['P_left'], 'P_left'), Line.v(ln['stem_right'], 'stem_right'), Line.v(ln['under_end'], 'under_end'),
            Line.h(ln['crossbar_top'], 'crossbar_top'), Line.h(ln['crossbar_bottom'], 'crossbar_bottom'),
            Line.xy(ln['LL_outer']['a'], ln['LL_outer']['b'], 'LL_outer')]


def soft_half(xx, yy, a, b, c):
    """anti-aliased half-plane a*x + b*y + c > 0 (a, b normalised)."""
    return np.clip(0.5 + (a * xx + b * yy + c), 0, 1)


def hermite(p0, t0, p1, t1, n=400):
    p0, t0, p1, t1 = (np.asarray(v, float) for v in (p0, t0, p1, t1))
    L = np.hypot(*(p1 - p0))
    t = np.linspace(0, 1, n)[:, None]
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * p0 + h10 * L * t0 + h01 * p1 + h11 * L * t1


def side_dist(curve, xs, ys):
    """signed distance of pixel centres to a dense polyline: negative on the left of travel (y down)."""
    q = np.stack([xs + 0.5, ys + 0.5], 1)
    d2 = ((q[:, None, :] - curve[None]) ** 2).sum(-1)
    k = d2.argmin(1)
    tang = np.gradient(curve, axis=0)[k]
    v = q - curve[k]
    cr = tang[:, 0] * v[:, 1] - tang[:, 1] * v[:, 0]
    return np.sign(cr) * np.sqrt(d2[np.arange(len(k)), k])


def fix_low_contrast(M, rgb, lab):
    """Where two faces have nearly the same colour the watershed edge wanders; replace those stretches by
    smooth curves continued from the well-defined parts of the same edge.
    A: ribbon upper/lower band boundary where the bands swap colour (crossbar, x ~ 424-505).
    B: lower edge of the ribbon's back band over the left leg near the tip (x < 222)."""
    from lines import col_edges, row_edges, fit_line
    U, Lo = L['ribbon-upper'], L['ribbon-lower']
    # A ---------------------------------------------------------------
    pc = col_edges(rgb.astype(np.uint8), lab, [U], [Lo], (384, 426))
    a, b, *_ = fit_line(pc, 'x')               # y = a x + b on the crossbar
    pr = row_edges(rgb.astype(np.uint8), lab, [U], [Lo], (540, 570))
    a2, b2, *_ = fit_line(pr, 'y')             # x = a2 y + b2 on the arc (local)
    p0 = (424.0, a * 424 + b); t0 = np.array([1.0, a]); t0 /= np.hypot(*t0)
    y1 = 566.0; p1 = (a2 * y1 + b2, y1); t1 = np.array([-a2, -1.0]); t1 /= np.hypot(*t1)
    curve = hermite(p0, t0, p1, t1)
    ys, xs = np.nonzero(((lab == U) | (lab == Lo)))
    near = (xs > p0[0] - 1) & (xs < p1[0] + 1) & (ys > p1[1] - 12) & (ys < p0[1] + 12)
    ys, xs = ys[near], xs[near]
    sd = side_dist(curve, xs, ys)
    keep = np.abs(sd) < 9
    ys, xs, sd = ys[keep], xs[keep], sd[keep]
    tot = M[U, ys, xs] + M[Lo, ys, xs]
    M[U, ys, xs] = tot * np.clip(0.5 - sd, 0, 1)      # upper band on the left of travel
    M[Lo, ys, xs] = tot - M[U, ys, xs]
    # B ---------------------------------------------------------------
    legs = [L['a-left-outer'], L['a-left-bevel']]
    pts = col_edges(rgb.astype(np.uint8), lab, [Lo], legs, (220, 262))
    X = np.array([p[0] for p in pts]); Y = np.array([p[1] for p in pts])
    cq = np.polyfit(X, Y, 2)
    ys, xs = np.nonzero(np.isin(lab, [Lo] + legs))
    sel = xs < 222
    ys, xs = ys[sel], xs[sel]
    f = np.polyval(cq, xs + 0.5)
    fp = np.polyval(np.polyder(cq), xs + 0.5)
    d = (f - (ys + 0.5)) / np.sqrt(1 + fp ** 2)          # > 0: above the curve (back band)
    keep = np.abs(d) < 9
    ys, xs, d = ys[keep], xs[keep], d[keep]
    tot = M[Lo, ys, xs] + M[legs[0], ys, xs] + M[legs[1], ys, xs]
    M[Lo, ys, xs] = tot * np.clip(0.5 + d, 0, 1)
    M[legs[0], ys, xs] = tot - M[Lo, ys, xs]
    M[legs[1], ys, xs] = 0
    return M, {'A': {'p0': p0, 't0': t0.tolist(), 'p1': p1, 't1': t1.tolist()}, 'B': cq.tolist()}


def face_memberships(rgb, lab, ln):
    M = memberships(rgb, lab, len(NAMES))
    M, fixes = fix_low_contrast(M, rgb, lab)
    yy, xx = np.mgrid[0:H, 0:Wd] + 0.5
    F = {}
    U = M[L['ribbon-upper']]
    top = np.maximum(soft_half(xx, yy, 0, -1, ln['fold_top']), soft_half(xx, yy, 1, 0, -ln['top_split_x']))
    low = soft_half(xx, yy, 0, 1, -ln['seam_stem'])
    F['p-bowl-top'] = U * top
    F['ribbon-front-stem'] = U * (1 - top) * (1 - low)
    F['ribbon-front'] = U * (1 - top) * low
    F['ribbon-back'] = M[L['ribbon-lower']]
    F['p-bowl-fold'] = M[L['p-bowl-fold']]
    P = M[L['p-bowl-lower']] + M[L['p-bowl-under']] + M[L['p-stem']]
    s = soft_half(xx, yy, 0, 1, -ln['crease']) * soft_half(xx, yy, -1, 0, ln['under_end'])
    F['p-bowl-under'] = P * s
    F['p-bowl-lower'] = P * (1 - s)
    for n in POLY:
        F[n] = M[L[n]]
    F['bg'] = M[L['bg']]
    return F, fixes


def clip_poly(poly, a, b, c):
    """Sutherland-Hodgman: keep a*x + b*y + c >= 0."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] + c, a * q[0] + b * q[1] + c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def leg_polys(ln, delta=DELTA):
    """Leg faces as convex polygons from the fitted x = a*y + b lines; a lower face reaches `delta` px
    under the face above it (left bevel under left outer, right legs under the left bevel, outer under inner)."""
    def right_of(k, sh=0.0):
        return (1.0, -ln[k]['a'], -(ln[k]['b'] + sh))

    def left_of(k, sh=0.0):
        return (-1.0, ln[k]['a'], ln[k]['b'] + sh)
    below_top = (0.0, 1.0, -ln['top'])
    above_base = (0.0, -1.0, ln['base'])
    hp = {
        'a-left-outer': [right_of('LL_outer'), left_of('LL_crease'), below_top, above_base],
        'a-left-bevel': [right_of('LL_crease', -delta), left_of('LL_inner'), below_top, above_base],
        'a-right-inner': [right_of('RL_inner'), left_of('RL_internal'), right_of('LL_inner', -delta), below_top, above_base],
        'a-right-outer': [right_of('RL_internal', -delta), left_of('RL_outer'), right_of('LL_inner', -delta), below_top, above_base],
    }
    out = {}
    for n, hs in hp.items():
        p = [(0, 0), (1024, 0), (1024, 1024), (0, 1024)]
        for h in hs:
            p = clip_poly(p, *h)
        out[n] = p
    return out


def poly_d(p, nd=3):
    f = lambda v: ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
    return 'M' + ' L'.join('%s %s' % (f(x), f(y)) for x, y in p) + ' Z'


def blur(m, sigma):
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(m, r, mode='edge')
    p = sum(k[i] * p[:, i:i + m.shape[1]] for i in range(2 * r + 1))
    return sum(k[i] * p[i:i + m.shape[0]] for i in range(2 * r + 1))


def reach(m, delta, sigma=1.5):
    """Smooth outward offset of a soft mask by ~delta px (Gaussian-blur level set), so the hidden edge a
    face tucks under its upper neighbour is a clean curve, not a copy of pixel noise."""
    from math import erf, sqrt
    # level t of the blurred mask that sits `delta` outside a straight edge: Phi(-delta/sigma)
    t = 0.5 * (1 + erf(-delta / sigma / sqrt(2)))
    g = blur(np.asarray(m, float), sigma)
    return np.clip(0.5 + (g - t) / (2 * t), 0, 1)


def trace_face(mask, upscale=4, blur=0.35):
    ys, xs = np.nonzero(mask > 0.01)
    y0, y1 = max(0, ys.min() - 6), min(mask.shape[0], ys.max() + 7)
    x0, x1 = max(0, xs.min() - 6), min(mask.shape[1], xs.max() + 7)
    ds = kit.trace_mask(mask[y0:y1, x0:x1], upscale=upscale, blur=blur, noise=4)
    return ' '.join(kit.transform_d(d, 1.0, x0, y0) for d in ds)


def stack_masks(F, faces, delta=DELTA):
    """Mask each face is traced from: its own soft coverage plus whatever is stacked above it (the faces
    above, and the background, so its outer edge falls outside the silhouette and is cut by it later),
    limited to `delta` px around its own visible region."""
    out = {}
    for i, n in enumerate(faces):
        upper = sum(F[m] for m in faces[i + 1:]) if i + 1 < len(faces) else 0
        out[n] = np.minimum(np.clip(F[n] + upper + F['bg'], 0, 1), reach(F[n], delta))
    return out


if __name__ == '__main__':
    rgb = kit.load('06').astype(float)
    lab = np.load(W / 'labels06.npy')
    ln = lines_dict()
    F, fixes = face_memberships(rgb, lab, ln)
    print('low-contrast fixes', fixes)
    np.save(W / 'F_faces.npy', np.stack([F[n] for n in FACES]).astype(np.float32))
    np.save(W / 'F_bg.npy', F['bg'].astype(np.float32))
    masks = stack_masks(F, FACES)
    polys = leg_polys(ln)
    geo = {'silhouette': trace_face(1 - F['bg'])}
    for n in FACES:
        geo[n] = poly_d(polys[n]) if n in POLY else trace_face(masks[n])
        print(n, 'segments', geo[n].count('C') + geo[n].count('L'))
    json.dump(geo, open(W / 'geo_raw.json', 'w'), indent=1)
