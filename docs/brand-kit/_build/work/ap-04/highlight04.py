"""hero-04, stage 5 (optional): specular highlights as small faces. A highlight is where 04 is much lighter
than the fitted gradient of its host face (L* excess > T over the current render): that region is traced
at sub-pixel precision (soft excess map), extended across the silhouette edge it sits on and cut by the
shared silhouette, and placed right above its host. Its own gradient is fitted by color04.py.
usage: python highlight04.py <geo in> <render svg> <geo out> [name ...]"""
import json
import sys
import numpy as np

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from build_hero import FACES
from fitcurve import rebuild, count_anchors
from pathops import vc_pathfinder
from seg04 import W4
from color04 import visible_labels
from build04 import REBUILD, isect

T = 8.0       # L* excess that marks a highlight
SPECS = {     # name: (host face, box x0 y0 x1 y1, L* excess threshold[, shape])
    'p-bowl-lower-highlight': ('p-bowl-lower', (494, 340, 542, 384), T),   # crescent on the counter's lower right
    'ribbon-front-highlight': ('ribbon-front', (306, 394, 370, 416), T),   # rim light where the ribbon crosses the A counter
    'p-bowl-fold-highlight': ('p-bowl-fold', (446, 302, 522, 313), T),     # lip under the fold band
    # soft spot on the bowl's top-right shoulder: a traced 2-L* contour is lumpy, a fitted ellipse reads clean
    'p-bowl-top-highlight': ('p-bowl-top', (520, 259, 582, 306), 2.0, 'ellipse'),
}
# not a highlight face: the bright rim on the P stem's right edge sits outside the silhouette (glow), see report


def components(m):
    """4-connected components of a boolean mask -> list of index arrays (small boxes only)."""
    lab = np.zeros(m.shape, int)
    n = 0
    comps = []
    for y, x in zip(*np.nonzero(m)):
        if lab[y, x]:
            continue
        n += 1
        stack, pts = [(y, x)], []
        lab[y, x] = n
        while stack:
            cy, cx = stack.pop()
            pts.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    stack.append((yy, xx))
        comps.append(np.array(pts))
    return comps


def ellipse_d(keep, w, sil_d, name):
    """A soft spot as a smooth ellipse (4 cubic arcs) with the excess-weighted centroid and covariance of the
    highlight pixels (uniform-ellipse moments: semi-axis = 2 sigma), cut by the silhouette."""
    ys, xs = np.nonzero(keep)
    wt = np.clip(w[ys, xs], 1e-3, None)
    p = np.stack([xs + 0.5, ys + 0.5], 1)
    c = (p * wt[:, None]).sum(0) / wt.sum()
    cov = ((p - c).T * wt) @ (p - c) / wt.sum()
    ev, V = np.linalg.eigh(cov)
    a, b = 2 * np.sqrt(ev[1]), 2 * np.sqrt(ev[0])
    ua, ub = V[:, 1] * a, V[:, 0] * b
    k = 0.5522847498
    P = [c + ua, c + ub, c - ua, c - ub]
    T = [ub, -ua, -ub, ua]   # tangent direction at each quadrant point (counter-clockwise in y-down)
    segs = []
    for i in range(4):
        p0, p1 = P[i], P[(i + 1) % 4]
        c1, c2 = p0 + k * T[i], p1 - k * T[(i + 1) % 4]
        segs.append(('C', c1[0], c1[1], c2[0], c2[1], p1[0], p1[1]))
    d = kit.format_d([{'start': tuple(P[0]), 'segs': segs, 'closed': True}], 3)
    return isect(sil_d, name, d)


def build(name, host, box, thr, E, lab, order, sil_cov, sil_d, min_px=12, mode='trace'):
    x0, y0, x1, y1 = box
    hi = order.index(host)
    reg = np.zeros(E.shape, bool)
    reg[y0:y1, x0:x1] = True
    host_vis = kit.dilate(lab == hi, 1) & reg
    core = (E > thr) & (lab == hi) & reg
    keep = np.zeros_like(core)
    for c in components(core):
        if len(c) >= min_px:
            keep[c[:, 0], c[:, 1]] = True
    if not keep.any():
        return None
    if mode == 'ellipse':
        return ellipse_d(keep, E - thr, sil_d, name)
    near = kit.dilate(keep, 2)
    # soft map: 0.5 at E = T inside the host; solid across the silhouette edge next to the highlight
    soft = np.clip((E - thr) / 6.0 + 0.5, 0, 1) * (host_vis & near)
    outside = near & (sil_cov < 0.98) & reg   # also the silhouette's own anti-aliased boundary pixels
    soft = np.maximum(soft, outside.astype(float))
    ys, xs = np.nonzero(soft > 0.01)
    by0, by1, bx0, bx1 = max(0, ys.min() - 6), ys.max() + 7, max(0, xs.min() - 6), xs.max() + 7
    try:
        ds = kit.trace_mask(soft[by0:by1, bx0:bx1], upscale=8, blur=0.25, noise=6)
    except RuntimeError:   # a weak highlight leaves too much grey for logo-mode tracing: trace its 0.5 level
        ds = kit.trace_mask((soft[by0:by1, bx0:bx1] > 0.5).astype(float), upscale=8, blur=0.5, noise=6)
    d = ' '.join(kit.transform_d(q, 1.0, bx0, by0) for q in ds)
    d = rebuild(d, lines=(), **dict(REBUILD, sigma=0.6, step=0.25))   # thin shapes: lighter smoothing
    return drop_specks(isect(sil_d, name, d))


def drop_specks(d, min_area=1.5):
    """Remove sub-paths smaller than min_area px^2 that the silhouette cut leaves along the edge."""
    keep = []
    for sp in kit.parse_d(d):
        P = np.asarray(kit.flatten([sp], tol=0.05)[0])
        area = 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], -1)) - np.dot(np.roll(P[:, 0], -1), P[:, 1]))
        if area >= min_area:
            keep.append(sp)
    return kit.format_d(keep, 3)


if __name__ == '__main__':
    gin, rsvg, gout = sys.argv[1:4]
    names = sys.argv[4:] or list(SPECS)
    g = json.load(open(W4 / gin))
    geo, order = g['geo'], g.get('order', list(FACES))
    rgb = kit.load('04').astype(float)
    h, w = rgb.shape[:2]
    rgba = kit.render_svg((W4 / rsvg).read_text(encoding='utf-8'))
    comp = kit.over(rgba, '#132032')
    E = kit.srgb_to_lab(rgb)[..., 0] - kit.srgb_to_lab(comp)[..., 0]
    lab_order = list(order)   # label indices refer to this order (highlights are inserted below)
    lab = visible_labels(geo, (h, w), lab_order)
    sil_cov = kit.raster(g['silhouette'], w, h)
    for n in names:
        host, box, thr, *mode = SPECS[n]
        d = build(n, host, box, thr, E, lab, lab_order, sil_cov, g['silhouette'], mode=(mode or ['trace'])[0])
        if not d:
            print(n, 'no highlight found'); continue
        geo[n] = d
        if n not in order:
            order.insert(order.index(host) + 1, n)
        area = float(kit.raster(d, w, h).sum())
        print(n, 'anchors', count_anchors(d), 'area %.1f px' % area)
    json.dump({'geo': geo, 'silhouette': g['silhouette'], 'order': order}, open(W4 / gout, 'w'), indent=1)
