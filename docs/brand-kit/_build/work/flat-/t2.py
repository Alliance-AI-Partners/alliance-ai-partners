import sys, os, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from PIL import Image

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-'
NAVY, CYAN = kit.hexrgb('#121B2A'), kit.hexrgb('#00D5FF')

a = kit.load('12').astype(float)
bg, cy = kit.hexrgb('#121F32'), kit.hexrgb('#1CC5EB')
d = cy - bg
al_o = np.clip(((a - bg) @ d) / (d @ d), 0, 1)

res = eval(open(os.path.join(W, 't1.txt')).read())
cyan_d = [p for p, f in res if f == '#00D5FF']
body = '<rect id="bg" width="1024" height="1024" fill="#121B2A"/>' + ''.join(
    f'<path fill="#00D5FF" fill-rule="evenodd" d="{p}"/>' for p in cyan_d)
svg = kit.svg_doc(1024, 1024, body)
rgba = kit.render_svg(svg, 1)
r = kit.over(rgba, '#121B2A')
dd = CYAN - NAVY
al_r = np.clip(((r - NAVY) @ dd) / (dd @ dd), 0, 1)
mo, mr = al_o > 0.5, al_r > 0.5
print('IoU', kit.iou(mo, mr), 'orig px', mo.sum(), 'render px', mr.sum(), 'coverage sum orig', al_o[al_o > 0.05].sum().round(), 'render', al_r.sum().round())
# our own rasterizer as cross-check
cov = kit.raster(cyan_d, 1024, 1024)
print('IoU kit.raster', kit.iou(mo, cov > 0.5), 'cov sum', cov.sum().round())
c = kit.compare(a, r)
print('dE mean', c['de_mean'], 'p95', c['de_p95'])
Image.fromarray(np.round(r).astype(np.uint8)).save(os.path.join(W, 'r12_raw.png'))
# error image: red = orig only, green = render only
err = np.zeros(a.shape, np.uint8)
err[mo & ~mr] = (255, 0, 0); err[mr & ~mo] = (0, 255, 0); err[mo & mr] = (60, 60, 60)
Image.fromarray(err).save(os.path.join(W, 'e12_raw.png'))
