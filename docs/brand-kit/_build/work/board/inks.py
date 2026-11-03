"""Scratch: measure ink colors (core pixels) of original 02 regions (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

a = kit.load('02').astype(float)
lab = kit.srgb_to_lab(a)
BG = np.array([245.2, 249.2, 252.6])
bglab = kit.srgb_to_lab(BG)
de_bg = kit.de2000(lab, bglab)


def core(x0, y0, x1, y1, q=0.85, label=''):
    """Median color of the pixels farthest from the background (top 1-q quantile) inside a box."""
    reg = a[y0:y1, x0:x1].reshape(-1, 3)
    d = de_bg[y0:y1, x0:x1].reshape(-1)
    thr = np.quantile(d, q)
    sel = reg[d >= thr]
    med = np.median(sel, 0)
    nm, hx, de = kit.nearest_palette(med)
    print('%-28s n=%5d median=%s hex=%s  nearest=%s %s dE=%.2f' % (label, len(sel), med.round(1), kit.rgbhex(med), nm, hx, de))
    return med


if __name__ == '__main__':
    core(370, 40, 630, 85, 0.6, 'title ALLIANCE')
    core(635, 40, 705, 85, 0.6, 'title AI')
    core(720, 40, 1000, 85, 0.6, 'title PARTNERS')
    core(440, 95, 935, 120, 0.8, 'subtitle')
    core(55, 160, 290, 180, 0.8, 'label 01')
    core(55, 505, 390, 545, 0.7, 'typo row1')
    core(55, 680, 280, 715, 0.7, 'typo digits')
    core(450, 505, 650, 540, 0.7, 'HEADLINE')
    core(60, 342, 160, 368, 0.7, 'lockup ALLIANCE')
    core(168, 342, 192, 368, 0.7, 'lockup AI')
    core(195, 342, 372, 368, 0.7, 'lockup PARTNERS')
    core(90, 370, 345, 388, 0.85, 'tagline')
    core(510, 205, 655, 232, 0.7, 'horiz ALLIANCE')
    core(510, 235, 535, 255, 0.7, 'horiz AI')
    core(540, 235, 655, 255, 0.7, 'horiz PARTNERS')
    core(745, 225, 830, 310, 0.5, 'circle blue')
    core(865, 225, 950, 310, 0.5, 'circle cyan')
    core(985, 225, 1070, 310, 0.5, 'circle navy')
    core(1110, 230, 1185, 305, 0.0, 'circle white (all)')
    core(1230, 230, 1305, 305, 0.0, 'circle offwhite (all)')
    core(405, 297, 515, 405, 0.0, 'tile1 (all)')
    core(542, 297, 652, 405, 0.0, 'tile2 (all)')
    core(715, 505, 990, 512, 0.9, 'dashed red top')
