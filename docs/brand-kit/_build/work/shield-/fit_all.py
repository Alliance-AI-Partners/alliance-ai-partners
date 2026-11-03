# Fit every frame boundary of original 17 (both halves mirrored onto the left about AX) -> edges.json
import json
from fit_edges import *


def line_fit(name, y686, xr_L, xr_R, m0=-0.308, excl_R=()):
    """Top-edge straight boundary y = m x + c (left half)."""
    c0 = np.array([m0, y686 - m0 * 686])
    P = []
    for side, xr in (('L', xr_L), ('R', xr_R)):
        xs = np.arange(xr[0], xr[1] + 1e-9, 1.0)
        if side == 'R':
            xs = np.array([x for x in xs if not any(a <= x <= b for a, b in excl_R)])
        Q = refine_y_of_x(c0, xs, side, down=True)
        P.append(np.c_[Q, np.full(len(Q), 0 if side == 'L' else 1)])
    P = np.vstack(P)
    c, rms, mx, nk, n = robust_polyfit(P[:, 0], P[:, 1], 1)
    r = P[:, 1] - np.polyval(c, P[:, 0])
    asym = {s: round(float(r[P[:, 2] == i].mean()), 3) for i, s in enumerate('LR')}
    print(f'{name:8s} slope {c[0]:.5f} y@686 {np.polyval(c, 686):.3f} rms {rms:.3f} max {mx:.3f} n {nk}/{n} {asym}')
    return {'kind': 'y_of_x', 'coef': c.tolist(), 'rms': rms, 'max': mx, 'n': nk, 'side_resid': asym}


E = {'axis': AX}
E['T_o'] = line_fit('T_o', 50.58, (384, 684), (384, 684))
E['T_b1'] = line_fit('T_b1', 75.8, (406, 684), (406, 684))
E['T_b2'] = line_fit('T_b2', 82.74, (412, 684), (412, 684))
E['T_b3'] = line_fit('T_b3', 105.85, (432, 684), (432, 684), excl_R=[(425, 575)])

rough_side = {
    'S_o': [(170, 375.6), (200, 374.6), (250, 375.5), (300, 379.6), (350, 387.5), (400, 398.2), (450, 413.1)],
    'S_b1': [(180, 398.7), (220, 398.4), (260, 399.6), (300, 403.1), (350, 411.0), (400, 422.5), (440, 434.6)],
    'S_b2': [(180, 405.6), (220, 404.6), (260, 406.3), (300, 410.0), (350, 417.7), (400, 428.8), (450, 444.8), (470, 452.7)],
    'S_b3': [(190, 426.5), (220, 425.6), (260, 427.5), (300, 431), (350, 439.1), (400, 450.8), (450, 467.6), (470, 475.6)],
}
ranges_side = {
    'S_o': {'L': [(160, 462)], 'R': [(160, 462)]},
    'S_b1': {'L': [(172, 430)], 'R': [(172, 468)]},
    'S_b2': {'L': [(176, 330)], 'R': [(176, 468)]},
    'S_b3': {'L': [(192, 390)], 'R': [(192, 222), (302, 468)]},
}
for k in rough_side:
    E[k], _ = fit_side(k, rough_side[k], ranges_side[k], deg=3)

rough_low = {
    'D_o': [(483, 592.5), (490, 599.6), (500, 609.4), (520, 626.5), (540, 642.5), (560, 656.6), (580, 669.6), (600, 681.5), (620, 692.6), (640, 703), (660, 712.4), (680, 720.9), (686, 723.5)],
    'D_b1': [(520, 595.46), (530, 603.56), (540, 612.44), (550, 620.41), (560, 627.5), (570, 634.48), (580, 641.48), (590, 647.53), (600, 654.4), (610, 659.57), (620, 665.49), (630, 670.59), (640, 676.39), (650, 680.75), (660, 685.52), (670, 690.46), (680, 694.52), (686, 697.48)],
    'D_b2': [(520, 586.5), (530, 595.49), (540, 603.54), (550, 611.54), (560, 619.49), (570, 626.51), (580, 633.51), (590, 639.62), (600, 646.49), (610, 652.44), (620, 657.89), (630, 663.5), (640, 668.54), (650, 673.56), (660, 678.53), (670, 683.46), (680, 687.54), (686, 690.45)],
    'D_b3': [(560, 592.31), (570, 599.97), (580, 607.48), (590, 614.53), (600, 621.34), (610, 627.52), (620, 633.5), (630, 639.44), (640, 644.52), (650, 649.55), (660, 654.53), (670, 659.51), (680, 663.6), (686, 666.5)],
    'C_t': [(600, 602.41), (610, 606.51), (620, 610.51), (630, 614.33), (640, 617.58), (650, 621.42), (660, 624.56), (670, 627.56), (680, 630.49), (686, 632.18)],
    'C_b': [(610, 612.49), (620, 618.67), (630, 624.61), (640, 630.45), (650, 635.53), (660, 640.62), (670, 645.54), (680, 650.41), (686, 652.73)],
}
ranges_low = {
    'D_o': {'L': [(488, 684)], 'R': [(488, 684)]},
    'D_b1': {'L': [(512, 684)], 'R': [(512, 684)]},
    'D_b2': {'L': [(512, 610)], 'R': [(512, 684)]},
    'D_b3': {'L': [(561, 684)], 'R': [(561, 684)]},
    'C_t': {'L': [(598, 684)], 'R': [(598, 684)]},
    'C_b': {'L': [(604, 684)], 'R': [(604, 684)]},
}
for k in rough_low:
    E[k], _ = fit_lowcurve(k, rough_low[k], ranges_low[k], deg=3, down=(k != 'C_t'))

# banner: horizontal edges and wing lines
def hfit(name, y0, xr, down):
    pts = []
    for x in np.arange(xr[0], xr[1] + 1e-9, 2.0):
        q, A, B = edge_pos((x, y0), (0, 1.0) if down else (0, -1.0), w=3.0, gap=1.4)
        if q is not None:
            pts.append(q[1])
    v = float(np.median(pts))
    print(f'{name:8s} y = {v:.3f} (n {len(pts)}, iqr {np.percentile(pts, 75) - np.percentile(pts, 25):.3f})')
    return v

E['U_top'] = hfit('U_top', 470.6, (436, 940), True)
E['U_bot'] = hfit('U_bot', 490.4, (312, 1063), False)
E['L_top'] = hfit('L_top', 569.75, (340, 1035), True)
E['L_botin'] = hfit('L_botin', 589.37, (562, 813), False)


def wing(name, c0, xr, down):
    P = []
    for side in 'LR':
        Q = refine_y_of_x(c0, np.arange(xr[0], xr[1] + 1e-9, 1.0), side, down=down)
        P.append(np.c_[Q, np.full(len(Q), 0 if side == 'L' else 1)])
    P = np.vstack(P)
    c, rms, mx, nk, n = robust_polyfit(P[:, 0], P[:, 1], 1)
    print(f'{name:8s} slope {c[0]:.5f} rms {rms:.3f} max {mx:.3f} n {nk}/{n}')
    return {'kind': 'y_of_x', 'coef': c.tolist(), 'rms': rms, 'max': mx, 'n': nk}

m = (464.5 - 490.4) / (417.7 - 306)
E['UW'] = wing('UW', np.array([m, 490.4 - m * 306]), (316, 410), True)
m2 = (592.5 - 569.75) / (483 - 331)
E['LW'] = wing('LW', np.array([m2, 569.75 - m2 * 331]), (342, 476), False)

json.dump(E, open('edges.json', 'w'), indent=1)
print('saved edges.json')
