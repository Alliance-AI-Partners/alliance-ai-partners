"""hero-04, stage 2: sub-pixel straight-edge fits on original 04 (A legs, tops, baseline, P stem, P bar
edges, ribbon flats), by the area method on 2-colour profiles across each edge (lines.py), robust LSQ.
Writes lines04.json: x = a*y + b for near-vertical edges, y = a*x + b for near-horizontal ones."""
import json
import sys
import numpy as np

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from lines import row_edges, col_edges, fit_line, edge_pos
from seg04 import NAMES, W4

L = {n: k for k, n in enumerate(NAMES)}
bg, lo, lb, ri, ro = L['bg'], L['a-left-outer'], L['a-left-bevel'], L['a-right-inner'], L['a-right-outer']
U, Lo, fold, P = L['ribbon-upper'], L['ribbon-lower'], L['p-bowl-fold'], L['p-bowl']

# name: [(left labels, right labels, (y0, y1))]  -> x = a*y + b
ROWS = {
    'LL_outer': [([bg], [lo], (262, 402)), ([bg], [lo], (484, 507))],
    'LL_crease': [([lo], [lb], (262, 402)), ([lo], [lb], (478, 507))],
    'LL_inner': [([lb], [bg], (322, 386)), ([lb], [ri, ro], (266, 316)), ([lb], [bg], (466, 507))],
    'RL_inner': [([bg], [ri], (326, 386)), ([bg], [ri], (462, 507))],
    'RL_internal': [([ri], [ro], (296, 372)), ([ri], [ro], (452, 507))],
    'RL_outer': [([ro], [bg], (262, 326)), ([ro], [bg, P], (436, 507))],
    'P_left': [([bg], [U], (262, 336))],
    # the P stem's right side is three runs in 04, not one line: the cyan ribbon's edge (y 309-345, bright
    # rim plus glow), the P body beside the counter (too dark to measure, left free) and the lower stem
    'stem_right': [([P], [bg], (424, 462))],
    'stem_right_hi': [([Lo], [bg], (314, 343))],
    'stem_mid': [([U], [Lo], (290, 334))],          # ribbon-front-stem | ribbon-back, inside the stem
    'stem_diag': [([Lo], [fold], (288, 307))],      # 45 deg mitre where the ribbon turns into the fold
}
# name: [(top labels, bottom labels, (x0, x1))]  -> y = a*x + b
COLS = {
    'A_top': [([bg], [lo, lb], (293, 345))],
    'P_top': [([bg], [U], (402, 470))],
    'L_base': [([lo, lb], [bg], (183, 238))],
    'R_base': [([ri, ro], [bg], (400, 465))],
    'fold_top': [([U], [fold], (428, 505))],
    'counter_top': [([fold], [bg], (452, 500))],
    'counter_bottom': [([bg], [P], (452, 498))],
    'bowl_bottom': [([P], [bg], (452, 504))],
    'crossbar_top': [([bg], [U], (262, 318))],
    'crossbar_mid': [([U], [Lo], (270, 318))],
    'crossbar_bottom': [([Lo], [bg], (262, 318))],
}


def crease_edges(rgb, lab, xr, yr=(390, 410), half=6):
    """horizontal colour edge inside the P label (the P bar's crease): strongest step per column."""
    pts = []
    for x in range(*xr):
        col = rgb[:, x].astype(float)
        best = None
        for y in range(yr[0] + half, yr[1] - half):
            if not (lab[y - half:y + half, x] == P).all():
                continue
            pos, c = edge_pos(col[y - half:y + half])
            if pos is not None and c > 6 and abs(pos - half) < 1.5 and (best is None or c > best[1]):
                best = (y - half + pos, c)
        if best:
            pts.append((x + 0.5, best[0]))
    return pts


def fit_all(rgb, lab):
    out = {}
    for name, parts in ROWS.items():
        pts = []
        for left, right, yr in parts:
            pts += row_edges(rgb, lab, left, right, yr)
        a, b, rms, n, r = fit_line(pts, 'y')
        p = np.asarray(pts)
        bands = [(int(y0), round(float(np.mean(r[(p[:, 1] >= y0) & (p[:, 1] < y0 + 30)])), 2))
                 for y0 in range(260, 510, 30) if ((p[:, 1] >= y0) & (p[:, 1] < y0 + 30)).any()]
        out[name] = {'a': a, 'b': b, 'rms': rms, 'n': n, 'N': len(pts), 'bands': bands}
        print(f'{name:15s} x = {a:.5f}*y + {b:.3f}  rms={rms:.3f} n={n}/{len(pts)}  x@262={a*262+b:.2f} x@508={a*508+b:.2f}  {bands}')
    cols = dict(COLS)
    for name, parts in cols.items():
        pts = []
        for top, bot, xr in parts:
            pts += col_edges(rgb, lab, top, bot, xr)
        a, b, rms, n, r = fit_line(pts, 'x')
        xm = float(np.mean(np.asarray(pts)[:, 0]))
        out[name] = {'a': a, 'b': b, 'rms': rms, 'n': n, 'N': len(pts), 'y_mid': a * xm + b, 'x_mid': xm}
        print(f'{name:15s} y = {a:.5f}*x + {b:.3f}  rms={rms:.3f} n={n}/{len(pts)}  y@mid={a*xm+b:.3f} (x {xm:.0f})')
    pts = crease_edges(rgb, lab, (452, 522))
    a, b, rms, n, r = fit_line(pts, 'x')
    xm = float(np.mean(np.asarray(pts)[:, 0]))
    out['crease'] = {'a': a, 'b': b, 'rms': rms, 'n': n, 'N': len(pts), 'y_mid': a * xm + b, 'x_mid': xm}
    print(f'{"crease":15s} y = {a:.5f}*x + {b:.3f}  rms={rms:.3f} n={n}/{len(pts)}  y@mid={a*xm+b:.3f}')
    return out


def final_lines(raw):
    """The line set used by the build. Designed flats of the letters (tops, baseline, P stem, P bars) are
    snapped to exact horizontals / verticals (every fitted tilt there is < 0.2 px over its run and the A and
    P tops agree to 0.02 px, so the tilt is measurement bias); the A legs and the ribbon's straight runs on
    the crossbar keep their fitted tilt. Artificial cuts (seam_stem, under_end, top_split_x) are the master's
    cuts placed into 04 by the similarity transform."""
    ln = {k: {'a': raw[k]['a'], 'b': raw[k]['b']} for k in
          ('LL_outer', 'LL_crease', 'LL_inner', 'RL_inner', 'RL_internal', 'RL_outer', 'stem_mid', 'stem_diag')}
    ymid = lambda k: raw[k]['y_mid']
    xm = lambda k, y: raw[k]['a'] * y + raw[k]['b']
    ln['top'] = (raw['A_top']['y_mid'] * raw['A_top']['n'] + raw['P_top']['y_mid'] * raw['P_top']['n']) / (raw['A_top']['n'] + raw['P_top']['n'])
    ln['base'] = (raw['L_base']['y_mid'] * raw['L_base']['n'] + raw['R_base']['y_mid'] * raw['R_base']['n']) / (raw['L_base']['n'] + raw['R_base']['n'])
    ln['P_left'] = xm('P_left', 300)
    ln['stem_right'] = xm('stem_right', 443)
    ln['stem_right_hi'] = xm('stem_right_hi', 328)
    for k in ('fold_top', 'counter_top', 'counter_bottom', 'crease', 'bowl_bottom', 'crossbar_mid'):
        ln[k] = ymid(k)
    for k in ('crossbar_top', 'crossbar_bottom'):    # y = ah * x + bh
        ln[k] = {'ah': raw[k]['a'], 'bh': raw[k]['b']}
    s, tx, ty = 0.6045, 73.321, 74.123
    ln['seam_stem'] = 480.0 * s + ty
    ln['under_end'] = 760.0 * s + tx
    ln['top_split_x'] = 640.0 * s + tx
    return ln


if __name__ == '__main__':
    rgb = kit.load('04')
    lab = np.load(W4 / 'labels04.npy')
    out = fit_all(rgb, lab)
    json.dump(out, open(W4 / 'lines04_raw.json', 'w'), indent=1)
    ln = final_lines(out)
    json.dump(ln, open(W4 / 'lines04.json', 'w'), indent=1)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in ln.items()})
