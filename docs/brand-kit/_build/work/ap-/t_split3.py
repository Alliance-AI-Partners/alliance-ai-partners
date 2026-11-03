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
def fitm(m, Kmax=3):
    sel = m & ((ys % 2 == 0) & (xs % 2 == 0))
    if sel.sum() < 200: sel = m
    g = gradfit.fit(xy[sel], c[sel], Kmax=Kmax)
    B = gradfit.hat_basis(xy[m] @ g['u'], g['knots']); g['colors'], _ = gradfit.solve(B, c[m])
    return (xy[m], c[m], g)
X, Y = xy[:, 0], xy[:, 1]
for top_cut in ('miter', 'h352'):
    A = ((X - 541.4) > (Y - 313.38)) if top_cut == 'miter' else ((Y < 352.5) | (X > 640))
    A = A | (X > 640)
    seamA = np.stack([np.linspace(542, 580, 30), np.linspace(314, 352, 30)], 1) if top_cut == 'miter' else np.stack([np.linspace(542, 580, 30), np.full(30, 352.5)], 1)
    for yb in (420, 450, 480, 510):
        S = ~A & (Y < yb)
        B = ~A & ~S
        seamB = np.stack([np.linspace(530, 585, 40), np.full(40, yb)], 1)
        seamB = seamB[np.isin(np.round(seamB).astype(int)[:, 0] + 1024 * np.round(seamB).astype(int)[:, 1], (xs + 1024 * ys)[B | S])]
        res = {'top': fitm(A), 'stem': fitm(S), 'front': fitm(B)}
        seams = [('top', 'stem', seamA), ('stem', 'front', seamB)]
        J = gradfit.joint(res, seams, lam=3.0)
        gj = {k: dict(res[k][2], colors=J[k]) for k in res}
        jd = {k: stats(gj[k], res[k][0], res[k][1]) for k in res}
        sd = [kit.de2000(lab(gradfit.predict(gj[a], p)), lab(gradfit.predict(gj[b], p))) for a, b, p in seams]
        print(f"{top_cut} yb={yb}: " + ' '.join(f"{k} {jd[k][0]:.2f}/{jd[k][1]:.2f} K{res[k][2]['K']} a{res[k][2]['angle']:.0f}" for k in res) +
              f" | seams max {sd[0].max():.2f}/{sd[1].max():.2f} mean {sd[0].mean():.2f}/{sd[1].mean():.2f}")
