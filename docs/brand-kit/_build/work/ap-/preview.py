"""Quick flat-colour preview of the traced hero geometry + anchor-point overlay."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from build_hero import FACES, W

PAL = {'p-bowl-lower': '#3A5077', 'p-stem': '#1C3152', 'a-right-outer': '#3B5379', 'a-right-inner': '#1F3354',
       'a-left-bevel': '#25427F', 'a-left-outer': '#2856B8', 'p-bowl-top': '#13A8D8', 'p-bowl-fold': '#2368BD',
       'ribbon-front': '#0CCFEB', 'ribbon-back': '#1C76BD'}


def anchors(d):
    pts = []
    for s in kit.parse_d(d):
        pts.append(s['start'])
        for g in s['segs']:
            pts.append((g[-2], g[-1]))
    return pts


if __name__ == '__main__':
    geo = json.load(open(W / 'geo_hero.json'))
    body = '\n'.join(f'<path id="face-{n}" d="{geo[n]}" fill="{PAL[n]}" fill-rule="evenodd"/>' for n in FACES)
    svg = kit.svg_doc(1024, 1024, body)
    (W / 'flat_preview.svg').write_text(svg, encoding='utf-8')
    rgba = kit.render_svg(svg)
    comp = kit.over(rgba, '#FFFFFF')
    orig = kit.load('06')
    s = 3
    box = tuple(int(v) for v in sys.argv[1:5]) if len(sys.argv) > 4 else (160, 300, 870, 720)
    x0, y0, x1, y1 = box
    im = Image.fromarray(comp.astype(np.uint8)).crop(box).resize(((x1 - x0) * s, (y1 - y0) * s), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    for n in FACES:
        for x, y in anchors(geo[n]):
            if x0 <= x <= x1 and y0 <= y <= y1:
                X, Y = (x - x0) * s, (y - y0) * s
                dr.rectangle([X - 2, Y - 2, X + 2, Y + 2], outline=(255, 0, 0))
    im.save(W / 'flat_anchors.png')
    o = Image.fromarray(orig).crop(box).resize(((x1 - x0) * s, (y1 - y0) * s), Image.LANCZOS)
    o.save(W / 'orig_crop.png')
