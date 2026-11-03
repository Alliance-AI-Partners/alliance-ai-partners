"""Scratch: glow falloff around the wave in original 02 - colour vs distance outside the fitted silhouette."""
import numpy as np
import kit
import wavegeom as g
from fit_colors import poly_d

M = g.load()
F = g.faces(M)
q = g.outline(F["ribbon"])
im = kit.load('02').astype(float)
X0, X1, Y0, Y1 = 1000, 1350, 470, 620
yy, xx = np.mgrid[Y0:Y1, X0:X1]
P = np.stack([xx + 0.5, yy + 0.5], -1).reshape(-1, 2)
# distance to the outline polyline
a, b = q[:-1], q[1:]
best = np.full(len(P), 1e9)
for k in range(0, len(a), 1):
    ab = b[k] - a[k]
    t = np.clip(((P - a[k]) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    dd = np.linalg.norm(P - (a[k] + t[:, None] * ab), axis=1)
    best = np.minimum(best, dd)
cov = kit.raster(poly_d(q), 1376, 768)[Y0:Y1, X0:X1].ravel()
dist = np.where(cov > 0.5, -best, best).reshape(yy.shape)
np.save(r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics\glow_dist.npy', dist)
bg = np.array([245.0, 249.5, 252.5])
rgb = im[Y0:Y1, X0:X1]
for lo, hi, label in ((1040, 1110, 'left/blue'), (1140, 1200, 'mid/cyan'), (1250, 1318, 'right')):
    sel_x = (xx + 0.5 >= lo) & (xx + 0.5 <= hi)
    print(label)
    for d0 in np.arange(0, 22, 1.0):
        m = sel_x & (dist >= d0) & (dist < d0 + 1)
        if m.sum() < 5:
            continue
        c = rgb[m].mean(0)
        print('  d %4.1f  n %4d  rgb %s  |bg-c| %.1f  hex %s' % (d0 + 0.5, m.sum(), np.round(c).astype(int), np.linalg.norm(bg - c), kit.rgbhex(c)))
