"""Post-merge per-face metrics and seam checks from the written components; patches the JSONs."""
import json
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from build_hero import FACES, W, lines_dict
from make_hero import seams
from make_dark import face_masks, wrap_svg, BG04

COMP = kit.COMP


def grad_at(fill, pts):
    p1 = np.array([fill['x1'], fill['y1']]); p2 = np.array([fill['x2'], fill['y2']])
    v = p2 - p1
    t = np.clip(((np.asarray(pts) - p1) @ v) / (v @ v), 0, 1)
    offs = np.array([s['offset'] for s in fill['stops']])
    cols = np.array([kit.hexrgb(s['hex']) for s in fill['stops']])
    return np.stack([np.interp(t, offs, cols[:, c]) for c in range(3)], 1)


def face_stats(orig, comp, masks):
    out = {}
    de = kit.de2000(kit.srgb_to_lab(orig), kit.srgb_to_lab(comp))
    for n, m in masks.items():
        d = de[m]
        out[n] = {'de_mean': round(float(d.mean()), 2), 'de_p95': round(float(np.percentile(d, 95)), 2), 'pixels': int(m.sum())}
    return out


if __name__ == '__main__':
    ln = lines_dict()
    jh = json.load(open(COMP / 'ap-hero.json'))
    jd = json.load(open(COMP / 'ap-hero-dark.json'))
    fills_h = {f['id'][5:]: f['fill'] for f in jh['faces']}
    fills_d = {f['id'][5:]: f['fill'] for f in jd['faces']}
    # hero, per face over its visible interior in 06
    Fs = np.load(W / 'F_faces.npy')
    F = {n: Fs[i].astype(float) for i, n in enumerate(FACES)}
    rgb06 = kit.load('06').astype(float)
    comp06 = kit.over(kit.render_svg(COMP / 'ap-hero.svg'), '#FFFFFF')
    hm = face_stats(rgb06, comp06, {n: kit.erode(F[n] > 0.98, 1) for n in FACES})
    sm = []
    for a, b, pts in seams(ln, F):
        for var, fl in (('hero', fills_h), ('dark', fills_d)):
            d = kit.de2000(kit.srgb_to_lab(grad_at(fl[a], pts)), kit.srgb_to_lab(grad_at(fl[b], pts)))
            sm.append({'variant': var, 'faces': [a, b], 'de_max': round(float(d.max()), 2), 'de_mean': round(float(d.mean()), 2)})
    for q in sm:
        print('seam', q)
    jh['metrics']['per_face'] = hm
    jh['metrics']['seams'] = [q for q in sm if q['variant'] == 'hero']
    # dark, per face over its visible interior in 04
    tr = jd['transform_to_04']
    s, tx, ty = tr['scale'], tr['tx'], tr['ty']
    rgb04 = kit.load('04').astype(float)
    geo = {f['id'][5:]: None for f in jd['faces']}
    import re
    t = (COMP / 'ap-hero.svg').read_text(encoding='utf-8')
    geo = {a['id'][5:]: d for d, a in kit.parse_svg_paths(t)}
    lab, _ = face_masks(geo, s, tx, ty, 1376, 768)
    m04 = np.load(W / 'mask04.npy')
    comp04 = kit.over(kit.render_svg(wrap_svg(geo, fills_d, s, tx, ty, 1376, 768)), BG04)
    dmask = {n: kit.erode(lab == i, 3) & kit.erode(m04, 2) for i, n in enumerate(FACES)}
    dm = face_stats(rgb04, comp04, dmask)
    jd['metrics']['per_face'] = dm
    jd['metrics']['seams'] = [q for q in sm if q['variant'] == 'dark']
    for n in FACES:
        print(f"{n:18s} hero {hm[n]['de_mean']:5.2f}/{hm[n]['de_p95']:5.2f}   dark {dm[n]['de_mean']:5.2f}/{dm[n]['de_p95']:5.2f}")
    json.dump(jh, open(COMP / 'ap-hero.json', 'w'), indent=1)
    json.dump(jd, open(COMP / 'ap-hero-dark.json', 'w'), indent=1)
