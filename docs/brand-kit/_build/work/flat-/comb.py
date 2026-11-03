"""Curvature comb of one built SVG layer drawn over the original (for wobble review).
usage: comb.py <oid> <layer id> <x0> <y0> <x1> <y1> <zoom> <out> [comb_scale]"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F
from flatlib import kit, np
from PIL import Image, ImageDraw

oid, lid = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
z = int(sys.argv[7])
out = os.path.join(F.WORK, sys.argv[8])
cs = float(sys.argv[9]) if len(sys.argv) > 9 else 400.0
if lid.endswith('.txt'):
    d = open(os.path.join(F.WORK, lid)).read()
else:
    svg = open(os.path.join(F.BUILD, 'components', 'flat-%s.svg' % oid)).read()
    d = {m.group(1): m.group(2) for m in re.finditer(r'<path id="([^"]+)"[^>]* d="([^"]+)"', svg)}[lid]
im = Image.open(kit.orig(oid)).convert('RGB').crop((x0, y0, x1, y1))
im = im.resize((im.width * z, im.height * z), Image.NEAREST)
im = Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), 0.5)
dr = ImageDraw.Draw(im)
T = lambda p: ((p[0] - x0) * z, (p[1] - y0) * z)
for s in kit.parse_d(d):
    cur = np.array(s['start'])
    for g in s['segs']:
        if g[0] == 'L':
            dr.line([T(cur), T(g[1:3])], fill=(255, 0, 255), width=1)
            cur = np.array(g[1:3]); continue
        p0, p1, p2, p3 = cur, np.array(g[1:3]), np.array(g[3:5]), np.array(g[5:7])
        u = np.linspace(0, 1, 30)
        B, d1, d2 = F.bez(p0, p1, p2, p3, u), F.bez_d1(p0, p1, p2, p3, u), F.bez_d2(p0, p1, p2, p3, u)
        sp = np.linalg.norm(d1, axis=1)
        k = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum(sp ** 3, 1e-9)
        nrm = np.stack([-d1[:, 1], d1[:, 0]], 1) / np.maximum(sp[:, None], 1e-9)
        tips = B - nrm * (k * cs)[:, None]
        for b, t in zip(B, tips):
            dr.line([T(b), T(t)], fill=(90, 200, 90), width=1)
        dr.line([T(t) for t in tips], fill=(255, 220, 0), width=1)
        dr.line([T(b) for b in B], fill=(255, 60, 60), width=1)
        q = T(p3)
        dr.rectangle([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], outline=(255, 255, 255))
        cur = p3
im.save(out)
