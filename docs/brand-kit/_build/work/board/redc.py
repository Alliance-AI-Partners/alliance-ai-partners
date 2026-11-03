"""Scratch: colors of the clear-space red elements (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
a = kit.load('02').astype(float)
BG = np.array([245.2, 249.2, 252.6])
def darkest(x0, y0, x1, y1, n, label):
    reg = a[y0:y1, x0:x1].reshape(-1, 3)
    d = (BG - reg) @ np.array([0.299, 0.587, 0.114])
    idx = np.argsort(-d)[:n]
    sel = reg[idx]
    print('%-22s darkest%d median=%s %s  max-dark=%s' % (label, n, np.median(sel, 0).round(1), kit.rgbhex(np.median(sel, 0)), reg[idx[0]]))
    for y in range(y0, y1):
        print('   ', y, ' '.join('%3d,%3d,%3d' % tuple(a[y, x]) for x in range(x0, x1)))
darkest(722, 503, 736, 509, 6, 'dash top row')
darkest(713, 515, 719, 530, 6, 'dash left col')
darkest(725, 520, 745, 535, 10, 'X marker')
darkest(855, 512, 862, 535, 8, 'arrow shaft v')
darkest(860, 518, 875, 530, 8, 'x label')
