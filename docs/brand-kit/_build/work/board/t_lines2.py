"""Scratch: fit dividers / guides cross-section (center, width) + true ink via thin.fit (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import thin, kit
def hline(y, xa, xb, w0, label, pad=5):
    box = (xa, int(np.floor(y)) - pad, xb, int(np.floor(y)) + pad + 1)
    cov = lambda p: thin.rect_cov(xa - 2, p[0] - p[1] / 2, xb + 2, p[0] + p[1] / 2, box)
    p, ink, r = thin.fit(None, [y, w0], [0.3, 0.3], box, covfn=cov)
    nm, hx, de = kit.nearest_palette(np.clip(ink, 0, 255))
    print('%-14s H y=%.2f w=%.2f ink=%s %s rms=%.2f nearest %s dE=%.1f' % (label, p[0], p[1], ink.round(1), kit.rgbhex(np.clip(ink, 0, 255)), r, nm, de))
    return p, ink
def vline(x, ya, yb, w0, label, pad=5):
    box = (int(np.floor(x)) - pad, ya, int(np.floor(x)) + pad + 1, yb)
    cov = lambda p: thin.rect_cov(p[0] - p[1] / 2, ya - 2, p[0] + p[1] / 2, yb + 2, box)
    p, ink, r = thin.fit(None, [x, w0], [0.3, 0.3], box, covfn=cov)
    nm, hx, de = kit.nearest_palette(np.clip(ink, 0, 255))
    print('%-14s V x=%.2f w=%.2f ink=%s %s rms=%.2f nearest %s dE=%.1f' % (label, p[0], p[1], ink.round(1), kit.rgbhex(np.clip(ink, 0, 255)), r, nm, de))
    return p, ink
hline(147.4, 40, 1330, 1.8, 'div-H1')
hline(440.6, 40, 670, 1.7, 'div-H2a')
hline(440.6, 706, 994, 1.7, 'div-H2b')
hline(440.6, 1030, 1338, 1.7, 'div-H2c')
vline(688.0, 176, 424, 1.8, 'div-V1a')
vline(688.0, 460, 738, 1.8, 'div-V1b')
vline(1011.0, 460, 738, 1.7, 'div-V2')
hline(205.05, 75, 170, 1.0, 'guide-H205')
hline(205.05, 500, 650, 1.0, 'guide-H205b')
hline(264.7, 545, 650, 1.0, 'guide-H264')
hline(293.75, 658, 680, 1.0, 'guide-H293')
hline(410.0, 70, 395, 1.0, 'guide-H410')
vline(62.2, 212, 335, 1.0, 'guide-V62')
vline(371.05, 188, 330, 1.0, 'guide-V371')
vline(401.4, 413, 435, 1.0, 'guide-V401')
vline(517.2, 413, 435, 1.0, 'guide-V517')
vline(538.1, 413, 435, 1.0, 'guide-V538')
vline(654.5, 413, 435, 1.0, 'guide-V654')
