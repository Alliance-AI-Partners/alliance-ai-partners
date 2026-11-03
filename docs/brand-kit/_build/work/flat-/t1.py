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
al = np.clip(((a - bg) @ d) / (d @ d), 0, 1)
al = np.where(al < 0.1, 0, np.where(al > 0.9, 1, al))
clean = NAVY + al[..., None] * (CYAN - NAVY)
Image.fromarray(np.round(clean).astype(np.uint8)).save(os.path.join(W, 'clean12.png'))
t = time.time()
res = kit.trace_image(clean, ['#121B2A', '#00D5FF'])
print('time', round(time.time() - t, 1), 'n paths', len(res))
for d_, f in res:
    subs = kit.parse_d(d_)
    print(f, 'subpaths', len(subs), 'segs', [len(s['segs']) for s in subs][:20], d_[:100])
open(os.path.join(W, 't1.txt'), 'w').write(repr(res))
