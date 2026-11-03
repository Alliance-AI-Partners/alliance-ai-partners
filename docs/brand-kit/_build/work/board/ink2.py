"""Scratch: interior (eroded) ink colors of large text in original 02 (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

a = kit.load('02').astype(float)
BG = np.array([245.2, 249.2, 252.6])
fg = kit.bg_mask(a.astype(np.uint8), kit.rgbhex(BG), 40)

def interior(x0, y0, x1, y1, r, label):
    m = np.zeros(fg.shape, bool); m[y0:y1, x0:x1] = fg[y0:y1, x0:x1]
    e = kit.erode(m, r)
    sel = a[e]
    med = np.median(sel, 0); mean = sel.mean(0)
    nm, hx, de = kit.nearest_palette(med)
    print('%-18s r=%d n=%5d median=%s %s mean=%s  vs %s dE=%.2f' % (label, r, len(sel), med.round(1), kit.rgbhex(med), mean.round(1), nm, de))
    return med

meds = []
for r in (2, 3):
    meds.append(interior(370, 40, 630, 85, r, 'title ALLIANCE'))
    meds.append(interior(720, 40, 1000, 85, r, 'title PARTNERS'))
    interior(635, 40, 705, 85, r, 'title AI')
    meds.append(interior(450, 505, 650, 540, r, 'HEADLINE'))
    meds.append(interior(55, 505, 390, 545, r, 'typo row1'))
    meds.append(interior(55, 590, 400, 630, r, 'typo row3'))
    meds.append(interior(55, 680, 280, 715, r, 'typo digits'))
m = np.median(np.array(meds), 0)
print('overall', m.round(1), kit.rgbhex(m), kit.nearest_palette(m))
L = kit.srgb_to_lab(np.array([m, kit.hexrgb('#121B2A')]))
print('lab ink', L[0].round(2), 'lab deep navy', L[1].round(2))
