import sys, json, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model
from b_drawmesh import draw
src, dst = sys.argv[1], sys.argv[2]
DEV, DE, SHORT, DECOL = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
V, F = pickle.load(open(src, 'rb'))
img = kit.load('15')
M = Model(img, V, F, (258, 217, 768, 608), ss=4)
print('start err %.0f verts %d' % (M.error(), len(M.inc)))
# 1. prune bends
while True:
    best = None
    for v in sorted(M.inc):
        if not M.removable(v): continue
        dev = M.chord_dev(v)
        if dev >= DEV and dev >= 1.0 and True:
            pass
        d = M.remove_delta(v)
        if (dev < DEV or d < DE) and (best is None or d < best[0]):
            best = (d, v, dev)
    if best is None: break
    M.remove_delta(best[1], commit=True)
    print('removed v%d dE %.0f dev %.2f' % (best[1], best[0], best[2]))
# 2. collapse short edges
changed = True
while changed:
    changed = False
    edges = set()
    for f in M.F:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            edges.add((min(a, b), max(a, b)))
    cands = []
    for a, b in edges:
        L = np.hypot(*(M.V[a] - M.V[b]))
        if L < SHORT:
            for u, v in ((a, b), (b, a)):
                d = M.collapse_delta(u, v)
                if d is not None: cands.append((d, u, v, L))
    cands.sort()
    if cands and cands[0][0] < DECOL:
        d, u, v, L = cands[0]
        M.collapse_delta(u, v, commit=True)
        print('collapsed v%d -> v%d (len %.2f) dE %.0f' % (u, v, L, d))
        changed = True
print('after topology: err %.0f verts %d' % (M.error(), len(M.inc)))
M.fit_colors(); M.render()
M.optimize(steps=(1.0, 0.5, 0.25), sweeps=4)
pickle.dump((M.V, M.F), open(dst, 'wb'))
draw(M.V, {i: f for i, f in enumerate(M.F)}, 255, 215, 775, 615, 3, dst.replace('.pkl', '.png'), labels=False)
print('final err %.0f verts %d' % (M.error(), len(M.inc)))
