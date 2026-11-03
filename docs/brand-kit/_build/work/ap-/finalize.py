"""Final assembly of the AP monogram components: merge supporting tones across hero + dark (palette snap
<= 4 dE2000 already applied; remaining stops merged when within dE2000 3, complete linkage, medoid kept),
write components/ap-hero(.svg/.json), ap-hero-dark(.svg/.json), verify sheets."""
import json
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from build_hero import FACES, W, lines_dict
from make_hero import svg_for, metrics
from make_dark import wrap_svg, BG04

COMP, VER = kit.COMP, kit.VERIFY
lab = lambda h: kit.srgb_to_lab(kit.hexrgb(h))


def merge_tones(hexes, thr=3.0):
    """complete-linkage agglomeration in dE2000; returns {hex: representative hex}."""
    cl = [[h] for h in sorted(set(hexes))]
    D = lambda a, b: max(float(kit.de2000(lab(x), lab(y))) for x in a for y in b)
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
        cl[i] = cl[i] + cl[j]
        cl.pop(j)
    rep = {}
    for c in cl:
        med = min(c, key=lambda h: sum(float(kit.de2000(lab(h), lab(o))) for o in c))
        for h in c:
            rep[h] = med
    return rep


def tone_name(hx, used=None):
    """family from CIE LCh: Cyan (h < 230), Azure (230-272, C >= 35), Blue (>= 272, C >= 35),
    Slate (C < 35, L >= 22), Navy (L < 22)."""
    L, a, b = lab(hx)
    h = np.degrees(np.arctan2(b, a)) % 360
    C = np.hypot(a, b)
    if L < 22:
        fam = 'Navy'
    elif C < 35:
        fam = 'Slate'
    elif h < 230:
        fam = 'Cyan'
    elif h < 272:
        fam = 'Azure'
    else:
        fam = 'Blue'
    return fam, L


def bbox_of(d):
    P = np.vstack([np.asarray(p) for p in kit.flatten(kit.parse_d(d), tol=0.05)])
    return [round(float(P[:, 0].min()), 2), round(float(P[:, 1].min()), 2), round(float(P[:, 0].max()), 2), round(float(P[:, 1].max()), 2)]


def faces_json(geo, fl, names):
    out = []
    for z, n in enumerate(FACES):
        f = json.loads(json.dumps(fl[n]))
        for s in f['stops']:
            s['palette'] = s.get('swatch') is not None
            s['swatch'] = s['swatch'] if s['palette'] else names[s['hex']]
            s.pop('tone', None)
        out.append({'id': 'face-' + n, 'z': z, 'fill': f, 'anchors': sum(len(q['segs']) for q in kit.parse_d(geo[n]))})
    return out


if __name__ == '__main__':
    hero = json.load(open(W / (sys.argv[1] if len(sys.argv) > 1 else 'hero_v6.json')))
    dark = json.load(open(W / (sys.argv[2] if len(sys.argv) > 2 else 'dark_v3.json')))
    geo, sil = hero['geo'], hero['silhouette']
    fills = {'hero': hero['fills'], 'dark': dark['fills']}
    free = [s['hex'] for v in fills.values() for f in v.values() for s in f['stops'] if not s['swatch']]
    rep = merge_tones(free)
    for v in fills.values():
        for f in v.values():
            for s in f['stops']:
                if not s['swatch']:
                    s['hex'] = rep[s['hex']]
    # supporting tone table, named by family and lightness, with where each is used
    usage = {}
    for var, v in fills.items():
        for n, f in v.items():
            for k, s in enumerate(f['stops']):
                if not s['swatch']:
                    usage.setdefault(s['hex'], []).append(f'{var}:face-{n}#{k}')
    fam = {}
    for hx in usage:
        fm, L = tone_name(hx)
        fam.setdefault(fm, []).append((L, hx))
    names = {}
    for fm, lst in fam.items():
        for i, (L, hx) in enumerate(sorted(lst, reverse=True)):
            names[hx] = f'AP {fm} {i + 1}' if len(lst) > 1 else f'AP {fm}'
    for v in fills.values():
        for f in v.values():
            for s in f['stops']:
                if not s['swatch']:
                    s['swatch'] = None
                    s['tone'] = names[s['hex']]
    tones = [{'name': names[h], 'hex': h, 'used_in': usage[h]} for h in sorted(usage, key=lambda h: names[h])]
    print(len(free), 'free stops ->', len(tones), 'supporting tones')
    for t in tones:
        print(' ', t['name'], t['hex'], len(t['used_in']))
    json.dump({'fills': fills, 'tones': tones, 'rep': rep}, open(W / 'final_fills.json', 'w'), indent=1)

    # ------------------------------------------------ hero
    ln = lines_dict()
    rgb06 = kit.load('06').astype(float)
    svg = svg_for(geo, fills['hero'])
    (COMP / 'ap-hero.svg').write_text(svg, encoding='utf-8')
    comp = kit.over(kit.render_svg(COMP / 'ap-hero.svg'), '#FFFFFF')
    met, de_map = metrics(rgb06, comp)
    print('hero', met)
    kit.diff_sheet(rgb06[296:728, 156:872], comp[296:728, 156:872], VER / 'ap-hero_diff.png', de_map[296:728, 156:872],
                   'ap-hero vs 06  IoU %.4f  dE mean %.2f p95 %.2f' % (met['iou'], met['de_mean'], met['de_p95']))
    json.dump({'hero_metrics': met}, open(W / 'final_hero_metrics.json', 'w'), indent=1)
    # ------------------------------------------------ dark
    tr = dark['result']['transform']
    s, tx, ty = tr['scale'], tr['tx'], tr['ty']
    rgb04 = kit.load('04').astype(float)
    dsvg = svg_for(geo, fills['dark'], prefix='grad-dark-')
    (COMP / 'ap-hero-dark.svg').write_text(dsvg, encoding='utf-8')
    wsvg = wrap_svg(geo, fills['dark'], s, tx, ty, 1376, 768)
    dcomp = kit.over(kit.render_svg(wsvg), BG04)
    m04 = np.load(W / 'mask04.npy')
    rm = kit.raster([kit.transform_d(d, s, tx, ty) for d in geo.values()], 1376, 768) > 0.5
    dm = kit.compare(rgb04, dcomp, m04)
    dm2 = kit.compare(rgb04, dcomp, kit.erode(m04, 2))
    dmet = {'iou_04': round(kit.iou(m04, rm), 4), 'de_mean_04': dm['de_mean'], 'de_p95_04': dm['de_p95'],
            'de_mean_04_interior2px': dm2['de_mean'], 'de_p95_04_interior2px': dm2['de_p95']}
    print('dark', dmet)
    box = (150, 230, 620, 540)
    x0, y0, x1, y1 = box
    kit.diff_sheet(rgb04[y0:y1, x0:x1], dcomp[y0:y1, x0:x1], VER / 'ap-hero-dark_diff.png', dm['de_map'][y0:y1, x0:x1],
                   'ap-hero-dark in 04 frame (s %.4f, t %.1f,%.1f)  IoU %.4f  dE mean %.2f p95 %.2f' % (s, tx, ty, dmet['iou_04'], dmet['de_mean_04'], dmet['de_p95_04']))
    json.dump({'dark_metrics': dmet}, open(W / 'final_dark_metrics.json', 'w'), indent=1)

    # ------------------------------------------------ JSON
    hero_rep = hero.get('report', {})
    seam_note = 'one ribbon band is split into p-bowl-top | ribbon-front-stem | ribbon-front and the P bowl bar into p-bowl-lower | p-bowl-under; their stops were fitted jointly so the cuts do not show'
    tones_hero = [t for t in tones if any(u.startswith('hero:') for u in t['used_in'])]
    tones_dark = [t for t in tones if any(u.startswith('dark:') for u in t['used_in'])]
    common = {'viewBox': [0, 0, 1024, 1024], 'source_space': 'original 06 pixel space (y down)',
              'bbox': bbox_of(sil), 'baseline_y': ln['base'], 'apex_top_y': ln['top'],
              'mark_height': round(ln['base'] - ln['top'], 2), 'silhouette_d': sil,
              'z_order': 'faces listed bottom to top; each lower face reaches 2.5 px under the face stacked above it (no seams); all faces are cut by one shared silhouette'}
    jh = dict(common, component='ap-hero', source='06', faces=faces_json(geo, fills['hero'], names),
              supporting_tones=[{'name': t['name'], 'hex': t['hex'], 'used_in': [u.split(':', 1)[1] for u in t['used_in'] if u.startswith('hero:')]} for t in tones_hero],
              palette_used=sorted({s['swatch'] for f in fills['hero'].values() for s in f['stops'] if s.get('swatch')}),
              metrics=dict(met, per_face=hero_rep, note=seam_note,
                           method='VectorCraft render at 1x composited on white vs 06; IoU of kit.bg_mask(dE>18 from white) masks; dE2000 over the original mark mask'))
    json.dump(jh, open(COMP / 'ap-hero.json', 'w'), indent=1)
    jd = dict(common, component='ap-hero-dark', source='04', background_measured=BG04, background_palette='Deep Navy #121B2A (dE2000 2.1 from the measured 04 background)',
              transform_to_04=dict(tr, iou_fit=dark['result'].get('iou_04')),
              faces=faces_json(geo, fills['dark'], names),
              supporting_tones=[{'name': t['name'], 'hex': t['hex'], 'used_in': [u.split(':', 1)[1] for u in t['used_in'] if u.startswith('dark:')]} for t in tones_dark],
              palette_used=sorted({s['swatch'] for f in fills['dark'].values() for s in f['stops'] if s.get('swatch')}),
              metrics=dict(dmet, per_face=dark['result']['faces'],
                           method='master geometry placed by the fitted similarity into 04 (1376x768), rendered, composited on the measured 04 background; mask of 04 = dE2000 > 7 from the background with the outer glow peeled (mask04.py)'))
    json.dump(jd, open(COMP / 'ap-hero-dark.json', 'w'), indent=1)
    print('wrote', COMP / 'ap-hero.svg', COMP / 'ap-hero.json', COMP / 'ap-hero-dark.svg', COMP / 'ap-hero-dark.json')
