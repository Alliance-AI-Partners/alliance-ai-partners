"""Render a geometry (json with 'geo' or an svg) with every face in a flat distinct colour (VectorCraft),
crop + scale. usage: python flat.py geo.json|file.svg x0 y0 x1 y1 scale out.png"""
import sys
import numpy as np
from PIL import Image
from common import kit, FACES, H, Wd
from ov import load_geo

COLS = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080']

if __name__ == '__main__':
    geo = load_geo(sys.argv[1])
    x0, y0, x1, y1, sc = (int(v) for v in sys.argv[2:7])
    body = '\n'.join(f'<path d="{geo[n]}" fill="{c}" fill-rule="evenodd"/>' for n, c in zip(FACES, COLS) if n in geo)
    r = kit.over(kit.render_svg(kit.svg_doc(Wd, H, body)), '#000000')
    Image.fromarray(r[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST).save(sys.argv[7])
