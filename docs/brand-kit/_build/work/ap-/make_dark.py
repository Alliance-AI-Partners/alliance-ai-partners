"""ap-hero-dark: the master geometry recoloured from original 04 (navy background, mark at the left).
1. similarity transform master -> 04 by maximising silhouette IoU;  2. every face's gradient re-fitted
from 04's pixels under the transformed master faces (seam-continuous like the hero);  3. SVG in the
master 1024 space + verification in 04's frame."""
import json
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import gradfit
from build_hero import FACES, W, lines_dict
from make_hero import fill_entry, svg_for, lab_of, seams as hero_seams

SEAM_FACES = {'p-bowl-top', 'ribbon-front-stem', 'ribbon-front', 'p-bowl-under', 'p-bowl-lower'}
LAM = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
BG04 = '#132031'   # measured in 04's corners and around the mark (dE2000 2.1 from Deep Navy)
THR = 18.0         # kit.bg_mask default


def bilinear(img, x, y):
    H, Wd = img.shape
    x0 = np.clip(np.floor(x).astype(int), 0, Wd - 2); y0 = np.clip(np.floor(y).astype(int), 0, H - 2)
    fx = np.clip(x - x0, 0, 1); fy = np.clip(y - y0, 0, 1)
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def fit_similarity(alpha_m, mask04, box, s_range=(0.54, 0.70)):
    """maximise IoU(alpha_m transformed, mask04) over p04 = s * p_m + t (pixel-centre convention)."""
    x0, y0, x1, y1 = box
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    B = mask04[y0:y1, x0:x1]
    ym, xm = np.nonzero(alpha_m > 0.5)
    cm = np.array([xm.mean() + 0.5, ym.mean() + 0.5])
    yb, xb = np.nonzero(B)
    cb = np.array([xb.mean() + x0 + 0.5, yb.mean() + y0 + 0.5])

    def iou(s, tx, ty):
        A = bilinear(alpha_m, (xx - tx) / s - 0.5, (yy - ty) / s - 0.5) > 0.5
        return (A & B).sum() / max(1, (A | B).sum())
    best = (0, None)
    for s in np.arange(s_range[0], s_range[1], 0.005):
        t0 = cb - s * cm
        for dx in range(-12, 13, 3):
            for dy in range(-12, 13, 3):
                v = iou(s, t0[0] + dx, t0[1] + dy)
                if v > best[0]:
                    best = (v, (s, t0[0] + dx, t0[1] + dy))
    for step_s, step_t, rng in ((0.002, 1.0, 3), (0.0005, 0.25, 4)):
        s0, tx0, ty0 = best[1]
        for s in s0 + step_s * np.arange(-rng, rng + 1):
            for tx in tx0 + step_t * np.arange(-rng, rng + 1):
                for ty in ty0 + step_t * np.arange(-rng, rng + 1):
                    v = iou(s, tx, ty)
                    if v > best[0]:
                        best = (v, (s, tx, ty))
    return best


def face_masks(geo, s, tx, ty, w, h):
    """visible-face label map of the transformed master faces in the target frame (-1 = none)."""
    lab = np.full((h, w), -1, int)
    cov = {}
    for i, n in enumerate(FACES):
        cov[n] = kit.raster(kit.transform_d(geo[n], s, tx, ty), w, h)
    for i, n in enumerate(FACES):
        lab[cov[n] > 0.5] = i
    return lab, cov


def wrap_svg(geo, fills, s, tx, ty, w, h):
    inner = svg_for(geo, fills)
    body = inner[inner.index('<svg'):]
    body = body[body.index('>') + 1:body.rindex('</svg>')]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'<g transform="translate({tx:.4f} {ty:.4f}) scale({s:.6f})">{body}</g></svg>\n')


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'hero_v4.json'
    tag = sys.argv[2] if len(sys.argv) > 2 else 'v1'
    hero = json.load(open(W / src))
    geo = hero['geo']
    rgb = kit.load('04').astype(float)
    h, w = rgb.shape[:2]
    box = (150, 230, 620, 540)
    m04_mark = np.load(W / 'mask04.npy')   # mask04.py: dE > 7 from the background, outer glow peeled
    alpha_m = kit.raster(list(geo.values()), 1024, 1024)
    if len(sys.argv) > 4:   # reuse a transform fitted before on the same geometry
        tr = json.load(open(W / sys.argv[4]))['result']['transform']
        s, tx, ty, v = tr['scale'], tr['tx'], tr['ty'], float('nan')
    else:
        v, (s, tx, ty) = fit_similarity(alpha_m, m04_mark, box)
    print('similarity: s=%.5f tx=%.3f ty=%.3f IoU=%.4f' % (s, tx, ty, v))
    lab, cov = face_masks(geo, s, tx, ty, w, h)
    fits = {}
    ln = lines_dict()
    Fs = np.load(W / 'F_faces.npy')
    F = {n: Fs[i].astype(float) for i, n in enumerate(FACES)}
    sm = hero_seams(ln, F)
    # the faces on the far side of each cut keep their gradient flat (padded) along it, so the cut can
    # be made invisible by the joint solve even where 04's light runs across the band
    PAD = {'p-bowl-top': sm[0][2] * s + np.array([tx, ty]), 'ribbon-front': sm[1][2] * s + np.array([tx, ty])}
    for i, n in enumerate(FACES):
        vis = kit.erode(lab == i, 3) & kit.erode(m04_mark, 2)
        ys, xs = np.nonzero(vis)
        xy04 = np.stack([xs + 0.5, ys + 0.5], 1)
        c = rgb[ys, xs]
        keep = np.ones(len(c), bool)
        for it in range(2):   # fit, drop pixels the two drawings disagree on (residual outliers), refit
            if n.startswith('a-'):
                ax = np.degrees(np.arctan2(1, ln['LL_crease' if n.startswith('a-left') else 'RL_internal']['a']))
                g = gradfit.fit(xy04[keep], c[keep], Kmax=5, angles=np.arange(ax - 15, ax + 15.01, 3.0), improve=0.85, n_min=8)
            elif n in SEAM_FACES and n in hero.get('report', {}):
                # faces split from one band: keep the hero's gradient direction (+-6 deg) so the
                # joint solve can make the cuts between them disappear in this colourway too
                a0 = hero['report'][n]['angle']
                g = gradfit.fit(xy04[keep], c[keep], Kmax=3, n_min=8, angles=np.arange(a0 - 6, a0 + 6.01, 1.5), pad=PAD.get(n))
            else:
                g = gradfit.fit(xy04[keep], c[keep], Kmax=3, n_min=8)
            res = kit.de2000(lab_of(c), lab_of(gradfit.predict(g, xy04)))
            keep = res < max(8.0, 3 * np.median(res))
        g['colors'], g['mse'] = gradfit.solve(gradfit.hat_basis(xy04[keep] @ g['u'], g['knots']), c[keep])
        g['kept'] = float(keep.mean())
        # express in master space: s04 = u.(s p + t) -> knots_m = (k - u.t)/s
        gm = dict(g, knots=(np.asarray(g['knots']) - g['u'] @ np.array([tx, ty])) / s)
        xym = (xy04[keep] - np.array([tx, ty])) / s
        gm['center'] = xym.mean(0)
        fits[n] = (xym, c[keep], gm)
    J = gradfit.joint({n: fits[n] for n in {a for q in sm for a in q[:2]}}, sm, lam=LAM)
    fills, report = {}, {}
    for n in FACES:
        xy, c, g = fits[n]
        fills[n] = fill_entry(g, J.get(n, g['colors']))
        gg = dict(g, colors=np.array([kit.hexrgb(q['hex']) for q in fills[n]['stops']]))
        de = kit.de2000(lab_of(c), lab_of(gradfit.predict(gg, xy)))
        report[n] = {'K': g['K'], 'angle': g['angle'], 'kept': round(g['kept'], 3), 'de_mean': round(float(de.mean()), 2), 'de_p95': round(float(np.percentile(de, 95)), 2)}
        print(f"{n:18s} K{g['K']} a{g['angle']:6.1f} dE {report[n]['de_mean']:.2f}/{report[n]['de_p95']:.2f}",
              [q['hex'] + ('*' if q['swatch'] else '') for q in fills[n]['stops']])
    svg = svg_for(geo, fills)
    (W / f'dark_{tag}.svg').write_text(svg, encoding='utf-8')
    wsvg = wrap_svg(geo, fills, s, tx, ty, w, h)
    (W / f'dark_{tag}_in04.svg').write_text(wsvg, encoding='utf-8')
    comp = kit.over(kit.render_svg(wsvg), BG04)
    rm_mark = kit.raster([kit.transform_d(d, s, tx, ty) for d in geo.values()], w, h) > 0.5
    met = kit.compare(rgb, comp, m04_mark)
    inner = kit.erode(m04_mark, 2)
    met2 = kit.compare(rgb, comp, inner)
    res = {'transform': {'scale': round(s, 5), 'tx': round(tx, 3), 'ty': round(ty, 3),
                         'note': 'p04 = scale * p_master + (tx, ty), pixel-centre convention'},
           'iou_04': round(kit.iou(m04_mark, rm_mark), 4), 'de_mean_04': met['de_mean'], 'de_p95_04': met['de_p95'],
           'de_mean_04_interior': met2['de_mean'], 'de_p95_04_interior': met2['de_p95'], 'faces': report}
    print({k: v for k, v in res.items() if k != 'faces'})
    json.dump({'fills': fills, 'result': res}, open(W / f'dark_{tag}.json', 'w'), indent=1)
    x0, y0, x1, y1 = box
    kit.diff_sheet(rgb[y0:y1, x0:x1], comp[y0:y1, x0:x1], W / f'dark_{tag}_diff.png', met['de_map'][y0:y1, x0:x1], f'ap-hero-dark {tag} (in 04 frame)')
