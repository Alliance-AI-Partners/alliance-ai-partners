"""Build the flat-colour mark vectors (agent prefix flat-): originals 12, 16, 09, 07, 10, 11, 03.
Writes components/flat-<id>.svg, fit/flat-<id>.json, verify/flat-<id>_diff.png (+ _tips.png where tips.py runs
a tip on), verify/flat_sheet.png.
usage: python build_flat.py [ids...]"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F  # noqa: E402
import tips as TP  # noqa: E402
from flatlib import kit, np  # noqa: E402
from PIL import Image  # noqa: E402

IDS = ['12', '16', '09', '07', '10', '11', '03']
COMP, FIT, VER = (os.path.join(F.BUILD, d) for d in ('components', 'fit', 'verify'))
for d in (COMP, FIT, VER):
    os.makedirs(d, exist_ok=True)

KIND = {'12': '2c', '16': '2c', '09': '2c', '07': '2c', '10': '2c', '11': '3c', '03': '2c'}
HAS_TEXT = {'16', '09', '07', '10'}
RING = {'03'}


def hexs(c):
    return kit.rgbhex(c)


def color_rec(name, measured, snapped):
    return {'measured': hexs(measured), 'snapped': snapped,
            'de2000_measured_to_snapped': round(float(kit.de2000(kit.srgb_to_lab(measured), kit.srgb_to_lab(kit.hexrgb(snapped)))), 2),
            'nearest_palette': kit.nearest_palette(hexs(measured))[0]}


def text_region(a, bg):
    """White wordmark: bbox (+ per-line bboxes) of pixels with white coverage > 0.5 (low chroma, light)."""
    L, C = F.lab_chroma(a)
    core = (C < 12) & (L > 60)
    if core.sum() < 200:
        return None
    x0, y0, x1, y1 = F.box_of(core, pad=4)
    sub = a[y0:y1, x0:x1]
    w_meas = np.median(a[core], 0)
    v = F.cov2(sub, bg, w_meas)
    m = v > 0.5
    rows = np.nonzero(m.any(1))[0]
    bx = F.box_of(m)
    box = [bx[0] + x0, bx[1] + y0, bx[2] + x0, bx[3] + y0]
    # split into lines on empty rows
    lines, start = [], rows[0]
    for r0, r1 in zip(rows[:-1], rows[1:]):
        if r1 - r0 > 3:
            lines.append((start, r0)); start = r1
    lines.append((start, rows[-1]))
    lb = []
    for s, e in lines:
        mm = np.zeros_like(m); mm[s:e + 1] = m[s:e + 1]
        b = F.box_of(mm)
        lb.append([b[0] + x0, b[1] + y0, b[2] + x0, b[3] + y0])
    return {'bbox': box, 'lines': lb, 'white_measured': w_meas, 'pad_box': [x0 - 6, y0 - 6, x1 + 6, y1 + 6]}


def measure_ring(al):
    """Rounded-square ring of original 03: straight edges from sub-pixel 0.5 crossings, corner radii from
    circle fits on radial scans. Returns dict with outer/inner boxes and radii."""
    H, W = al.shape
    mid = np.arange(int(H * 0.3), int(H * 0.7))
    out = {}
    # left / right: scan rows
    xs = np.arange(W, dtype=float)
    lo_l, li_l, lo_r, li_r = [], [], [], []
    for y in mid:
        cr = F.crossings(al[y], xs)
        rise = [p for p, s in cr if s > 0]
        fall = [p for p, s in cr if s < 0]
        lo_l.append(rise[0]); li_l.append(fall[0]); lo_r.append(fall[-1]); li_r.append(rise[-1])
    ys = np.arange(H, dtype=float)
    lo_t, li_t, lo_b, li_b = [], [], [], []
    for x in mid:
        cr = F.crossings(al[:, x], ys)
        rise = [p for p, s in cr if s > 0]
        fall = [p for p, s in cr if s < 0]
        lo_t.append(rise[0]); li_t.append(fall[0]); lo_b.append(fall[-1]); li_b.append(rise[-1])
    med = lambda v: float(np.median(v))
    # crossing positions are pixel centres; pixel i covers [i, i+1] -> edge at p + 0.5
    ox0, ox1, oy0, oy1 = med(lo_l) + 0.5, med(lo_r) + 0.5, med(lo_t) + 0.5, med(lo_b) + 0.5
    ix0, ix1, iy0, iy1 = med(li_l) + 0.5, med(li_r) + 0.5, med(li_t) + 0.5, med(li_b) + 0.5
    out['outer_box'] = [ox0, oy0, ox1, oy1]
    out['inner_box'] = [ix0, iy0, ix1, iy1]
    out['edge_spread_px'] = round(max(np.std(v) for v in (lo_l, li_l, lo_r, li_r, lo_t, li_t, lo_b, li_b)), 3)
    # corner radii: rays from a provisional centre, then from the fitted centre
    radii = {'outer': [], 'inner': []}
    centres = {'outer': [], 'inner': []}
    corners = [((ox0, oy0), (1, 1), (180, 270)), ((ox1, oy0), (-1, 1), (270, 360)),
               ((ox1, oy1), (-1, -1), (0, 90)), ((ox0, oy1), (1, -1), (90, 180))]
    fit_res = {'outer': [], 'inner': []}
    for (kx, ky), (sx, sy), (a0, a1) in corners:
        for which in ('outer', 'inner'):
            c = np.array([kx + sx * 60.0, ky + sy * 60.0])
            for it in range(4):
                pts = []
                span = (a0 + 25, a1 - 25) if it == 0 else (a0 + 10, a1 - 10)
                for ang in np.linspace(span[0], span[1], 80):
                    d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
                    t = np.arange(0, 160, 0.25)
                    p = c[None] + t[:, None] * d[None]
                    prof = F.bilinear(al, p[:, 0] - 0.5, p[:, 1] - 0.5)
                    cr = F.crossings(prof, t)
                    rise = [q for q, s in cr if s > 0]
                    fall = [q for q, s in cr if s < 0]
                    if which == 'outer' and fall:
                        pts.append(c + fall[-1] * d)
                    elif which == 'inner' and rise:
                        pts.append(c + rise[0] * d)
                cf = F.fit_circle(pts)
                c = np.array([cf[0], cf[1]])
            radii[which].append(cf[2])
            centres[which].append((cf[0], cf[1]))
            fit_res[which].append(round(cf[3], 3))
    out['circle_fit_max_residual'] = fit_res
    out['r_outer_each'] = [round(r, 2) for r in radii['outer']]
    out['r_inner_each'] = [round(r, 2) for r in radii['inner']]
    out['centre_offset_inner_vs_outer'] = [round(float(np.hypot(a[0] - b[0], a[1] - b[1])), 2)
                                          for a, b in zip(centres['outer'], centres['inner'])]
    out['r_outer'] = float(np.mean(radii['outer']))
    out['r_inner'] = float(np.mean(radii['inner']))
    return out


def ring_ideal(rg, W, H):
    """Constructed ring: one square size, one stroke width, concentric corners (r_in = r_out - stroke),
    centred on the measured centre (snapped to the canvas centre when within 0.1 px)."""
    ox0, oy0, ox1, oy1 = rg['outer_box']
    ix0, iy0, ix1, iy1 = rg['inner_box']
    cx, cy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    if abs(cx - W / 2) < 0.1 and abs(cy - H / 2) < 0.1:
        cx, cy = W / 2, H / 2
    half = ((ox1 - ox0) + (oy1 - oy0)) / 4
    stroke = float(np.mean([ix0 - ox0, iy0 - oy0, ox1 - ix1, oy1 - iy1]))
    r_o = rg['r_outer']
    ideal = {'centre': [round(cx, 3), round(cy, 3)], 'outer_size': round(2 * half, 3), 'stroke': round(stroke, 3),
             'r_outer': round(r_o, 3), 'r_inner': round(r_o - stroke, 3),
             'r_inner_measured': round(rg['r_inner'], 3)}
    meas = [ox0, oy0, ox1, oy1, ix0, iy0, ix1, iy1]
    idl = [cx - half, cy - half, cx + half, cy + half,
           cx - half + stroke, cy - half + stroke, cx + half - stroke, cy + half - stroke]
    ideal['max_edge_dev_vs_measured_px'] = round(float(max(abs(a - b) for a, b in zip(meas, idl))), 3)
    return ideal, idl


def ring_d(rg, W=1024, H=1024):
    ideal, (ox0, oy0, ox1, oy1, ix0, iy0, ix1, iy1) = ring_ideal(rg, W, H)
    outer = F.rrect_els(ox0, oy0, ox1, oy1, ideal['r_outer'], cw=True)
    inner = F.rrect_els(ix0, iy0, ix1, iy1, ideal['r_inner'], cw=False)
    return F.els_to_d(outer) + ' ' + F.els_to_d(inner)


def path_bbox(ds):
    pts = np.vstack([np.array(p) for d in ds for p in kit.flatten(kit.parse_d(d), tol=0.05)])
    return [round(float(v), 2) for v in (pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max())]


def trace_layer(alpha, label):
    """Trace a 0..1 coverage map as flat cyan on navy; returns the refitted path d of the cyan face."""
    clean = F.NAVY + alpha[..., None] * (F.CYAN - F.NAVY)
    Image.fromarray(np.round(clean).astype(np.uint8)).save(os.path.join(F.WORK, 'clean_%s.png' % label))
    res = kit.trace_image(clean, [F.NAVY_HEX, F.CYAN_HEX])
    cy = [d for d, f in res if f == F.CYAN_HEX]
    raw = ' '.join(cy)
    d, info = F.refit_path(raw, alpha=alpha)
    raw_anchors = sum(len(s['segs']) for s in kit.parse_d(raw))
    info['trace_anchors'] = raw_anchors
    return d, raw, info


def build(oid):
    t0 = time.time()
    a = kit.load(oid).astype(float)
    H, W, _ = a.shape
    frame = F.frame_mask(H, W)
    bg = np.median(a[frame], 0)
    rec = {'id': oid, 'source': kit.ORIGINALS[oid][0], 'description': kit.ORIGINALS[oid][1], 'size': [W, H],
           'svg': 'components/flat-%s.svg' % oid, 'colors': {}, 'notes': []}
    rec['colors']['background'] = color_rec('navy', bg, F.NAVY_HEX)
    text = text_region(a, bg) if oid in HAS_TEXT else None
    work = a.copy()
    if text:
        x0, y0, x1, y1 = text['pad_box']
        work[max(0, y0):y1, max(0, x0):x1] = bg
        rec['text_bbox'] = text['bbox']
        rec['text_lines_bbox'] = text['lines']
        rec['colors']['text_white'] = color_rec('white', text['white_measured'], F.WHITE_HEX)
    else:
        rec['text_bbox'] = None
    L, C = F.lab_chroma(work)
    fg = kit.bg_mask(work, hexs(bg), 18)
    core = kit.erode(fg, 3)
    cyan_m = np.median(work[core & (C >= 25)], 0)
    rec['colors']['cyan'] = color_rec('cyan', cyan_m, F.CYAN_HEX)
    layers = []  # (id, fill, d)
    ring = None
    tip_recs = []
    if KIND[oid] == '2c':
        al = F.cov2(work, bg, cyan_m)
        mark_cov_o = al.copy()
        if oid in RING:
            ring = measure_ring(al)
            ix0, iy0, ix1, iy1 = ring['inner_box']
            keep = np.zeros((H, W), bool)
            keep[int(iy0) + 12:int(iy1) - 12, int(ix0) + 12:int(ix1) - 12] = True
            al = np.where(keep, al, 0.0)
        alpha = F.snap01(al)
        d, raw, info = trace_layer(alpha, oid)
        # thin tapered ends (crescent / spike tips) that the 0.5-coverage trace cuts short: run on to the measured tips
        d_trace = d
        d, tip_recs = TP.extend(oid, d, TP.maps(work, bg, cyan_m))
        info.update(TP.counts(d))
        layers.append(('ap-cyan', F.CYAN_HEX, d, info))
    else:
        white_m = np.median(work[core & (C < 12) & (L > 80)], 0)
        rec['colors']['white'] = color_rec('white', white_m, F.WHITE_HEX)
        u, v = F.cov3(work, bg, cyan_m, white_m)
        u, v = F.snap01(u), F.snap01(v)
        # white face sits under the cyan face: extend it ~2 px into the cyan (not up to cyan/navy edges)
        # smooth offsets (Gaussian iso-levels) so the hidden edge is a clean curve, not dilation stair-steps
        grow = F.soft_offset(v, +2.0)          # white pushed 2 px outward
        inside = F.soft_offset(u + v, -1.0)    # whole mark shrunk 1 px: the extension stays 1 px off navy
        v_ext = np.maximum(v, np.minimum(grow, inside))
        dw, raw_w, info_w = trace_layer(v_ext, oid + 'w')
        dc, raw_c, info_c = trace_layer(u, oid + 'c')
        layers.append(('a-white', F.WHITE_HEX, dw, info_w))
        layers.append(('ribbon-p-cyan', F.CYAN_HEX, dc, info_c))
        mark_cov_o = np.clip(u + v, 0, 1)
        rec['colors']['note'] = 'white face extends ~2 px under the cyan face along white/cyan borders (no seams)'
    if ring:
        layers.append(('frame-ring', F.CYAN_HEX, ring_d(ring, W, H), {'subpaths': 2, 'anchors': 16, 'line_segs': 8, 'curve_segs': 8, 'construction': 'true rounded rectangles (4 lines + 4 quarter-circle cubics each, kappa 0.5523), concentric corners'}))
    # ---- SVG
    body = ['<rect id="bg" x="0" y="0" width="%d" height="%d" fill="%s"/>' % (W, H, F.NAVY_HEX), '<g id="mark">']
    for lid, fill, d, _ in layers:
        body.append('<path id="%s" fill="%s" fill-rule="nonzero" d="%s"/>' % (lid, fill, d))
    body.append('</g>')
    svg = kit.svg_doc(W, H, '\n'.join(body))
    svg_path = os.path.join(COMP, 'flat-%s.svg' % oid)
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg)
    # ---- verify
    r = F.render_rgb(svg_path)
    orig = kit.load(oid).astype(float)
    if KIND[oid] == '2c':
        cov_r = F.cov2(r, F.NAVY, F.CYAN)
        mo, mr = mark_cov_o > 0.5, cov_r > 0.5
        if text:
            x0, y0, x1, y1 = text['pad_box']
            mo[max(0, y0):y1, max(0, x0):x1] = False
            mr[max(0, y0):y1, max(0, x0):x1] = False
        met = {'mark_iou': round(kit.iou(mo, mr), 4)}
        if ring:
            ap = np.zeros((H, W), bool)
            ix0, iy0, ix1, iy1 = ring['inner_box']
            ap[int(iy0) + 12:int(iy1) - 12, int(ix0) + 12:int(ix1) - 12] = True
            met['ap_iou'] = round(kit.iou(mo & ap, mr & ap), 4)
            met['ring_iou'] = round(kit.iou(mo & ~ap, mr & ~ap), 4)
    else:
        ur, vr = F.cov3(r, F.NAVY, F.CYAN, F.WHITE)
        u0, v0 = F.cov3(orig, bg, cyan_m, white_m)
        mo, mr = (u0 + v0) > 0.5, (ur + vr) > 0.5
        met = {'mark_iou': round(kit.iou(mo, mr), 4), 'cyan_iou': round(kit.iou(u0 > 0.5, ur > 0.5), 4),
               'white_iou': round(kit.iou(v0 > 0.5, vr > 0.5), 4)}
    cmp_all = kit.compare(orig, r)
    region = kit.dilate(mo | mr, 2)
    cmp_mark = kit.compare(orig, r, region)
    bgreg = ~kit.dilate(mo | mr, 3)
    if text:
        x0, y0, x1, y1 = text['pad_box']
        bgreg[max(0, y0):y1, max(0, x0):x1] = False
    cmp_bg = kit.compare(orig, r, bgreg)
    met.update({'de_mean_canvas': cmp_all['de_mean'], 'de_p95_canvas': cmp_all['de_p95'],
                'de_mean_mark_region': cmp_mark['de_mean'], 'de_p95_mark_region': cmp_mark['de_p95'],
                'de_mean_background': cmp_bg['de_mean'],
                'note': 'canvas dE includes the excluded wordmark (drawn by another agent) where present' if text else ''})
    if not met['note']:
        del met['note']
    # dE with the text area excluded, so the mark+background number is not dominated by missing text
    if text:
        noText = np.ones((H, W), bool)
        x0, y0, x1, y1 = text['pad_box']
        noText[max(0, y0):y1, max(0, x0):x1] = False
        c2 = kit.compare(orig, r, noText)
        met['de_mean_canvas_excl_text'] = c2['de_mean']
        met['de_p95_canvas_excl_text'] = c2['de_p95']
    # geometry-only control: the same vectors filled with the measured colours instead of the palette
    meas = {F.NAVY_HEX: hexs(bg), F.CYAN_HEX: hexs(cyan_m)}
    if KIND[oid] == '3c':
        meas[F.WHITE_HEX] = hexs(white_m)
    svg_m = svg
    for k, v in meas.items():
        svg_m = svg_m.replace('fill="%s"' % k, 'fill="%s"' % v)
    ctrl_path = os.path.join(F.WORK, 'measured_%s.svg' % oid)
    with open(ctrl_path, 'w', encoding='utf-8') as f:
        f.write(svg_m)
    rm = F.render_rgb(ctrl_path, hexs(bg))
    keep = np.ones((H, W), bool)
    if text:
        x0, y0, x1, y1 = text['pad_box']
        keep[max(0, y0):y1, max(0, x0):x1] = False
    cm = kit.compare(orig, rm, keep)
    met['de_mean_if_measured_colours'] = cm['de_mean']
    met['de_p95_if_measured_colours'] = cm['de_p95']
    # soft (coverage) IoU and mean edge offset in a 4 px band around the mark
    if KIND[oid] == '2c':
        co, cr = mark_cov_o, F.cov2(r, F.NAVY, F.CYAN)
    else:
        co, cr = np.clip(u0 + v0, 0, 1), np.clip(ur + vr, 0, 1)
    band = kit.dilate(mo | mr, 4) & keep
    co, cr = np.where(band, co, 0), np.where(band, cr, 0)
    gy, gx = np.gradient(cr)
    per = float(np.hypot(gx, gy).sum())  # visible outline length (integral of |grad coverage|)
    met['soft_iou_band'] = round(float(np.minimum(co, cr).sum() / np.maximum(co, cr).sum()), 4)
    met['mean_edge_offset_px'] = round(float((cr.sum() - co.sum()) / per), 3)
    for c in rec['colors'].values():
        if isinstance(c, dict):
            c['exceeds_snap_threshold_4'] = c['de2000_measured_to_snapped'] > 4.0
    rec['method'] = ('coverage map of the measured colours -> clean palette resynthesis (wordmark/ring masked) -> '
                     'VectorCraft logo trace -> every edge snapped to the original 0.5 iso-line (smoothed per-point '
                     'shift) -> straight runs refit as true lines meeting at sharp corners, curves as C2 cubic splines '
                     'merged to few G1 cubics (tol 0.3 px); verified on a 4x VectorCraft render box-filtered to 1x')
    rec['mark_bbox'] = path_bbox([d for _, _, d, _ in layers])
    rec['layers'] = [{'id': lid, 'fill': fill, 'bbox': path_bbox([d]), **{k: v for k, v in info.items()}} for lid, fill, d, info in layers]
    if ring:
        rec['ring'] = {k: (round(v, 3) if isinstance(v, float) else ([round(x, 3) for x in v] if isinstance(v, list) and v and isinstance(v[0], float) else v)) for k, v in ring.items()}
        ox0, oy0, ox1, oy1 = ring['outer_box']
        ix0, iy0, ix1, iy1 = ring['inner_box']
        rec['ring']['stroke_width_each'] = [round(ix0 - ox0, 2), round(iy0 - oy0, 2), round(ox1 - ix1, 2), round(oy1 - iy1, 2)]
        rec['ring']['centre_measured'] = [round((ox0 + ox1) / 2, 3), round((oy0 + oy1) / 2, 3)]
        rec['ring']['constructed'] = ring_ideal(ring, W, H)[0]
    if tip_recs:
        rec['tips'] = TP.report(tip_recs, svg, d_trace, d, orig, r, rm, meas, hexs(bg), mo,
                                text['pad_box'] if text else None, mark_cov_o, os.path.join(VER, 'flat-%s_tips.png' % oid))
        rec['notes'].append('thin tapered ends run on to their measured tips (tips.py); before/after per tip in "tips", '
                            'zoomed crops in verify/flat-%s_tips.png' % oid)
    rec['metrics'] = met
    kit.diff_sheet(orig, r, os.path.join(VER, 'flat-%s_diff.png' % oid), cmp_all['de_map'],
                   label='flat-%s  IoU %.4f  dE mean %.2f' % (oid, met['mark_iou'], met['de_mean_canvas']))
    Image.fromarray(np.clip(np.round(r), 0, 255).astype(np.uint8)).save(os.path.join(F.WORK, 'render_%s.png' % oid))
    with open(os.path.join(FIT, 'flat-%s.json' % oid), 'w', encoding='utf-8') as f:
        json.dump(rec, f, indent=1, default=lambda o: float(o) if isinstance(o, np.floating) else str(o))
    print(oid, 'done %.1fs' % (time.time() - t0), json.dumps(met), [l['anchors'] for l in rec['layers']])
    return rec, orig, r


def sheet(ids):
    ims, labs = [], []
    for oid in ids:
        o = Image.open(kit.orig(oid)).convert('RGB')
        rp = os.path.join(F.WORK, 'render_%s.png' % oid)
        if not os.path.exists(rp):
            continue
        r = Image.open(rp).convert('RGB')
        j = json.load(open(os.path.join(FIT, 'flat-%s.json' % oid), encoding='utf-8'))
        cell = Image.new('RGB', (o.width * 2 + 16, o.height), 'white')
        cell.paste(o, (0, 0)); cell.paste(r, (o.width + 16, 0))
        ims.append(cell)
        labs.append('flat-%s  original | vector (wordmark excluded)  mark IoU %.4f  dE canvas %.2f' % (
            oid, j['metrics']['mark_iou'], j['metrics']['de_mean_canvas']))
    kit.contact(ims, labs, os.path.join(VER, 'flat_sheet.png'), cols=2, width=900)


if __name__ == '__main__':
    ids = sys.argv[1:] or IDS
    for oid in ids:
        build(oid)
    sheet(IDS)
