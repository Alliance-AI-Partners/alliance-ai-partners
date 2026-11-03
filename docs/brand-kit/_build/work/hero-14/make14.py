"""hero-14, stage 2: clean geometry (span-limited snapped lines, minimal G1 Beziers within 0.3 px), one shared
silhouette cutting every face, least-squares linear gradients from 14's visible pixels (seam-continuous
across the invisible cuts), SVG + VectorCraft verification. usage: python make14.py [tag]"""
import json
import sys
import numpy as np
from common import kit, W14, FACES, POLY, H, Wd, BG, REGION_Y1, MARK_BOX
import snap14  # noqa: F401  (span-limited line runs)
from snap14 import make as make_lines
from fitcurve import rebuild, count_anchors, micro_cleanup
from pathops import vc_pathfinder
import gradfit
from make_hero import fill_entry, svg_for, lab_of
from build14 import CUTS, lines

SIL_LINES = ['top', 'base', 'LL_outer', 'LL_inner_u', 'LL_inner_l', 'RL_inner_u', 'RL_inner_l', 'RL_outer_u', 'RL_outer_l',
             'P_left', 'stem_right', 'counter_top', 'counter_bottom', 'bowl_bottom', 'crossbar_top', 'crossbar_bottom']
FACE_LINES = SIL_LINES + ['fold_top', 'fold_diag', 'stem_mid', 'crease', 'LL_crease_u', 'LL_crease_l',
                          'RL_internal_u', 'RL_internal_l', 'seam_stem', 'under_end', 'top_split']


def region_mask():
    m = np.zeros((H, Wd), bool)
    x0, y0, x1, y1 = MARK_BOX
    m[y0 - 12:min(y1 + 12, REGION_Y1), x0 - 12:x1 + 12] = True
    return m


def with_cuts(ln):
    ln = dict(ln)
    ln['seam_stem'] = {'kind': 'cut_h', 'c': CUTS['seam_stem'], 'span': [500, 570]}
    ln['under_end'] = {'kind': 'cut_v', 'c': CUTS['under_end'], 'span': [470, 515]}
    ln['top_split'] = {'kind': 'cut_v', 'c': CUTS['top_split_x'], 'span': [330, 400]}
    ln['fold_diag'] = dict(ln['fold_diag'], span=[555, 594])
    return ln


def face_rasters(geo, ss=4):
    """visible coverage of every face (top faces cover lower ones), from the final geometry"""
    cov = {n: kit.raster(geo[n], Wd, H, ss=ss) for n in FACES}
    vis, above = {}, np.zeros((H, Wd))
    for n in FACES[::-1]:
        vis[n] = np.clip(cov[n] - above, 0, 1)
        above = np.clip(above + cov[n], 0, 1)
    return cov, vis


def visible_pixels(vis_n, rgb, erode=1):
    core = kit.erode(vis_n > 0.999, erode)
    ys, xs = np.nonzero(core)
    return np.stack([xs + 0.5, ys + 0.5], 1), rgb[ys, xs], (ys, xs)


def fit_faces(vis, rgb, ln, sub=2, pad=None):
    """Every face: free direction, up to 5 stops (a stop is only added when it cuts the error by 15%).
    Leg faces also try the master's choice (along the leg axis +-15 deg) and keep whichever fits 14
    better: in 14 the ribbon's shadow crosses the right leg's outer stripe at a steep angle."""
    axis_l = np.degrees(np.arctan2(1, ln['LL_crease_u']['a']))
    axis_r = np.degrees(np.arctan2(1, ln['RL_internal_u']['a']))
    out = {}
    for n in FACES:
        xy, c, (ys, xs) = visible_pixels(vis[n], rgb)
        sel = (ys % sub == 0) & (xs % sub == 0)
        cands = [gradfit.fit(xy[sel], c[sel], Kmax=5, improve=0.85, pad=(pad or {}).get(n))]
        if n.startswith('a-'):
            ax = axis_l if n.startswith('a-left') else axis_r
            cands.append(gradfit.fit(xy[sel], c[sel], Kmax=5, angles=np.arange(ax - 15, ax + 15.01, 3.0), improve=0.85))
        for g in cands:
            g['colors'], g['mse'] = gradfit.solve(gradfit.hat_basis(xy @ g['u'], g['knots']), c)
        g = min(cands, key=lambda q: q['mse'])
        g['center'] = xy.mean(0)
        out[n] = (xy, c, g)
    return out


def seams(ln, vis):
    """sample points on the invisible cuts, kept where the point lies inside the band the cut divides"""
    def inside(a, b, pts):
        return np.array([p for p in pts if vis[a][int(p[1]), int(p[0])] + vis[b][int(p[1]), int(p[0])] > 0.9])
    ft = ln['fold_top']['c']
    s1 = np.stack([np.linspace(ln['P_left']['c'] + 1, ln['stem_mid']['c'] - 1, 30), np.full(30, ft)], 1)
    s2 = np.stack([np.linspace(500, 570, 80), np.full(80, CUTS['seam_stem'])], 1)
    s3 = np.stack([np.full(30, CUTS['under_end']), np.linspace(ln['crease']['c'] + 1, ln['bowl_bottom']['c'] - 1, 30)], 1)
    raw = [('p-bowl-top', 'ribbon-front-stem', s1), ('ribbon-front-stem', 'ribbon-front', s2), ('p-bowl-under', 'p-bowl-lower', s3)]
    return [(a, b, inside(a, b, pts)) for a, b, pts in raw]


def metrics(orig, comp, region):
    om = kit.bg_mask(orig, BG) & region
    rm = kit.bg_mask(comp, BG) & region
    m = kit.compare(orig, comp, om)
    m2 = kit.compare(orig, comp, kit.erode(om, 1))
    return {'iou': round(kit.iou(om, rm), 4), 'de_mean': m['de_mean'], 'de_p95': m['de_p95'],
            'de_mean_interior': m2['de_mean'], 'de_p95_interior': m2['de_p95']}, m['de_map'], om, rm


def stem_block(ln, delta=2.5):
    """The P stem below the bowl narrows to a point where the leg's outer edge meets the stem's right edge
    (y ~557); the traced outline rounds that tip off and leaves a notch inside the silhouette. The stem is
    a plain block there: from the leg's inner seam (hidden under the leg) to delta past the stem's right
    edge (cut by the silhouette)."""
    x_r = ln['stem_right']['c'] + delta
    o = ln['RL_outer_l']
    y_tip = (ln['stem_right']['c'] - o['b']) / o['a']          # stem right edge meets the leg's outer edge
    y0, y1 = ln['bowl_bottom']['c'] - 3.0, y_tip + 1.0         # bottom-right corner falls outside the silhouette
    xl = lambda y: ln['RL_internal_l']['a'] * y + ln['RL_internal_l']['b'] + 2.0
    return f'M{xl(y0):.3f} {y0:.3f} L{x_r:.3f} {y0:.3f} L{x_r:.3f} {y1:.3f} L{xl(y1):.3f} {y1:.3f} Z'


def drop_null_segments(d, eps=0.02):
    """remove zero-length segments Pathfinder leaves where a face edge meets the silhouette at a vertex"""
    out = []
    for sp in kit.parse_d(d):
        cur, segs = sp['start'], []
        for g in sp['segs']:
            if np.hypot(g[-2] - cur[0], g[-1] - cur[1]) < eps:
                continue
            segs.append(g)
            cur = g[-2:]
        if sp['closed'] and segs and np.hypot(segs[-1][-2] - sp['start'][0], segs[-1][-1] - sp['start'][1]) < eps and segs[-1][0] == 'L':
            segs = segs[:-1]
        out.append({'start': sp['start'], 'segs': segs, 'closed': sp['closed']})
    return kit.format_d(out, 3)


def clean(d):
    return micro_cleanup(drop_null_segments(d), min_len=1.0)


def build_geometry(ln, geo_raw, err=0.3):
    sil = rebuild(geo_raw['silhouette'], lines=make_lines(ln, SIL_LINES), err=0.3, line_tol=0.25)
    flines = make_lines(ln, FACE_LINES)
    geo = {}
    for n in FACES:
        d = geo_raw[n] if n in POLY else rebuild(geo_raw[n], lines=flines, err=err, line_tol=0.3)
        if n == 'p-bowl-under':
            d = ' '.join(vc_pathfinder([(n, d), ('stem', stem_block(ln))], 'unite', W14 / f'_unite_{n}.svg'))
        geo[n] = clean(' '.join(vc_pathfinder([('silhouette', sil), (n, d)], 'intersect', W14 / f'_isect_{n}.svg')))
    return sil, geo


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'v1'
    rgb = kit.load('14').astype(float)
    ln = with_cuts(lines())
    geo_raw = json.load(open(W14 / 'geo_raw14.json'))['geo']
    sil, geo = build_geometry(ln, geo_raw)
    cov, vis = face_rasters(geo)
    sm = seams(ln, vis)
    fits = fit_faces(vis, rgb, ln, pad={'p-bowl-top': sm[0][2], 'ribbon-front': sm[1][2]})
    J = gradfit.joint({n: fits[n] for n in {a for s in sm for a in s[:2]}}, sm, lam=3.0)
    fills, report = {}, {}
    for n in FACES:
        xy, c, g = fits[n]
        cols = np.clip(J.get(n, g['colors']), 0, 255)
        p1, p2, offs = gradfit.svg_vector(g, g['center'])
        fills[n] = {'type': 'linear', 'x1': round(float(p1[0]), 3), 'y1': round(float(p1[1]), 3),
                    'x2': round(float(p2[0]), 3), 'y2': round(float(p2[1]), 3),
                    'stops': [{'offset': round(float(o), 4), 'hex': kit.rgbhex(col), 'rgb': [round(float(v), 2) for v in col]}
                              for o, col in zip(offs, cols)]}
        gg = dict(g, colors=np.array([kit.hexrgb(s['hex']) for s in fills[n]['stops']]))
        de = kit.de2000(lab_of(c), lab_of(gradfit.predict(gg, xy)))
        report[n] = {'K': g['K'], 'angle': round(g['angle'], 2), 'de_mean': round(float(de.mean()), 2),
                     'de_p95': round(float(np.percentile(de, 95)), 2), 'anchors': count_anchors(geo[n]), 'pixels': len(xy)}
        print(f"{n:18s} K{g['K']} a{g['angle']:6.1f} dE {report[n]['de_mean']:.2f}/{report[n]['de_p95']:.2f} anchors {report[n]['anchors']:3d} px {len(xy)}",
              [s['hex'] for s in fills[n]['stops']])
    for a, b, pts in sm:
        ga = dict(fits[a][2], colors=np.array([kit.hexrgb(s['hex']) for s in fills[a]['stops']]))
        gb = dict(fits[b][2], colors=np.array([kit.hexrgb(s['hex']) for s in fills[b]['stops']]))
        d = kit.de2000(lab_of(gradfit.predict(ga, pts)), lab_of(gradfit.predict(gb, pts)))
        print(f'seam {a} | {b}: n {len(pts)} dE max {d.max():.2f} mean {d.mean():.2f}')
    svg = svg_for(geo, fills, w=Wd, h=H)
    (W14 / f'hero14_{tag}.svg').write_text(svg, encoding='utf-8')
    json.dump({'geo': geo, 'silhouette': sil, 'fills': fills, 'report': report, 'cuts': CUTS}, open(W14 / f'hero14_{tag}.json', 'w'), indent=1)
    comp = kit.over(kit.render_svg(svg), BG)
    met, de_map, om, rm = metrics(rgb, comp, region_mask())
    print(met)
    x0, y0, x1, y1 = 240, 290, 780, 630
    kit.diff_sheet(rgb[y0:y1, x0:x1], comp[y0:y1, x0:x1], W14 / f'hero14_{tag}_diff.png', de_map[y0:y1, x0:x1] * (om | rm)[y0:y1, x0:x1], f'hero-14 {tag}')
    np.save(W14 / f'comp_{tag}.npy', comp.astype(np.float32))
