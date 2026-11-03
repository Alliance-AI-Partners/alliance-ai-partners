
"""Final geometry refinement: p2f.pkl -> p3.pkl (ss=4 coarse, prune, ss=8 fine)."""
import sys, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model, cover
from b_compact import compact
from b_check import lint
from pipeline import prune, BOX, log
src, dst = sys.argv[1], sys.argv[2]
V, F, names = pickle.load(open(src, 'rb'))
from collections import Counter
E = Counter(frozenset((f[k], f[(k + 1) % len(f)])) for f in F for k in range(len(f)))
log('edge multiplicities', dict(Counter(E.values())))
img = kit.load('15')
t = time.time()
M = Model(img, V, F, BOX, ss=4)
log('start err %.0f' % M.error())
M.optimize(steps=(1.0, 0.5, 0.25), sweeps=4, log=log)
log('pruned', prune(M, DEV=0.5, DE=20000))
M.fit_colors(); M.render()
M8 = Model(img, M.V, M.F, BOX, ss=8)
log('ss8 err %.0f' % M8.error())
M8.optimize(steps=(0.25, 0.125), sweeps=3, log=log)
V2, F2 = compact(M8.V, M8.F)
S = np.zeros((BOX[3] - BOX[1], BOX[2] - BOX[0]))
for f in F2: S += cover(V2[f], BOX[0], BOX[1], BOX[2] - BOX[0], BOX[3] - BOX[1], 4)
log('max coverage sum %.3f' % S.max())
for line in lint(V2, F2, names=names): log(line)
pickle.dump((V2, F2, names), open(dst, 'wb'))
log('final err %.0f verts %d time %.0f' % (M8.error(), len(V2), time.time() - t))
