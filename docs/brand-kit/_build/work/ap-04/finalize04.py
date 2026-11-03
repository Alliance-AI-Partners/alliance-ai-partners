"""hero-04 final assembly: components/rec/hero-04.svg (04's own pixel space, identity placement, mark only),
components/rec/hero-04.json, verify/hero-04_diff.png. Verification renders the written SVG with VectorCraft,
composites it over 04's measured background and scores it against 04's mark mask (work/ap-/mask04.npy:
dE2000 > 7 from the background, outer glow peeled, wordmark excluded)."""
import json
import re
import sys
import numpy as np

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from build_hero import FACES
from make_hero import svg_for
from finalize import tone_name
from seg04 import W4
from build04 import drop_degenerate, DELTA
from color04 import visible_labels, seam_points, SNAP_DE, MERGE_DE
from verify04 import measured_background, DIFF_BOX
from highlight04 import SPECS

W, H = 1376, 768
OUT_SVG = kit.COMP / 'rec' / 'hero-04.svg'
OUT_JSON = kit.COMP / 'rec' / 'hero-04.json'
OUT_DIFF = kit.VERIFY / 'hero-04_diff.png'


def grad_at(fill, pts):
    """colour of an SVG userSpaceOnUse linear gradient (pad spread) at points."""
    p1 = np.array([fill['x1'], fill['y1']]); p2 = np.array([fill['x2'], fill['y2']])
    v = p2 - p1
    t = np.clip(((np.asarray(pts, float) - p1) @ v) / (v @ v), 0, 1)
    offs = np.array([s['offset'] for s in fill['stops']])
    cols = np.array([kit.hexrgb(s['hex']) for s in fill['stops']])
    return np.stack([np.interp(t, offs, cols[:, c]) for c in range(3)], 1)


def joins(d):
    """tangent turn (deg) at every anchor of every sub-path."""
    out = []
    for sp in kit.parse_d(d):
        segs = list(sp['segs'])
        if np.hypot(*(np.array(segs[-1][-2:]) - np.array(sp['start']))) > 1e-6:
            segs.append(('L',) + tuple(sp['start']))
        tans, cur = [], np.array(sp['start'])
        for q in segs:
            pts = [np.array(q[i:i + 2]) for i in range(1, len(q), 2)]
            first = next((p - cur for p in pts if np.hypot(*(p - cur)) > 1e-6), pts[-1] - cur)
            prev = [cur] + pts[:-1]
            last = next((pts[-1] - p for p in reversed(prev) if np.hypot(*(pts[-1] - p)) > 1e-6), pts[-1] - cur)
            tans.append((first, last))
            cur = pts[-1]
        for i in range(len(segs)):
            a, b = tans[i - 1][1], tans[i][0]
            out.append(float(np.degrees(np.arccos(np.clip(a @ b / np.hypot(*a) / np.hypot(*b), -1, 1)))))
    return out


def glow_profile(rgb, geo, order, sil_cov, bg):
    """median |RGB excess over the background| by distance outside the mark, split by the adjacent face group."""
    lab = visible_labels(geo, (H, W), order)
    sil = sil_cov > 0.5
    dist = np.full((H, W), 99, int); near = np.full((H, W), -1, int)
    cur, nl = sil.copy(), lab.copy()
    for r in range(1, 13):
        nxt = kit.dilate(cur, 1)
        ring = nxt & ~cur
        dist[ring] = r
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            sh = np.roll(np.roll(nl, dy, 0), dx, 1)
            m = ring & (near < 0) & (sh >= 0)
            near[m] = sh[m]; nl[m] = sh[m]
        cur = nxt
    box = np.zeros((H, W), bool); box[230:540, 150:615] = True
    groups = {'cyan ribbon and bowl': ['p-bowl-top', 'ribbon-back', 'ribbon-front', 'ribbon-front-stem'],
              'blue left leg': ['a-left-outer', 'a-left-bevel'], 'right leg': ['a-right-outer', 'a-right-inner'],
              'slate P body': ['p-bowl-lower', 'p-bowl-under']}
    out = {}
    for gname, names in groups.items():
        ids = [order.index(n) for n in names]
        prof = {}
        for r in (2, 3, 4, 6, 8, 10):
            m = box & (dist == r) & np.isin(near, ids)
            if m.sum() >= 5:
                prof[str(r)] = round(float(np.median(np.linalg.norm(rgb[m] - kit.hexrgb(bg), axis=1))), 1)
        out[gname] = prof
    return out


if __name__ == '__main__':
    g = json.load(open(W4 / 'geo04h.json'))
    order, sil_d = g['order'], drop_degenerate(g['silhouette'], eps=0.01)
    geo = {n: drop_degenerate(d, eps=0.01) for n, d in g['geo'].items()}
    F = json.load(open(W4 / 'fills04h.json'))
    fills, report = F['fills'], F['report']
    svg = svg_for(geo, fills, order, W, H)
    assert not re.search(r'<(filter|mask|clipPath)\b|\b(filter|mask|clip-path)=', svg)
    assert all(re.fullmatch(r'#[0-9A-F]{6}', h) for h in re.findall(r'stop-color="([^"]+)"', svg))
    OUT_SVG.write_text(svg, encoding='utf-8')

    # ------------------------------------------------ verification from the written file
    rgb = kit.load('04').astype(float)
    m04 = np.load(kit.WORK / 'ap-' / 'mask04.npy')
    bg, nbg = measured_background(rgb, m04)
    rgba = kit.render_svg(OUT_SVG)
    comp = kit.over(rgba, bg)
    sil_r = rgba[..., 3] > 0.5
    met = kit.compare(rgb, comp, m04)
    inner = kit.erode(m04, 2)
    met2 = kit.compare(rgb, comp, inner)
    iou = round(kit.iou(sil_r, m04), 4)
    x0, y0, x1, y1 = DIFF_BOX
    kit.diff_sheet(rgb[y0:y1, x0:x1], comp[y0:y1, x0:x1], OUT_DIFF, met['de_map'][y0:y1, x0:x1],
                   'hero-04 vs 04  IoU %.4f  dE2000 mean %.2f p95 %.2f (in mark mask)' % (iou, met['de_mean'], met['de_p95']))
    lab = visible_labels(geo, (H, W), order)
    per_face = {}
    for i, n in enumerate(order):
        r = (lab == i) & inner
        if r.any():
            per_face[n] = {'pixels': int(r.sum()), 'de_mean': round(float(met['de_map'][r].mean()), 2),
                           'de_p95': round(float(np.percentile(met['de_map'][r], 95)), 2)}
    Fs = np.load(W4 / 'F04.npy')
    Fsoft = {n: Fs[i].astype(float) for i, n in enumerate(FACES)}
    ln = json.load(open(W4 / 'lines04.json'))
    seams = []
    for a, b, pts in seam_points(ln, Fsoft):
        d = kit.de2000(kit.srgb_to_lab(grad_at(fills[a], pts)), kit.srgb_to_lab(grad_at(fills[b], pts)))
        seams.append({'faces': [a, b], 'points': len(pts), 'de_max': round(float(d.max()), 2), 'de_mean': round(float(d.mean()), 2)})
    turns = [t for n in order for t in joins(geo[n])] + joins(sil_d)
    g1 = {'anchors': len(turns), 'smooth_lt_0.5deg': sum(t < 0.5 for t in turns),
          'corners_ge_15deg': sum(t >= 15 for t in turns), 'between': sorted(round(t, 1) for t in turns if 0.5 <= t < 15)}
    print('IoU', iou, 'dE', met['de_mean'], met['de_p95'], 'interior', met2['de_mean'], met2['de_p95'], 'bg', bg)
    print('seams', seams); print('joins', g1)

    # ------------------------------------------------ tones
    usage = {}
    for n in order:
        for k, s in enumerate(fills[n]['stops']):
            usage.setdefault(s['hex'], {'palette': s.get('palette'), 'used_in': []})['used_in'].append(f'face-{n}#{k}')
    tones = []
    for hx in sorted(usage, key=lambda h: (tone_name(h)[0], -tone_name(h)[1])):
        fam, L = tone_name(hx)
        pn, ph, pde = kit.nearest_palette(hx)
        tones.append({'hex': hx, 'family': fam, 'L': round(float(L), 1), 'palette': usage[hx]['palette'],
                      'nearest_palette': {'name': pn, 'hex': ph, 'de2000': round(pde, 2)}, 'used_in': usage[hx]['used_in']})
    pb = kit.nearest_palette(bg)
    P = np.vstack([np.asarray(p) for p in kit.flatten(kit.parse_d(sil_d), tol=0.05)])
    faces = []
    for z, n in enumerate(order):
        f = json.loads(json.dumps(fills[n]))
        host = SPECS[n][0] if n in SPECS else None
        faces.append({'id': 'face-' + n, 'gradient': 'grad-' + n, 'z': z, 'role': 'highlight' if host else 'face',
                      **({'host': 'face-' + host} if host else {}), 'fill': f,
                      'segments': sum(len(s['segs']) for s in kit.parse_d(geo[n])), 'fit': report.get(n),
                      'verify': per_face.get(n)})
    glow = glow_profile(rgb, geo, order, rgba[..., 3], bg)
    out = {
        'component': 'hero-04', 'source': '04', 'source_file': kit.ORIGINALS['04'][0],
        'viewBox': [0, 0, W, H], 'placement': 'identity: original 04 pixel space (y down); mark only, no text, no background',
        'bbox': [round(float(P[:, 0].min()), 2), round(float(P[:, 1].min()), 2), round(float(P[:, 0].max()), 2), round(float(P[:, 1].max()), 2)],
        'background_measured': bg,
        'background_note': f'median of 04 more than 30 px from the mark and its glow, left of the wordmark ({nbg} px); '
                           f'nearest palette {pb[0]} {pb[1]} at dE2000 {pb[2]:.2f} (not snapped: the background is not part of this file)',
        'structure': {
            'z_order': ['face-' + n for n in order],
            'faces_from_master': FACES,
            'highlights': {('face-' + n): {'host': 'face-' + SPECS[n][0], 'shape': (SPECS[n][3] if len(SPECS[n]) > 3 else 'traced'),
                                           'threshold_L_excess': SPECS[n][2]} for n in order if n in SPECS},
            'stacking': f'faces listed bottom to top; each lower face reaches {DELTA} px (04 px) under the face stacked above it; '
                        'all faces (and highlights) are cut by one shared silhouette (VectorCraft Pathfinder intersect)',
            'seams': 'one ribbon band is split into p-bowl-top | ribbon-front-stem | ribbon-front and the P bar into '
                     'p-bowl-under | p-bowl-lower by straight cuts; stops solved jointly so the cuts do not show '
                     '(ribbon-front-stem kept vertical so both of its horizontal cuts can close)',
        },
        'silhouette_d': sil_d,
        'lines': ln,
        'colour_rule': f'fidelity first: least-squares stops in sRGB (<= 5 per face, inside the visible pixels only); a stop '
                       f'snaps to a kit.PALETTE colour only within dE2000 {SNAP_DE} (none did: nearest is '
                       f'{min(t["nearest_palette"]["de2000"] for t in tones):.2f}); stops within dE2000 {MERGE_DE} '
                       f'of each other (complete linkage) share one tone, re-solved by least squares over every pixel that uses it',
        'tones': tones,
        'palette_used': sorted({t['palette'] for t in tones if t['palette']}),
        'faces': faces,
        'metrics': {
            'iou': iou, 'de_mean': met['de_mean'], 'de_p95': met['de_p95'],
            'de_mean_interior2px': met2['de_mean'], 'de_p95_interior2px': met2['de_p95'],
            'targets': {'iou_min': 0.985, 'de_mean_max': 3.0},
            'mask_px': int(m04.sum()), 'render_only_px': int((sil_r & ~m04).sum()), 'mask_only_px': int((m04 & ~sil_r).sum()),
            'per_face_interior2px': per_face, 'seams': seams, 'joins': g1,
            'method': 'kit.render_svg(components/rec/hero-04.svg) at 1x composited over the measured background; IoU of '
                      'render alpha > 0.5 vs 04 mark mask (work/ap-/mask04.py: dE2000 > 7 from the background, outer glow '
                      'peeled, wordmark excluded); dE2000 over that mask (and over the mask eroded 2 px)',
        },
        'glow': {'reproduced': False, 'profile_median_rgb_excess_by_distance_px': glow,
                 'note': 'the soft outer glow is face-dependent (strong cyan halo around the ribbon and bowl, a weak blue '
                         'one around the left leg, almost none around the slate P body) and also spills over neighbouring '
                         'faces inside the silhouette; one stack of offset copies with fill-opacity cannot reproduce that '
                         'cleanly, and even a perfect glow would lower the in-mask mean dE2000 by only ~0.06, so it is left out'},
        'pipeline': 'work/ap-04: seg04.py, lines04.py, build04.py, color04.py (fitgrad04.py), verify04.py, highlight04.py, '
                    'color04.py again, finalize04.py',
    }
    json.dump(out, open(OUT_JSON, 'w'), indent=1)
    print('wrote', OUT_SVG, OUT_JSON, OUT_DIFF)
