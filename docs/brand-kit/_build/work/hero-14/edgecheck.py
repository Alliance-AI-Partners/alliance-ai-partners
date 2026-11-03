"""Edge-position check: along every visible outline of the final geometry, measure the sub-pixel edge
in original 14 and in the VectorCraft render along the same normals; report the offset (original minus
render, + = outward of the face) per face and the worst stretches. usage: python edgecheck.py tag"""
import json
import sys
import numpy as np
from common import kit, W14, FACES
from edges import normal_edges
from make14 import face_rasters


def outline_samples(d, spacing=2.0):
    out = []
    for poly in kit.flatten(kit.parse_d(d), tol=0.05):
        p = np.asarray(poly)
        seg = np.hypot(*np.diff(p, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        if s[-1] < 4:
            continue
        t = np.arange(0, s[-1], spacing)
        q = np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)
        out.append(q)
    return out


if __name__ == '__main__':
    tag = sys.argv[1]
    h = json.load(open(W14 / f'hero14_{tag}.json'))
    geo = h['geo']
    o = kit.load('14').astype(float)
    r = np.load(W14 / f'comp_{tag}.npy').astype(float)
    cov, vis = face_rasters(geo, ss=2)
    rows = []
    for n in FACES:
        for q in outline_samples(geo[n]):
            # keep samples where this face is visible on one side (its edge is a visible edge)
            tang = np.gradient(q, axis=0)
            tang /= np.maximum(np.hypot(*tang.T), 1e-9)[:, None]
            nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
            inside = q - 1.5 * nrm
            outside = q + 1.5 * nrm
            vi = np.array([vis[n][int(y), int(x)] if 0 <= int(y) < 1024 and 0 <= int(x) < 1024 else 0 for x, y in inside])
            vo = np.array([vis[n][int(y), int(x)] if 0 <= int(y) < 1024 and 0 <= int(x) < 1024 else 0 for x, y in outside])
            if vi.mean() < vo.mean():   # orientation: make nrm point out of the face
                nrm = -nrm; vi, vo = vo, vi
            ok = (vi > 0.9) & (vo < 0.1)
            if ok.sum() < 3:
                continue
            eo, co = normal_edges(o, q, half=3.0, step=0.25, cmin=15)
            er, cr = normal_edges(r, q, half=3.0, step=0.25, cmin=15)
            d = ((eo - er) * nrm).sum(1)
            good = ok & np.isfinite(d) & (np.abs(d) < 2.5)
            for (x, y), dd in zip(q[good], d[good]):
                rows.append((n, x, y, dd))
    rows = np.array(rows, dtype=object)
    names = rows[:, 0]
    d = rows[:, 3].astype(float)
    print('all visible edges: n %d  mean offset %+.3f  mean |offset| %.3f  p90 |offset| %.2f' % (len(d), d.mean(), np.abs(d).mean(), np.percentile(np.abs(d), 90)))
    for n in FACES:
        m = names == n
        if m.sum():
            print(f'{n:18s} n {m.sum():4d}  mean {d[m].mean():+.3f}  |mean| {np.abs(d[m]).mean():.3f}')
    # worst 10 px stretches
    xy = rows[:, 1:3].astype(float)
    key = np.floor(xy / 12).astype(int)
    agg = {}
    for (kx, ky), dd, nn in zip(key, d, names):
        agg.setdefault((kx, ky, nn), []).append(dd)
    worst = sorted(((np.mean(v), k) for k, v in agg.items() if len(v) >= 4), key=lambda t: -abs(t[0]))[:14]
    for mval, (kx, ky, nn) in worst:
        print(f'  {nn:18s} near ({kx * 12 + 6}, {ky * 12 + 6}) mean offset {mval:+.2f} (n {len(agg[(kx, ky, nn)])})')
