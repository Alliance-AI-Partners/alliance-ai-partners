"""Render an SVG and overlay its path anchors (red) and control points (blue) for a box.
usage: anchors_view.py file.svg x0 y0 x1 y1 scale out.png [face-substring]"""
import sys, re
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
svgf, x0, y0, x1, y1, s, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
only = sys.argv[8] if len(sys.argv) > 8 else None
txt = open(svgf, encoding='utf-8').read()
body = txt[txt.index('>', txt.index('<svg')) + 1:txt.rindex('</svg>')]
crop_svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{(x1 - x0) * s}" height="{(y1 - y0) * s}" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}">' + body + '</svg>')
comp = kit.over(kit.render_svg(crop_svg), '#FFFFFF')
im = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8))
dr = ImageDraw.Draw(im)
for d, at in kit.parse_svg_paths(txt):
    if only and only not in at.get('id', ''):
        continue
    for sp in kit.parse_d(d):
        cur = sp['start']
        pts = [cur]
        for g in sp['segs']:
            if g[0] == 'C':
                for cx, cy in ((g[1], g[2]), (g[3], g[4])):
                    X, Y = (cx - x0) * s, (cy - y0) * s
                    dr.ellipse([X - 2, Y - 2, X + 2, Y + 2], outline=(0, 90, 255))
                dr.line([((cur[0] - x0) * s, (cur[1] - y0) * s), ((g[1] - x0) * s, (g[2] - y0) * s)], fill=(0, 90, 255))
                dr.line([((g[5] - x0) * s, (g[6] - y0) * s), ((g[3] - x0) * s, (g[4] - y0) * s)], fill=(0, 90, 255))
            cur = (g[-2], g[-1]); pts.append(cur)
        for x, y in pts:
            X, Y = (x - x0) * s, (y - y0) * s
            dr.rectangle([X - 2, Y - 2, X + 2, Y + 2], outline=(255, 0, 0), width=1)
im.save(out)
