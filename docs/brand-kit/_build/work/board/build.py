"""Build components/board-02.svg (vector recreation of original 02, the brand guidelines & style board)
from the board agent's measurements, then verify it against the original.

inputs (work/board/): tf2_P*.json (text fits, pass 2), fit_x.json (clear-space 'x' labels), cs_joint.json
(dashed grid / arrows / crosses), ring_fit.json (white-swatch outlines), slots_raw.json (logo / graphic slots).
outputs: components/board-02.svg, fit/board-02.json, fit/board-slots.json, verify/board-02_diff.png,
verify/board-02_zoom.png"""
import json
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
from PIL import Image
import kit
import jpegsim as J
import textfit as tf
import thin
from dashes import along
from runs import RUNS

WB = kit.WORK / 'board'
IMG = kit.load('02')
IMGf = IMG.astype(float)
H_, W_ = IMG.shape[:2]
LUM = np.array([0.299, 0.587, 0.114])
P = kit.PALETTE
RUN = {r[0]: r for r in RUNS}


def lab(c):
    return kit.srgb_to_lab(np.clip(np.asarray(c, float), 0, 255))


def de(c1, c2):
    return float(kit.de2000(lab(c1), lab(c2)))


def snap(c, name):
    """Palette colour if within dE2000 4, else the measured colour (rounded) as a supporting tone."""
    nm, hx, d = kit.nearest_palette(np.clip(c, 0, 255))
    if d <= 4.0:
        return {"hex": hx, "palette": nm, "measured": kit.rgbhex(c), "dE_to_palette": round(d, 2), "name": nm}
    return {"hex": kit.rgbhex(c), "palette": None, "measured": kit.rgbhex(c), "dE_to_palette": round(d, 2),
            "nearest_palette": nm, "name": name}


# ------------------------------------------------------------------ text: final per-run parameters
def ink_area(v, st):
    """mean over the group's runs of sum(fitted coverage) / sum(original alpha)."""
    inks = json.loads((WB / 'inks_apparent.json').read_text())
    r = []
    for rid, p in zip(v['runs'], v['trials'][st]['runs']):
        k = p['kerned']
        _, s, box, ink, gi = RUN[rid]
        run = tf.Run(rid, s, box, inks[rid], {i: 1 for i in gi})
        r.append(run.render(st, [k['size'], k['tracking'], k['x'], k['baseline']], offs=k['offsets_px']).sum() / run.alpha.sum())
    return float(np.mean(r))


def load_text():
    out, choice = {}, {}
    for f in ['tf2_P1.json', 'tf2_P2.json', 'tf2_P3.json', 'tf2_P4.json']:
        d = json.loads((WB / f).read_text())
        for g, v in d.items():
            if g == '_runs' or g == 'csx':
                continue
            # weight = argmax(binary IoU + soft IoU), both averaged over the group's kerned runs; the ink-area
            # ratio (sum coverage / sum alpha) is recorded where the two IoUs disagree on their own
            sb = max(v['trials'], key=lambda s: v['trials'][s]['mean_bin'])
            ss = max(v['trials'], key=lambda s: v['trials'][s]['mean_soft'])
            st = max(v['trials'], key=lambda s: v['trials'][s]['mean_bin'] + v['trials'][s]['mean_soft'])
            area = {s: round(ink_area(v, s), 3) for s in {sb, ss}} if sb != ss else {}
            how = ("argmax(binary IoU + soft IoU); binary alone prefers %s, soft alone %s" % (sb, ss)) if sb != ss else \
                "argmax(binary IoU + soft IoU); both agree"
            choice[g] = {"style": st, "by": how, "ink_area_ratio": area,
                         "mean_iou": {s: round(t['mean_bin'], 4) for s, t in v['trials'].items()},
                         "mean_iou_soft": {s: round(t['mean_soft'], 4) for s, t in v['trials'].items()},
                         "size": v['trials'][st]['size']}
            for rid, p in zip(v['runs'], v['trials'][st]['runs']):
                out[rid] = dict(p['kerned'], group=g)
    X = json.loads((WB / 'fit_x.json').read_text())
    st = 'Medium'     # ink-area match (see fit_x / report): IoU cannot separate weights on 10 px glyphs
    choice['csx'] = {"style": st, "by": "ink area (rendered coverage / original luma coverage = 0.96); 1x IoU "
                     "cannot separate weights on these 10 px glyphs", "size": X['trials'][st]['size'],
                     "mean_iou": {s: round(float(np.mean([r['iou'] for r in t['runs']])), 4) for s, t in X['trials'].items()}}
    for rid, p in zip(['cs-x-top', 'cs-x-bottom', 'cs-x-left', 'cs-x-right'], X['trials'][st]['runs']):
        out[rid] = dict(p, group='csx', offsets_px=[0.0], kerning={})
    return out, choice


def glyph_ds(rid, p):
    """Per-glyph path data (kit.text_paths geometry + per-glyph kerning offsets)."""
    s = RUN[rid][1]
    ds = kit.text_paths(s, p['style'], p['size'], p['tracking'], p['x'], p['baseline'])
    offs = p.get('offsets_px') or [0.0] * len(ds)
    lay = tf.layout(s, p['style'])
    return [(lay[i][1], kit.transform_d(d, 1.0, offs[i], 0.0)) for i, d in enumerate(ds)]


def clean_d(d, nd=3):
    """Degenerate cubics (handles on the anchors) -> straight segments; drop zero-length segments."""
    subs = kit.parse_d(d)
    for s in subs:
        cur, segs = s['start'], []
        for g in s['segs']:
            if g[0] == 'C':
                x1, y1, x2, y2, x, y = g[1:]
                if np.hypot(x1 - cur[0], y1 - cur[1]) < 1e-3 and np.hypot(x2 - x, y2 - y) < 1e-3:
                    g = ('L', x, y)
            if np.hypot(g[-2] - cur[0], g[-1] - cur[1]) < 1e-4:
                continue
            segs.append(g)
            cur = (g[-2], g[-1])
        if s['closed'] and segs and segs[-1][0] == 'L' and np.hypot(segs[-1][1] - s['start'][0], segs[-1][2] - s['start'][1]) < 1e-4:
            segs.pop()       # Z closes it
        s['segs'] = segs
    return kit.format_d(subs, nd)


# ------------------------------------------------------------------ colours
def interior_median(runs, T):
    px = []
    for rid in runs:
        s, box, gi = RUN[rid][1], RUN[rid][2], RUN[rid][4]
        p = T[rid]
        g = tf.run_glyphs(s, p['style'], p['size'], p['tracking'], p['x'], p['baseline'], p.get('offsets_px'))
        cov = tf.coverage([gg for gg in g if gg[1] not in gi], box)
        inside = kit.erode(cov >= 0.999, 2)
        x0, y0, x1, y1 = box
        px.append(IMGf[y0:y1, x0:x1][inside])
    return np.median(np.concatenate(px), 0)


def ls_ink_runs(runs, T, which='main'):
    inks = []
    for rid in runs:
        s, box, gi = RUN[rid][1], RUN[rid][2], RUN[rid][4]
        p = T[rid]
        g = tf.run_glyphs(s, p['style'], p['size'], p['tracking'], p['x'], p['baseline'], p.get('offsets_px'))
        sel = [gg for gg in g if (gg[1] in gi) == (which == 'other')]
        cov = tf.coverage(sel, box)
        mask = np.ones(cov.shape, bool)
        if gi:   # keep the other ink's glyphs out of this ink's solve
            oth = tf.coverage([gg for gg in g if (gg[1] in gi) != (which == 'other')], box)
            mask = ~kit.dilate(oth > 0, 2)
        ink, r = thin.ls_ink(cov, box, mask=mask)
        inks.append(ink)
    return np.array(inks)


# ------------------------------------------------------------------ straight rules / guides
def line_ends(o, c, lo, hi, plateau_range):
    """Sub-pixel ends of a rule from the luma integral across it (area-based edge)."""
    integ, _ = along(o, c, lo, hi, win=3)
    a, b = plateau_range
    plat = np.median(integ[a - lo:b - lo])
    full = np.nonzero(integ >= 0.9 * plat)[0]
    i0, i1 = full[0], full[-1]
    start = lo + i0 - np.clip(integ[max(0, i0 - 3):i0] / plat, 0, 1).sum()
    end = lo + i1 + 1 + np.clip(integ[i1 + 1:i1 + 4] / plat, 0, 1).sum()
    return float(start), float(end), float(plat)


def main():
    T, choice = load_text()
    # ---------------- colours
    BGc = snap(tf.BG, 'Board Background')
    navy_int = interior_median(['title', 'headline', 'spec-1', 'spec-2', 'spec-3', 'spec-4', 'spec-5', 'horiz-line1'], T)
    INK = snap(navy_int, 'Ink Navy')
    char_runs = ['hex-blue', 'hex-cyan', 'hex-navy', 'hex-white', 'hex-offwhite', 'hero-tagline']
    char_ls = ls_ink_runs(char_runs, T)       # recorded only: unstable on these 1.5 px strokes (drifts green)
    app = json.loads((WB / 'inks_apparent.json').read_text())
    char = np.median([app[r][0] for r in char_runs], 0)   # apparent stroke colour (hex codes + tagline merged: dE<=3 to both)
    CHAR = snap(char, 'Charcoal')
    royal_ls = ls_ink_runs(['hero-wordmark', 'horiz-line2'], T, 'other')
    ROYAL = snap(royal_ls.mean(0), 'Royal Blue')
    # title AI: interior of the big cyan glyphs
    s, box, gi = RUN['title'][1], RUN['title'][2], RUN['title'][4]
    p = T['title']
    g = tf.run_glyphs(s, p['style'], p['size'], p['tracking'], p['x'], p['baseline'], p.get('offsets_px'))
    cv = tf.coverage([gg for gg in g if gg[1] in gi], box)
    x0, y0, x1, y1 = box
    cyan_int = np.median(IMGf[y0:y1, x0:x1][kit.erode(cv >= 0.999, 2)], 0)
    CYAN = snap(cyan_int, 'Title Cyan')
    CS = json.loads((WB / 'cs_joint.json').read_text())
    RED = snap(np.array(CS['ink']), 'Clear-space Red')
    RINGS = json.loads((WB / 'ring_fit.json').read_text())

    # rules (Deep Navy) and guides: centre / width from thin fits (see t_lines2.py), widths re-expressed for the
    # snapped palette colour so the luma integral (what the eye integrates) is preserved
    navy = kit.hexrgb(P['Deep Navy'])
    Yn = navy @ LUM
    Ybg = tf.BG @ LUM
    rules_fit = {  # name: (orient, centre, fitted width, fitted ink luma, along lo, hi, plateau sample)
        'divider-header': ('h', 147.42, 1.75, np.array([3.5, 9.5, 18.9]) @ LUM, 20, 1360, (100, 1300)),
        'divider-row-left': ('h', 440.59, 1.60, np.array([19.5, 25.4, 35.9]) @ LUM, 20, 688, (60, 650)),
        'divider-row-mid': ('h', 440.58, 1.61, np.array([17.9, 22.5, 34.3]) @ LUM, 688, 1011, (720, 980)),
        'divider-row-right': ('h', 440.59, 1.61, np.array([17.9, 21.3, 33.7]) @ LUM, 1011, 1360, (1040, 1330)),
        'divider-col1-top': ('v', 687.98, 2.09, np.array([51.5, 57.1, 69.0]) @ LUM, 150, 440, (190, 410)),
        'divider-col1-bottom': ('v', 687.92, 2.00, np.array([43.4, 52.3, 57.5]) @ LUM, 441, 768, (470, 730)),
        'divider-col2': ('v', 1011.63, 1.59, np.array([17.6, 22.5, 30.9]) @ LUM, 441, 768, (470, 730)),
    }
    rules = {}
    for n, (o, c, w, Yi, lo, hi, pr) in rules_fit.items():
        a, b, plat = line_ends(o, c, lo, hi, pr)
        rules[n] = {"orient": o, "center": round(c, 2), "from": round(a, 2), "to": round(b, 2),
                    "width": round(w * (Ybg - Yi) / (Ybg - Yn), 2), "width_at_fitted_ink": w}
    guide_fit = {   # centre, width, ink from thin fits; spans from the guide grid topology + measured free ends
        'guide-h-205': ('h', 205.09, (203.5, 205.2, 210.4), 1.25), 'guide-h-265': ('h', 264.66, (208.1, 211.9, 214.0), 1.12),
        'guide-h-294': ('h', 293.63, (204.1, 208.4, 212.1), 1.30), 'guide-h-410': ('h', 409.96, (198.4, 200.1, 205.2), 1.14),
        'guide-v-62': ('v', 62.17, (210.8, 211.4, 214.5), 1.41), 'guide-v-371': ('v', 371.04, (207.5, 209.6, 213.8), 1.33),
        'guide-v-401': ('v', 401.42, (206.1, 208.6, 214.1), 1.26), 'guide-v-517': ('v', 517.20, (197.4, 199.6, 203.3), 1.02),
        'guide-v-538': ('v', 538.10, (206.1, 206.9, 210.2), 1.29), 'guide-v-654': ('v', 654.37, (202.5, 207.5, 209.2), 1.10)}
    g_inks = np.array([v[2] for v in guide_fit.values()])
    g_w = np.array([v[3] for v in guide_fit.values()])
    gw = float(np.median(g_w))
    # one guide colour at one width: integral-preserving average of the fits
    dark = np.median((tf.BG - g_inks) * g_w[:, None], 0) / gw
    GUIDE = snap(tf.BG - dark, 'Guide Grey')
    # spans: free ends measured; ends that abut another guide snap to that guide's centre
    top_v = line_ends('v', 62.17, 150, 300, (230, 330))[0]
    bot_v = float(np.median([line_ends('v', c, 380, 441, (412, 432))[1] for c in (62.17, 371.04, 401.42, 517.20, 538.10, 654.37)]))
    right_h = float(np.median([line_ends('h', c, 600, 690, (658, 678))[1] for c in (205.09, 264.66, 293.63, 409.96)]))
    left_h = float(np.median([line_ends('h', c, 0, 120, (35, 58))[0] for c in (205.09, 409.96)]))
    guides = {}
    for n, (o, c, ink, w) in guide_fit.items():
        if o == 'h':
            a = left_h if n in ('guide-h-205', 'guide-h-410') else 371.04
            b = right_h
        else:
            a = 264.66 if n in ('guide-v-517', 'guide-v-538') else top_v
            b = bot_v
        guides[n] = {"orient": o, "center": c, "from": round(a, 2), "to": round(b, 2), "width": round(gw, 2)}

    # ---------------- SVG
    body, defs = [], []
    hx = lambda t: t["hex"]
    body.append('<rect id="background" x="0" y="0" width="%d" height="%d" fill="%s"/>' % (W_, H_, hx(BGc)))
    body.append('<g id="layout-guides" fill="none" stroke="%s" stroke-width="%.2f">' % (hx(GUIDE), gw))
    for n, g_ in guides.items():
        if g_["orient"] == 'h':
            body.append('  <path id="%s" d="M%.2f %.2f H%.2f"/>' % (n, g_["from"], g_["center"], g_["to"]))
        else:
            body.append('  <path id="%s" d="M%.2f %.2f V%.2f"/>' % (n, g_["center"], g_["from"], g_["to"]))
    body.append('</g>')
    body.append('<g id="dividers" fill="none" stroke="%s">' % P['Deep Navy'])
    for n, r in rules.items():
        if r["orient"] == 'h':
            body.append('  <path id="%s" d="M%.2f %.2f H%.2f" stroke-width="%.2f"/>' % (n, r["from"], r["center"], r["to"], r["width"]))
        else:
            body.append('  <path id="%s" d="M%.2f %.2f V%.2f" stroke-width="%.2f"/>' % (n, r["center"], r["from"], r["to"], r["width"]))
    body.append('</g>')
    # swatches: palette fills; Pure White / Off-White outlined; Bright Cyan with its soft outer glow
    sw = [('swatch-vibrant-blue', 788.32, P['Vibrant Blue']), ('swatch-bright-cyan', 908.22, P['Bright Cyan']),
          ('swatch-deep-navy', 1027.94, P['Deep Navy'])]
    R0 = 45.35
    CY = 268.75
    rw = RINGS['swatch-pure-white']
    ro = RINGS['swatch-off-white']
    white_ring_w = rw['width'] * (Ybg - np.array(rw['ink']) @ LUM) / (Ybg - Yn)   # Deep Navy, same luma integral
    OUTLINE = snap(np.array(ro['ink']), 'Swatch Outline Grey')
    defs.append('<radialGradient id="swatch-bright-cyan-glow-gradient" cx="908.22" cy="%.2f" r="49.6" gradientUnits="userSpaceOnUse">'
                '<stop offset="%.4f" stop-color="%s" stop-opacity="0.34"/><stop offset="%.4f" stop-color="%s" stop-opacity="0.12"/>'
                '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>' % (
                    CY, R0 / 49.6, P['Bright Cyan'], (R0 + 1.4) / 49.6, P['Bright Cyan'], P['Bright Cyan']))
    body.append('<g id="color-palette-swatches">')
    body.append('  <circle id="swatch-bright-cyan-glow" cx="908.22" cy="%.2f" r="49.6" fill="url(#swatch-bright-cyan-glow-gradient)"/>' % CY)
    for n, cx, col in sw:
        body.append('  <circle id="%s" cx="%.2f" cy="%.2f" r="%.2f" fill="%s"/>' % (n, cx, CY, R0, col))
    body.append('  <circle id="swatch-pure-white" cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (
        rw['cx'], CY, R0 - white_ring_w / 2, P['Pure White'], P['Deep Navy'], white_ring_w))
    body.append('  <circle id="swatch-off-white" cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (
        ro['cx'], CY, ro['r_stroke'], P['Off-White'], hx(OUTLINE), ro['width']))
    body.append('</g>')
    tiles = {'tile-two-tone': (401.41, 293.49, 517.54, 410.14), 'tile-flat': (538.04, 293.46, 654.61, 410.06)}
    body.append('<g id="logo-variation-tiles" fill="%s">' % P['Deep Navy'])
    for n, (a, b, c, d) in tiles.items():
        body.append('  <rect id="%s" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (n, a, b, c - a, d - b))
    body.append('</g>')
    # clear-space diagram
    E = CS['elements']
    dash_w = float(np.median([E[n]['params'][1] for n in E if n.startswith('cs-h') or n.startswith('cs-v')]))
    ar = [E[n]['params'] for n in E if n.startswith('cs-arrow')]
    shaft_w, head_l, head_h = [float(np.median([a[i] for a in ar])) for i in (3, 4, 5)]
    cr = [E[n]['params'] for n in E if n.startswith('cs-cross')]
    cross_half, cross_w = float(np.median([c[2] for c in cr])), float(np.median([c[3] for c in cr]))
    body.append('<g id="clear-space-diagram">')
    body.append('  <g id="clear-space-grid" fill="none" stroke="%s" stroke-width="%.2f">' % (hx(RED), dash_w))
    grid = {}
    # the grid is closed: horizontals run between the outer edges of the outer verticals and vice versa
    hw = dash_w / 2
    xa, xb = E['cs-v1']['params'][0] - hw, E['cs-v4']['params'][0] + hw
    ya, yb = E['cs-h1']['params'][0] - hw, E['cs-h4']['params'][0] + hw
    for n in ['cs-h1', 'cs-h2', 'cs-h3', 'cs-h4', 'cs-v1', 'cs-v2', 'cs-v3', 'cs-v4']:
        c, w, s0, Pp, D = E[n]['params']
        o = 'h' if n.startswith('cs-h') else 'v'
        lo, hi = (xa, xb) if o == 'h' else (ya, yb)
        # keep the fitted dash phase without stroke-dashoffset (Illustrator ignores it): the dash cut by the
        # corner becomes a short solid stub, the dashed path starts at the next whole dash
        k0 = int(np.floor((lo - s0) / Pp))
        a = s0 + k0 * Pp                 # start of the dash that contains / follows the corner
        pid = {'cs-h1': 'cs-grid-h-top', 'cs-h2': 'cs-grid-h-mark-top', 'cs-h3': 'cs-grid-h-mark-bottom', 'cs-h4': 'cs-grid-h-bottom',
               'cs-v1': 'cs-grid-v-left', 'cs-v2': 'cs-grid-v-mark-left', 'cs-v3': 'cs-grid-v-mark-right', 'cs-v4': 'cs-grid-v-right'}[n]
        seg = lambda u, v: ('M%.2f %.2f H%.2f' % (u, c, v)) if o == 'h' else ('M%.2f %.2f V%.2f' % (c, u, v))
        stub = None
        if a < lo:
            if a + D > lo + 0.3:
                stub = (lo, a + D)
                body.append('    <path id="%s-corner" d="%s"/>' % (pid, seg(lo, a + D)))
            a += Pp
        grid[n] = {"orient": o, "center": c, "from": lo, "to": hi, "dash_start": a, "corner_stub": stub,
                   "dash": D, "gap": Pp - D, "period": Pp}
        body.append('    <path id="%s" d="%s" stroke-dasharray="%.2f %.2f"/>' % (pid, seg(a, hi), D, Pp - D))
    body.append('  </g>')
    body.append('  <g id="clear-space-arrows" fill="%s">' % hx(RED))
    arrows = {}
    for n in ['cs-arrow-top', 'cs-arrow-bottom', 'cs-arrow-left', 'cs-arrow-right']:
        axis, ta, tb = E[n]['params'][:3]
        vert = n in ('cs-arrow-top', 'cs-arrow-bottom')
        sw2 = shaft_w / 2
        if vert:
            pts = [(axis, ta), (axis + head_h, ta + head_l), (axis + sw2, ta + head_l), (axis + sw2, tb - head_l),
                   (axis + head_h, tb - head_l), (axis, tb), (axis - head_h, tb - head_l), (axis - sw2, tb - head_l),
                   (axis - sw2, ta + head_l), (axis - head_h, ta + head_l)]
        else:
            pts = [(ta, axis), (ta + head_l, axis - head_h), (ta + head_l, axis - sw2), (tb - head_l, axis - sw2),
                   (tb - head_l, axis - head_h), (tb, axis), (tb - head_l, axis + head_h), (tb - head_l, axis + sw2),
                   (ta + head_l, axis + sw2), (ta + head_l, axis + head_h)]
        arrows[n] = {"axis": axis, "tip_a": ta, "tip_b": tb, "vertical": vert}
        body.append('    <path id="%s" d="M%s Z"/>' % (n, ' L'.join('%.2f %.2f' % q for q in pts)))
    body.append('  </g>')
    body.append('  <g id="clear-space-crosses" fill="none" stroke="%s" stroke-width="%.2f">' % (hx(RED), cross_w))
    crosses = {}
    for n in ['cs-cross-tl', 'cs-cross-tr', 'cs-cross-bl', 'cs-cross-br']:
        cx, cy = E[n]['params'][:2]
        L = cross_half
        crosses[n] = {"cx": cx, "cy": cy}
        body.append('    <path id="%s" d="M%.2f %.2f L%.2f %.2f M%.2f %.2f L%.2f %.2f"/>' % (n, cx - L, cy - L, cx + L, cy + L, cx - L, cy + L, cx + L, cy - L))
    body.append('  </g>')
    body.append('</g>')
    # text
    ink_of = {}
    for rid, s, box, ink, gi in RUNS:
        main = CHAR if rid in ('hex-blue', 'hex-cyan', 'hex-navy', 'hex-white', 'hex-offwhite', 'hero-tagline') else (
            RED if rid.startswith('cs-x') else INK)
        other = CYAN if rid == 'title' else ROYAL
        ink_of[rid] = (main, other if gi else None)
    sections = [('text-header', ['title', 'subtitle']),
                ('text-section-labels', ['label-01', 'label-02', 'label-03', 'label-04', 'label-05']),
                ('text-logo-variations', ['hero-wordmark', 'hero-tagline', 'horiz-line1', 'horiz-line2']),
                ('text-color-palette', ['name-vibrant', 'name-blue', 'name-cyan', 'name-navy', 'name-white', 'name-offwhite',
                                        'hex-blue', 'hex-cyan', 'hex-navy', 'hex-white', 'hex-offwhite']),
                ('text-typography', ['spec-1', 'spec-2', 'spec-3', 'spec-4', 'spec-5', 'headline', 'headline-note',
                                     'subheader', 'subheader-note', 'body', 'body-note']),
                ('text-clear-space', ['cs-x-top', 'cs-x-bottom', 'cs-x-left', 'cs-x-right'])]
    for gid, ids in sections:
        body.append('<g id="%s">' % gid)
        for rid in ids:
            gi = RUN[rid][4]
            gl = glyph_ds(rid, T[rid])
            main = ' '.join(clean_d(d) for idx, d in gl if idx not in gi)
            body.append('  <path id="txt-%s" fill="%s" d="%s"/>' % (rid, hx(ink_of[rid][0]), main))
            if gi:
                oth = ' '.join(clean_d(d) for idx, d in gl if idx in gi)
                body.append('  <path id="txt-%s-ai" fill="%s" d="%s"/>' % (rid, hx(ink_of[rid][1]), oth))
        body.append('</g>')
    # slots (placeholders for marks / graphics drawn by other components)
    S = json.loads((WB / 'slots_raw.json').read_text())
    tb = lambda rid: [round(v, 2) for v in text_bbox(rid, T)]
    slots = {
        "slot-hero-stacked": {"mark": S['hero-stacked.mark']['bbox'], "wordmark": tb('hero-wordmark'), "tagline": tb('hero-tagline'),
                              "note": "big gradient AP (mark) with the fitted wordmark 'ALLIANCE AI PARTNERS' and tagline below"},
        "slot-hero-horizontal": {"mark": S['hero-horizontal.mark']['bbox'], "wordmark_line1": tb('horiz-line1'), "wordmark_line2": tb('horiz-line2'),
                                 "note": "small gradient AP beside 'ALLIANCE / AI PARTNERS' (text fitted in the board)"},
        "slot-tile-twotone": {"mark": S['tile-twotone.mark']['bbox'], "tile": list(tiles['tile-two-tone']), "note": S['tile-twotone.mark']['note']},
        "slot-tile-flat": {"mark": S['tile-flat.mark']['bbox'], "tile": list(tiles['tile-flat']), "note": S['tile-flat.mark']['note']},
        "slot-clearspace-mark": {"mark": S['clearspace.mark']['bbox'], "note": S['clearspace.mark']['note']},
        "slot-graphic-wave": {"bbox": S['graphic-wave']['bbox'], "bbox_with_glow": S['graphic-wave.glow']['bbox'], "note": S['graphic-wave']['note']},
        "slot-graphic-datamesh": {"bbox": S['graphic-datamesh']['bbox'], "note": S['graphic-datamesh']['note']},
    }
    for k, v in slots.items():
        v["rect"] = v.get("mark") or v.get("bbox")
    body.append('<g id="slots" fill="none" stroke="#FF00FF" stroke-width="1">')
    for k, v in slots.items():
        a, b, c, d = v["rect"]
        body.append('  <rect id="%s" x="%.2f" y="%.2f" width="%.2f" height="%.2f"/>' % (k, a, b, c - a, d - b))
    body.append('</g>')
    svg = kit.svg_doc(W_, H_, '\n'.join(body), '\n'.join(defs))
    out_svg = kit.COMP / 'board-02.svg'
    out_svg.write_text(svg, encoding='utf-8')
    print('wrote', out_svg, len(svg) // 1024, 'KB')

    # ---------------- verify
    png = WB / 'board-02_render4.png'
    kit._vc(['convert', out_svg, png, '--scale', 4])
    rim = Image.open(png).convert('RGBA')
    rgba = np.asarray(rim.reduce(4), float) / 255.0
    ren = kit.over(rgba, BGc['hex'])
    slotmask = np.zeros((H_, W_), bool)
    for k, v in slots.items():
        boxes = [v["rect"]] + ([v["bbox_with_glow"]] if "bbox_with_glow" in v else [])
        for a, b, c, d in boxes:
            slotmask[max(0, int(b) - 3):int(np.ceil(d)) + 3, max(0, int(a) - 3):int(np.ceil(c)) + 3] = True
    region = ~slotmask
    cmp = kit.compare(IMG, ren, region)
    dmap = cmp['de_map'].copy()
    dmap[slotmask] = 0
    kit.diff_sheet(IMG, ren, kit.VERIFY / 'board-02_diff.png', dmap,
                   'board-02 (slots masked: dE mean %.2f p95 %.2f)' % (cmp['de_mean'], cmp['de_p95']))
    # text IoU measured on the VectorCraft render
    inks_app = json.loads((WB / 'inks_apparent.json').read_text())
    text_out = {}
    for rid, s, box, ink, gi in RUNS:
        x0, y0, x1, y1 = box
        p = T[rid]
        main, oth = ink_of[rid]
        if rid.startswith('cs-x'):
            Yi = json.loads((WB / 'fit_x.json').read_text())['ink_luma'] if False else None
        app = [np.array(c) for c in inks_app[rid]]
        a_o, _ = tf.unmix(IMGf[y0:y1, x0:x1], app)
        rin = [kit.hexrgb(main["hex"])] + ([kit.hexrgb(oth["hex"])] if oth else [])
        a_r, _ = tf.unmix(ren[y0:y1, x0:x1], rin, bg=kit.hexrgb(BGc["hex"]))
        if rid.startswith('cs-x'):   # luma alpha for the red 10 px labels (as fitted)
            Yo = float(np.median([np.sort((IMGf[b_[1]:b_[3], b_[0]:b_[2]] @ LUM).ravel())[:8].mean() for b_ in
                                  [(861, 514, 881, 533), (861, 681, 881, 700), (725, 579, 745, 598), (957, 579, 977, 598)]]))
            a_o = np.clip((Ybg - IMGf[y0:y1, x0:x1] @ LUM) / (Ybg - Yo), 0, 1)
            a_r = np.clip((Ybg - ren[y0:y1, x0:x1] @ LUM) / (Ybg - kit.hexrgb(main["hex"]) @ LUM), 0, 1)
        a_o = np.where(a_o < 0.25, 0, a_o)
        a_r = np.where(a_r < 0.25, 0, a_r)
        gl = tf.run_glyphs(s, p['style'], p['size'], p['tracking'], p['x'], p['baseline'], p.get('offsets_px'))
        cov = tf.coverage(gl, box)
        # sub-pixel IoU: original alpha bilinearly upsampled 4x vs the outlines rasterised on the 4x grid
        a4 = np.asarray(Image.fromarray(a_o.astype(np.float32), 'F').resize(((x1 - x0) * 4, (y1 - y0) * 4), Image.BILINEAR))
        cov4 = tf.coverage([(ch, ix, [c * 4 for c in cons]) for ch, ix, cons in gl], (x0 * 4, y0 * 4, x1 * 4, y1 * 4), 4)
        text_out[rid] = {
            "string": s, "group": p.get('group'), "style": "Montserrat " + p['style'], "size": round(p['size'], 3),
            "tracking": round(p['tracking'], 2), "x": round(p['x'], 3), "baseline": round(p['baseline'], 3),
            "kerning": p.get('kerning', {}), "glyph_offsets_px": p.get('offsets_px'),
            "fill": main["hex"], "fill_name": main["name"], "ai_fill": oth["hex"] if oth else None,
            "ai_glyph_indices": sorted(gi) if gi else [],
            "iou": round(kit.iou(a_o >= 0.5, cov >= 0.5), 4), "iou_soft": round(tf.soft_iou(a_o, cov), 4),
            "iou_render": round(kit.iou(a_o >= 0.5, a_r >= 0.5), 4),
            "iou_4x": round(kit.iou(a4 >= 0.5, cov4 >= 0.5), 4),
            "iou_ceiling_raster_vs_render": round(kit.iou(cov >= 0.5, a_r >= 0.5), 4),
            "fit_box": list(box), "bbox": [round(v, 2) for v in text_bbox(rid, T)]}
    # ---------------- report data
    tones = {"Ink Navy": INK, "Charcoal": CHAR, "Royal Blue": ROYAL, "Guide Grey": GUIDE,
             "Swatch Outline Grey": OUTLINE, "Clear-space Red": RED}
    used = {"Ink Navy": "all navy text: title (except AI), subtitle, section labels, lockup wordmarks, swatch names, "
                        "typography specimens, HEADLINE/SUBHEADER/BODY TEXT and their notes",
            "Charcoal": "swatch hex codes (#1B56FF ... #F4F7FB) and the tagline 'Partners in AI. Partners in growth.'",
            "Royal Blue": "'AI' in the two lockup wordmarks of the logo-variation panel",
            "Guide Grey": "logo-variation layout guides (%.2f px hairlines)" % gw,
            "Swatch Outline Grey": "outline of the Off-White swatch",
            "Clear-space Red": "clear-space dashed grid, double arrows, corner crosses and the 'x' unit labels"}
    for k, v in tones.items():
        v["used_for"] = used[k]
    sup = {k: v for k, v in tones.items() if v["palette"] is None}
    # per-region error (slots masked): flat background, swatch interiors, everything else
    dm = cmp['de_map']
    flat = kit.erode(~kit.bg_mask(IMG, BGc["hex"], 6.0), 3) & region
    yy, xx = np.mgrid[0:H_, 0:W_]
    sw_in = np.zeros((H_, W_), bool)
    for cx in (788.32, 908.22, 1027.94, 1147.07, 1266.30):
        sw_in |= np.hypot(xx + 0.5 - cx, yy + 0.5 - CY) < R0 - 4
    rest = region & ~flat & ~sw_in
    region_stats = {k: {"de_mean": round(float(dm[m].mean()), 2), "de_p95": round(float(np.percentile(dm[m], 95)), 2),
                        "pixels": int(m.sum())} for k, m in (("flat_background", flat), ("swatch_interiors", sw_in),
                                                            ("edges_text_lines", rest))}
    pair = {}
    ks = list(sup)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            pair['%s / %s' % (ks[i], ks[j])] = round(de(kit.hexrgb(sup[ks[i]]["hex"]), kit.hexrgb(sup[ks[j]]["hex"])), 2)
    fitj = {
        "component": "board-02", "source": kit.ORIGINALS['02'][0], "viewBox": [0, 0, W_, H_],
        "svg": str(out_svg), "method": {
            "text": "Montserrat outlines from kit.text_paths; style/size/tracking/x/baseline fitted per run by mask IoU "
                    "(alpha = per-pixel unmix of bg->apparent ink), shared style+size inside obvious groups, then "
                    "per-glyph manual kerning (Illustrator kerning, 1/1000 em, at the given character index).",
            "iou": "binary IoU of alpha>=0.5 (original) vs coverage>=0.5 (exact raster of the fitted outlines) at 1x; "
                   "iou_render uses the VectorCraft render of the SVG instead of the raster; iou_soft = sum(min)/sum(max).",
            "colors": "large-glyph interiors / least squares through a JPEG 4:2:0 chroma model of the original "
                      "(it is quality-100 4:2:0, so thin features lose chroma, not luma); snapped to the palette within dE2000 4."},
        "style_choice": choice, "text_runs": text_out,
        "colors": {"background": BGc, "palette_used": {k: P[k] for k in P}, "supporting_tones": sup,
                   "supporting_tone_pairwise_dE2000": pair,
                   "measurements": {"ink_navy_interior": kit.rgbhex(navy_int), "charcoal_ls_per_run_unstable_not_used": [kit.rgbhex(c) for c in char_ls],
                                    "royal_ls_per_run": [kit.rgbhex(c) for c in royal_ls], "title_ai_interior": kit.rgbhex(cyan_int),
                                    "clear_space_red_joint": kit.rgbhex(CS['ink']), "pure_white_ring_fitted": kit.rgbhex(rw['ink']),
                                    "off_white_ring_fitted": kit.rgbhex(ro['ink'])}},
        "shapes": {"background": {"fill": BGc["hex"]}, "guides": dict(guides, _style={"stroke": GUIDE["hex"], "width": gw}),
                   "dividers": dict(rules, _style={"stroke": P['Deep Navy']}),
                   "swatches": {"radius": R0, "cy": CY, "centers_x": {n: cx for n, cx, c in sw},
                                "pure_white": {"cx": rw['cx'], "stroke": P['Deep Navy'], "stroke_width": round(white_ring_w, 3),
                                               "outer_radius": R0, "fitted": {"width": rw['width'], "ink": kit.rgbhex(rw['ink'])}},
                                "off_white": {"cx": ro['cx'], "r_stroke": ro['r_stroke'], "stroke": OUTLINE["hex"], "stroke_width": ro['width']},
                                "bright_cyan_glow": "radial gradient Bright Cyan 34% -> 0 over r 45.35..49.6 (soft glow in the original)"},
                   "tiles": tiles,
                   "clear_space": {"color": RED["hex"], "grid_stroke_width": round(dash_w, 3), "grid": grid,
                                   "arrows": dict(arrows, _style={"shaft_width": shaft_w, "head_length": head_l, "head_half_width": head_h}),
                                   "crosses": dict(crosses, _style={"half_size": cross_half, "stroke_width": cross_w})}},
        "verify": {"de_mean_excl_slots": cmp['de_mean'], "de_p95_excl_slots": cmp['de_p95'], "regions": region_stats,
                   "render": "VectorCraft at 4x, box-downsampled to 1x; slots (+3 px) excluded from every metric",
                   "text_iou_mean": round(float(np.mean([t['iou'] for t in text_out.values()])), 4),
                   "text_iou_4x_mean": round(float(np.mean([t['iou_4x'] for t in text_out.values()])), 4),
                   "text_iou_min": round(float(np.min([t['iou'] for t in text_out.values()])), 4),
                   "text_runs_below_0.88": [k for k, t in text_out.items() if t['iou'] < 0.88]},
    }
    (kit.FIT / 'board-02.json').write_text(json.dumps(fitj, indent=1, default=float), encoding='utf-8')
    slot_doc = {"component": "board-02", "units": "px in original 02 (1376x768), y down; bbox = [x0, y0, x1, y1]",
                "method": "tight bbox from the original's pixels: object coverage estimated as RGB distance from the "
                          "backdrop over the max distance in a 7x7 neighbourhood, bbox at coverage 0.5, sub-pixel "
                          "refined by the outermost row/column coverage", "slots": slots}
    (kit.FIT / 'board-slots.json').write_text(json.dumps(slot_doc, indent=1), encoding='utf-8')
    # zoom sheet for visual inspection
    crops = [(360, 30, 1020, 130), (20, 150, 690, 440), (690, 150, 1360, 440), (20, 440, 690, 750), (690, 440, 1010, 750), (1010, 440, 1376, 768)]
    ims, labs = [], []
    for c in crops:
        ims += [IMG[c[1]:c[3], c[0]:c[2]], ren[c[1]:c[3], c[0]:c[2]]]
        labs += ['orig %s' % (c,), 'vector %s' % (c,)]
    kit.contact(ims, labs, kit.VERIFY / 'board-02_zoom.png', cols=2, width=900)
    print('dE mean %.2f p95 %.2f (slots masked)' % (cmp['de_mean'], cmp['de_p95']))
    for k, t in text_out.items():
        print('  %-15s %-20s %6.2f iou=%.3f soft=%.3f render=%.3f 4x=%.3f ceil=%.3f fill=%s' % (
            k, t['style'], t['size'], t['iou'], t['iou_soft'], t['iou_render'], t['iou_4x'], t['iou_ceiling_raster_vs_render'], t['fill']))
    print('tones', {k: v['hex'] for k, v in tones.items()}, 'pairwise', pair)
    return fitj


def text_bbox(rid, T):
    s = RUN[rid][1]
    p = T[rid]
    g = tf.run_glyphs(s, p['style'], p['size'], p['tracking'], p['x'], p['baseline'], p.get('offsets_px'))
    return tf.glyph_extent(g)


if __name__ == '__main__':
    main()
