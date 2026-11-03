import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
alpha = np.load(kit.WORK / 'ap-' / 'alpha12.npy')
H12 = 371.11
for k in 'ab':
    g = np.load(kit.WORK / 'ap-' / f'gap12_{k}.npy')
    g = kit.dilate(g, 2) & (alpha < 0.98)          # include the anti-aliased rims of the cut
    ys, xs = np.nonzero(g)
    w = 1 - alpha[ys, xs]
    P = np.stack([xs + 0.5, ys + 0.5], 1)
    if k == 'a':
        c = np.polyfit(P[:, 0], P[:, 1], 3, w=w); u = np.linspace(P[:, 0].min(), P[:, 0].max(), 400); cen = np.stack([u, np.polyval(c, u)], 1)
    else:
        c = np.polyfit(P[:, 1], P[:, 0], 3, w=w); u = np.linspace(P[:, 1].max(), P[:, 1].min(), 400); cen = np.stack([np.polyval(c, u), u], 1)
    L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(cen, axis=0).T))])
    d2 = ((P[:, None, :] - cen[None]) ** 2).sum(-1)
    s = L[d2.argmin(1)]
    bins = np.arange(0, L[-1] + 4, 4.0)
    area = np.histogram(s, bins, weights=w)[0]
    width = area / 4.0
    print('gap', k, 'from', np.round(cen[0], 1), 'to', np.round(cen[-1], 1), 'length %.1f' % L[-1])
    print('  width per 4px bin:', ' '.join('%.1f' % v for v in width))
    print('  max %.2f px = %.4f of 12 mark height; mean over first 40%% %.2f' % (width.max(), width.max() / H12, width[:max(1, int(len(width) * 0.4))].mean()))
