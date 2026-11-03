"""Sub-pixel straight-edge fits on original 14 (work/ap-/lines.py method: area method on the two-colour
unmixing profile per scanline, robust LSQ). Every straight edge of the mark is measured on its own
visible run(s):

- A legs: in 14 the legs are not one straight line each across the ribbon: the right leg below the
  ribbon is rotated ~0.6 deg and shifted ~2.5 px against its part above it, the left leg's inner edge
  and crease are shifted ~1.4 px. So every leg edge except the left leg's outer edge gets an upper and
  a lower line; the corner joining them is placed where the ribbon covers that edge (build14.py).
- edges that measure within 0.15 px of axis-aligned over their run are set exactly horizontal/vertical
  at their measured position (top, base, P stem, counter, fold top, bowl bottom, crossbar runs).

Writes work/hero-14/lines14.json: {name: {'kind': 'xy'|'h'|'v'|'pd', ..., 'span': [lo, hi], 'rms', 'n'}}
 xy: x = a*y + b (span in y); h: y = c (span in x); v: x = c (span in y); pd: point + direction."""
import json
import numpy as np
from common import kit, W14
from seg14 import NAMES
from lines import row_edges, col_edges, fit_line
from edges import normal_edges, seg_points, fit_line_tls, step_pos

L = {n: k for k, n in enumerate(NAMES)}


def rows_fit(rgb, lab, parts):
    pts = []
    for left, right, yr in parts:
        pts += row_edges(rgb, lab, [L[n] for n in left], [L[n] for n in right], yr)
    a, b, rms, n, r = fit_line(pts, 'y')
    return a, b, rms, n, len(pts), np.asarray(pts)


def cols_fit(rgb, lab, top, bottom, xr):
    pts = col_edges(rgb, lab, [L[n] for n in top], [L[n] for n in bottom], xr)
    a, b, rms, n, r = fit_line(pts, 'x')
    return a, b, rms, n, len(pts), np.asarray(pts)


def crease_pts(rgb, xs, y_split=478):
    """the bowl's lower/under crease is a sharp one-row step; label-free profile of rows y_split-4 .. y_split+3"""
    pts = []
    for x in xs:
        prof = rgb[y_split - 4:y_split + 4, x].astype(float)
        pos, c = step_pos(prof, 3)
        if pos is not None and c >= 20:
            pts.append((x + 0.5, y_split - 4 + pos))
    return np.asarray(pts)


SB = ['bg']
LEGS = {   # name: row specs (left labels, right labels, (y0, y1)); span = y range the line is used on
    'LL_outer': ([(SB, ['a-left-outer'], (308, 606))], (303, 612)),
    'LL_crease_u': ([(['a-left-outer'], ['a-left-bevel'], (310, 495))], (303, 500)),
    'LL_crease_l': ([(['a-left-outer'], ['a-left-bevel'], (555, 606))], (548, 612)),
    'LL_inner_u': ([(['a-left-bevel'], ['a-right-inner', 'a-right-outer'], (318, 380)), (['a-left-bevel'], SB, (380, 495))], (303, 500)),
    'LL_inner_l': ([(['a-left-bevel'], SB, (545, 606))], (540, 612)),
    'RL_inner_u': ([(SB, ['a-right-inner'], (384, 482))], (375, 486)),
    'RL_inner_l': ([(SB, ['a-right-inner'], (530, 606))], (525, 612)),
    'RL_internal_u': ([(['a-right-inner'], ['a-right-outer'], (348, 448))], (335, 462)),
    'RL_internal_l': ([(['a-right-inner'], ['a-right-outer'], (520, 606))], (515, 612)),
    'RL_outer_u': ([(['a-right-outer'], SB, (312, 420))], (303, 428)),
    'RL_outer_l': ([(['a-right-outer'], SB + ['p-stem'], (512, 546)), (['a-right-outer'], SB, (556, 606))], (505, 612)),
}
PL = ['p-bowl-lower', 'p-bowl-under', 'p-stem']

if __name__ == '__main__':
    rgb = kit.load('14')
    lab = np.load(W14 / 'labels14.npy')
    out = {}
    for name, (parts, span) in LEGS.items():
        a, b, rms, n, N, pts = rows_fit(rgb, lab, parts)
        if name == 'LL_crease_l':
            # low-contrast crease, short run: its free slope is not determined (rms 0.5 px over 50 px), so it
            # keeps the upper crease's slope and only its offset (+1 px, s.e. 0.08) is measured
            a = out['LL_crease_u']['a']
            r = pts[:, 0] - a * pts[:, 1]
            keep = np.abs(r - np.median(r)) < 1.5
            b = float(r[keep].mean()); rms = float((r[keep] - b).std()); n = int(keep.sum())
        out[name] = {'kind': 'xy', 'a': a, 'b': b, 'span': list(span), 'rms': round(rms, 3), 'n': n,
                     'angle_deg': round(float(np.degrees(np.arctan(a))), 3)}
        print(f'{name:14s} x = {a:+.5f} y + {b:8.3f}  ({out[name]["angle_deg"]:+.2f} deg)  rms {rms:.3f}  n {n}/{N}')
    # near-axis edges: fit, then set exactly axis-aligned at the run's mean position if the drift is < 0.15 px
    V = {'P_left': ([(SB, ['ribbon-upper'], (306, 400))], (303, 410)),
         'stem_right': ([(['ribbon-lower'], SB, (366, 446)), (PL, SB, (518, 554))], (360, 560)),
         'stem_mid': ([(['ribbon-upper'], ['ribbon-lower'], (338, 392))], (334, 394))}
    for name, (parts, span) in V.items():
        a, b, rms, n, N, pts = rows_fit(rgb, lab, parts)
        y = pts[:, 1]
        drift = abs(a) * (y.max() - y.min())
        c = float(np.mean(a * y + b))
        out[name] = {'kind': 'v', 'c': c, 'span': list(span), 'rms': round(rms, 3), 'n': n, 'fit_slope': a,
                     'drift_px': round(float(drift), 3)}
        print(f'{name:14s} x = {c:8.3f}  (fit slope {a:+.5f}, drift {drift:.2f} px over the run)  rms {rms:.3f}  n {n}/{N}')
    Hs = {'A_top': (SB, ['a-left-outer', 'a-left-bevel', 'a-right-outer'], (398, 461)),
          'P_top': (SB, ['ribbon-upper'], (534, 660)),
          'L_base': (['a-left-outer', 'a-left-bevel'], SB, (262, 330)),
          'R_base': (['a-right-inner', 'a-right-outer'], SB, (548, 616)),
          'fold_top': (['ribbon-upper'], ['p-bowl-fold'], (566, 660)),
          'counter_top': (['p-bowl-fold'], SB, (594, 664)),
          'counter_bottom': (SB, PL, (594, 664)),
          'bowl_bottom': (PL, SB, (594, 664)),
          'crossbar_top': (SB, ['ribbon-upper'], (386, 436)),
          'crossbar_bottom': (['ribbon-lower'], SB, (356, 440))}
    hfit = {}
    for name, (top, bottom, xr) in Hs.items():
        a, b, rms, n, N, pts = cols_fit(rgb, lab, top, bottom, xr)
        x = pts[:, 0]
        hfit[name] = (float(np.mean(a * x + b)), abs(a) * (x.max() - x.min()), rms, n, N, a)
    cp = crease_pts(rgb, range(593, 668))
    a, b, rms, n, r = fit_line(cp, 'x')
    hfit['crease'] = (float(np.mean(a * cp[:, 0] + b)), abs(a) * (cp[:, 0].max() - cp[:, 0].min()), rms, n, len(cp), a)
    spans = {'top': (390, 470), 'base': (255, 625), 'fold_top': (555, 670), 'counter_top': (588, 670),
             'counter_bottom': (588, 670), 'bowl_bottom': (588, 672), 'crossbar_top': (378, 442),
             'crossbar_bottom': (345, 444), 'crease': (588, 690), 'P_top': (525, 665)}
    for name, (c, drift, rms, n, N, a) in hfit.items():
        print(f'{name:14s} y = {c:8.3f}  (fit slope {a:+.5f}, drift {drift:.2f} px)  rms {rms:.3f}  n {n}/{N}')
    def H(name, c, src):
        out[name] = {'kind': 'h', 'c': c, 'span': list(spans[name]), 'from': src}
    H('top', (hfit['A_top'][0] * hfit['A_top'][3] + hfit['P_top'][0] * hfit['P_top'][3]) / (hfit['A_top'][3] + hfit['P_top'][3]), 'A_top + P_top')
    out['top']['span'] = [390, 665]
    H('base', (hfit['L_base'][0] * hfit['L_base'][3] + hfit['R_base'][0] * hfit['R_base'][3]) / (hfit['L_base'][3] + hfit['R_base'][3]), 'L_base + R_base')
    for k in ('fold_top', 'counter_top', 'counter_bottom', 'bowl_bottom', 'crossbar_top', 'crossbar_bottom', 'crease'):
        H(k, hfit[k][0], k)
    out['_fits'] = {k: {'c': v[0], 'drift_px': round(float(v[1]), 3), 'rms': round(float(v[2]), 3), 'n': v[3], 'slope': v[5]} for k, v in hfit.items()}
    # the fold's 45-degree edge (fold | ribbon back band at the top of the P stem), along its normal
    e, c = normal_edges(rgb.astype(float), seg_points((563.5, 339.5), (588.0, 363.5), 0.5), half=4, step=0.25)
    ok = np.isfinite(e).all(1)
    p, d, rms, r = fit_line_tls(e[ok])
    out['fold_diag'] = {'kind': 'pd', 'p': p.tolist(), 'd': d.tolist(), 'rms': round(rms, 3), 'n': int(ok.sum()),
                        'angle_deg': round(float(np.degrees(np.arctan2(d[1], d[0]))), 3)}
    print(f'fold_diag      through {p.round(3)} dir {d.round(5)} ({out["fold_diag"]["angle_deg"]} deg) rms {rms:.3f} n {ok.sum()}')
    json.dump(out, open(W14 / 'lines14.json', 'w'), indent=1)
