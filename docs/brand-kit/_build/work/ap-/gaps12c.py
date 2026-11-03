import sys
from collections import deque
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from PIL import Image
alpha = np.load(kit.WORK / 'ap-' / 'alpha12.npy')
mask = alpha > 0.5
closed = kit.erode(kit.dilate(mask, 6), 6)
gap = closed & ~mask

def component(seed):
    sy, sx = seed[1], seed[0]
    # nearest gap pixel to the seed
    ys, xs = np.nonzero(gap[sy-6:sy+7, sx-6:sx+7])
    k = np.argmin((ys-6)**2 + (xs-6)**2); sy, sx = sy - 6 + ys[k], sx - 6 + xs[k]
    seen = np.zeros_like(gap); seen[sy, sx] = True; q = deque([(sy, sx)])
    while q:
        y, x = q.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if gap[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; q.append((yy, xx))
    return seen

out = {}
for k, seed in (('a', (300, 552)), ('b', (575, 520))):
    g = component(seed)
    ys, xs = np.nonzero(g)
    print(k, 'pixels', len(ys), 'x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
    out[k] = g
viz = np.zeros(alpha.shape + (3,), np.uint8); viz[..., 1] = (alpha * 200).astype(np.uint8)
viz[out['a']] = [255, 0, 0]; viz[out['b']] = [255, 255, 0]
Image.fromarray(viz).crop((200, 290, 840, 700)).save(kit.WORK / 'ap-' / 'gaps12_viz.png')
np.save(kit.WORK / 'ap-' / 'gap12_a.npy', out['a']); np.save(kit.WORK / 'ap-' / 'gap12_b.npy', out['b'])
