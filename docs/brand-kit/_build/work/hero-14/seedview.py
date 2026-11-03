"""Preview: seeds drawn over original 14 (2x) to check every seed sits inside its face."""
import sys
import numpy as np
from PIL import Image, ImageDraw
from common import kit, W14, CROP
from seg14 import SEEDS

COLS = {'bg': (255, 0, 0), 'a-left-outer': (255, 255, 0), 'a-left-bevel': (255, 128, 0), 'a-right-inner': (0, 255, 0),
        'a-right-outer': (255, 0, 255), 'ribbon-upper': (0, 0, 0), 'ribbon-lower': (255, 255, 255),
        'p-bowl-fold': (128, 0, 255), 'p-bowl-lower': (0, 255, 255), 'p-bowl-under': (255, 0, 128), 'p-stem': (128, 255, 0)}

if __name__ == '__main__':
    im = kit.load('14')
    x0, y0, x1, y1 = CROP
    sc = 2
    big = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.LANCZOS)
    d = ImageDraw.Draw(big)
    for n, pls in SEEDS.items():
        for pl in pls:
            d.line([((x - x0) * sc, (y - y0) * sc) for x, y in pl], fill=COLS[n], width=3)
            d.text(((pl[0][0] - x0) * sc + 3, (pl[0][1] - y0) * sc + 3), n[:8], fill=COLS[n])
    big.save(sys.argv[1] if len(sys.argv) > 1 else W14 / 'seeds_preview.png')
