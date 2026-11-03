import sys, pickle, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_export import boundary_loops
from b_place import similarity
V, F = pickle.load(open(sys.argv[1], 'rb'))
oid = sys.argv[2]; p = [float(v) for v in sys.argv[3].split(',')]
loops = [V[L] for L in boundary_loops(V, F)]
allm = np.concatenate(loops); mc = 0.5 * (allm.min(0) + allm.max(0))
A, t = similarity(p, mc)
img = kit.load(oid)
x0, y0, x1, y1 = [int(v) for v in sys.argv[4].split(',')]
z = 3
im = Image.fromarray(img[y0:y1, x0:x1]).resize(((x1-x0)*z, (y1-y0)*z), Image.LANCZOS)
d = ImageDraw.Draw(im)
for f in F:
    P = V[f] @ A.T + t
    pts = [((x - x0) * z, (y - y0) * z) for x, y in P]
    d.line(pts + [pts[0]], fill=(255, 0, 0), width=1)
im.save('place_%s.png' % oid)
