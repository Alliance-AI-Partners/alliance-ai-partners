import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_ws import watershed
from b_seeds import SEEDS
e = np.load('edge_s.npy'); dw = np.load('dwhite.npy')
fg = dw > 10
names = list(SEEDS)
im = Image.new('I', (1024, 1024), 0); d = ImageDraw.Draw(im)
for i, n in enumerate(names, 1):
    d.line(SEEDS[n], fill=i, width=1)
s = np.asarray(im, np.int64)
s[(e > 3.0) | (dw < 15)] = 0          # keep seed pixels only in calm facet interiors
for i, n in enumerate(names, 1):
    if not (s == i).any(): print('EMPTY seed', n)
lab = watershed(e, s, fg)
np.save('ws_m.npy', lab)
print(' '.join('%d:%s:%d' % (i, n, int((lab == i).sum())) for i, n in enumerate(names, 1)))
