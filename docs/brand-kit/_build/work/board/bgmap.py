"""Scratch: local background map of original 02 (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from PIL import Image
a = kit.load('02').astype(float)
# block medians on a 16px grid
H, W = a.shape[:2]
B = 8
hb, wb = H // B, W // B
blk = a[:hb * B, :wb * B].reshape(hb, B, wb, B, 3).transpose(0, 2, 1, 3, 4).reshape(hb, wb, B * B, 3)
med = np.median(blk, 2)
spread = blk.std(2).mean(-1)
# keep only flat blocks
flat = spread < 2.0
lum = med @ np.array([0.299, 0.587, 0.114])
vis = np.where(flat, np.clip((lum - 240) * 16, 0, 255), 0).astype(np.uint8)
Image.fromarray(vis).resize((wb * 4, hb * 4), Image.NEAREST).save(kit.WORK / 'board' / 'bgmap.png')
for (x, y) in [(730, 560), (800, 600), (900, 690), (960, 600), (700, 600), (1000, 600), (705, 480), (990, 480), (720, 740), (850, 735), (560, 600), (1200, 740), (1100, 560)]:
    by, bx = y // B, x // B
    print((x, y), med[by, bx].round(1), 'flat' if flat[by, bx] else 'busy', 'L=%.1f' % lum[by, bx])
