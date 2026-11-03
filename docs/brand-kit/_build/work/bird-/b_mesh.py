"""Planar mesh from a facet label map: shared vertices, facet polygons as vertex cycles.

lab: (H, W) int, 0 = background (white gaps + outside), 1..N = facets.
Boundary chains are traced on the pixel-corner lattice between junction corners (3+ labels),
nearby junctions are clustered, chains are simplified with Douglas-Peucker."""
import numpy as np


def _dp(pts, tol):
    """Douglas-Peucker on an open polyline (list of (x, y)); returns kept indices."""
    pts = np.asarray(pts, float)
    keep = [0, len(pts) - 1]
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        L = np.hypot(*ab)
        seg = pts[i + 1:j]
        if L < 1e-9:
            d = np.hypot(*(seg - a).T)
        else:
            d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / L
        k = int(np.argmax(d))
        if d[k] > tol:
            m = i + 1 + k
            keep.append(m)
            stack += [(i, m), (m, j)]
    return sorted(set(keep))


def build(lab, tol=1.2, cluster=3.0):
    H, W = lab.shape
    P = np.zeros((H + 2, W + 2), lab.dtype)
    P[1:-1, 1:-1] = lab
    # corner (i, j) in padded-corner coords sits between padded pixels (i-1..i, j-1..j);
    # image coords of corner = (x=j-1, y=i-1)
    # horizontal lattice edge (i, j)-(i, j+1): between padded pixel (i-1, j) above and (i, j) below
    hb = P[:-1, :] != P[1:, :]          # shape (H+1, W+2): hb[i, j] edge between rows i, i+1 at col j
    vb = P[:, :-1] != P[:, 1:]          # shape (H+2, W+1)
    # corner degree: corner (i, j) (i in 1..H+1, j in 1..W+1 in padded-corner indexing)
    # incident edges: h-edge left  = hb[i-1, j-1], h-edge right = hb[i-1, j]; v-edge up = vb[i-1, j-1], v-edge down = vb[i, j-1]
    def edges_at(i, j):
        out = []
        if hb[i - 1, j - 1]: out.append((i, j - 1))
        if hb[i - 1, j]:     out.append((i, j + 1))
        if vb[i - 1, j - 1]: out.append((i - 1, j))
        if vb[i, j - 1]:     out.append((i + 1, j))
        return out

    junction = {}
    # find corners with >= 3 labels or checkerboard 2-label degree-4
    a = P[:-1, :-1]; b = P[:-1, 1:]; c = P[1:, :-1]; d = P[1:, 1:]
    nlab = (1 + (b != a) + ((c != a) & (c != b)) + ((d != a) & (d != b) & (d != c)))
    checker = (a == d) & (b == c) & (a != b)
    J = (nlab >= 3) | checker
    for i, j in zip(*np.nonzero(J)):
        junction[(i + 1, j + 1)] = True   # J[r, c] is the corner between padded pixels r..r+1, c..c+1
    # trace chains
    visited = set()
    chains = []
    def ekey(p, q):
        return (p, q) if p < q else (q, p)
    for (i, j) in list(junction):
        for q in edges_at(i, j):
            if ekey((i, j), q) in visited:
                continue
            path = [(i, j), q]
            visited.add(ekey((i, j), q))
            prev, cur = (i, j), q
            while cur not in junction:
                nxt = [r for r in edges_at(*cur) if r != prev]
                if len(nxt) != 1:
                    break
                visited.add(ekey(cur, nxt[0]))
                prev, cur = cur, nxt[0]
                path.append(cur)
            chains.append(path)
    # labels on each side of a chain: take the first lattice edge
    def side_labels(p, q):
        (i0, j0), (i1, j1) = p, q
        if i0 == i1:   # horizontal edge, col min(j0, j1)
            jj = min(j0, j1)
            return frozenset((P[i0 - 1, jj], P[i0, jj]))
        ii = min(i0, i1)
        return frozenset((P[ii, j0 - 1], P[ii, j0]))
    # cluster junctions
    jl = list(junction)
    jxy = np.array([(j - 1.0, i - 1.0) for i, j in jl])
    parent = list(range(len(jl)))
    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]; k = parent[k]
        return k
    for k in range(len(jl)):
        dd = np.hypot(*(jxy - jxy[k]).T)
        for m in np.nonzero(dd <= cluster)[0]:
            ra, rb = find(k), find(m)
            if ra != rb: parent[ra] = rb
    groups = {}
    for k in range(len(jl)):
        groups.setdefault(find(k), []).append(k)
    jvert = {}
    verts = []
    for g, members in groups.items():
        verts.append(tuple(jxy[members].mean(0)))
        for m in members:
            jvert[jl[m]] = len(verts) - 1
    # simplify chains into vertex sequences
    edges = []   # (labels frozenset, [vertex ids])
    for path in chains:
        labs = side_labels(path[0], path[1])
        if path[-1] not in junction:
            continue  # open/odd chain (should not happen)
        va, vb_ = jvert[path[0]], jvert[path[-1]]
        if va == vb_ and len(path) < 4 * cluster:
            continue  # collapsed inside a cluster
        xy = [(j - 1.0, i - 1.0) for i, j in path]
        xy[0] = verts[va]; xy[-1] = verts[vb_]
        keep = _dp(xy, tol)
        ids = [va]
        for k in keep[1:-1]:
            verts.append(xy[k]); ids.append(len(verts) - 1)
        ids.append(vb_)
        edges.append((labs, ids))
    return np.array(verts), edges


def facet_cycles(edges, nfacets):
    """Assemble each facet's boundary into an ordered vertex cycle from the chains that touch it."""
    cycles = {}
    for f in range(1, nfacets + 1):
        segs = [ids[:] for labs, ids in edges if f in labs]
        if not segs:
            continue
        # chain the segments end to end
        cyc = segs.pop(0)
        guard = 0
        while segs and guard < 1000:
            guard += 1
            end = cyc[-1]
            for k, s in enumerate(segs):
                if s[0] == end:
                    cyc += s[1:]; segs.pop(k); break
                if s[-1] == end:
                    cyc += s[::-1][1:]; segs.pop(k); break
            else:
                break
        if cyc[0] == cyc[-1]:
            cyc = cyc[:-1]
        cycles[f] = (cyc, len(segs))
    return cycles
