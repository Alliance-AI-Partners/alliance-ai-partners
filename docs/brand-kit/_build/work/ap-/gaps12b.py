import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
alpha = np.load(kit.WORK / 'ap-' / 'alpha12.npy')
mask = alpha > 0.5
closed = kit.erode(kit.dilate(mask, 7), 7)
gap = closed & ~mask
# keep the two gap regions: windows around the cuts
win = {'a': (240, 520, 360, 590), 'b': (495, 420, 630, 600)}
res = {}
for k, (x0, y0, x1, y1) in win.items():
    g = np.zeros_like(gap); g[y0:y1, x0:x1] = gap[y0:y1, x0:x1]
    ys, xs = np.nonzero(g)
    w = (1 - alpha[ys, xs])
    if k == 'a':
        c = np.polyfit(xs + 0.5, ys + 0.5, 3, w=w)
        u = np.linspace(xs.min(), xs.max() + 1, 60)
        cen = np.stack([u, np.polyval(c, u)], 1)
    else:
        c = np.polyfit(ys + 0.5, xs + 0.5, 3, w=w)
        u = np.linspace(ys.min(), ys.max() + 1, 60)
        cen = np.stack([np.polyval(c, u), u], 1)
    tang = np.gradient(cen, axis=0); tang /= np.hypot(*tang.T)[:, None]
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    widths = []
    for p, n in zip(cen, nrm):
        q = p[None] + np.arange(-6, 6.01, 0.25)[:, None] * n[None]
        x, y = q[:, 0] - 0.5, q[:, 1] - 0.5
        xi, yi = np.floor(x).astype(int), np.floor(y).astype(int); fx, fy = x - xi, y - yi
        a = (alpha[yi, xi] * (1 - fx) * (1 - fy) + alpha[yi, xi + 1] * fx * (1 - fy) + alpha[yi + 1, xi] * (1 - fx) * fy + alpha[yi + 1, xi + 1] * fx * fy)
        widths.append((1 - a).sum() * 0.25)
    widths = np.array(widths)
    L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(cen, axis=0).T))])
    res[k] = (cen, widths, L)
    print('gap', k, 'centerline from', np.round(cen[0], 1), 'to', np.round(cen[-1], 1), 'length %.1f' % L[-1])
    print('   width profile (every 3rd):', ' '.join('%.2f' % v for v in widths[::3]))
    print('   max %.2f  median of middle third %.2f' % (widths.max(), np.median(widths[20:40])))
np.save(kit.WORK / 'ap-' / 'gaps12.npy', np.array([res['a'][0], res['b'][0]], dtype=object), allow_pickle=True)
