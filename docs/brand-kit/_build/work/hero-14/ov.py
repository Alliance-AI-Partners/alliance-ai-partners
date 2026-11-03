"""Outlines of a geometry JSON ({'geo': {name: d}} or an SVG) drawn over original 14.
usage: python ov.py geo.json|file.svg x0 y0 x1 y1 scale out.png [face,face,...]"""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw
from common import kit

COLS = {'silhouette': (255, 255, 255), 'p-bowl-lower': (230, 25, 75), 'p-bowl-under': (60, 180, 75), 'a-right-outer': (255, 225, 25),
        'a-right-inner': (67, 99, 216), 'a-left-bevel': (245, 130, 49), 'a-left-outer': (145, 30, 180), 'p-bowl-top': (70, 240, 240),
        'p-bowl-fold': (240, 50, 230), 'ribbon-front-stem': (188, 246, 12), 'ribbon-front': (250, 190, 190), 'ribbon-back': (0, 128, 128)}


def load_geo(path):
    if path.endswith('.svg'):
        t = open(path, encoding='utf-8').read()
        return {a.get('id', '')[5:] if a.get('id', '').startswith('face-') else a.get('id', ''): d for d, a in kit.parse_svg_paths(t)}
    g = json.load(open(path))
    return g['geo'] if 'geo' in g else g


if __name__ == '__main__':
    geo = load_geo(sys.argv[1])
    x0, y0, x1, y1, sc = (int(v) for v in sys.argv[2:7])
    out = sys.argv[7]
    only = sys.argv[8].split(',') if len(sys.argv) > 8 else None
    im = kit.load('14')
    big = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST if sc >= 4 else Image.LANCZOS)
    d = ImageDraw.Draw(big)
    for n, dd in geo.items():
        if only and n not in only:
            continue
        if not isinstance(dd, str):
            continue
        for poly in kit.flatten(kit.parse_d(dd), tol=0.1):
            pts = [((x - x0) * sc, (y - y0) * sc) for x, y in poly]
            d.line(pts + [pts[0]], fill=COLS.get(n, (255, 0, 0)), width=1)
    step = 10 if sc >= 3 else 50
    for gx in range((x0 // step + 1) * step, x1, step):
        d.text(((gx - x0) * sc + 1, 1), str(gx), fill=(0, 0, 0))
    for gy in range((y0 // step + 1) * step, y1, step):
        d.text((1, (gy - y0) * sc + 1), str(gy), fill=(0, 0, 0))
    big.save(out)
