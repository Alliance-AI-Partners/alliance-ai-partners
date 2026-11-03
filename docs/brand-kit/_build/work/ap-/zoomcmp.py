"""Side-by-side zoom: original | render | dE heat for a box.  usage: zoomcmp.py render.svg x0 y0 x1 y1 scale out.png [orig_id]"""
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit

svg, x0, y0, x1, y1, s, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
oid = sys.argv[8] if len(sys.argv) > 8 else '06'
bg = sys.argv[9] if len(sys.argv) > 9 else '#FFFFFF'
orig = kit.load(oid).astype(float)
comp = kit.over(kit.render_svg(svg), bg)
de = kit.de2000(kit.srgb_to_lab(orig), kit.srgb_to_lab(comp))
box = (x0, y0, x1, y1)
sz = ((x1 - x0) * s, (y1 - y0) * s)
a = Image.fromarray(orig.astype(np.uint8)).crop(box).resize(sz, Image.NEAREST)
b = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).crop(box).resize(sz, Image.NEAREST)
t = np.clip(de / 10, 0, 1)[..., None]
h = Image.fromarray((255 * (1 - t) + np.array([220, 30, 30]) * t).astype(np.uint8)).crop(box).resize(sz, Image.NEAREST)
sheet = Image.new('RGB', (sz[0] * 3 + 20, sz[1]), 'white')
for k, im in enumerate((a, b, h)):
    sheet.paste(im, (k * (sz[0] + 10), 0))
sheet.save(out)
reg = de[y0:y1, x0:x1]
print('box dE mean %.2f p95 %.2f' % (reg.mean(), np.percentile(reg, 95)))
