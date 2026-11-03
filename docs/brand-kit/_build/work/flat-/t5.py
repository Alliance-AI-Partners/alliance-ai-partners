import sys, os, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-')
import flatlib as F
from flatlib import kit, np
from PIL import Image

W = F.WORK
a = kit.load('12').astype(float)
bg, cy = kit.hexrgb('#121F32'), kit.hexrgb('#1CC5EB')
al_o = F.cov2(a, bg, cy)
res = eval(open(os.path.join(W, 't1.txt')).read())
cyan_d = [p for p, f in res if f == '#00D5FF'][0]
t = time.time()
d, info = F.refit_path(cyan_d)
print('refit time', round(time.time() - t, 2), info)
open(os.path.join(W, 't5_d.txt'), 'w').write(d)
body = '<rect id="bg" width="1024" height="1024" fill="#121B2A"/><path fill="#00D5FF" d="%s"/>' % d
svg = kit.svg_doc(1024, 1024, body)
r = F.render_rgb(svg)
al_r = F.cov2(r, F.NAVY, F.CYAN)
mo, mr = al_o > 0.5, al_r > 0.5
print('IoU', round(kit.iou(mo, mr), 5), mo.sum(), mr.sum())
Image.fromarray(np.round(r).astype(np.uint8)).save(os.path.join(W, 'r12_fit.png'))
err = np.zeros(a.shape, np.uint8)
err[mo & ~mr] = (255, 0, 0); err[mr & ~mo] = (0, 255, 0); err[mo & mr] = (60, 60, 60)
Image.fromarray(err).save(os.path.join(W, 'e12_fit.png'))
# anchor overlay: draw nodes on a 2x render
big = Image.fromarray(np.round(r).astype(np.uint8)).resize((2048, 2048), Image.NEAREST)
from PIL import ImageDraw
dr = ImageDraw.Draw(big)
for s in kit.parse_d(d):
    pts = [s['start']] + [g[-2:] for g in s['segs']]
    for g, p in zip(s['segs'], pts[1:]):
        col = (255, 60, 60) if g[0] == 'L' else (255, 255, 0)
        dr.ellipse([p[0] * 2 - 4, p[1] * 2 - 4, p[0] * 2 + 4, p[1] * 2 + 4], outline=col, width=2)
big.save(os.path.join(W, 'n12_fit.png'))
