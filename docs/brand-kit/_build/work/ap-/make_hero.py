"""ap-hero, stage 2: clean geometry (snapped lines, minimal Beziers), least-squares gradients from 06
(seam-continuous where one band is split into several faces), SVG + verification."""
import json
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import gradfit
from fitcurve import rebuild, count_anchors, Line, micro_cleanup
from build_hero import FACES, POLY, W, lines_dict, snap_lines
from pathops import vc_pathfinder


def lab_of(c):
    return kit.srgb_to_lab(np.asarray(c, float))


def snap(c):
    hx = kit.rgbhex(c)
    name, phex, de = kit.nearest_palette(hx)
    return (phex, name) if de <= 4.0 else (hx, None)


def visible_pixels(Fn, rgb):
    vis = kit.erode(Fn > 0.98, 1)
    ys, xs = np.nonzero(vis)
    return np.stack([xs + 0.5, ys + 0.5], 1), rgb[ys, xs], (ys, xs)


def fit_faces(F, rgb, ln, sub=2, faces=FACES, pad=None):
    """Leg faces: gradient along the leg axis (+-15 deg), up to 5 stops (the ribbon's shadow falls across
    them); the other faces: free direction, up to 3 stops."""
    axis_l = np.degrees(np.arctan2(1, ln['LL_crease']['a']))
    axis_r = np.degrees(np.arctan2(1, ln['RL_internal']['a']))
    out = {}
    for n in faces:
        xy, c, (ys, xs) = visible_pixels(F[n], rgb)
        sel = (ys % sub == 0) & (xs % sub == 0)
        if n.startswith('a-'):
            ax = axis_l if n.startswith('a-left') else axis_r
            g = gradfit.fit(xy[sel], c[sel], Kmax=5, angles=np.arange(ax - 15, ax + 15.01, 3.0), improve=0.85)
        else:
            g = gradfit.fit(xy[sel], c[sel], Kmax=3, pad=(pad or {}).get(n))
        g['colors'], g['mse'] = gradfit.solve(gradfit.hat_basis(xy @ g['u'], g['knots']), c)
        g['center'] = xy.mean(0)
        out[n] = (xy, c, g)
    return out


def seams(ln, F):
    inside = lambda pts, n1, n2: pts[[(F[n1][int(y), int(x)] + F[n2][int(y), int(x)]) > 0.9 for x, y in pts]]
    s1 = np.stack([np.linspace(ln['P_left'] + 1, 579, 40), np.full(40, ln['fold_top'])], 1)
    s2 = np.stack([np.linspace(520, 590, 80), np.full(80, ln['seam_stem'])], 1)
    s3 = np.stack([np.full(40, ln['under_end']), np.linspace(ln['crease'] + 1, 575, 40)], 1)
    return [('p-bowl-top', 'ribbon-front-stem', inside(s1, 'p-bowl-top', 'ribbon-front-stem')),
            ('ribbon-front-stem', 'ribbon-front', inside(s2, 'ribbon-front-stem', 'ribbon-front')),
            ('p-bowl-under', 'p-bowl-lower', inside(s3, 'p-bowl-under', 'p-bowl-lower'))]


def fill_entry(g, colors):
    p1, p2, offs = gradfit.svg_vector(g, g['center'])
    stops = []
    for o, col in zip(offs, colors):
        hx, sw = snap(col)
        stops.append({'offset': round(float(o), 4), 'hex': hx, 'swatch': sw})
    return {'type': 'linear', 'x1': round(float(p1[0]), 3), 'y1': round(float(p1[1]), 3),
            'x2': round(float(p2[0]), 3), 'y2': round(float(p2[1]), 3), 'stops': stops}


def svg_for(geo, fills, faces=FACES, w=1024, h=1024, prefix='grad-'):
    defs, body = [], []
    for n in faces:
        f = fills[n]
        if f['type'] == 'solid':
            paint = f['hex']
        else:
            gid = prefix + n
            defs.append(kit.lin_grad(gid, f['x1'], f['y1'], f['x2'], f['y2'], [(s['offset'], s['hex']) for s in f['stops']]))
            paint = f'url(#{gid})'
        body.append(f'<path id="face-{n}" d="{geo[n]}" fill="{paint}" fill-rule="evenodd"/>')
    return kit.svg_doc(w, h, '\n'.join(body), '\n'.join(defs))


def metrics(orig, comp, bg='#FFFFFF'):
    om = kit.bg_mask(orig, bg)
    rm = kit.bg_mask(comp, bg)
    m = kit.compare(orig, comp, om)
    m2 = kit.compare(orig, comp, kit.erode(om, 1))
    return {'iou': round(kit.iou(om, rm), 4), 'de_mean': m['de_mean'], 'de_p95': m['de_p95'],
            'de_mean_interior': m2['de_mean'], 'de_p95_interior': m2['de_p95']}, m['de_map']


if __name__ == '__main__':
    rgb = kit.load('06').astype(float)
    ln = lines_dict()
    geo_raw = json.load(open(W / 'geo_raw.json'))
    Fs = np.load(W / 'F_faces.npy')
    F = {n: Fs[i].astype(float) for i, n in enumerate(FACES)}
    err = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
    lines = snap_lines(ln) + [Line.xy(ln[q]['a'], ln[q]['b'], q) for q in ('LL_inner', 'RL_inner', 'RL_outer')]
    sil_lines = lines + [Line.h(ln['base'], 'base')]
    sil = rebuild(geo_raw["silhouette"], lines=sil_lines, err=0.3, line_tol=0.25)
    geo = {}
    for n in FACES:
        d = geo_raw[n] if n in POLY else rebuild(geo_raw[n], lines=lines, err=err, line_tol=0.3)
        geo[n] = ' '.join(vc_pathfinder([('silhouette', sil), (n, d)], 'intersect', W / f'_isect_{n}.svg'))
        if n in ('ribbon-front', 'ribbon-back'):
            # Pathfinder leaves 1-2 px hooks where the ribbon edge meets the silhouette at the two
            # interlace mouths (the ribbon's top edge leaving the A's outer edge; its outer edge reaching
            # the lower counter): fold them into the neighbouring segment
            geo[n] = micro_cleanup(geo[n], near=[(223.7, 600.0), (508.3, 611.0)])
    sm = seams(ln, F)
    # the face beyond each cut keeps its gradient flat along the cut, so the joint solve can close it exactly
    fits = fit_faces(F, rgb, ln, pad={'p-bowl-top': sm[0][2], 'ribbon-front': sm[1][2]})
    J = gradfit.joint({n: fits[n] for n in {a for s in sm for a in s[:2]}}, sm, lam=3.0)
    fills, report = {}, {}
    for n in FACES:
        xy, c, g = fits[n]
        cols = J.get(n, g['colors'])
        fills[n] = fill_entry(g, cols)
        gg = dict(g, colors=np.array([kit.hexrgb(s['hex']) for s in fills[n]['stops']]))
        de = kit.de2000(lab_of(c), lab_of(gradfit.predict(gg, xy)))
        report[n] = {'K': g['K'], 'angle': g['angle'], 'de_mean': round(float(de.mean()), 2),
                     'de_p95': round(float(np.percentile(de, 95)), 2), 'anchors': count_anchors(geo[n])}
        print(f"{n:18s} K{g['K']} a{g['angle']:6.1f} dE {report[n]['de_mean']:.2f}/{report[n]['de_p95']:.2f} anchors {report[n]['anchors']:3d}",
              [s['hex'] + ('*' if s['swatch'] else '') for s in fills[n]['stops']])
    for a, b, pts in sm:
        ga = dict(fits[a][2], colors=np.array([kit.hexrgb(s['hex']) for s in fills[a]['stops']]))
        gb = dict(fits[b][2], colors=np.array([kit.hexrgb(s['hex']) for s in fills[b]['stops']]))
        d = kit.de2000(lab_of(gradfit.predict(ga, pts)), lab_of(gradfit.predict(gb, pts)))
        print(f'seam {a} | {b}: dE max {d.max():.2f} mean {d.mean():.2f}')
    tag = sys.argv[2] if len(sys.argv) > 2 else 'v2'
    svg = svg_for(geo, fills)
    (W / f'hero_{tag}.svg').write_text(svg, encoding='utf-8')
    json.dump({'geo': geo, 'silhouette': sil, 'fills': fills, 'report': report}, open(W / f'hero_{tag}.json', 'w'), indent=1)
    comp = kit.over(kit.render_svg(svg), '#FFFFFF')
    met, de_map = metrics(rgb, comp)
    print(met)
    kit.diff_sheet(rgb[296:728, 156:872], comp[296:728, 156:872], W / f'hero_{tag}_diff.png', de_map[296:728, 156:872], f'ap-hero {tag}')
