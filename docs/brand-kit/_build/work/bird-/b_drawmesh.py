import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
def draw(verts, cycles, x0, y0, x1, y1, z, out, img=None, labels=True):
    img = kit.load('15') if img is None else img
    im = Image.fromarray(img[y0:y1, x0:x1]).resize(((x1-x0)*z, (y1-y0)*z), Image.NEAREST).convert('RGB')
    d = ImageDraw.Draw(im)
    T = lambda p: ((p[0]-x0)*z, (p[1]-y0)*z)
    for f, cyc in cycles.items():
        pts = [T(verts[v]) for v in cyc]
        d.line(pts + [pts[0]], fill=(255, 0, 0), width=1)
    used = sorted({v for c in cycles.values() for v in c})
    for k in used:
        x, y = T(verts[k])
        if -5 < x < im.width + 5 and -5 < y < im.height + 5:
            d.ellipse([x-2, y-2, x+2, y+2], outline=(255, 255, 0))
            if labels: d.text((x+3, y-10), str(k), fill=(255, 255, 0))
    im.save(out)
