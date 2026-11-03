"""Overlay a path d (outline + anchors) on a zoomed crop of an original.
usage: overlay.py <oid> <dfile> <x0> <y0> <x1> <y1> <zoom> <out.png>"""
import sys, os
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-')
import flatlib as F
from flatlib import kit, np
from PIL import Image, ImageDraw


def overlay(oid, ds, box, z, out, src=None):
    x0, y0, x1, y1 = box
    im = (Image.open(kit.orig(oid)) if src is None else Image.open(src)).convert('RGB').crop(box)
    im = im.resize((im.width * z, im.height * z), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    T = lambda p: ((p[0] - x0) * z, (p[1] - y0) * z)
    for d in ds:
        for s in kit.parse_d(d):
            poly = kit.flatten([s], tol=0.05)[0]
            if s['closed']:
                poly = poly + [poly[0]]
            dr.line([T(p) for p in poly], fill=(255, 40, 40), width=1)
            cur = s['start']
            for g in s['segs']:
                p = g[-2:]
                col = (255, 0, 255) if g[0] == 'L' else (255, 255, 0)
                q = T(p)
                dr.rectangle([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], outline=col)
                if g[0] == 'C':
                    for h, base in ((g[1:3], cur), (g[3:5], p)):
                        dr.line([T(base), T(h)], fill=(120, 255, 120), width=1)
                cur = p
    im.save(out)


if __name__ == '__main__':
    oid, dfile = sys.argv[1], sys.argv[2]
    box = tuple(int(v) for v in sys.argv[3:7])
    z = int(sys.argv[7])
    out = os.path.join(F.WORK, sys.argv[8])
    ds = open(os.path.join(F.WORK, dfile)).read().split('\n')
    overlay(oid, [d for d in ds if d.strip()], box, z, out)
