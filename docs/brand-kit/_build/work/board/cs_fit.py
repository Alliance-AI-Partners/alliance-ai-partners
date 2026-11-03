"""Clear-space diagram fit (board agent): dashed grid lines, double arrows, corner crosses.
Geometry by Nelder-Mead, colour by least squares through the JPEG 4:2:0 model (thin.fit). Writes cs_fit.json."""
import json
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import thin
from dashes import along, segments

W = kit.WORK / 'board'
LUM = np.array([0.299, 0.587, 0.114])


def dash_pattern(o, c, lo, hi, excl=()):
    """Regular dash pattern (s0, period, dash) from the along-line luma integral (half-max crossings),
    then refined by least squares of a 1-D pulse model against the integral profile."""
    integ, _ = along(o, c, lo, hi, win=3)
    xs_all = np.arange(lo, hi)
    free = np.ones(len(xs_all), bool)
    for e0, e1 in excl:
        free &= ~((xs_all >= e0 - 3) & (xs_all <= e1 + 3))
    plateau = np.percentile(integ[free], 85)
    segs = [s for s in segments(integ, lo, 0.5 * plateau) if 4.5 < s[1] - s[0] < 9.5
            and not any(e0 - 2 <= (s[0] + s[1]) / 2 <= e1 + 2 for e0, e1 in excl)]
    st = np.array([s for s, e in segs]); en = np.array([e for s, e in segs])
    P0 = np.median(np.diff(st)[np.diff(st) < 11])
    k = np.round((st - st[0]) / P0)
    A = np.stack([np.ones_like(k), k], 1)
    (s0, P), *_ = np.linalg.lstsq(A, (st + en) / 2, rcond=None)
    D = float(np.median(en - st))
    s0 = s0 - D / 2
    # 1-D refinement: integ(x) ~ amp * overlap([x, x+1], dashes); masked where other features cross
    xs = np.arange(lo, hi)
    keep = np.ones(len(xs), bool)
    for e0, e1 in excl:
        keep &= ~((xs >= e0 - 3) & (xs <= e1 + 3))
    K0, K1 = int(np.floor((lo - s0) / P)) - 1, int(np.ceil((hi - s0) / P)) + 1

    def model(p):
        s, Pp, Dd = p
        cov = np.zeros(len(xs))
        for kk in range(K0, K1 + 1):
            a, b = s + kk * Pp, s + kk * Pp + Dd
            cov += np.clip(np.minimum(xs + 1, b) - np.maximum(xs, a), 0, 1)
        return cov

    def f(p):
        cov = model(p)[keep]
        y = integ[keep]
        amp = (cov @ y) / max(1e-9, cov @ cov)
        return float(((amp * cov - y) ** 2).mean())
    import textfit as tf
    p, v = tf.nelder_mead(f, np.array([s0, P, D]), [0.3, 0.02, 0.3], 300)
    return [float(x) for x in p], len(segs)


def fit_cross_section(o, c, intervals, w0=1.6):
    """Centre, width and true ink of a dashed line from its dash interiors (list of (a, b) along-line)."""
    res = []
    for a, b in intervals:
        a, b = int(np.ceil(a + 0.8)), int(np.floor(b - 0.8))
        if b - a < 3:
            continue
        if o == 'h':
            box = (a, int(np.floor(c)) - 4, b, int(np.floor(c)) + 5)
            cov = lambda p, box=box, a=a, b=b: thin.rect_cov(a - 2, p[0] - p[1] / 2, b + 2, p[0] + p[1] / 2, box)
        else:
            box = (int(np.floor(c)) - 4, a, int(np.floor(c)) + 5, b)
            cov = lambda p, box=box, a=a, b=b: thin.rect_cov(p[0] - p[1] / 2, a - 2, p[0] + p[1] / 2, b + 2, box)
        res.append((box, cov))
    # joint fit over all intervals: shared centre / width / ink
    def total(p, want_ink=False):
        covs = [cv(p) for box, cv in res]
        # stack all intervals into one tall image for a single least-squares ink
        return covs
    import textfit as tf

    def f(p):
        err, n = 0.0, 0
        inks = []
        for (box, cv) in res:
            ink, r = thin.ls_ink(cv(p), box)
            inks.append(ink)
            err += r ** 2; n += 1
        return np.sqrt(err / n)
    p, v = tf.nelder_mead(f, np.array([c, w0]), [0.2, 0.2], 120)
    inks = np.array([thin.ls_ink(cv(p), box)[0] for box, cv in res])
    return float(p[0]), float(p[1]), np.median(inks, 0), float(v)


def arrow_polys(p, vertical):
    """p = (axis, a, b, w, h, half) : shaft on `axis` from tip a to tip b, shaft width w,
    head length h and head half-width `half` (filled triangles at both ends)."""
    ax, a, b, w, h, half = p
    if vertical:
        shaft = thin.rect(ax - w / 2, a + h * 0.9, ax + w / 2, b - h * 0.9)
        t1 = [(ax, a), (ax + half, a + h), (ax - half, a + h)]
        t2 = [(ax, b), (ax - half, b - h), (ax + half, b - h)]
    else:
        shaft = thin.rect(a + h * 0.9, ax - w / 2, b - h * 0.9, ax + w / 2)
        t1 = [(a, ax), (a + h, ax - half), (a + h, ax + half)]
        t2 = [(b, ax), (b - h, ax + half), (b - h, ax - half)]
    return [shaft, t1, t2]


def cross_polys(p):
    cx, cy, L, w = p
    return [thin.seg_poly(cx - L, cy - L, cx + L, cy + L, w), thin.seg_poly(cx - L, cy + L, cx + L, cy - L, w)]


if __name__ == '__main__':
    out = {}
    # ---- dashed lines
    H = {'cs-h1': 505.65, 'cs-h2': 543.67, 'cs-h3': 671.95, 'cs-h4': 709.65}
    V = {'cs-v1': 715.96, 'cs-v2': 752.70, 'cs-v3': 949.97, 'cs-v4': 987.04}
    # along-line exclusions: crossings with the perpendicular dashed lines, arrows, the mark
    exH = {'cs-h1': [(714, 718), (750, 755), (855, 862), (947, 953), (985, 990)],
           'cs-h2': [(714, 718), (750, 960), (985, 990)],
           'cs-h3': [(714, 718), (750, 960), (985, 990)],
           'cs-h4': [(714, 718), (750, 755), (855, 862), (947, 953), (985, 990)]}
    exV = {'cs-v1': [(503, 508), (541, 547), (598, 606), (669, 675), (707, 712)],
           'cs-v2': [(503, 508), (541, 547), (598, 606), (640, 676), (707, 712)],
           'cs-v3': [(503, 508), (541, 547), (560, 612), (669, 675), (707, 712)],
           'cs-v4': [(503, 508), (541, 547), (598, 606), (669, 675), (707, 712)]}
    for name, c in list(H.items()) + list(V.items()):
        o = 'h' if name in H else 'v'
        lo, hi = (705, 1000) if o == 'h' else (495, 720)
        excl = exH[name] if o == 'h' else exV[name]
        (s0, P, D), n = dash_pattern(o, c, lo, hi, excl)
        # dash interiors that are clear of crossings for the cross-section fit
        ints = []
        for kk in range(-2, 40):
            a, b = s0 + kk * P, s0 + kk * P + D
            if a < lo + 2 or b > hi - 2:
                continue
            if any(not (b < e0 - 2 or a > e1 + 2) for e0, e1 in excl):
                continue
            ints.append((a, b))
        cc, w, ink, r = fit_cross_section(o, c, ints)
        out[name] = {"orient": o, "center": cc, "width": w, "s0": s0, "period": P, "dash": D, "gap": P - D,
                     "ink": ink.tolist(), "rms": r, "n_dashes_used": len(ints)}
        print('%-6s %s c=%.2f w=%.2f s0=%.2f P=%.3f D=%.2f gap=%.2f ink=%s %s rms=%.2f (n=%d)' % (
            name, o, cc, w, s0, P, D, P - D, ink.round(1), kit.rgbhex(np.clip(ink, 0, 255)), r, len(ints)), flush=True)
    # ---- arrows (tips touch the dashed lines)
    arrows = {'cs-arrow-top': (True, (858.3, 505.6, 543.6, 1.6, 5.0, 3.2), (849, 501, 868, 548)),
              'cs-arrow-bottom': (True, (858.3, 671.9, 709.6, 1.6, 5.0, 3.2), (849, 667, 868, 714)),
              'cs-arrow-left': (False, (602.4, 716.0, 752.7, 1.6, 5.0, 3.2), (711, 594, 757, 611)),
              'cs-arrow-right': (False, (602.4, 950.0, 987.0, 1.6, 5.0, 3.2), (945, 594, 992, 611))}
    for name, (vert, p0, box) in arrows.items():
        # mask out the dashed lines the tips touch (their bands) from the residual
        x0, y0, x1, y1 = box
        mask = np.ones((y1 - y0, x1 - x0), bool)
        for d in (H if vert else V).values():
            if vert:
                r = int(np.floor(d)) - y0
                mask[max(0, r - 1):r + 2] = False
            else:
                cidx = int(np.floor(d)) - x0
                mask[:, max(0, cidx - 1):cidx + 2] = False
        build = lambda p, vert=vert: arrow_polys(p, vert)
        p, ink, r = thin.fit(build, p0, [0.3, 0.4, 0.4, 0.3, 0.6, 0.4], box, mask=mask, iters=250)
        out[name] = {"vertical": vert, "axis": p[0], "tip_a": p[1], "tip_b": p[2], "shaft_width": p[3],
                     "head_length": p[4], "head_half_width": p[5], "ink": ink.tolist(), "rms": r}
        print('%-16s axis=%.2f tips=%.2f..%.2f w=%.2f head L=%.2f half=%.2f ink=%s %s rms=%.2f' % (
            name, p[0], p[1], p[2], p[3], p[4], p[5], ink.round(1), kit.rgbhex(np.clip(ink, 0, 255)), r), flush=True)
    # ---- corner crosses (centred in the corner cells)
    crosses = {'cs-cross-tl': (734.3, 524.7), 'cs-cross-tr': (968.5, 524.7),
               'cs-cross-bl': (734.3, 690.8), 'cs-cross-br': (968.5, 690.8)}
    for name, (cx, cy) in crosses.items():
        box = (int(cx) - 14, int(cy) - 14, int(cx) + 15, int(cy) + 15)
        p, ink, r = thin.fit(cross_polys, (cx, cy, 8.5, 1.5), [0.4, 0.4, 0.5, 0.3], box, iters=200)
        out[name] = {"cx": p[0], "cy": p[1], "half": p[2], "width": p[3], "ink": ink.tolist(), "rms": r}
        print('%-12s c=(%.2f, %.2f) half=%.2f w=%.2f ink=%s %s rms=%.2f' % (
            name, p[0], p[1], p[2], p[3], ink.round(1), kit.rgbhex(np.clip(ink, 0, 255)), r), flush=True)
    (W / 'cs_fit.json').write_text(json.dumps(out, indent=1))
