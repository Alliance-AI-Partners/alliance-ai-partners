"""Compare gradient-fit variants per face on the current geometry (visible pixels from the geometry).
usage: python gradtest.py tag"""
import json
import sys
import numpy as np
from common import kit, W14, FACES
import gradfit
from make14 import face_rasters, visible_pixels
from make_hero import lab_of
from build14 import lines


def evaluate(g, xy, c):
    gg = dict(g, colors=np.clip(np.round(g['colors']), 0, 255))
    de = kit.de2000(lab_of(c), lab_of(gradfit.predict(gg, xy)))
    return de.mean(), np.percentile(de, 95)


if __name__ == '__main__':
    tag = sys.argv[1]
    geo = json.load(open(W14 / f'hero14_{tag}.json'))['geo']
    rgb = kit.load('14').astype(float)
    ln = lines()
    cov, vis = face_rasters(geo)
    axis_l = np.degrees(np.arctan2(1, ln['LL_crease_u']['a']))
    axis_r = np.degrees(np.arctan2(1, ln['RL_internal_u']['a']))
    for n in FACES:
        xy, c, (ys, xs) = visible_pixels(vis[n], rgb)
        sel = (ys % 2 == 0) & (xs % 2 == 0)
        res = []
        variants = {'K3free': dict(Kmax=3), 'K5free': dict(Kmax=5, improve=0.85)}
        if n.startswith('a-'):
            ax = axis_l if n.startswith('a-left') else axis_r
            variants = {'K5axis': dict(Kmax=5, angles=np.arange(ax - 15, ax + 15.01, 3.0), improve=0.85), 'K5free': dict(Kmax=5, improve=0.85)}
        for vn, kw in variants.items():
            g = gradfit.fit(xy[sel], c[sel], **kw)
            g['colors'], g['mse'] = gradfit.solve(gradfit.hat_basis(xy @ g['u'], g['knots']), c)
            m, p = evaluate(g, xy, c)
            res.append(f"{vn}: K{g['K']} a{g['angle']:6.1f} {m:.2f}/{p:.2f}")
        print(f'{n:18s} n{len(xy):6d}  ' + '   '.join(res))
