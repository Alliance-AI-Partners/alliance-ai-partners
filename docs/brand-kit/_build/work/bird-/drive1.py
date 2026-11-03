import sys, json, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model
from b_drawmesh import draw
m = json.load(open('mesh0.json'))
verts = np.array(m['verts']); cyc = m['cycles']
facets = [cyc[str(f)] for f in range(1, 32)]
img = kit.load('15')
box = (258, 217, 768, 608)
t = time.time()
M = Model(img, verts, facets, box, ss=4)
print('init err', M.error(), 'time', time.time() - t)
t = time.time()
M.optimize(steps=(2.0, 1.0), sweeps=3)
print('time', time.time() - t)
pickle.dump((M.V, M.F), open('m1.pkl', 'wb'))
