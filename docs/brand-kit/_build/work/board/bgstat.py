"""Scratch: background statistics of original 02 (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
a = kit.load('02').astype(float)
H, W = a.shape[:2]
B = 8
hb, wb = H // B, W // B
blk = a[:hb * B, :wb * B].reshape(hb, B, wb, B, 3).transpose(0, 2, 1, 3, 4).reshape(hb, wb, B * B, 3)
med = np.median(blk, 2); spread = blk.std(2).mean(-1)
lum = med @ np.array([0.299, 0.587, 0.114])
flat = (spread < 2.0) & (lum > 240)
vals = med[flat]
print('flat blocks', flat.sum(), 'median', np.median(vals, 0), 'p5', np.percentile(vals, 5, 0), 'p95', np.percentile(vals, 95, 0))
m = np.median(vals, 0)
print('median hex', kit.rgbhex(m), kit.nearest_palette(m))
de = kit.de2000(kit.srgb_to_lab(vals), kit.srgb_to_lab(kit.hexrgb('#F4F7FB')))
print('dE vs F4F7FB: mean %.2f p95 %.2f max %.2f' % (de.mean(), np.percentile(de, 95), de.max()))
# smooth trend: luma by columns / rows
ys, xs = np.nonzero(flat)
for name, coord, n in (('x', xs * B, W), ('y', ys * B, H)):
    bins = np.linspace(0, n, 9)
    print(name, [round(float(np.median(lum[flat][(coord >= bins[i]) & (coord < bins[i + 1])])), 1) for i in range(8)])
