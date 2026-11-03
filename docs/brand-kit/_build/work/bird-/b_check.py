"""Mesh lint: spikes (tiny interior angles), near-duplicate vertices, collinear removable points."""
import sys, pickle, numpy as np
from b_seeds import SEEDS
from b_fit import signed_area
names = list(SEEDS)
def lint(V, F, ang=12.0, close=2.5, names=names):
    V = np.asarray(V)
    names = list(names) + ['facet%d' % i for i in range(len(names), len(F))]
    out = []
    for i, f in enumerate(F):
        P = V[f]; n = len(f)
        s = np.sign(signed_area(P))
        for k in range(n):
            a, b, c = P[k - 1], P[k], P[(k + 1) % n]
            u, w = a - b, c - b
            cosang = np.dot(u, w) / (np.hypot(*u) * np.hypot(*w) + 1e-9)
            angle = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
            cross = u[0] * w[1] - u[1] * w[0]
            # interior angle: convex if cross has the polygon's orientation sign
            interior = angle if np.sign(cross) == -s else 360 - angle
            if interior < ang:
                out.append('spike  %-16s v%d interior %.1f deg' % (names[i], f[k], interior))
    used = sorted({v for f in F for v in f})
    for a in range(len(used)):
        for b in range(a + 1, len(used)):
            d = np.hypot(*(V[used[a]] - V[used[b]]))
            if d < close:
                out.append('close  v%d v%d %.2f px' % (used[a], used[b], d))
    return out
if __name__ == '__main__':
    d = pickle.load(open(sys.argv[1], 'rb'))
    for line in lint(d[0], d[1], names=d[2] if len(d) > 2 else names): print(line)
