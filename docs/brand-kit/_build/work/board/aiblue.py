"""Scratch: blue 'AI' ink in the lockups (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
a = kit.load('02').astype(float)
for (x0, y0, x1, y1, lab) in [(190, 338, 240, 372, 'hero AI'), (505, 232, 545, 260, 'horiz AI'), (630, 40, 710, 90, 'title AI')]:
    reg = a[y0:y1, x0:x1].reshape(-1, 3)
    sat = reg[:, 2] - reg[:, 0]          # blue minus red
    dark = 248 - reg @ np.array([0.299, 0.587, 0.114])
    sel = reg[(sat > 0.6 * np.percentile(sat, 99))]
    print(lab, 'n', len(sel), 'median', np.median(sel, 0).round(1), kit.rgbhex(np.median(sel, 0)), kit.nearest_palette(np.median(sel, 0)))
    sel2 = reg[(sat > 0.85 * np.percentile(sat, 99))]
    print('    strict n', len(sel2), np.median(sel2, 0).round(1), kit.rgbhex(np.median(sel2, 0)), kit.nearest_palette(np.median(sel2, 0)))
