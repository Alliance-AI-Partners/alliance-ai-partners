"""hero-14, stage 3: colour rule for recreations (fidelity first: every stop keeps its measured colour; it
snaps to a kit.PALETTE colour only within dE2000 2.0; near-identical tones merge within dE2000 2.0,
complete linkage, medoid kept), end stops made redundant by the merge dropped (the pad already shows
that colour), components/rec/hero-14.svg + hero-14.json, VectorCraft verification and verify/hero-14_diff.png.
usage: python finalize14.py [tag]"""
import json
import sys
import numpy as np
from common import kit, W14, FACES, POLY, BG, H, Wd, MARK_BOX, REGION_Y1
from make14 import face_rasters, metrics, region_mask, seams, with_cuts
from build14 import CUTS, KINK, lines
from finalize import merge_tones, tone_name, bbox_of
from final_metrics import grad_at

SNAP, MERGE = 2.0, 2.0
REC = kit.COMP / 'rec'


def de(h1, h2):
    return float(kit.de2000(kit.srgb_to_lab(kit.hexrgb(h1)), kit.srgb_to_lab(kit.hexrgb(h2))))


def apply_colour_rule(fills):
    pal = {v: k for k, v in kit.PALETTE.items()}
    snapped = []
    for n, f in fills.items():
        for s in f['stops']:
            s['measured'] = s['hex']
            name, phex, d = kit.nearest_palette(s['hex'])
            s['palette'] = d <= SNAP
            if s['palette']:
                s['hex'] = phex
                s['swatch'] = name
                snapped.append((n, s['measured'], name, round(d, 2)))
    return snapped, merge_pass(fills), pal


def merge_pass(fills):
    free = sorted({s['hex'] for f in fills.values() for s in f['stops'] if not s['palette']})
    rep = merge_tones(free, thr=MERGE)
    for f in fills.values():
        for s in f['stops']:
            if not s['palette']:
                s['hex'] = rep[s['hex']]
    return rep


def drop_repeated_ends(fills):
    """drop end stops that repeat their neighbour (SVG and Illustrator pad the end colour anyway)"""
    for f in fills.values():
        st = f['stops']
        while len(st) > 2 and st[0]['hex'] == st[1]['hex']:
            st.pop(0)
        while len(st) > 2 and st[-1]['hex'] == st[-2]['hex']:
            st.pop()


def refit_shared(fills, vis, rgb, seam_list, lam=3.0):
    """Every merged tone is one unknown shared by all the stops it replaced: least squares in sRGB over the
    visible pixels of every face (pixel-weighted), with the invisible cuts kept continuous; stop offsets
    and gradient vectors unchanged. The medoid would only pick an existing member; this picks the colour
    the pixels of all its users agree on best."""
    from gradfit import hat_basis
    from make14 import visible_pixels
    keys = sorted({s['hex'] for f in fills.values() for s in f['stops'] if not s['palette']})
    idx = {h: i for i, h in enumerate(keys)}

    def rows(n, pts):
        f = fills[n]
        p1 = np.array([f['x1'], f['y1']]); v = np.array([f['x2'], f['y2']]) - p1
        t = np.clip(((pts - p1) @ v) / (v @ v), 0, 1)
        B = hat_basis(t, [s['offset'] for s in f['stops']])
        A = np.zeros((len(pts), len(keys))); const = np.zeros((len(pts), 3))
        for k, s in enumerate(f['stops']):
            if s['palette']:
                const += np.outer(B[:, k], kit.hexrgb(s['hex']))
            else:
                A[:, idx[s['hex']]] += B[:, k]
        return A, const
    As, Cs, Ns = [], [], []
    for n in FACES:
        xy, c, _ = visible_pixels(vis[n], rgb)
        A, const = rows(n, xy)
        As.append(A); Cs.append(c - const); Ns.append(len(xy))
    w = np.sqrt(np.mean(Ns))
    for a, b, pts in seam_list:
        Aa, ca = rows(a, pts); Ab, cb = rows(b, pts)
        s = lam * w / np.sqrt(len(pts))
        As.append(s * (Aa - Ab)); Cs.append(s * (cb - ca))
    X, *_ = np.linalg.lstsq(np.vstack(As), np.vstack(Cs), rcond=None)
    members = {}
    for f in fills.values():
        for s in f['stops']:
            if not s['palette']:
                members.setdefault(s['hex'], set()).add(s['measured'])
    new = {}
    for h, i in idx.items():
        # a merged tone stays within MERGE of every stop it replaced: pull it toward the cluster's medoid if not
        c, anchor = np.clip(X[i], 0, 255), kit.hexrgb(h)
        for _ in range(20):
            if max(de(kit.rgbhex(c), m) for m in members[h]) <= MERGE:
                break
            c = anchor + 0.8 * (c - anchor)
        new[h] = kit.rgbhex(c)
    for f in fills.values():
        for s in f['stops']:
            if not s['palette']:
                s['hex'] = new[s['hex']]
    return new


def name_tones(fills):
    usage = {}
    for n, f in fills.items():
        for k, s in enumerate(f['stops']):
            if not s['palette']:
                usage.setdefault(s['hex'], []).append(f'face-{n}#{k}')
    fam = {}
    for hx in usage:
        fm, Lv = tone_name(hx)
        fam.setdefault(fm, []).append((Lv, hx))
    names = {}
    for fm, lst in fam.items():
        for i, (Lv, hx) in enumerate(sorted(lst, reverse=True)):
            names[hx] = f'AP14 {fm} {i + 1}' if len(lst) > 1 else f'AP14 {fm}'
    for f in fills.values():
        for s in f['stops']:
            if not s['palette']:
                s['swatch'] = names[s['hex']]
    return [{'name': names[h], 'hex': h, 'used_in': usage[h]} for h in sorted(usage, key=lambda h: names[h])]


def svg_text(geo, fills):
    defs, body = [], []
    for n in FACES:
        f = fills[n]
        gid = 'grad-' + n
        defs.append(kit.lin_grad(gid, f['x1'], f['y1'], f['x2'], f['y2'], [(s['offset'], s['hex']) for s in f['stops']]))
        body.append(f'<path id="face-{n}" d="{geo[n]}" fill="url(#{gid})" fill-rule="evenodd"/>')
    return kit.svg_doc(Wd, H, '\n'.join(body), '\n'.join(defs))


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'v8'
    src = json.load(open(W14 / f'hero14_{tag}.json'))
    geo, sil = src['geo'], src['silhouette']
    fills = json.loads(json.dumps(src['fills']))
    for f in fills.values():
        for s in f['stops']:
            s.pop('rgb', None)
    rgb = kit.load('14').astype(float)
    cov, vis = face_rasters(geo)
    ln = with_cuts(lines())
    seam_list = seams(ln, vis)
    # one clustering pass on the measured stop colours (complete linkage, so every member of a tone is within
    # MERGE of every other: no chaining), then each tone re-solved once from the pixels of all its users
    snapped, rep, pal = apply_colour_rule(fills)
    refit_shared(fills, vis, rgb, seam_list)
    drop_repeated_ends(fills)
    members = {}
    for n, f in fills.items():
        for s in f['stops']:
            if not s['palette']:
                members.setdefault(s['hex'], set()).add(s['measured'])
    merged = {h: sorted(m) for h, m in members.items() if len(m) > 1}
    worst = max((de(h, m) for h, ms in members.items() for m in ms), default=0.0)
    tones = name_tones(fills)
    print('palette snaps (<= %.1f dE):' % SNAP, snapped or 'none')
    print('merged tones (re-solved, members):', {h: [(m, round(de(h, m), 2)) for m in ms] for h, ms in merged.items()})
    print('largest move of a stop from its own measured colour: %.2f dE2000' % worst)
    print(len(tones), 'tones')

    REC.mkdir(parents=True, exist_ok=True)
    out_svg = REC / 'hero-14.svg'
    out_svg.write_text(svg_text(geo, fills), encoding='utf-8')

    # ------------------------------------------------ verification (VectorCraft render of the written file)
    comp = kit.over(kit.render_svg(out_svg), BG)
    region = region_mask()
    met, de_map, om, rm = metrics(rgb, comp, region)
    de_all = kit.de2000(kit.srgb_to_lab(rgb), kit.srgb_to_lab(comp))
    per_face = {}
    for n in FACES:
        m = kit.erode(vis[n] > 0.999, 1)
        d = de_all[m]
        per_face[n] = {'de_mean': round(float(d.mean()), 2), 'de_p95': round(float(np.percentile(d, 95)), 2), 'pixels': int(m.sum())}
    seam_rep = []
    for a, b, pts in seam_list:
        d = kit.de2000(kit.srgb_to_lab(grad_at(fills[a], pts)), kit.srgb_to_lab(grad_at(fills[b], pts)))
        seam_rep.append({'faces': [a, b], 'de_max': round(float(d.max()), 2), 'de_mean': round(float(d.mean()), 2), 'n': len(pts)})
    print('metrics', met)
    for n in FACES:
        print(f'  {n:18s} {per_face[n]}')
    for s in seam_rep:
        print('  seam', s)
    x0, y0, x1, y1 = 240, 290, 780, 630
    kit.diff_sheet(rgb[y0:y1, x0:x1], comp[y0:y1, x0:x1], kit.VERIFY / 'hero-14_diff.png', de_map[y0:y1, x0:x1],
                   'hero-14 vs 14 (identity)  IoU %.4f  dE mean %.2f p95 %.2f' % (met['iou'], met['de_mean'], met['de_p95']))

    # ------------------------------------------------ JSON
    raw = json.load(open(W14 / 'lines14.json'))
    def line_entry(k):
        l = raw[k]
        e = {kk: (round(v, 5) if isinstance(v, float) else v) for kk, v in l.items() if kk in ('kind', 'a', 'b', 'c', 'p', 'd', 'span', 'rms', 'n', 'angle_deg')}
        if 'p' in e:
            e['p'] = [round(v, 3) for v in e['p']]; e['d'] = [round(v, 5) for v in e['d']]
        return e
    faces_out = []
    for z, n in enumerate(FACES):
        f = fills[n]
        faces_out.append({'id': 'face-' + n, 'z': z, 'fill': {'type': 'linear', 'gradient_id': 'grad-' + n,
                          'x1': f['x1'], 'y1': f['y1'], 'x2': f['x2'], 'y2': f['y2'],
                          'stops': [{'offset': s['offset'], 'hex': s['hex'], 'measured': s['measured'], 'swatch': s['swatch'], 'palette': s['palette']}
                                    for s in f['stops']]},
                          'geometry': 'polygon from measured lines' if n in POLY else 'traced + rebuilt (snapped lines, G1 cubics)',
                          'anchors': sum(len(q['segs']) for q in kit.parse_d(geo[n])),
                          'fit': {k: src['report'][n][k] for k in ('K', 'angle')}})
    out = {
        'component': 'hero-14', 'source': '14', 'master': 'ap-hero (06)',
        'viewBox': [0, 0, Wd, H], 'source_space': 'original 14 pixel space (y down), identity placement',
        'background_measured': BG, 'mark_box_14': list(MARK_BOX), 'wordmark_excluded_below_y': REGION_Y1,
        'bbox': bbox_of(sil), 'apex_top_y': round(raw['top']['c'], 3), 'baseline_y': round(raw['base']['c'], 3),
        'mark_height': round(raw['base']['c'] - raw['top']['c'], 3), 'silhouette_d': sil,
        'z_order': 'faces listed bottom to top (same 11 faces and order as ap-hero); each lower face reaches 2.5 px under the face stacked above it; all faces are cut by the one shared silhouette',
        'faces': faces_out,
        'tones': tones,
        'palette_used': sorted({s['swatch'] for f in fills.values() for s in f['stops'] if s['palette']}),
        'colour_rule': {'palette_snap_dE2000': SNAP, 'merge_dE2000': MERGE, 'palette_snaps': snapped,
                        'merged_tones': {h: [{'measured': m, 'dE2000': round(de(h, m), 2)} for m in ms] for h, ms in merged.items()},
                        'largest_stop_move_dE2000': round(worst, 2),
                        'method': 'stops fitted by least squares in sRGB per face; a stop within 2.0 of a kit.PALETTE colour would snap to it (none is); stop colours within 2.0 of each other are clustered (complete linkage) and each cluster becomes one tone, re-solved by least squares over the pixels of every face that uses it (seams kept continuous)'},
        'measured_lines': {k: line_entry(k) for k in raw if not k.startswith('_')},
        'invisible_cuts': dict(CUTS, fold_top_cut='p-bowl-top | ribbon-front-stem along fold_top, x P_left..stem_mid'),
        'leg_kinks': {k: {'y_upper_line': v[0], 'y_lower_line': v[1]} for k, v in KINK.items()},
        'differences_from_master': [
            'leg slopes: left leg -24.0 deg (06: -25.4), right leg +26.0/+26.9 deg (06: +27.2)',
            "14's leg edges are not collinear across the ribbon: below it the right leg's edges are turned 0.45-0.87 deg and land 2.5-3.1 px further right at the base, the left leg's inner edge and crease are shifted +1.5 and +1.0 px (its outer edge is one straight line); each such edge is an upper and a lower line joined by corners the ribbon covers",
            'ribbon: thicker over the crossbar (61.8 px vs 58.1 transformed), flat runs at y 489.53 / 551.36; its upper band runs out as a 1-4 px strip along the A outer edge to y 584',
            'P: stem 528.46-590.67, counter 365.02-447.14, crease 477.91, bowl bottom 508.94, fold top 334.13 with a 44.6 deg fold edge; the P stem below the bowl ends in a point where the leg crosses (y 556.98)'],
        'metrics': dict(met, per_face=per_face, seams=seam_rep,
                        method='VectorCraft render (kit.render_svg) of components/rec/hero-14.svg at 1x, composited on the measured 14 background #FFFFFF; IoU of kit.bg_mask(dE2000 > 18 from #FFFFFF) masks inside the mark box + 12 px, rows >= 636 (wordmark) excluded; dE2000 over the original mark mask (interior = mask eroded 1 px); per face over its visible interior eroded 1 px'),
    }
    json.dump(out, open(REC / 'hero-14.json', 'w'), indent=1)
    print('wrote', out_svg, REC / 'hero-14.json', kit.VERIFY / 'hero-14_diff.png')
