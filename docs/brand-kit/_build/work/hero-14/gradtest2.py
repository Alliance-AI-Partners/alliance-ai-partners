"""Seam faces: free K<=5 fits with/without pad, then the joint seam solve; per-face dE and seam dE.
usage: python gradtest2.py tag"""
import json
import sys
import numpy as np
from common import kit, W14
import gradfit
from make14 import face_rasters, visible_pixels, seams, with_cuts
from make_hero import lab_of
from build14 import lines

SEAMF = ['p-bowl-top', 'ribbon-front-stem', 'ribbon-front', 'p-bowl-under', 'p-bowl-lower']


def ev(g, cols, xy, c):
    gg = dict(g, colors=np.clip(np.round(cols), 0, 255))
    de = kit.de2000(lab_of(c), lab_of(gradfit.predict(gg, xy)))
    return de.mean(), np.percentile(de, 95)


if __name__ == '__main__':
    tag = sys.argv[1]
    geo = json.load(open(W14 / f'hero14_{tag}.json'))['geo']
    rgb = kit.load('14').astype(float)
    ln = with_cuts(lines())
    cov, vis = face_rasters(geo)
    sm = seams(ln, vis)
    data = {}
    for n in SEAMF:
        xy, c, (ys, xs) = visible_pixels(vis[n], rgb)
        data[n] = (xy, c, (ys % 2 == 0) & (xs % 2 == 0))
    for label, Kmax, use_pad in (('K3 pad', 3, True), ('K5 pad', 5, True), ('K5 nopad', 5, False), ('K3 nopad', 3, False)):
        pads = {'p-bowl-top': sm[0][2], 'ribbon-front': sm[1][2]} if use_pad else {}
        fits = {}
        for n in SEAMF:
            xy, c, sel = data[n]
            g = gradfit.fit(xy[sel], c[sel], Kmax=Kmax, improve=0.85, pad=pads.get(n))
            g['colors'], g['mse'] = gradfit.solve(gradfit.hat_basis(xy @ g['u'], g['knots']), c)
            fits[n] = (xy, c, g)
        for lam in (3.0, 10.0):
            J = gradfit.joint(fits, sm, lam=lam)
            out = []
            for n in SEAMF:
                xy, c, g = fits[n]
                m, p = ev(g, J[n], xy, c)
                out.append(f"{n.replace('ribbon-', 'r-').replace('p-bowl-', 'pb-')} K{g['K']} {m:.2f}/{p:.2f}")
            sd = []
            for a, b, pts in sm:
                ga = dict(fits[a][2], colors=np.clip(np.round(J[a]), 0, 255)); gb = dict(fits[b][2], colors=np.clip(np.round(J[b]), 0, 255))
                d = kit.de2000(lab_of(gradfit.predict(ga, pts)), lab_of(gradfit.predict(gb, pts)))
                sd.append(f'{d.max():.2f}/{d.mean():.2f}')
            print(f'{label:9s} lam{lam:4.0f} | ' + ' | '.join(out) + ' | seams max/mean ' + ' '.join(sd))
