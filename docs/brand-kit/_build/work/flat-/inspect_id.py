"""Error map (red = original only, green = vector only) + outline overlay for one built id.
usage: inspect_id.py <oid> <x0> <y0> <x1> <y1> <zoom>"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F
from flatlib import kit, np
from PIL import Image
import overlay as O

oid = sys.argv[1]
box = tuple(int(v) for v in sys.argv[2:6])
z = int(sys.argv[6])
a = kit.load(oid).astype(float)
H, W, _ = a.shape
bg = np.median(a[F.frame_mask(H, W)], 0)
r = np.asarray(Image.open(os.path.join(F.WORK, 'render_%s.png' % oid)).convert('RGB'), float)
L, C = F.lab_chroma(a)
fg = kit.bg_mask(a, kit.rgbhex(bg), 18)
cy = np.median(a[kit.erode(fg, 3) & (C >= 25)], 0)
mo = F.cov2(a, bg, cy) > 0.5
mr = F.cov2(r, F.NAVY, F.CYAN) > 0.5
err = np.zeros((H, W, 3), np.uint8)
err[mo & ~mr] = (255, 0, 0); err[mr & ~mo] = (0, 255, 0); err[mo & mr] = (60, 60, 60)
Image.fromarray(err).crop(box).resize(((box[2] - box[0]) * z, (box[3] - box[1]) * z), Image.NEAREST).save(
    os.path.join(F.WORK, 'err_%s.png' % oid))
svg = open(os.path.join(F.BUILD, 'components', 'flat-%s.svg' % oid)).read()
ds = [m.group(1) for m in re.finditer(r'<path id="[^"]+"[^>]* d="([^"]+)"', svg)]
O.overlay(oid, ds, box, z, os.path.join(F.WORK, 'ovl_%s.png' % oid))
print('orig-only', int((mo & ~mr).sum()), 'vector-only', int((mr & ~mo).sum()))
