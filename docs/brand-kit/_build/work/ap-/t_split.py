import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit, gradfit
from build_hero import FACES
rgb = kit.load('06').astype(float)
Fs = np.load('F_faces.npy'); F = {n: Fs[i] for i, n in enumerate(FACES)}
U = F['p-bowl-top'] + F['ribbon-front']
vis = kit.erode(U > 0.98, 1)
ys, xs = np.nonzero(vis)
xy = np.stack([xs + 0.5, ys + 0.5], 1); c = rgb[ys, xs]
lab = lambda a: kit.srgb_to_lab(a)
def stats(g, xy_, c_):
    de = kit.de2000(lab(c_), lab(gradfit.predict(g, xy_))); return de.mean(), np.percentile(de, 95)
opts = {
 'miter': (lambda x, y: (x - 541.4) > (y - 313.38), np.stack([np.linspace(542, 580, 30), np.linspace(314, 352, 30)], 1)),
}
for yc in (352.5, 400, 440, 470):
    opts['h%d' % yc] = ((lambda yc: lambda x, y: (y < yc) | (x > 640))(yc), np.stack([np.linspace(542, 580, 30), np.full(30, yc)], 1))
for name, (fa, seam) in opts.items():
    A = fa(xy[:, 0], xy[:, 1])
    res = {}
    for k, m in (('top', A), ('front', ~A)):
        sel = m & ((ys % 2 == 0) & (xs % 2 == 0))
        g = gradfit.fit(xy[sel], c[sel], Kmax=3)
        B = gradfit.hat_basis(xy[m] @ g['u'], g['knots']); g['colors'], _ = gradfit.solve(B, c[m])
        res[k] = (xy[m], c[m], g)
    ind = {k: stats(res[k][2], res[k][0], res[k][1]) for k in res}
    def seam_de(gA, gB):
        return kit.de2000(lab(gradfit.predict(gA, seam)), lab(gradfit.predict(gB, seam)))
    sd = seam_de(res['top'][2], res['front'][2])
    J = gradfit.joint({'top': res['top'], 'front': res['front']}, [('top', 'front', seam)], lam=3.0)
    gj = {k: dict(res[k][2], colors=J[k]) for k in res}
    jd = {k: stats(gj[k], res[k][0], res[k][1]) for k in res}
    sj = seam_de(gj['top'], gj['front'])
    print(f"{name:6s} ind: top {ind['top'][0]:.2f}/{ind['top'][1]:.2f} K{res['top'][2]['K']} a{res['top'][2]['angle']:.0f}  front {ind['front'][0]:.2f}/{ind['front'][1]:.2f} K{res['front'][2]['K']} a{res['front'][2]['angle']:.0f} seam max {sd.max():.2f} mean {sd.mean():.2f} | joint: top {jd['top'][0]:.2f}/{jd['top'][1]:.2f} front {jd['front'][0]:.2f}/{jd['front'][1]:.2f} seam max {sj.max():.2f} mean {sj.mean():.2f}")
