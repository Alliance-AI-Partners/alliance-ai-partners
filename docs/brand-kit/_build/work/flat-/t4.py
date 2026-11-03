import sys, os
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-'
res = eval(open(os.path.join(W, 't1.txt')).read())
cyan_d = [p for p, f in res if f == '#00D5FF'][0]
poly = np.array(kit.flatten(kit.parse_d(cyan_d), tol=0.02)[0])


def seg_dev(p0, p1, lo, hi):
    """deviation of trace points between two points (by nearest index) from the best-fit line"""
    i0 = np.argmin(np.linalg.norm(poly - p0, axis=1)); i1 = np.argmin(np.linalg.norm(poly - p1, axis=1))
    if i1 < i0: i0, i1 = i1, i0
    q = poly[i0:i1 + 1]
    q = q[int(len(q) * lo):int(len(q) * hi)]
    c = q.mean(0); u, s, vt = np.linalg.svd(q - c); dvec = vt[0]; nrm = np.array([-dvec[1], dvec[0]])
    dist = (q - c) @ nrm
    t = (q - c) @ dvec
    # quadratic fit of dist vs t for systematic bow
    A = np.stack([t * t, t, np.ones_like(t)], 1); co = np.linalg.lstsq(A, dist, rcond=None)[0]
    L = t.max() - t.min()
    print('len %.1f  max dev %.3f  rms %.3f  bow(sagitta) %.3f' % (L, np.abs(dist).max(), dist.std(), abs(co[0]) * (L / 2) ** 2))


print('A left outer edge'); seg_dev((382, 307.6), (258.7, 569.9), 0.05, 0.95)
print('A right leg inner'); seg_dev((456.8, 307.3), (533, 460.2), 0.05, 0.95)
print('A counter right'); seg_dev((419.7, 396.7), (477.7, 522.7), 0.05, 0.95)
print('P top edge'); seg_dev((543.3, 307.2), (690, 307.1), 0.05, 0.95)
print('A leg right outer'); seg_dev((647, 678.1), (627, 625), 0.05, 0.95)
print('ribbon lower (curve)'); seg_dev((437.9, 601.5), (514.5, 580.9), 0.05, 0.95)
print('ribbon right (curve)'); seg_dev((600, 497.5), (547.3, 565.9), 0.05, 0.95)
