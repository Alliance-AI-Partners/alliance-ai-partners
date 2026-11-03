"""Zoomed view of original 14 with the label-map boundaries (red) and seeds (yellow) drawn over it.
usage: python zoomseg.py x0 y0 x1 y1 [scale] [out.png]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from common import kit, W14
from seg14 import SEEDS

if __name__ == '__main__':
    x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
    sc = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    out = sys.argv[6] if len(sys.argv) > 6 else str(W14 / 'zoomseg.png')
    im = kit.load('14')
    lab = np.load(W14 / 'labels14.npy')
    big = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST)
    d = ImageDraw.Draw(big)
    L = lab[y0:y1, x0:x1]
    ys, xs = np.nonzero(L[:, 1:] != L[:, :-1])
    for y, x in zip(ys, xs):
        d.line([((x + 1) * sc, y * sc), ((x + 1) * sc, (y + 1) * sc)], fill=(255, 0, 0))
    ys, xs = np.nonzero(L[1:] != L[:-1])
    for y, x in zip(ys, xs):
        d.line([(x * sc, (y + 1) * sc), ((x + 1) * sc, (y + 1) * sc)], fill=(255, 0, 0))
    for n, pls in SEEDS.items():
        for pl in pls:
            d.line([((x - x0) * sc, (y - y0) * sc) for x, y in pl], fill=(255, 255, 0), width=1)
    for gx in range((x0 // 10 + 1) * 10, x1, 10):
        d.text(((gx - x0) * sc + 1, 1), str(gx), fill=(0, 0, 0))
    for gy in range((y0 // 10 + 1) * 10, y1, 10):
        d.text((1, (gy - y0) * sc + 1), str(gy), fill=(0, 0, 0))
    big.save(out)
