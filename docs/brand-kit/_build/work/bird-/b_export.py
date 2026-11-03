"""Facet colours -> linear gradients, seam extension, SVG / mono compound path writing."""
import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from b_fit import cover, signed_area


# ------------------------------------------------------------------ gradient fit
def fit_gradient(px, py, rgb, poly, w=None):
    """Least-squares rank-1 linear gradient C = a + b * s, s = projection on direction th.
    Returns dict(th, p1, p2, c1, c2, rms, rms_solid) with p1/p2 spanning the polygon's extent."""
    w = np.ones(len(px)) if w is None else w
    sw = np.sqrt(w)[:, None]
    cx, cy = np.average(px, weights=w), np.average(py, weights=w)
    X, Y = px - cx, py - cy

    def solve(th):
        s = X * np.cos(th) + Y * np.sin(th)
        A = np.stack([np.ones_like(s), s], 1)
        coef, *_ = np.linalg.lstsq(A * sw, rgb * sw, rcond=None)
        r = (A @ coef - rgb) ** 2
        return float((r.sum(1) * w).sum()), coef

    ths = np.linspace(0, np.pi, 72, endpoint=False)
    errs = [solve(t)[0] for t in ths]
    k = int(np.argmin(errs))
    lo, hi = ths[k] - np.pi / 72, ths[k] + np.pi / 72
    for _ in range(30):  # golden-section refine
        m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
        if solve(m1)[0] < solve(m2)[0]:
            hi = m2
        else:
            lo = m1
    th = 0.5 * (lo + hi)
    err, coef = solve(th)
    u = np.array([np.cos(th), np.sin(th)])
    sp = X * u[0] + Y * u[1]          # gradient vector spans the sampled interior: no extrapolated stops
    smin, smax = sp.min(), sp.max()
    c1 = coef[0] + coef[1] * smin
    c2 = coef[0] + coef[1] * smax
    mean = np.average(rgb, 0, weights=w)
    rms_solid = np.sqrt((((rgb - mean) ** 2).sum(1) * w).sum() / w.sum() / 3)
    return dict(th=th, p1=(cx + smin * u[0], cy + smin * u[1]), p2=(cx + smax * u[0], cy + smax * u[1]),
                c1=c1, c2=c2, mean=mean, rms=np.sqrt(err / w.sum() / 3), rms_solid=rms_solid,
                center=(cx, cy), coef=coef)


def grad_eval(g, px, py):
    """Evaluate a 2-stop gradient dict (with possibly snapped c1/c2) at points -> RGB (pad spread)."""
    p1, p2 = np.array(g['p1']), np.array(g['p2'])
    d = p2 - p1
    L2 = max(1e-9, float(d @ d))
    t = np.clip(((px - p1[0]) * d[0] + (py - p1[1]) * d[1]) / L2, 0, 1)
    c1, c2 = np.asarray(g['c1'], float), np.asarray(g['c2'], float)
    return c1 + t[..., None] * (c2 - c1)


# ------------------------------------------------------------------ geometry helpers
def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def line_isect(p, d, q, e):
    """Intersection of lines p + t d and q + s e (None if parallel)."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-9:
        return None
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return p + t * d


def edge_owner(F):
    """{frozenset(a,b): [facet indices]}"""
    own = {}
    for fi, f in enumerate(F):
        for k in range(len(f)):
            own.setdefault(frozenset((f[k], f[(k + 1) % len(f)])), []).append(fi)
    return own


def extend_facets(V, F, delta=1.0):
    """Push every edge a facet shares with a facet painted later (higher index) outward by delta,
    so the later facet covers the join: no hairline seams. Silhouette edges keep their lines; any
    extension that would show (not covered by this facet or a later one) is shrunk away.
    Returns list of polygons (arrays)."""
    own = edge_owner(F)
    exact = [V[f].astype(float) for f in F]

    def on_boundary(pt, P, eps=1e-3):
        a = P; b = np.roll(P, -1, 0)
        ab = b - a
        t = np.clip(((pt - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
        d = np.hypot(*(a + t[:, None] * ab - pt).T)
        return d.min() < eps

    def hidden(pt, fi):
        return on_boundary(pt, exact[fi]) or any(point_in_poly(pt, exact[fj]) for fj in range(fi, len(F)))

    out = []
    for fi, f in enumerate(F):
        P = exact[fi]
        n = len(f)
        dists, normals = [], []
        for k in range(n):
            a, b = f[k], f[(k + 1) % n]
            others = [o for o in own[frozenset((a, b))] if o != fi]
            dists.append(delta if others and min(others) > fi else 0.0)
            d = P[(k + 1) % n] - P[k]
            L = np.hypot(*d)
            nrm = np.array([d[1], -d[0]]) / max(L, 1e-9)
            if point_in_poly(0.5 * (P[k] + P[(k + 1) % n]) + 0.05 * nrm, P):
                nrm = -nrm
            normals.append(nrm)
            while dists[k] > 0.05 and not all(hidden(P[k] + t * d + dists[k] * nrm, fi) for t in np.linspace(0.05, 0.95, 19)):
                dists[k] *= 0.5
            if dists[k] <= 0.05:
                dists[k] = 0.0
        moves = []
        for k in range(n):
            kp = (k - 1) % n
            d0, d1 = dists[kp], dists[k]
            if d0 == 0 and d1 == 0:
                moves.append(np.zeros(2)); continue
            e_prev = P[k] - P[kp]; e_next = P[(k + 1) % n] - P[k]
            X = line_isect(P[kp] + d0 * normals[kp], e_prev, P[k] + d1 * normals[k], e_next)
            if X is None or np.hypot(*(X - P[k])) > 4 * delta:
                if d0 == 0 or d1 == 0:
                    X = P[k]                    # never leave a silhouette line
                else:
                    X = P[k] + 0.5 * (d0 * normals[kp] + d1 * normals[k])
            # sliding along an unmoved edge is only allowed outward (beyond the vertex): never shrink the facet
            if d0 == 0 and np.dot(X - P[k], e_prev) < 0:
                X = P[k]
            if d1 == 0 and np.dot(X - P[k], e_next) > 0:
                X = P[k]
            t = 1.0
            while t > 0.02 and not hidden(P[k] + t * (X - P[k]), fi):
                t *= 0.5
            moves.append((t if t > 0.02 else 0.0) * (X - P[k]))
        # every new edge must stay covered along its whole length; otherwise shrink its end moves
        for _ in range(8):
            bad = False
            for k in range(n):
                k2 = (k + 1) % n
                if dists[k] == 0 and not moves[k].any() and not moves[k2].any():
                    continue
                a, b = P[k] + moves[k], P[k2] + moves[k2]
                if not all(hidden(a + t * (b - a), fi) for t in np.linspace(0.0, 1.0, 41)):
                    moves[k] = moves[k] * 0.5; moves[k2] = moves[k2] * 0.5
                    bad = True
            if not bad:
                break
        else:
            moves = [np.zeros(2) for _ in range(n)]
        # the extended facet must contain the exact one (thin slivers can rotate inward): revert offending moves
        from b_poke import sub_inside
        bx0 = int(np.floor(P[:, 0].min())) - 3; by0 = int(np.floor(P[:, 1].min())) - 3
        bw = int(np.ceil(P[:, 0].max())) + 4 - bx0; bh = int(np.ceil(P[:, 1].max())) + 4 - by0
        inside0 = sub_inside(P, bx0, by0, bw, bh, 8)
        def lost(mv):
            return int((inside0 & ~sub_inside(np.array([P[k] + mv[k] for k in range(n)]), bx0, by0, bw, bh, 8)).sum())
        order = sorted(range(n), key=lambda k: -np.hypot(*moves[k]))
        for k in order:
            if lost(moves) == 0:
                break
            if moves[k].any():
                moves[k] = np.zeros(2)
        out.append(np.array([P[k] + moves[k] for k in range(n)]))
    return out


def boundary_loops(V, F):
    """Edges used by exactly one facet, chained into closed loops (vertex index lists).
    Walks undirected edges; at pinch vertices any continuation is fine for even-odd filling."""
    own = edge_owner(F)
    adj = {}
    for e, fs in own.items():
        if len(fs) == 1:
            a, b = tuple(e)
            adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    used = set()
    loops = []
    for a0 in sorted(adj):
        for b0 in adj[a0]:
            if frozenset((a0, b0)) in used:
                continue
            loop = [a0]; prev, cur = a0, b0
            used.add(frozenset((a0, b0)))
            while cur != a0:
                loop.append(cur)
                nxt = [c for c in adj[cur] if frozenset((cur, c)) not in used]
                if not nxt:
                    break
                # prefer the continuation that turns least sharply (keeps loops simple at pinches)
                d0 = V[cur] - V[prev]
                def turn(c):
                    d1 = V[c] - V[cur]
                    return -np.dot(d0, d1) / (np.hypot(*d0) * np.hypot(*d1) + 1e-9)
                c = min(nxt, key=turn)
                used.add(frozenset((cur, c))); prev, cur = cur, c
            loops.append(loop)
    return loops


def fmt(v):
    s = '%.2f' % v
    s = s.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def path_d(poly):
    return 'M' + ' L'.join('%s %s' % (fmt(x), fmt(y)) for x, y in poly) + ' Z'


def fit_gradient_k(px, py, rgb, poly, k=3, th0=None, w=None):
    """Piecewise-linear gradient with k stops (offsets 0, free..., 1) along one direction.
    Returns dict(th, p1, p2, offsets, colors, rms). Middle offsets scanned on a grid, direction around th0."""
    w = np.ones(len(px)) if w is None else np.asarray(w, float)
    sw = np.sqrt(w)[:, None]
    cx, cy = np.average(px, weights=w), np.average(py, weights=w)
    X, Y = px - cx, py - cy
    def basis(t, offs):
        B = np.zeros((len(t), len(offs)))
        for j in range(len(offs) - 1):
            a, b = offs[j], offs[j + 1]
            m = (t >= a) & (t <= b) if j == len(offs) - 2 else (t >= a) & (t < b)
            u = (t[m] - a) / max(b - a, 1e-9)
            B[m, j] += 1 - u; B[m, j + 1] += u
        return B
    def solve(th, offs):
        u = np.array([np.cos(th), np.sin(th)])
        sp = X * u[0] + Y * u[1]
        smin, smax = sp.min(), sp.max()
        t = np.clip((sp - smin) / max(smax - smin, 1e-9), 0, 1)
        B = basis(t, offs)
        C, *_ = np.linalg.lstsq(B * sw, rgb * sw, rcond=None)
        return float((((B @ C - rgb) ** 2).sum(1) * w).sum()), C, smin, smax, u
    ths = np.linspace(0, np.pi, 36, endpoint=False) if th0 is None else th0 + np.radians(np.linspace(-30, 30, 21))
    grid = [0.2, 0.35, 0.5, 0.65, 0.8] if k == 3 else [0.5]
    best = None
    for th in ths:
        for g in grid:
            offs = [0.0, g, 1.0] if k == 3 else [0.0, 1.0]
            e = solve(th, offs)
            if best is None or e[0] < best[0]:
                best = e + (th, offs)
    # local refine of th and the middle offset
    err, C, smin, smax, u, th, offs = best
    step_t, step_o = np.radians(2.0), 0.05
    for _ in range(25):
        improved = False
        for dth, do in ((step_t, 0), (-step_t, 0), (0, step_o), (0, -step_o)):
            o2 = list(offs)
            if k == 3:
                o2[1] = float(np.clip(o2[1] + do, 0.05, 0.95))
            e = solve(th + dth, o2)
            if e[0] < err - 1e-6:
                err, C, smin, smax, u = e; th = th + dth; offs = o2; improved = True
        if not improved:
            step_t *= 0.5; step_o *= 0.5
            if step_t < np.radians(0.05):
                break
    return dict(th=th, p1=(cx + smin * u[0], cy + smin * u[1]), p2=(cx + smax * u[0], cy + smax * u[1]),
                offsets=offs, colors=[np.clip(c, 0, 255) for c in C], rms=np.sqrt(err / w.sum() / 3))
