import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F
from flatlib import kit, np
from PIL import Image


def wobble(d):
    """inflections (curvature sign flips with |k| > 0.004) and curvature total variation over all curves"""
    flips, tv = 0, 0.0
    for s in kit.parse_d(d):
        cur = np.array(s['start'])
        ks = []
        for g in s['segs']:
            if g[0] == 'L':
                ks.append(None); cur = np.array(g[1:3]); continue
            p0, p1, p2, p3 = cur, np.array(g[1:3]), np.array(g[3:5]), np.array(g[5:7])
            u = np.linspace(0, 1, 40)
            d1, d2 = F.bez_d1(p0, p1, p2, p3, u), F.bez_d2(p0, p1, p2, p3, u)
            k = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum(np.linalg.norm(d1, axis=1) ** 3, 1e-9)
            ks.append(k); cur = p3
        seq = np.concatenate([k for k in ks if k is not None]) if any(k is not None for k in ks) else np.zeros(1)
        sig = seq[np.abs(seq) > 0.004]
        flips += int(np.sum(np.sign(sig[1:]) != np.sign(sig[:-1])))
        tv += float(np.abs(np.diff(seq)).sum())
    return flips, round(tv, 2)


if __name__ == '__main__':
    oid, lab = sys.argv[1], sys.argv[2]
    raw_alpha = np.asarray(Image.open(os.path.join(F.WORK, 'clean_%s.png' % lab)).convert('RGB'), float)
    alpha = F.cov2(raw_alpha, F.NAVY, F.CYAN)
    res = kit.trace_image(raw_alpha, [F.NAVY_HEX, F.CYAN_HEX])
    raw = ' '.join(d for d, f in res if f == F.CYAN_HEX)
    H, W = alpha.shape
    print('raw trace wobble', wobble(raw))
    for tol, sig, eps, spl, mt in [(0.3, 3.0, 0, False, 0), (0.3, 3.0, 0, True, 0.1), (0.3, 3.0, 0, True, 0.2), (0.4, 3.0, 0, True, 0.15), (0.4, 3.0, 0, True, 0.25)]:
        d, info = F.refit_path(raw, alpha=alpha, tol=tol, snap_sigma=sig, smooth_eps=eps, spline=spl, merge_tol=mt)
        open(os.path.join(F.WORK, 'spl_%s_%s_%s.txt' % (oid, tol, spl)), 'w').write(d)
        cov = kit.raster([d], W, H, ss=8)
        print(tol, sig, eps, spl, mt, 'anchors', info['anchors'], 'IoU', round(kit.iou(alpha > 0.5, cov > 0.5), 4), 'wobble', wobble(d))
