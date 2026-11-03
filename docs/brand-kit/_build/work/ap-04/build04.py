"""hero-04, stage 3: soft face memberships on 04 -> traced outlines -> clean geometry (lines snapped to the
04 line fits, minimal G1 cubics within 0.3 px), legs as exact polygons, every face cut by one silhouette.
Writes F04.npy (soft faces, FACES order + bg last) and geo04.json."""
import json
import sys
import numpy as np

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
import fitcurve
from functools import partial
from soft import memberships
from build_hero import FACES, POLY, soft_half, leg_polys, poly_d, stack_masks, trace_face
from fitcurve import Line, rebuild, micro_cleanup, count_anchors
from pathops import vc_pathfinder
from seg04 import NAMES, W4, BOX, TIP_X

DELTA = 1.5   # px of 04 a lower face reaches under the face stacked above it (the master's 2.5 px x 0.6045)
L = {n: k for k, n in enumerate(NAMES)}
# a contour run snaps to a measured line only within 0.5 px of it (fitcurve's 0.8 px default is for 06's scale)
fitcurve.line_runs = partial(fitcurve.line_runs, dtol=0.5)


class RLine(Line):
    """A measured line that only claims contour runs inside a coordinate range (axis 0: x, 1: y), so two
    nearby parallel runs (the P stem's upper and lower right edge) cannot steal each other's points."""

    def __init__(self, base, lo, hi, axis):
        self.n, self.d, self.t, self.name = base.n, base.d, base.t, base.name
        self.rng, self.axis = (lo, hi), axis

    def dist(self, p):
        q = np.asarray(p, float)
        c = q[..., self.axis]
        return np.where((c >= self.rng[0]) & (c <= self.rng[1]), q @ self.n - self.d, 1e3)

    def project(self, p):
        p = np.asarray(p, float)
        return p - (p @ self.n - self.d) * self.n


def lines04():
    return json.load(open(W4 / 'lines04.json'))


def soft_memberships(rgb, lab, pad=8):
    """soft.memberships on the mark box only (the full frame would need ~2 GB)."""
    x0, y0, x1, y1 = BOX
    sub = memberships(rgb[y0:y1, x0:x1], lab[y0:y1, x0:x1], len(NAMES))
    M = np.zeros((len(NAMES),) + lab.shape)
    M[0] = 1.0
    M[:, y0:y1, x0:x1] = sub
    return M


def face_memberships(M, ln, shape):
    H, Wd = shape
    yy, xx = np.mgrid[0:H, 0:Wd] + 0.5
    F = {}
    U = M[L['ribbon-upper']]
    top = np.maximum(soft_half(xx, yy, 0, -1, ln['fold_top']), soft_half(xx, yy, 1, 0, -ln['top_split_x']))
    low = soft_half(xx, yy, 0, 1, -ln['seam_stem'])
    F['p-bowl-top'] = U * top
    F['ribbon-front-stem'] = U * (1 - top) * (1 - low)
    F['ribbon-front'] = U * (1 - top) * low
    F['ribbon-back'] = M[L['ribbon-lower']]
    F['p-bowl-fold'] = M[L['p-bowl-fold']]
    P = M[L['p-bowl']]
    s = soft_half(xx, yy, 0, 1, -ln['crease']) * soft_half(xx, yy, -1, 0, ln['under_end'])
    F['p-bowl-under'] = P * s
    F['p-bowl-lower'] = P * (1 - s)
    for n in POLY:
        F[n] = M[L[n]]
    F['bg'] = M[L['bg']]
    return F


def hline(a, b, name):
    """y = a*x + b as a Line (n.p = d)."""
    return Line((-a, 1.0), b, name)


def snap_lines(ln):
    out = [Line.h(ln[k], k) for k in ('top', 'fold_top', 'counter_top', 'counter_bottom', 'crease', 'bowl_bottom',
                                      'seam_stem')]
    out += [Line.v(ln[k], k) for k in ('P_left', 'under_end')]
    out += [RLine(Line.v(ln['stem_right'], 'stem_right'), 380, 470, 1),
            RLine(Line.v(ln['stem_right_hi'], 'stem_right_hi'), 300, 350, 1)]
    out += [RLine(hline(ln[k]['ah'], ln[k]['bh'], k), 236, 345, 0) for k in ('crossbar_top', 'crossbar_bottom')]
    out += [RLine(Line.h(ln['crossbar_mid'], 'crossbar_mid'), 240, 345, 0)]
    out += [Line.xy(ln[k]['a'], ln[k]['b'], k) for k in ('LL_outer', 'LL_inner', 'RL_inner', 'RL_outer', 'stem_mid', 'stem_diag')]
    return out


def fix_tip(M):
    """The ribbon's lower band over the left leg near the tip: replace the low-contrast part of the band | leg
    boundary by the cubic fitted to its colour step (seg04.tip_edge), anti-aliased to sub-pixel precision."""
    t = json.load(open(W4 / 'tip04.json'))
    c = np.asarray(t['coef'])
    Lo, lo, lb = L['ribbon-lower'], L['a-left-outer'], L['a-left-bevel']
    x0, x1 = TIP_X
    ys, xs = np.mgrid[440:500, x0:x1]
    f = np.polyval(c, xs + 0.5)
    fp = np.polyval(np.polyder(c), xs + 0.5)
    d = (f - (ys + 0.5)) / np.sqrt(1 + fp ** 2)          # > 0: above the edge (band side)
    sel = np.abs(d) < 6
    ys, xs, d = ys[sel], xs[sel], d[sel]
    tot = M[Lo, ys, xs] + M[lo, ys, xs] + M[lb, ys, xs]
    leg = M[lo, ys, xs] + M[lb, ys, xs]
    share_lo = np.where(leg > 1e-6, M[lo, ys, xs] / np.maximum(leg, 1e-6), 1.0)
    M[Lo, ys, xs] = tot * np.clip(0.5 + d, 0, 1)
    rest = tot - M[Lo, ys, xs]
    M[lo, ys, xs] = rest * share_lo
    M[lb, ys, xs] = rest * (1 - share_lo)
    return M


REBUILD = dict(err=0.3, line_tol=0.3, sigma=1.2, snap_px=4.0, merge_px=5.0, meet_px=3.0)


def drop_degenerate(d, eps=1e-3, flat=0.01):
    """Pathfinder leaves zero-length segments where two input edges coincide, and re-emits some straight
    edges as cubics with collinear handles: drop the former, turn the latter back into true lines."""
    out = []
    for sp in kit.parse_d(d):
        cur, segs = np.array(sp['start']), []
        for g in sp['segs']:
            pts = np.array(g[1:], float).reshape(-1, 2)
            if np.abs(pts - cur).max() < eps:
                continue
            if g[0] == 'C':
                v = pts[2] - cur
                L = np.hypot(*v)
                if L > eps:
                    off = np.abs((pts[:2, 0] - cur[0]) * v[1] - (pts[:2, 1] - cur[1]) * v[0]) / L
                    t = (pts[:2] - cur) @ v / (L * L)
                    if off.max() < flat and t.min() >= -1e-6 and t.max() <= 1 + 1e-6:
                        g = ('L', pts[2][0], pts[2][1])
            segs.append(g)
            cur = pts[-1]
        if segs:
            out.append({'start': sp['start'], 'segs': segs, 'closed': sp['closed']})
    return kit.format_d(out, 3)


def isect(sil, name, d):
    """face d cut by the shared silhouette (VectorCraft Pathfinder intersect), degenerate segments removed."""
    return drop_degenerate(' '.join(vc_pathfinder([('silhouette', sil), (name, d)], 'intersect', W4 / f'_isect_{name}.svg')))


if __name__ == '__main__':
    rgb = kit.load('04').astype(float)
    shape = rgb.shape[:2]
    lab = np.load(W4 / 'labels04.npy')
    ln = lines04()
    M = fix_tip(soft_memberships(rgb, lab))
    F = face_memberships(M, ln, shape)
    np.save(W4 / 'F04.npy', np.stack([F[n] for n in FACES] + [F['bg']]).astype(np.float32))
    masks = stack_masks(F, FACES, DELTA)
    polys = leg_polys(ln, DELTA)
    # the legs are exact polygons on measured lines: where a dark leg face meets the background its soft
    # membership reads low (it is close to the navy), so the silhouette takes the polygon coverage there
    leg_cov = kit.raster([poly_d(polys[n]) for n in POLY], shape[1], shape[0])
    raw = {'silhouette': trace_face(np.maximum(1 - F['bg'], leg_cov))}
    for n in FACES:
        raw[n] = poly_d(polys[n]) if n in POLY else trace_face(masks[n])
    json.dump(raw, open(W4 / 'geo04_raw.json', 'w'), indent=1)
    lines = snap_lines(ln)
    sil = rebuild(raw['silhouette'], lines=lines + [Line.h(ln['base'], 'base')], **REBUILD)
    geo = {}
    for n in FACES:
        d = raw[n] if n in POLY else rebuild(raw[n], lines=lines, **REBUILD)
        geo[n] = isect(sil, n, d)
        print(n, 'anchors', count_anchors(geo[n]))
    json.dump({'geo': geo, 'silhouette': sil}, open(W4 / 'geo04.json', 'w'), indent=1)
    print('silhouette anchors', count_anchors(sil))
