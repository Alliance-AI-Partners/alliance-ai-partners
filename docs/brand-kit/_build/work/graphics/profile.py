"""Scratch: vertical color profiles through the wave in original 02 (Lab L, chroma, hue per pixel)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
import kit

im = kit.load('02').astype(float)
lab = kit.srgb_to_lab(im)
L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
C = np.hypot(a, b)
H = np.degrees(np.arctan2(b, a)) % 360

xs = [int(v) for v in sys.argv[1:]] or list(range(1040, 1320, 20))
for x in xs:
    print('x=%d' % x)
    for y in range(498, 598):
        if C[y, x] < 25 and L[y, x] > 80:
            continue
        r, g, bb = im[y, x].astype(int)
        print('  y=%d #%02X%02X%02X L=%5.1f C=%5.1f h=%5.1f' % (y, r, g, bb, L[y, x], C[y, x], H[y, x]))
