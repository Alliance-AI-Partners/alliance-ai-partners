import sys, json, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model, try_collapse
from b_drawmesh import draw
src, dst = sys.argv[1], sys.argv[2]
LMAX, THR = float(sys.argv[3]), float(sys.argv[4])
V, F = pickle.load(open(src, 'rb'))
img = kit.load('15')
M = Model(img, V, F, (258, 217, 768, 608), ss=4)
print('start err %.0f verts %d' % (M.error(), len(M.inc)))
tried = set()
while True:
    E = set()
    for f in M.F:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]; E.add((min(a, b), max(a, b)))
    E = sorted((np.hypot(*(M.V[a] - M.V[b])), a, b) for a, b in E)
    E = [e for e in E if e[0] < LMAX and (e[1], e[2]) not in tried]
    if not E: break
    L, a, b = E[0]
    tried.add((a, b))
    d = try_collapse(M, a, b, THR)
    if d is None:
        d = try_collapse(M, b, a, THR)
    print('edge %d-%d len %.2f -> %s' % (a, b, L, 'kept' if d is None else 'collapsed dE %.0f' % d))
M.fit_colors(); M.render()
print('err %.0f verts %d' % (M.error(), len(M.inc)))
pickle.dump((M.V, M.F), open(dst, 'wb'))
cy = {i: f for i, f in enumerate(M.F)}
draw(M.V, cy, 255, 215, 775, 615, 3, dst.replace('.pkl', '.png'), labels=False)
