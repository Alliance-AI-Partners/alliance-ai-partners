import sys, json, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model
from b_drawmesh import draw
src, dst = sys.argv[1], sys.argv[2]
steps = tuple(float(s) for s in sys.argv[3].split(','))
sweeps = int(sys.argv[4])
V, F = pickle.load(open(src, 'rb'))
img = kit.load('15')
box = (258, 217, 768, 608)
M = Model(img, V, F, box, ss=4)
print('start err', M.error())
t = time.time()
M.optimize(steps=steps, sweeps=sweeps)
print('time', time.time() - t)
pickle.dump((M.V, M.F), open(dst, 'wb'))
cy = {i: f for i, f in enumerate(M.F)}
draw(M.V, cy, 255, 215, 775, 615, 3, dst.replace('.pkl', '.png'), labels=False)
err = np.sqrt(((M.R - M.O) ** 2).mean(-1))
from PIL import Image
Image.fromarray(np.clip(err * 4, 0, 255).astype(np.uint8)).resize((err.shape[1] * 2, err.shape[0] * 2)).save(dst.replace('.pkl', '_err.png'))
