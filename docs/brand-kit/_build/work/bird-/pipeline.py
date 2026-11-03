"""mesh json -> optimised + simplified mesh pickle. Usage: pipeline.py mesh.json out.pkl"""
import sys, json, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model, try_collapse
from b_compact import compact
from b_drawmesh import draw
BOX = (258, 217, 768, 608)
def log(*a):
    print(*a, flush=True)

def prune(M, DEV=0.6, DE=30000):
    n = 0
    while True:
        best = None
        for v in sorted(M.inc):
            if not M.removable(v): continue
            dev = M.chord_dev(v)
            d = M.remove_delta(v)
            if (dev < DEV or d < DE) and (best is None or d < best[0]):
                best = (d, v, dev)
        if best is None: return n
        M.remove_delta(best[1], commit=True); n += 1
        log('  removed v%d dE %.0f dev %.2f' % (best[1], best[0], best[2]))

def collapse(M, LMAX=4.5, THR=150000):
    tried = set(); n = 0
    while True:
        E = set()
        for f in M.F:
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]; E.add((min(a, b), max(a, b)))
        E = sorted((np.hypot(*(M.V[a] - M.V[b])), a, b) for a, b in E)
        E = [e for e in E if e[0] < LMAX and (e[1], e[2]) not in tried]
        if not E: return n
        L, a, b = E[0]; tried.add((a, b))
        d = try_collapse(M, a, b, THR)
        if d is None: d = try_collapse(M, b, a, THR)
        if d is not None: n += 1
        log('  edge %d-%d len %.2f -> %s' % (a, b, L, 'kept' if d is None else 'collapsed dE %.0f' % d))

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    names = None
    if src.endswith('.json'):
        m = json.load(open(src)); cyc = m['cycles']
        V = np.array(m['verts']); F = [cyc[k] for k in sorted(cyc, key=int)]
    else:
        d = pickle.load(open(src, 'rb'))
        V, F = d[0], d[1]
        names = d[2] if len(d) > 2 else None
    img = kit.load('15')
    t = time.time()
    M = Model(img, V, F, BOX, ss=4)
    log('init err %.0f' % M.error())
    M.optimize(steps=(2.0, 1.0, 0.5), sweeps=4, log=log)
    log('pruned', prune(M)); log('collapsed', collapse(M))
    M.fit_colors(); M.render()
    M.optimize(steps=(1.0, 0.5, 0.25), sweeps=4, log=log)
    log('pruned', prune(M)); log('collapsed', collapse(M))
    M.fit_colors(); M.render()
    M.optimize(steps=(0.5, 0.25), sweeps=4, log=log)
    V, F = compact(M.V, M.F)
    pickle.dump((V, F, names) if names else (V, F), open(dst, 'wb'))
    log('final err %.0f verts %d time %.0f' % (M.error(), len(V), time.time() - t))
    cy = {i: f for i, f in enumerate(F)}
    draw(V, cy, 255, 215, 775, 615, 3, dst.replace('.pkl', '.png'), labels=False)
