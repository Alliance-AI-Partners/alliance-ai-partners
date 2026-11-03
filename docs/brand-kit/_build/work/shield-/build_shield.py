# Build components/shield-frame.svg (+ .json), fit/shield-layout.json and verify/shield_diff.png
# from original 17. Geometry: faces.py (fitted, mirror-symmetric). Fills: fitted linear gradients.
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from faces import build, OV
from geom import E, AX
import gradfit

HERE = Path(__file__).resolve().parent
H, W = 768, 1376
ORIG = kit.load('17').astype(float)
LAB_O = kit.srgb_to_lab(ORIG)
WHITE = kit.srgb_to_lab(kit.hexrgb('#FFFFFF'))
DE_W = kit.de2000(LAB_O, WHITE)
FG_O = DE_W > 12
YY, XX = np.mgrid[0:H, 0:W]
PIX = np.stack([XX + 0.5, YY + 0.5], -1)  # pixel centers in SVG space

WHITE_FACES = {'field-upper', 'field-banner', 'field-lower'}


def geodesic(seed, cand, iters=40):
    m = seed & cand
    for _ in range(iters):
        n = kit.dilate(m, 1) & cand
        if (n == m).all():
            break
        m = n
    return m


def visible_masks(covs):
    vis, above = [None] * len(covs), np.zeros((H, W))
    for i in range(len(covs) - 1, -1, -1):
        vis[i] = (covs[i] > 0.999) & (above < 0.001)
        above = np.maximum(above, covs[i])
    return vis


def composite(faces, covs, fills):
    out = np.full((H, W, 3), 255.0)
    for fc, cov in zip(faces, covs):
        f = fills[fc.id]
        m = cov > 0
        if f['type'] == 'solid':
            col = np.broadcast_to(kit.hexrgb(f['hex']), (m.sum(), 3))
        else:
            col = gradfit.eval_grad(PIX[m], f['p1'], f['p2'], f['offs'], [kit.hexrgb(h) for h in f['hex']])
        a = cov[m][:, None]
        out[m] = out[m] * (1 - a) + col * a
    return out


def fit_faces(faces, vis, exclude, max_stops=5):
    fills = {}
    for fc, v in zip(faces, vis):
        if fc.id in WHITE_FACES:
            fills[fc.id] = {'type': 'solid', 'hex': '#FFFFFF', 'de': None, 'n': int(v.sum())}
            continue
        # frame faces never contain near-white pixels (those are keyline / antialias), and a trimmed
        # refit drops whatever else the face's own gradient can't explain (AP strokes over the band)
        m = kit.erode(v, 1) & ~exclude & (DE_W > 15)
        if m.sum() < 40:
            m = v & ~exclude & (DE_W > 15)
        g = gradfit.fit(PIX[m], ORIG[m], max_stops=max_stops)
        for _ in range(2):
            r = kit.de2000(LAB_O[m], kit.srgb_to_lab(g['pred']))
            keep = r <= max(8.0, 3.0 * float(np.median(r)))
            if keep.all():
                break
            idx = np.flatnonzero(m)
            m = m.copy()
            m.flat[idx[~keep]] = False
            g = gradfit.fit(PIX[m], ORIG[m], max_stops=max_stops)
        hexes = [kit.rgbhex(c) for c in g['cols']]
        if len(hexes) == 1:
            fills[fc.id] = {'type': 'solid', 'hex': hexes[0], 'de': g['de'], 'n': int(m.sum()), 'all': g['all']}
        else:
            fills[fc.id] = {'type': 'linear', 'p1': g['p1'], 'p2': g['p2'], 'offs': list(map(float, g['offs'])),
                            'hex': hexes, 'de': g['de'], 'n': int(m.sum()), 'theta': g['theta_deg'], 'all': g['all']}
    return fills


# ---------------------------------------------------------------- colour snapping / tone merging
def lab2hex(lab):
    L, a, b = lab
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    e, k = 216 / 24389, 24389 / 27
    xr = fx ** 3 if fx ** 3 > e else (116 * fx - 16) / k
    yr = fy ** 3 if L > k * e else L / k
    zr = fz ** 3 if fz ** 3 > e else (116 * fz - 16) / k
    xyz = np.array([xr * 0.95047, yr, zr * 1.08883])
    m = np.array([[3.2404542, -1.5371385, -0.4985314], [-0.9692660, 1.8760108, 0.0415560],
                  [0.0556434, -0.2040259, 1.0572252]])
    c = m @ xyz
    c = np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
    return kit.rgbhex(np.clip(c, 0, 1) * 255)


def tone_name(hexc):
    L, a, b = kit.srgb_to_lab(kit.hexrgb(hexc))
    h = np.degrees(np.arctan2(b, a)) % 360
    light = 'Deep' if L < 25 else 'Dark' if L < 42 else 'Mid' if L < 58 else 'Light' if L < 75 else 'Pale'
    hue = 'Indigo' if h > 300 else 'Blue' if h > 272 else 'Azure' if h > 252 else 'Cerulean' if h > 232 else 'Cyan'
    return f'Shield {light} {hue}'


def snap_and_merge(fills, weights, merge_de=3.0, snap_de=4.0):
    """Snap stops within snap_de of a core palette colour; merge remaining tones closer than merge_de
    (centroid linkage in Lab, weighted by pixel support). Rewrites fills in place; returns tone table."""
    snapped, tones = {}, []
    for fid, f in fills.items():
        hx = [f['hex']] if f['type'] == 'solid' else f['hex']
        for i, h in enumerate(hx):
            name, ph, de = kit.nearest_palette(h)
            if de <= snap_de:
                snapped[(fid, i)] = (ph, name)
            else:
                tones.append([kit.srgb_to_lab(kit.hexrgb(h)), weights.get(fid, 1.0) / len(hx), [(fid, i)]])
    while True:
        best = None
        for i in range(len(tones)):
            for j in range(i + 1, len(tones)):
                d = float(kit.de2000(tones[i][0], tones[j][0]))
                if d <= merge_de and (best is None or d < best[0]):
                    best = (d, i, j)
        if best is None:
            break
        _, i, j = best
        wi, wj = tones[i][1], tones[j][1]
        tones[i][0] = (tones[i][0] * wi + tones[j][0] * wj) / (wi + wj)
        tones[i][1] = wi + wj
        tones[i][2] += tones[j][2]
        tones.pop(j)

    def put(fid, i, hx):
        f = fills[fid]
        if f['type'] == 'solid':
            f['hex'] = hx
        else:
            f['hex'][i] = hx

    table = []
    for t in tones:
        hx = lab2hex(t[0])
        name, ph, de = kit.nearest_palette(hx)
        if de <= snap_de:  # a merged centroid can land near the palette
            for (fid, i) in t[2]:
                snapped[(fid, i)] = (ph, name)
            continue
        for (fid, i) in t[2]:
            put(fid, i, hx)
        table.append({'hex': hx, 'used_in': sorted({m[0] for m in t[2]}), 'n_stops': len(t[2])})
    for (fid, i), (ph, name) in snapped.items():
        put(fid, i, ph)
    table.sort(key=lambda t: -float(kit.srgb_to_lab(kit.hexrgb(t['hex']))[0]))
    seen = {}
    for t in table:
        nm = tone_name(t['hex'])
        seen[nm] = seen.get(nm, 0) + 1
        t['name'] = nm if seen[nm] == 1 else f'{nm} {seen[nm]}'
    palette_used = {}
    for (fid, i), (ph, name) in snapped.items():
        palette_used.setdefault(name, {'hex': ph, 'used_in': set()})['used_in'].add(fid)
    palette_used = [{'name': k, 'hex': v['hex'], 'used_in': sorted(v['used_in'])} for k, v in palette_used.items()]
    return table, palette_used


def svg_text(faces, fills):
    defs, body = [], []
    for fc in faces:
        f = fills[fc.id]
        d = fc.d()
        if f['type'] == 'solid':
            body.append(f'<path id="{fc.id}" fill="{f["hex"]}" d="{d}"/>')
        else:
            gid = 'grad-' + fc.id
            defs.append(kit.lin_grad(gid, f['p1'][0], f['p1'][1], f['p2'][0], f['p2'][1], list(zip(f['offs'], f['hex']))))
            body.append(f'<path id="{fc.id}" fill="url(#{gid})" d="{d}"/>')
    return kit.svg_doc(W, H, '<g id="shield-frame">\n' + '\n'.join(body) + '\n</g>', '\n'.join(defs))


def masks(faces, vis):
    vid = {fc.id: v for fc, v in zip(faces, vis)}
    banner = np.zeros((H, W), bool)
    banner[int(np.ceil(E['U_bot'] + 1.5)):int(np.floor(E['L_top'] - 1.0)), 280:1100] = True
    text = FG_O & banner
    ap_core = FG_O & kit.erode(vid['field-upper'], 1)
    return text, ap_core


def run():
    faces = build()
    covs = [kit.raster(fc.d(), W, H) for fc in faces]
    vis = visible_masks(covs)
    text, ap_core = masks(faces, vis)
    # pass 1: fit the frame well away from the mark (35 px clearance, at most 3 stops) so the AP strokes
    # and keyline over the bands can't bias it
    near = kit.dilate(ap_core, 35)
    excl1 = near | kit.dilate(text, 2)
    weights = {fc.id: float(v.sum()) for fc, v in zip(faces, vis)}
    fills1 = fit_faces(faces, vis, excl1, max_stops=3)
    comp1 = composite(faces, covs, fills1)
    diff1 = kit.de2000(LAB_O, kit.srgb_to_lab(comp1))
    # mark region = everything connected to the AP that the clean frame model can't explain.
    # Opening (r=2) drops the 1-2 px edge/antialias lines so the growth can't run along band edges;
    # the 16 px bridge crosses the white keyline between the in-field AP and the bands.
    cand = kit.dilate(kit.erode(diff1 > 10, 2), 2)
    seed = ap_core | (kit.dilate(ap_core, 16) & cand)
    upper = np.zeros((H, W), bool)
    upper[:int(E['U_top']) + 3] = True
    ap_reg = geodesic(seed, (cand | ap_core) & upper, iters=120)
    mark = kit.dilate(ap_reg, 2)
    excl2 = mark | kit.dilate(text, 2)
    fills = fit_faces(faces, vis, excl2)
    np.save(HERE / 'mark.npy', mark)
    np.save(HERE / 'text.npy', text)
    np.save(HERE / 'ap_reg.npy', ap_reg)
    return faces, covs, vis, text, ap_core, ap_reg, mark, fills, weights


def metrics(render, mark, text):
    de = kit.de2000(LAB_O, kit.srgb_to_lab(render))
    fg_r = kit.de2000(kit.srgb_to_lab(render), WHITE) > 12
    excl = mark | kit.dilate(text, 2)
    region = kit.dilate(FG_O | fg_r, 1) & ~excl
    return {'iou': round(kit.iou(FG_O & ~excl, fg_r & ~excl), 4), 'de_mean': round(float(de[region].mean()), 2),
            'de_p95': round(float(np.percentile(de[region], 95)), 2), 'n_px': int(region.sum())}, de, region


if __name__ == '__main__':
    faces, covs, vis, text, ap_core, ap_reg, mark, fills, weights = run()
    comp = composite(faces, covs, fills)
    m, de, region = metrics(comp, mark, text)
    print('pre-merge', m)
    for fc in faces:
        f = fills[fc.id]
        print(f"{fc.id:18s} {f['type']:6s} n={f['n']:6d} de={f.get('de') or 0:.2f} {f['hex']} {f.get('all', '')}")
    Image.fromarray(comp.astype(np.uint8)).save(HERE / 'comp_pre.png')
    kit.diff_sheet(ORIG, comp, HERE / 'comp_pre_diff.png', np.where(region, de, 0))
