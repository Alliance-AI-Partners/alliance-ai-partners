"""Shared constants for the hero-14 rebuild (original 14, light stacked logo, mark only)."""
import sys
from pathlib import Path

BUILD = Path(r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, str(BUILD))
sys.path.insert(0, str(BUILD / 'work' / 'ap-'))  # reuse the 06 pipeline (fitcurve, gradfit, soft, pathops)
import kit  # noqa: E402

W14 = kit.WORK / 'hero-14'
OID = '14'
H = Wd = 1024
BG = '#FFFFFF'                      # measured: median of the pixels around the mark is exactly 255,255,255
MARK_BOX = (259, 303, 762, 612)     # x0 y0 x1 y1 (wordmark starts at y = 660)
REGION_Y1 = 636                     # every mask is cut below this row so the wordmark never enters it
CROP = (240, 290, 780, 630)         # x0 y0 x1 y1 working crop around the mark

# master similarity 06 -> 14 (fit/placements.json "hero@14"); only used to seed the segmentation
S06, TX06, TY06 = 0.7456332244446643, 127.65577299258513, 75.77464311937871

# faces bottom -> top (same structure and z-order as the master)
FACES = ['p-bowl-lower', 'p-bowl-under', 'a-right-outer', 'a-right-inner', 'a-left-bevel', 'a-left-outer',
         'p-bowl-top', 'p-bowl-fold', 'ribbon-front-stem', 'ribbon-front', 'ribbon-back']
POLY = {'a-right-outer', 'a-right-inner', 'a-left-bevel', 'a-left-outer'}
DELTA = 2.5


def to14(x, y):
    return x * S06 + TX06, y * S06 + TY06
