
"""Topology fixes on p2.pkl -> p2f.pkl."""
import pickle, numpy as np
from b_seeds import SEEDS
from b_check import lint
N = {n: i for i, n in enumerate(SEEDS)}
V, F = pickle.load(open('p2.pkl', 'rb'))
V = [tuple(v) for v in np.asarray(V)]
def get(name): return F[N[name]]
def setf(name, cyc): F[N[name]] = list(cyc)
def merge(u, v):
    for i, f in enumerate(F):
        g = [v if w == u else w for w in f]
        F[i] = [w for k, w in enumerate(g) if w != g[k - 1]]
def drop(name, v):
    F[N[name]] = [w for w in F[N[name]] if w != v]
# leg: L1 ends on the line 60-14; no spike down the fold
merge(61, 14)
drop('leg-up-bright', 17)
# neck tip: one tip vertex; neck-blue / neck-bright boundary runs 13 -> tip
merge(52, 64)
drop('neck-blue', 26)
# head: the crown back corner 44 sits on the head's top edge
drop('head-top', 3)
# tail base / lower prong: one corner; 29 is collinear on the silhouette
merge(67, 73)
drop('tail-base', 29)
drop('tail-lower-light', 29)
# neck rim highlight: own facet (keeps neck-bright convex-ish)
nb = get('neck-bright')
assert nb[:3] == [10, 16, 53], nb
setf('neck-bright', [10] + nb[2:])
names = list(SEEDS) + ['neck-rim']
F.append([10, 16, 53])
# cyclic de-duplication
for i, f in enumerate(F):
    F[i] = [w for k, w in enumerate(f) if w != f[k - 1]]
V = np.array(V)
pickle.dump((V, F, names), open('p2f.pkl', 'wb'))
for line in lint(V, F, names=names): print(line)
for i, f in enumerate(F): print(i + 1, names[i], f)
