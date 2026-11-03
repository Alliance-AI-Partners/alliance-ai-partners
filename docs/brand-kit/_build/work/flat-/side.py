"""Original | vector render crops side by side, zoomed. usage: side.py <oid> <x0> <y0> <x1> <y1> <zoom> <out>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F
from flatlib import kit
from PIL import Image

oid = sys.argv[1]
box = tuple(int(v) for v in sys.argv[2:6])
z = int(sys.argv[6])
o = Image.open(kit.orig(oid)).convert('RGB').crop(box)
r = Image.open(os.path.join(F.WORK, 'render_%s.png' % oid)).convert('RGB').crop(box)
w, h = o.size
s = Image.new('RGB', (w * z * 2 + 8, h * z), 'white')
s.paste(o.resize((w * z, h * z), Image.NEAREST), (0, 0))
s.paste(r.resize((w * z, h * z), Image.NEAREST), (w * z + 8, 0))
s.save(os.path.join(F.WORK, sys.argv[7]))
