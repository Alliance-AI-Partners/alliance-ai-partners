"""hero-04, stage 4: per-face linear gradients fitted to 04's own pixels (least squares in sRGB, <= 5 stops,
stops only where the face is visible), seam-continuous across the straight cuts inside one band; colour rule
(fidelity first): snap to a kit.PALETTE colour only within dE2000 2.0, merge tones within dE2000 2.0.
Writes fills04.json; verify04.py renders and scores."""
import json
import sys
import numpy as np

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
import gradfit
import fitgrad04
from build_hero import FACES
from seg04 import W4

SNAP_DE = 2.0
MERGE_DE = 2.0
lab_of = lambda c: kit.srgb_to_lab(np.asarray(c, float))
labh = lambda h: kit.srgb_to_lab(kit.hexrgb(h))


def visible_labels(geo, shape, order=FACES):
    h, w = shape
    lab = np.full((h, w), -1, int)
    for i, n in enumerate(order):
        lab[kit.raster(geo[n], w, h) > 0.5] = i
    return lab


def load_geo(src):
    """geometry json -> (geo, face order bottom -> top); highlight faces sit right above their host face."""
    g = json.load(open(W4 / src))
    return g['geo'], g.get('order', FACES)


def seam_points(ln, F):
    """points on the straight cuts inside one band where both faces are present (make_hero.seams for 04)."""
    def on(pts, a, b):
        return pts[[(F[a][int(y), int(x)] + F[b][int(y), int(x)]) > 0.9 for x, y in pts]]
    s1 = np.stack([np.linspace(ln['P_left'] + 0.6, 430, 60), np.full(60, ln['fold_top'])], 1)
    s2 = np.stack([np.linspace(380, 440, 80), np.full(80, ln['seam_stem'])], 1)
    s3 = np.stack([np.full(40, ln['under_end']), np.linspace(ln['crease'] + 0.6, 428, 40)], 1)
    return [('p-bowl-top', 'ribbon-front-stem', on(s1, 'p-bowl-top', 'ribbon-front-stem')),
            ('ribbon-front-stem', 'ribbon-front', on(s2, 'ribbon-front-stem', 'ribbon-front')),
            ('p-bowl-under', 'p-bowl-lower', on(s3, 'p-bowl-under', 'p-bowl-lower'))]


def fit_face(n, xy, c, ln, pad=None, Kmax=5):
    keep = np.ones(len(c), bool)
    for it in range(2):   # fit, drop pixels far off the model (specular glints, JPEG ringing), refit
        idx = np.nonzero(keep)[0]
        if n.startswith('a-'):
            ax = np.degrees(np.arctan2(1, ln['LL_crease' if n.startswith('a-left') else 'RL_internal']['a']))
            g = fitgrad04.fit(xy[idx], c[idx], Kmax=Kmax, angles=np.arange(ax - 20, ax + 20.01, 4.0), pad=pad)
        elif n == 'ribbon-front-stem':
            # cut by two horizontal seams (fold_top, seam_stem): a vertical gradient is constant along both,
            # so the padded neighbours above and below can meet it exactly
            g = fitgrad04.fit(xy[idx], c[idx], Kmax=Kmax, angles=np.arange(84, 96.01, 2.0), pad=pad, angle_bounds=(84, 96))
        else:
            g = fitgrad04.fit(xy[idx], c[idx], Kmax=Kmax, angles=np.arange(0, 180, 4.0), pad=pad)
        res = kit.de2000(lab_of(c), lab_of(gradfit.predict(g, xy)))
        keep = res < max(6.0, 3 * np.median(res))
    g['colors'], g['mse'] = gradfit.solve(gradfit.hat_basis(xy[keep] @ g['u'], g['knots']), c[keep])
    g['kept'] = float(keep.mean())
    g['center'] = xy[keep].mean(0)
    return g, keep


def merge_tones(hexes, thr=MERGE_DE):
    """complete-linkage agglomeration in dE2000 (finalize.py), medoid kept: {hex: representative}."""
    cl = [[h] for h in sorted(set(hexes))]
    D = lambda a, b: max(float(kit.de2000(labh(x), labh(y))) for x in a for y in b)
    while True:
        best = None
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                d = D(cl[i], cl[j])
                if d <= thr and (best is None or d < best[0]):
                    best = (d, i, j)
        if best is None:
            break
        _, i, j = best
        cl[i] += cl.pop(j)
    rep = {}
    for c in cl:
        med = min(c, key=lambda h: sum(float(kit.de2000(labh(h), labh(o))) for o in c))
        for h in c:
            rep[h] = med
    return rep


def snap(hx):
    name, phex, de = kit.nearest_palette(hx)
    return (phex, name) if de <= SNAP_DE else (hx, None)


def fills_from(fits, J):
    fills = {}
    for n, (xy, c, g) in fits.items():
        p1, p2, offs = gradfit.svg_vector(g, g['center'])
        cols = J.get(n, g['colors'])
        stops = [{'offset': round(float(o), 4), 'hex': kit.rgbhex(np.clip(col, 0, 255))} for o, col in zip(offs, cols)]
        fills[n] = {'type': 'linear', 'x1': round(float(p1[0]), 3), 'y1': round(float(p1[1]), 3),
                    'x2': round(float(p2[0]), 3), 'y2': round(float(p2[1]), 3), 'stops': stops}
    return fills


def tied_solve(fits, sm, lam=3.0):
    """Colour rule, fidelity first. Raw stops = each face's least-squares colours (seam faces from the joint
    seam solve). Stops within SNAP_DE of a kit.PALETTE colour become that colour; the rest are clustered
    (complete linkage: every pair within MERGE_DE) and each cluster's one colour is re-solved by least squares
    over all pixels of every face that uses it, together with the seam-continuity rows, so merging costs as
    little fidelity as possible. Returns ({(face, k): (hex, palette name or None)}, {raw hex: tone hex})."""
    J = gradfit.joint({n: fits[n] for n in {a for q in sm for a in q[:2]}}, sm, lam=lam)
    raw = {n: J.get(n, g['colors']) for n, (xy, c, g) in fits.items()}
    stops = [(n, k) for n in fits for k in range(fits[n][2]['K'])]
    hexes = {q: kit.rgbhex(np.clip(raw[q[0]][q[1]], 0, 255)) for q in stops}
    fixed = {}
    for q, hx in hexes.items():
        p, name = snap(hx)
        if name:
            fixed[q] = (p, name)
    free = [q for q in stops if q not in fixed]
    rep = merge_tones([hexes[q] for q in free])
    tones = sorted(set(rep.values()))
    col = {q: tones.index(rep[hexes[q]]) for q in free}

    def block(n, pts):
        g = fits[n][2]
        B = gradfit.hat_basis(np.asarray(pts, float) @ g['u'], g['knots'])
        R = np.zeros((len(B), len(tones))); t = np.zeros((len(B), 3))
        for k in range(g['K']):
            if (n, k) in fixed:
                t += np.outer(B[:, k], kit.hexrgb(fixed[(n, k)][0]))
            else:
                R[:, col[(n, k)]] += B[:, k]
        return R, t
    rows, rhs = [], []
    for n, (xy, c, g) in fits.items():
        R, t = block(n, xy)
        rows.append(R); rhs.append(c - t)
    for a, b, pts in sm:
        Ra, ta = block(a, pts)
        Rb, tb = block(b, pts)
        wgt = lam * np.sqrt((len(fits[a][0]) + len(fits[b][0])) / 2.0 / max(1, len(pts)))
        rows.append((Ra - Rb) * wgt); rhs.append((tb - ta) * wgt)
    X, *_ = np.linalg.lstsq(np.vstack(rows), np.vstack(rhs), rcond=None)
    out = {}
    for q in stops:
        out[q] = fixed[q] if q in fixed else (kit.rgbhex(np.clip(X[col[q]], 0, 255)), None)
    tone_of = {hexes[q]: out[q][0] for q in free}
    return out, tone_of, hexes


if __name__ == '__main__':
    rgb = kit.load('04').astype(float)
    shape = rgb.shape[:2]
    ln = json.load(open(W4 / 'lines04.json'))
    geo, order = load_geo(sys.argv[1] if len(sys.argv) > 1 else 'geo04.json')
    out = sys.argv[2] if len(sys.argv) > 2 else 'fills04.json'
    Fs = np.load(W4 / 'F04.npy')
    F = {n: Fs[i].astype(float) for i, n in enumerate(FACES)}
    m04 = np.load(kit.WORK / 'ap-' / 'mask04.npy')
    lab = visible_labels(geo, shape, order)
    inner = kit.erode(m04, 1)
    sm = seam_points(ln, F)
    pads = {'p-bowl-top': sm[0][2], 'ribbon-front': sm[1][2]}
    fits, report = {}, {}
    for i, n in enumerate(order):
        # highlight faces are 2-6 px wide: fit on every pixel they cover
        vis = ((lab == i) if n.endswith('-highlight') else kit.erode(lab == i, 1)) & inner
        ys, xs = np.nonzero(vis)
        xy = np.stack([xs + 0.5, ys + 0.5], 1)
        c = rgb[ys, xs]
        g, keep = fit_face(n, xy, c, ln, pad=pads.get(n))
        fits[n] = (xy[keep], c[keep], g)
    sol, rep, raw_hex = tied_solve(fits, sm)
    fills = fills_from(fits, {})
    raw = json.loads(json.dumps(fills))
    for n in order:
        for k, s in enumerate(fills[n]['stops']):
            s['hex'], s['palette'] = sol[(n, k)]
            raw[n]['stops'][k]['hex'] = raw_hex[(n, k)]
    for n in order:
        xy, c, g = fits[n]
        gg = dict(g, colors=np.array([kit.hexrgb(s['hex']) for s in fills[n]['stops']]))
        de = kit.de2000(lab_of(c), lab_of(gradfit.predict(gg, xy)))
        report[n] = {'K': g['K'], 'angle': round(g['angle'], 1), 'kept': round(g['kept'], 3), 'pixels': len(c),
                     'de_mean': round(float(de.mean()), 2), 'de_p95': round(float(np.percentile(de, 95)), 2)}
        print(f"{n:18s} K{g['K']} a{g['angle']:6.1f} kept {g['kept']:.2f} n{len(c):5d} dE {report[n]['de_mean']:.2f}/{report[n]['de_p95']:.2f}",
              [s['hex'] + ('*' if s['palette'] else '') for s in fills[n]['stops']])
    for a, b, pts in sm:
        pa = lambda nm: gradfit.predict(dict(fits[nm][2], colors=np.array([kit.hexrgb(s['hex']) for s in fills[nm]['stops']])), pts)
        d = kit.de2000(lab_of(pa(a)), lab_of(pa(b)))
        print(f'seam {a} | {b}: {len(pts)} pts, dE max {d.max():.2f} mean {d.mean():.2f}')
    json.dump({'fills': fills, 'raw_fills': raw, 'merge': rep, 'report': report}, open(W4 / out, 'w'), indent=1)
