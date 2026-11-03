import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_seg import label_cc
e = np.load(sys.argv[2] if len(sys.argv) > 2 else 'edge.npy'); dw = np.load('dwhite.npy')
fg = dw > 12
T = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
core = fg & (e < T)
core = kit.erode(core, 1)
lab = label_cc(core)
n = lab.max()
sizes = np.bincount(lab.ravel())
keep = np.where(sizes >= 40)[0]; keep = keep[keep > 0]
print('components', n, 'kept', len(keep))
remap = np.zeros(n + 1, int); remap[keep] = np.arange(1, len(keep) + 1)
lab = remap[lab]
# grow labels into remaining fg pixels
for it in range(30):
    un = fg & (lab == 0)
    if not un.any(): break
    for dy, dx in ((0,1),(0,-1),(1,0),(-1,0)):
        nb = np.roll(np.roll(lab, dy, 0), dx, 1)
        take = un & (nb > 0) & (lab == 0)
        lab[take] = nb[take]
np.save('lab.npy', lab)
rng = np.random.default_rng(3)
cols = rng.integers(40, 255, (lab.max() + 1, 3)); cols[0] = 255
vis = cols[lab].astype(np.uint8)
im = Image.fromarray(vis)
d = ImageDraw.Draw(im)
for k in range(1, lab.max() + 1):
    ys, xs = np.where(lab == k)
    if len(xs) == 0: continue
    print(k, len(xs), int(xs.mean()), int(ys.mean()))
im = im.crop((255, 215, 775, 615)).resize((1560, 1200), Image.NEAREST)
d = ImageDraw.Draw(im)
for k in range(1, lab.max() + 1):
    ys, xs = np.where(lab == k)
    # label at the most interior point: median
    i = len(xs)//2
    o = np.argsort(xs + 0.0001*ys)
    cx, cy = np.median(xs), np.median(ys)
    # pick member pixel nearest to median
    j = np.argmin((xs-cx)**2 + (ys-cy)**2)
    d.text(((xs[j]-255)*3, (ys[j]-215)*3), str(k), fill=(0,0,0))
im.save('labels.png')
