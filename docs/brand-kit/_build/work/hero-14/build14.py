"""hero-14, stage 1: soft face masks from original 14 -> traced raw outlines; legs are exact polygons
from the measured lines (with the hidden kink under the ribbon where 14's leg edges are not collinear).
Writes work/hero-14/F_faces14.npy, F_bg14.npy, geo_raw14.json. Stage 2 is make14.py."""
import json
import numpy as np
from common import kit, W14, FACES, POLY, DELTA, H, Wd, REGION_Y1
from seg14 import NAMES
from soft import memberships
from build_hero import soft_half, stack_masks, trace_face, poly_d

L = {n: k for k, n in enumerate(NAMES)}

# invisible cuts (same roles as in the 06 master; positions chosen on 14's own geometry)
CUTS = {'top_split_x': 605.0,   # P top band | stem: anywhere between the stem's right edge (559) and the fold tip sliver (680)
        'seam_stem': 433.7,     # ribbon front stem | ribbon front (the master's cut mapped into 14)
        'under_end': 680.0}     # P under face ends where 14's crease fades out (x ~ 670-690)

# kinks of the leg edges: (y on the upper line, y on the lower line), both inside the run where the
# ribbon covers that edge (label scan along each line: LL_crease 495-558, LL_inner 489-551,
# RL_inner 479-533, RL_internal 458-514, RL_outer 423-490)
KINK = {'LL_crease': (512, 541), 'LL_inner': (505, 535), 'RL_inner': (493, 519),
        'RL_internal': (472, 500), 'RL_outer': (440, 473)}


def lines():
    return json.load(open(W14 / 'lines14.json'))


def xof(ln, name, y, shift=0.0):
    l = ln[name]
    return l['a'] * y + l['b'] + shift


def edge_poly(ln, e, y_top, y_bot, shift=0.0):
    """vertices of leg edge e (x = a*y + b lines, upper/lower + kink) from y_top down to y_bot"""
    if e == 'LL_outer':
        return [(xof(ln, e, y_top, shift), y_top), (xof(ln, e, y_bot, shift), y_bot)]
    ya, yb = KINK[e]
    pts = [(xof(ln, e + '_u', y_top, shift), y_top)]
    if y_top < ya:
        pts.append((xof(ln, e + '_u', ya, shift), ya))
    if y_bot > yb:
        pts.append((xof(ln, e + '_l', yb, shift), yb))
    pts.append((xof(ln, e + '_l' if y_bot > yb else e + '_u', y_bot, shift), y_bot))
    return pts


def meet_xy(l1, l2):
    """intersection of x = a1 y + b1 and x = a2 y + b2"""
    y = (l2[1] - l1[1]) / (l1[0] - l2[0])
    return l1[0] * y + l1[1], y


def leg_polys(ln, delta=DELTA):
    top, base = ln['top']['c'], ln['base']['c']
    ab = lambda n, s=0.0: (ln[n]['a'], ln[n]['b'] + s)
    out = {}
    # left leg: outer stripe over the bevel
    out['a-left-outer'] = edge_poly(ln, 'LL_crease', top, base) + edge_poly(ln, 'LL_outer', top, base)[::-1]
    # bevel: its left edge reaches delta under the outer stripe
    out['a-left-bevel'] = edge_poly(ln, 'LL_inner', top, base) + edge_poly(ln, 'LL_crease', top, base, -delta)[::-1]
    # right leg, inner stripe: under the bevel (clipped by LL_inner shifted delta to the left)
    x1, y1 = meet_xy(ab('RL_inner_u'), ab('LL_inner_u', -delta))
    x2, y2 = meet_xy(ab('RL_internal_u'), ab('LL_inner_u', -delta))
    out['a-right-inner'] = [(x1, y1), (x2, y2)] + edge_poly(ln, 'RL_internal', y2, base)[1:] + edge_poly(ln, 'RL_inner', y1, base)[::-1][:-1]
    # right leg, outer stripe: under the inner stripe (RL_internal - delta) and under the bevel
    x3, y3 = meet_xy(ab('RL_internal_u', -delta), ab('LL_inner_u', -delta))
    xt = xof(ln, 'LL_inner_u', top, -delta)
    out['a-right-outer'] = ([(xt, top)] + edge_poly(ln, 'RL_outer', top, base)
                            + edge_poly(ln, 'RL_internal', y3, base, -delta)[::-1])
    return out


# The ribbon's upper band runs out as a 1-4 px strip along the A's outer edge down to y ~584, where its
# colour (#2875A1) is close to the lower band's and the watershed gives the strip to the lower band.
# Its boundary is measured instead: along the normal of the band boundary (edges.normal_edges) down to
# y 564, then per row from the G-channel step between the strip and the lower band's dark rim (it reads
# the boundary while the strip is >= 1.7 px wide); the strip ends on the outer edge at y 584.
TIP_CURVE = [(360.0, 521.42), (350.87, 522.83), (341.86, 525.14), (332.9, 528.09), (323.97, 531.7), (314.8, 536.28),
             (305.71, 542.56), (296.68, 550.24), (288.14, 559.29), (285.59, 562.5), (282.59, 566.5), (279.9, 570.5),
             (277.41, 574.5), (274.94, 578.5), (273.88, 580.5)]


def fix_tip(M, ln):
    from build_hero import side_dist
    U, Lw = L['ribbon-upper'], L['ribbon-lower']
    tip_y = 584.0
    tip = (ln['LL_outer']['a'] * tip_y + ln['LL_outer']['b'], tip_y)
    pts = np.array(TIP_CURVE + [tip, (tip[0] - 4.0, tip_y + 4.0)])
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    t = np.linspace(0, s[-1], 800)
    curve = np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], 1)
    ys, xs = np.nonzero(M[U] + M[Lw] > 1e-3)
    sel = (ys >= 515) & (ys <= 592) & (xs < 362)
    ys, xs = ys[sel], xs[sel]
    sd = side_dist(curve, xs, ys)
    keep = np.abs(sd) < 6
    ys, xs, sd = ys[keep], xs[keep], sd[keep]
    tot = M[U, ys, xs] + M[Lw, ys, xs]
    up = 0.5 + sd  # the upper band lies on the positive side of the curve as it runs toward the tip
    M[U, ys, xs] = tot * np.clip(up, 0, 1)
    M[Lw, ys, xs] = tot - M[U, ys, xs]
    return M


# Where the ribbon's two bands swap tones over the crossbar (x ~444-468) their boundary has almost no
# contrast (5-16 RGB) and the watershed edge wanders. The boundary is measured along its normal where it
# is clear on both sides (x 420-442 and 470-496, contrast >= 20) and bridged by the cubic y(x) through
# those points.
SWAP_GUESS = [(420.0, 520.38), (430.0, 520.46), (440.0, 520.42), (470.0, 515.99), (480.0, 512.82), (488.0, 509.19), (496.0, 504.8)]


def fix_swap(M, rgb):
    from edges import normal_edges
    U, Lw = L['ribbon-upper'], L['ribbon-lower']
    g = np.array(SWAP_GUESS)
    xs = np.concatenate([np.arange(420, 442.1, 1.0), np.arange(470, 496.1, 1.0)])
    q = np.stack([xs, np.interp(xs, g[:, 0], g[:, 1])], 1)
    e, c = normal_edges(rgb, q, half=4, step=0.25, cmin=20)
    ok = np.isfinite(e).all(1)
    coef = np.polyfit(e[ok, 0], e[ok, 1], 3)
    ys, xs = np.nonzero(M[U] + M[Lw] > 1e-3)
    sel = (xs >= 436) & (xs <= 478) & (ys >= 500) & (ys <= 532)
    ys, xs = ys[sel], xs[sel]
    xc = xs + 0.5
    d = (np.polyval(coef, xc) - (ys + 0.5)) / np.sqrt(1 + np.polyval(np.polyder(coef), xc) ** 2)  # > 0: above (upper band)
    tot = M[U, ys, xs] + M[Lw, ys, xs]
    M[U, ys, xs] = tot * np.clip(0.5 + d, 0, 1)
    M[Lw, ys, xs] = tot - M[U, ys, xs]
    resid = e[ok, 1] - np.polyval(coef, e[ok, 0])
    print('swap bridge: cubic through %d boundary points, rms %.3f px' % (ok.sum(), np.sqrt(np.mean(resid ** 2))))
    return M


# The bowl's dark lower face reaches up between the lower band and the counter's left edge as a wedge
# whose tip (x 588-590.7, y 410-417) is under 2 px wide; the watershed hands that tip to the band.
# Boundary measured along its normal (edges.normal_edges) from y 417 to 446; above that it runs straight
# on to the counter edge (slope of the measured part), meeting it at y ~410.
WEDGE = [(588.74, 417.0), (587.67, 420.86), (586.93, 424.79), (586.06, 428.7), (585.1, 432.58), (584.09, 436.45),
         (582.99, 440.32), (581.82, 444.15), (581.13, 446.03)]


def fix_wedge(M, ln):
    from build_hero import side_dist
    Lw, Pl = L['ribbon-lower'], L['p-bowl-lower']
    p = np.array(WEDGE)
    d = (p[0] - p[2]) / np.hypot(*(p[0] - p[2]))
    x_edge = ln['stem_right']['c']
    t = (x_edge + 2.0 - p[0, 0]) / d[0]
    pts = np.vstack([p[0] + t * d, p])[::-1]  # run up the boundary, out past the counter edge
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    tt = np.linspace(0, s[-1], 400)
    curve = np.stack([np.interp(tt, s, pts[:, 0]), np.interp(tt, s, pts[:, 1])], 1)
    ys, xs = np.nonzero(M[Lw] + M[Pl] > 1e-3)
    sel = (xs >= 576) & (xs <= 592) & (ys >= 402) & (ys <= 446)
    ys, xs = ys[sel], xs[sel]
    sd = side_dist(curve, xs, ys)
    keep = np.abs(sd) < 4
    ys, xs, sd = ys[keep], xs[keep], sd[keep]
    tot = M[Lw, ys, xs] + M[Pl, ys, xs]
    M[Pl, ys, xs] = tot * np.clip(0.5 + sd, 0, 1)   # the wedge lies on the positive side running upward
    M[Lw, ys, xs] = tot - M[Pl, ys, xs]
    return M, curve


def face_memberships(rgb, lab, ln):
    M = memberships(rgb, lab, len(NAMES))
    M = fix_tip(M, ln)
    M = fix_swap(M, rgb)
    M, _ = fix_wedge(M, ln)
    yy, xx = np.mgrid[0:H, 0:Wd] + 0.5
    F = {}
    U = M[L['ribbon-upper']]
    top = np.maximum(soft_half(xx, yy, 0, -1, ln['fold_top']['c']), soft_half(xx, yy, 1, 0, -CUTS['top_split_x']))
    low = soft_half(xx, yy, 0, 1, -CUTS['seam_stem'])
    F['p-bowl-top'] = U * top
    F['ribbon-front-stem'] = U * (1 - top) * (1 - low)
    F['ribbon-front'] = U * (1 - top) * low
    F['ribbon-back'] = M[L['ribbon-lower']]
    F['p-bowl-fold'] = M[L['p-bowl-fold']]
    P = M[L['p-bowl-lower']] + M[L['p-bowl-under']] + M[L['p-stem']]
    s = soft_half(xx, yy, 0, 1, -ln['crease']['c']) * soft_half(xx, yy, -1, 0, CUTS['under_end'])
    F['p-bowl-under'] = P * s
    F['p-bowl-lower'] = P * (1 - s)
    for n in POLY:
        F[n] = M[L[n]]
    F['bg'] = M[L['bg']]
    for k in F:
        F[k][REGION_Y1:] = 0 if k != 'bg' else 1
    return F, M


if __name__ == '__main__':
    rgb = kit.load('14').astype(float)
    lab = np.load(W14 / 'labels14.npy')
    ln = lines()
    F, M = face_memberships(rgb, lab, ln)
    np.save(W14 / 'F_faces14.npy', np.stack([F[n] for n in FACES]).astype(np.float32))
    np.save(W14 / 'F_bg14.npy', F['bg'].astype(np.float32))
    masks = stack_masks(F, FACES)
    polys = leg_polys(ln)
    geo = {'silhouette': trace_face(1 - F['bg'])}
    for n in FACES:
        geo[n] = poly_d(polys[n]) if n in POLY else trace_face(masks[n])
        print(n, 'segments', geo[n].count('C') + geo[n].count('L'))
    json.dump({'geo': geo, 'cuts': CUTS, 'kinks': KINK}, open(W14 / 'geo_raw14.json', 'w'), indent=1)
