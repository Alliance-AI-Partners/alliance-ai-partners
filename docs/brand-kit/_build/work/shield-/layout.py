# Layout measurements inside the shield: AP mark bbox + keyline, banner text box, Montserrat fit.
import numpy as np
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from geom import E, AX

ORIG = kit.load('17').astype(float)
LAB = kit.srgb_to_lab(ORIG)
DE_W = kit.de2000(LAB, kit.srgb_to_lab(kit.hexrgb('#FFFFFF')))
H, W = ORIG.shape[:2]
TEXT_STR = 'ALLIANCE AI PARTNERS'


def bbox(m):
    ys, xs = np.nonzero(m)
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def runs(v):
    """[(start, end)] of True runs in a 1-D bool array."""
    out, s = [], None
    for i, b in enumerate(v):
        if b and s is None:
            s = i
        if not b and s is not None:
            out.append((s, i)); s = None
    if s is not None:
        out.append((s, len(v)))
    return out


def alpha_ink(px, ink):
    """Coverage of `ink` over white for RGB pixels (projection on the white->ink line)."""
    w = np.array([255.0, 255, 255])
    v = np.asarray(ink, float) - w
    return np.clip((np.asarray(px, float) - w) @ v / (v @ v), 0, 1.2)


def edge_cross(a, lo, hi):
    """Sub-pixel position (pixel-edge coordinates) where 1-D coverage a crosses 0.5 going up (lo) / down (hi)."""
    i = int(np.argmax(a > 0.5))
    top = i - (a[i] - 0.5) / max(a[i] - a[i - 1], 1e-6) + 0.5 if i > 0 else float(i)
    j = len(a) - 1 - int(np.argmax(a[::-1] > 0.5))
    bot = j + (a[j] - 0.5) / max(a[j] - a[j + 1], 1e-6) + 0.5 if j < len(a) - 1 else float(j + 1)
    return lo + top, lo + bot


def keyline_width(ap_reg):
    """White gap between the AP and the frame where the AP's keyline crosses the bands."""
    white = DE_W < 6
    vals = []
    # A's left leg over the left side bands: horizontal white runs, converted to the perpendicular width
    leg = np.array([190.0, -305.0]); leg /= np.linalg.norm(leg)
    sin_t = abs(leg[1])
    for y in range(418, 452, 3):
        row = white[y, 405:480] & ap_reg[y, 405:480]
        rr = [r for r in runs(row) if r[1] - r[0] >= 4]
        if rr:
            vals.append((rr[0][1] - rr[0][0]) * sin_t)
    # P bowl under the top-right inner band: vertical white runs between band and P
    for x in range(840, 905, 5):
        col = white[130:200, x] & ap_reg[130:200, x]
        rr = [r for r in runs(col) if r[1] - r[0] >= 4]
        if rr:
            vals.append(rr[0][1] - rr[0][0])
    return round(float(np.median(vals)), 1), [round(v, 1) for v in vals]


def components(mask):
    """4-connected components of a small bool mask -> list of bool masks sorted by min x."""
    lab = np.zeros(mask.shape, int)
    comps, n = [], 0
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        n += 1
        stack, pts = [(y0, x0)], []
        lab[y0, x0] = n
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
        if len(pts) >= 20:
            m = np.zeros(mask.shape, bool)
            pp = np.array(pts)
            m[pp[:, 0], pp[:, 1]] = True
            comps.append(m)
    return sorted(comps, key=lambda m: np.nonzero(m)[1].min())


def measure(ap_reg, text, faces, covs, render):
    out = {}
    # AP letters = non-white pixels reachable from the in-field AP without crossing the white keyline
    seed = ap_reg & (DE_W > 12) & (np.mgrid[0:H, 0:W][1] > 470) & (np.mgrid[0:H, 0:W][1] < 905)
    ap_px = seed.copy()
    cand = ap_reg & (DE_W > 12)
    cand[int(E['U_top']) - 1:] = False  # the bar's top edge under the A's foot is frame, not mark
    seed &= cand
    for _ in range(200):
        n = kit.dilate(ap_px, 1) & cand
        if (n == ap_px).all():
            break
        ap_px = n
    bx = bbox(ap_px)
    np.save('ap_letters.npy', ap_px)
    kw, kv = keyline_width(ap_reg)
    out['ap_mark'] = {
        'bbox_tight': bx, 'bbox_note': '[x0, y0, x1, y1] pixel edges of the AP mark pixels (dE>12 from white), '
                                       'including the parts of the A that cross the frame bands',
        'width': bx[2] - bx[0], 'height': bx[3] - bx[1],
        'center': [round((bx[0] + bx[2]) / 2, 1), round((bx[1] + bx[3]) / 2, 1)],
        'keyline_px': kw, 'keyline_samples': kv,
        'keyline_note': 'the original cuts a white keyline of about this width around the AP where it overlaps the '
                        'frame (left foot of the A over the left side bands, top of the P bowl under the top-right '
                        'inner band); the frame SVG runs its bands continuously underneath, so the AP should carry a '
                        'white outline stroke (or offset path) of this width to reproduce it',
    }
    # ---- text
    tm = text & (DE_W > 12)
    tm[:int(E['U_bot']) + 6] = False  # cyan glow under the bar's centre is not text
    tb = bbox(tm)
    comps = components(tm)
    rr = [(int(np.nonzero(c)[1].min()), int(np.nonzero(c)[1].max()) + 1) for c in comps]
    names = [c for c in TEXT_STR if c != ' ']
    info = {'n_letters_found': len(rr)}
    if len(rr) == len(names):
        # word groups
        groups = {'ALLIANCE ': range(0, 8), 'AI': range(8, 10), ' PARTNERS': range(10, 18)}
        cols = {}
        for g, idx in groups.items():
            m = np.zeros_like(tm)
            for i in idx:
                m |= comps[i]
            x0, x1 = rr[idx[0]][0], rr[idx[-1]][1]
            core = m & kit.erode(m, 1) & (DE_W > 40)
            px = ORIG[core]
            med = np.median(px, 0)
            # horizontal / vertical trend inside the word (gradient check)
            xs = np.nonzero(core)[1]; ys = np.nonzero(core)[0]
            left = np.median(px[xs < np.percentile(xs, 25)], 0); right = np.median(px[xs > np.percentile(xs, 75)], 0)
            top = np.median(px[ys < np.percentile(ys, 25)], 0); bot = np.median(px[ys > np.percentile(ys, 75)], 0)
            nm, ph, dd = kit.nearest_palette(med)
            cols[g] = {
                'hex': kit.rgbhex(med), 'nearest_palette': nm, 'nearest_hex': ph, 'dE': round(dd, 2),
                'left_hex': kit.rgbhex(left), 'right_hex': kit.rgbhex(right), 'top_hex': kit.rgbhex(top),
                'bottom_hex': kit.rgbhex(bot), 'x_range': [int(x0), int(x1)],
                'dE_left_right': round(float(kit.de2000(kit.srgb_to_lab(left), kit.srgb_to_lab(right))), 2)}
        info['word_colors'] = cols
        ink = kit.hexrgb(cols['ALLIANCE ']['hex'])
        # cap height / baseline from flat-topped, flat-bottomed stems: L, L, I (ALLIANCE), I (AI), T, E, N stems
        stem_tops, stem_bots = [], []
        for k in (1, 2, 3, 9, 13):  # L L I | I | T
            x0, x1 = rr[k]
            if k in (1, 2):  # L: use the vertical stem (left third)
                xa, xb = x0 + 1, x0 + max(2, (x1 - x0) // 3)
            elif k == 13:  # T: stem in the middle
                c = (x0 + x1) // 2; xa, xb = c - 2, c + 2
            else:
                xa, xb = x0 + 1, x1 - 1
            ink_k = kit.hexrgb(cols['AI']['hex']) if k == 9 else ink
            lo, hi = int(E['U_bot']) + 2, int(E['L_top']) - 1
            a = alpha_ink(ORIG[lo:hi, xa:xb].mean(1), ink_k)
            t, b = edge_cross(a, lo, hi)
            stem_tops.append(t)
            if k != 13:
                stem_bots.append(b)
        cap_top = float(np.median(stem_tops)); base = float(np.median(stem_bots))
        info['cap_top_y'] = round(cap_top, 2)
        info['baseline_y'] = round(base, 2)
        info['cap_height'] = round(base - cap_top, 2)
        info['stem_tops'] = [round(v, 2) for v in stem_tops]
        info['stem_bottoms'] = [round(v, 2) for v in stem_bots]
        info['montserrat_fit'] = fit_montserrat(tm, tb, base, base - cap_top)
    out['banner_text'] = {'string': TEXT_STR, 'bbox_tight': tb, 'width': tb[2] - tb[0], 'height': tb[3] - tb[1],
                          'center_x': round((tb[0] + tb[2]) / 2, 2), **info,
                          'bbox_note': '[x0, y0, x1, y1] pixel edges of the text pixels (dE>12 from white)'}
    out['banner'] = {'upper_bar_top_inside_y': round(E['U_top'] + 0.5, 3), 'upper_bar_bottom_y': round(E['U_bot'] + 0.5, 3),
                     'lower_bar_top_y': round(E['L_top'] + 0.5, 3), 'lower_bar_bottom_inside_y': round(E['L_botin'] + 0.5, 3),
                     'white_band_between_bars': [round(E['U_bot'] + 0.5, 3), round(E['L_top'] + 0.5, 3)]}
    return out


def measured_stem_ratio(cap_h):
    vals = []
    for (x0, x1) in ((428, 439), (696, 708)):  # the two I stems (ALLIANCE, AI), measured on row 530
        row = ORIG[530, x0 - 3:x1 + 3]
        ink = row[len(row) // 2]
        a = np.clip(((row - 255) @ (ink - 255)) / ((ink - 255) @ (ink - 255)), 0, 1)
        vals.append(float(a.sum()) / cap_h)
    return round(float(np.mean(vals)), 3)


def fit_montserrat(tm, tb, base, cap_h):
    """Best Montserrat weight / size / tracking / position for the banner text: analytic start from the
    measured cap height and ink width, then coordinate descent on the IoU with the text mask."""
    target = tm[tb[1] - 3:tb[3] + 3, tb[0] - 3:tb[2] + 3]
    oy, ox = tb[1] - 3, tb[0] - 3
    hh, ww = target.shape
    n = len(TEXT_STR)

    def score(style, size, trk, x, by):
        ds = kit.text_paths(TEXT_STR, style, size, trk, x - ox, by - oy)
        return kit.iou(kit.raster(ds, ww, hh, ss=2) > 0.5, target)

    per_style = {}
    best = None
    for style in ('SemiBold', 'Bold', 'ExtraBold'):
        ds = kit.text_paths(TEXT_STR, style, 100.0, 0.0, 0.0, 0.0)
        pts = np.vstack([np.array(p) for d in ds for p in kit.flatten(kit.parse_d(d))])
        xmin, xmax = pts[:, 0].min(), pts[:, 0].max()
        dI = kit.text_paths('AI', style, 100.0, 0.0, 0.0, 0.0)[1]
        pI = np.vstack([np.array(p) for p in kit.flatten(kit.parse_d(dI))])
        cap100 = pI[:, 1].max() - pI[:, 1].min()
        size = cap_h / cap100 * 100
        trk = ((tb[2] - tb[0]) - (xmax - xmin) * size / 100) / ((n - 1) * size / 1000)
        prm = [size, trk, tb[0] - xmin * size / 100, base]
        steps = [size * 0.004, 1.0, 0.4, 0.3]
        cur = score(style, *prm)
        for _ in range(4):
            moved = False
            for k in range(4):
                for sgn in (-1, 1):
                    q = list(prm)
                    q[k] += sgn * steps[k]
                    if k == 0:  # keep the ink's left edge in place while the size changes
                        q[2] = prm[2] - xmin * (q[0] - prm[0]) / 100
                    s2 = score(style, *q)
                    if s2 > cur + 1e-5:
                        prm, cur, moved = q, s2, True
            if not moved:
                steps = [v / 2 for v in steps]
        cand = {'style': 'Montserrat ' + style, 'size_px': round(float(prm[0]), 2), 'tracking': round(float(prm[1]), 1),
                'x_origin': round(float(prm[2]), 2), 'baseline_y': round(float(prm[3]), 2), 'iou': round(cur, 4)}
        per_style[style] = {k: v for k, v in cand.items() if k != 'style'}
        if best is None or cur > best['iou']:
            best = dict(cand)
    best['by_weight'] = per_style
    stem = {}
    for st in ('Bold', 'ExtraBold'):
        dI = kit.text_paths('AI', st, 100.0)[1]
        p = np.vstack([np.array(q) for q in kit.flatten(kit.parse_d(dI))])
        stem[st] = round(float((p[:, 0].max() - p[:, 0].min()) / (p[:, 1].max() - p[:, 1].min())), 3)
    best['stem_to_cap_ratio'] = {'montserrat': stem, 'measured_I': measured_stem_ratio(cap_h)}
    best['note'] = ('kit.text_paths(string, style, size, tracking, x_origin, baseline) reproduces the banner text in '
                    '1376x768 space (tracking in Illustrator units, 1/1000 em); the AI-drawn letters are a near '
                    'but not exact Montserrat, so IoU < 1 is expected')
    return best
