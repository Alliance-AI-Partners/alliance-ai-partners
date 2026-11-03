# Final stage: fit -> snap/merge tones -> write SVG -> VectorCraft render -> metrics, diff sheet, JSON.
import json
import numpy as np
from PIL import Image, ImageDraw
from build_shield import (run, composite, snap_and_merge, svg_text, metrics, kit, ORIG, LAB_O, WHITE, FG_O,
                          DE_W, H, W, HERE, E, AX)
from faces import OV
import layout

BUILD = HERE.parents[1]
COMP, FIT, VER = BUILD / 'components', BUILD / 'fit', BUILD / 'verify'


def region_metrics(de, region, fg_o, fg_r, excl, name, rows=None):
    r = region.copy()
    if rows is not None:
        sel = np.zeros_like(r)
        sel[rows[0]:rows[1]] = True
        r &= sel
        fo, fr = fg_o & sel & ~excl, fg_r & sel & ~excl
    else:
        fo, fr = fg_o & ~excl, fg_r & ~excl
    return {'region': name, 'iou': round(kit.iou(fo, fr), 4), 'de_mean': round(float(de[r].mean()), 2),
            'de_p95': round(float(np.percentile(de[r], 95)), 2), 'n_px': int(r.sum())}


def simplify(f):
    """Drop end stops that repeat their neighbour (pad makes them redundant); all-equal -> solid."""
    if f['type'] != 'linear':
        return
    offs, hx = list(f['offs']), list(f['hex'])
    while len(hx) > 1 and hx[-1] == hx[-2]:
        offs.pop(); hx.pop()
    while len(hx) > 1 and hx[0] == hx[1]:
        offs.pop(0); hx.pop(0)
    if len(set(hx)) == 1:
        f.update({'type': 'solid', 'hex': hx[0]})
        for k in ('p1', 'p2', 'offs'):
            f.pop(k, None)
    else:
        f['offs'], f['hex'] = offs, hx


def refit_offsets(f, xy, rgb):
    """After tone merging the stop colours are fixed; re-place the stop offsets to minimise the error."""
    from gradfit import _hat
    v = np.asarray(f['p2']) - np.asarray(f['p1'])
    t = (xy - f['p1']) @ v / (v @ v)
    cols = np.array([kit.hexrgb(h) for h in f['hex']])
    offs = np.array(f['offs'], float)
    lab = kit.srgb_to_lab(rgb)
    err = lambda o: float(kit.de2000(lab, kit.srgb_to_lab(_hat(t, o) @ cols)).mean())
    best, step = err(offs), 0.04
    while step > 0.002:
        moved = False
        for i in range(len(offs)):
            for d in (-step, step):
                o = offs.copy(); o[i] += d
                lo = o[i - 1] if i else -0.5
                hi = o[i + 1] if i < len(o) - 1 else 1.5
                if not (lo <= o[i] <= hi):
                    continue
                e = err(o)
                if e < best - 1e-9:
                    offs, best, moved = o, e, True
        if not moved:
            step /= 2
    # SVG needs offsets in [0, 1]: if a stop moved outside, extend the gradient vector instead
    lo, hi = min(offs[0], 0.0), max(offs[-1], 1.0)
    p1, p2 = np.asarray(f['p1']), np.asarray(f['p2'])
    f['p1'], f['p2'] = p1 + lo * (p2 - p1), p1 + hi * (p2 - p1)
    f['offs'] = list(map(float, (offs - lo) / (hi - lo)))


def main():
    faces, covs, vis, text, ap_core, ap_reg, mark, fills, weights = run()
    comp0 = composite(faces, covs, fills)
    m_pre, _, _ = metrics(comp0, mark, text)
    n_stops_pre = sum(1 if f['type'] == 'solid' else len(f['hex']) for f in fills.values())
    tones, palette_used = snap_and_merge(fills, weights)
    excl2 = mark | kit.dilate(text, 2)
    from build_shield import PIX
    for fc, v in zip(faces, vis):
        f = fills[fc.id]
        simplify(f)
        if f['type'] == 'linear':
            m = kit.erode(v, 1) & ~excl2 & (DE_W > 15)
            pred = composite([fc], [m.astype(float)], {fc.id: f})[m]
            m.flat[np.flatnonzero(m)[kit.de2000(LAB_O[m], kit.srgb_to_lab(pred)) > 8]] = False
            refit_offsets(f, PIX[m], ORIG[m])
            simplify(f)
    comp1 = composite(faces, covs, fills)
    m_post, _, _ = metrics(comp1, mark, text)
    print('own raster  pre-merge', m_pre, ' post-merge', m_post, ' tones', len(tones), 'stops', n_stops_pre)

    svg = svg_text(faces, fills)
    COMP.mkdir(parents=True, exist_ok=True)
    svg_path = COMP / 'shield-frame.svg'
    svg_path.write_text(svg, encoding='utf-8')
    rgba = kit.render_svg(svg_path, 1.0)
    render = kit.over(rgba, '#FFFFFF')
    Image.fromarray(np.clip(render, 0, 255).astype(np.uint8)).save(HERE / 'render.png')
    m_vc, de, region = metrics(render, mark, text)
    print('VectorCraft render', m_vc)

    fg_r = kit.de2000(kit.srgb_to_lab(render), WHITE) > 12
    excl = mark | kit.dilate(text, 2)
    parts = [region_metrics(de, region, FG_O, fg_r, excl, 'all'),
             region_metrics(de, region, FG_O, fg_r, excl, 'upper frame (y<464)', (0, 464)),
             region_metrics(de, region, FG_O, fg_r, excl, 'banner bars (464..593)', (464, 593)),
             region_metrics(de, region, FG_O, fg_r, excl, 'lower point (y>=593)', (593, H))]
    for p in parts:
        print(p)
    # transparency check: outside the frame the render must be fully transparent
    alpha_out = float(rgba[..., 3][~kit.dilate(np.max(np.array(covs), 0) > 0, 2)].max())

    # ---- diff sheet: masked areas shown hatched grey on the heatmap and outlined on the original
    heat_de = np.where(excl, 0, de)
    sheet_path = VER / 'shield_diff.png'
    kit.diff_sheet(ORIG, render, sheet_path, heat_de,
                   label='shield-frame vs original 17 (AP mark + banner text masked out: grey)')
    sh = Image.open(sheet_path).convert('RGB')
    a = np.asarray(sh).copy()
    hatch = ((np.add.outer(np.arange(H), np.arange(W)) // 4) % 2 == 0)
    off = 2 * (W + 10)
    sub = a[30:30 + H, off:off + W]
    sub[excl & hatch] = [150, 150, 150]
    sub[excl & ~hatch] = [205, 205, 205]
    edge = kit.dilate(excl, 1) & ~excl
    o = a[30:30 + H, 0:W]
    o[edge] = [255, 0, 200]
    sh = Image.fromarray(a)
    d = ImageDraw.Draw(sh)
    d.text((off + 6, 36), 'IoU %.4f  mean dE %.2f  p95 %.2f  (frame area, masks excluded)' % (m_vc['iou'], m_vc['de_mean'], m_vc['de_p95']), fill=(0, 0, 0))
    sh.save(sheet_path)
    # zoomed companion sheet (shield crop at 1x, stacked) for quick visual review
    box = (280, 35, 1096, 740)
    tiles = [Image.fromarray(ORIG.astype(np.uint8)).crop(box), Image.fromarray(np.clip(render, 0, 255).astype(np.uint8)).crop(box),
             sh.crop((off + box[0], 30 + box[1], off + box[2], 30 + box[3]))]
    kit.contact(tiles, ['original 17', 'shield-frame.svg (VectorCraft render)', 'dE2000 (grey = masked AP / text)'],
                VER / 'shield-diff-zoom.png', cols=3, width=600)

    # ---- layout + JSON
    lay = layout.measure(ap_reg, text, faces, covs, render)
    lay['symmetry_axis_x'] = round(AX + 0.5, 3)
    lay['coordinate_space'] = 'original 17 pixel space, 1376x768, y down (SVG user units = pixels)'
    lay['metrics'] = {'frame': m_vc, 'by_region': parts}
    FIT.mkdir(parents=True, exist_ok=True)
    (FIT / 'shield-layout.json').write_text(json.dumps(lay, indent=1), encoding='utf-8')

    face_rows = []
    for z, (fc, v) in enumerate(zip(faces, vis)):
        f = fills[fc.id]
        inner = kit.erode(v, 1) & ~excl
        row = {'id': fc.id, 'z': z, 'anchors': fc.n_anchors(), 'visible_px': int(v.sum()),
               'render_de_mean_interior': round(float(de[inner].mean()), 2) if inner.any() else None,
               'segments': ['line' if g[0] == 'L' else 'cubic' for g in fc.segs()[1]]}
        if f['type'] == 'solid':
            row['fill'] = {'type': 'solid', 'hex': f['hex']}
        else:
            row['fill'] = {'type': 'linearGradient', 'gradientUnits': 'userSpaceOnUse',
                           'x1': round(float(f['p1'][0]), 3), 'y1': round(float(f['p1'][1]), 3),
                           'x2': round(float(f['p2'][0]), 3), 'y2': round(float(f['p2'][1]), 3),
                           'stops': [{'offset': round(o, 4), 'hex': h} for o, h in zip(f['offs'], f['hex'])]}
        face_rows.append(row)
    meta = {
        'source': 'original 17 (' + kit.ORIGINALS['17'][0] + ')',
        'svg': 'components/shield-frame.svg',
        'viewBox': [0, 0, W, H],
        'symmetry_axis_x': round(AX + 0.5, 3),
        'excluded': ['AP mark (incl. its white keyline)', "banner text 'ALLIANCE AI PARTNERS'"],
        'construction': {
            'geometry': 'every boundary measured on both halves with sub-pixel edge refinement, right half mirrored '
                        'onto the left, fitted (lines / cubic polynomials = exact single cubic Beziers), right half '
                        'generated as the exact mirror; only the hidden 0.6 px under-laps break mirror identity',
            'edge_fit_rms_px': {k: round(v['rms'], 3) for k, v in E.items() if isinstance(v, dict) and 'rms' in v},
            'overlap_px': OV,
            'stacking': 'z order bottom->top as listed; each lower face runs 0.6 px (2 px under the upper bar) under '
                        'the face stacked above it, so there are no hairline seams',
        },
        'faces': face_rows,
        'palette_used': palette_used,
        'supporting_tones': [{'name': t['name'], 'hex': t['hex'], 'used_in': t['used_in']} for t in tones],
        'tone_rules': 'stops within dE2000 4 of a core palette colour snapped to it; remaining tones merged '
                      '(centroid linkage) until all are > dE2000 3 apart',
        'metrics': {'vectorcraft_render': m_vc, 'by_region': parts, 'own_raster_pre_merge': m_pre,
                    'own_raster_post_merge': m_post, 'outside_alpha_max': alpha_out,
                    'note': 'frame area = original or render foreground (dE>12 from white) dilated 1 px, minus '
                            'the AP mark (incl. keyline) and banner text masks; IoU on dE>12 foreground masks'},
    }
    (COMP / 'shield-frame.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    print('tones:')
    for t in tones:
        print('  ', t['name'], t['hex'], t['used_in'])
    print('palette used:', palette_used)
    print('layout:', json.dumps({k: v for k, v in lay.items() if k != 'metrics'}, indent=1))


if __name__ == '__main__':
    main()
