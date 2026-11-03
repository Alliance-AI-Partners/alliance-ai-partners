"""Manual topology fixes on p1.pkl -> p1f.pkl (facet indices 0-based in seed order)."""
import pickle, numpy as np
from b_seeds import SEEDS
N = {n: i for i, n in enumerate(SEEDS)}
V, F = pickle.load(open('p1.pkl', 'rb'))
V = [tuple(v) for v in np.asarray(V)]
def addv(x, y):
    V.append((float(x), float(y))); return len(V) - 1
def setf(name, cyc):
    F[N[name]] = list(cyc)
def merge(u, v):  # u -> v everywhere
    for i, f in enumerate(F):
        g = [v if w == u else w for w in f]
        F[i] = [w for k, w in enumerate(g) if w != g[k - 1]]
# wing: single hub (6), light/dark/blue converge there
merge(60, 6); merge(43, 6); merge(4, 6); merge(42, 0)
setf('wing-top-light', [0, 1, 6])
setf('wing-top-dark', [0, 41, 52, 6])
setf('wing-top-blue', [52, 6, 61])
setf('body-slate', [6, 61, 24, 23, 75])          # right edge hub -> 75 -> 23 -> 24 is the slate line
setf('wing2-dark', [47, 48, 51])
# shoulder / crossbar tip: one tip vertex T
T = 19; merge(18, T); merge(67, T)
setf('shoulder-top', [44, 16, T, 46, 45, 1])
setf('shoulder-mid', [1, 45, 46, 64, 11, 58, 6])
setf('crossbar-bright', [T, 32, 81, 29, 79])
setf('neck-blue', [16, T, 79, 80, 35, 66])
# leg
setf('leg-up-bright', [6, 59, 9, 17, 21, 76, 75])
setf('leg-twist-left', [23, 24, 28, 25, 21, 76, 75])
C = 77; merge(87, C)
P4 = addv(430, 508)
S = 86
J = 36; merge(90, J)
setf('leg-low-bright', [21, 26, 82, P4, 28, 25])
setf('leg-low-medium', [24, C, S, P4, 28])
setf('tail-upper-light', [C, 38, 89, J, S])
setf('tail-upper-dark', [J, 89, 38, 91, 95])
setf('tail-base', [82, P4, S, J, 95, 94, 92, 39, 83])
merge(84, 81)
setf('bottom-blue', [81, 32, 88, 37])
setf('bottom-cyan', [81, 37, 85, 31, 29])
V = np.array(V)
used = sorted({v for f in F for v in f})
print('facets', len(F), 'used verts', len(used))
for i, f in enumerate(F):
    print('%2d %-16s %s' % (i + 1, list(SEEDS)[i], f))
pickle.dump((V, F), open('p1f.pkl', 'wb'))
