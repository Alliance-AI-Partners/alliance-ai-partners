"""Fit a shared-vertex polygon mesh with per-facet colour fields to an original image.

Render model: R = W + sum_f cov_f * (C_f - W), cov_f = exact centre-sampled supersampled coverage,
C_f = per-facet colour field (affine per channel during geometry fitting).
Geometry is refined by coordinate descent on the squared RGB error."""
import numpy as np

WHITE = np.array([255.0, 255.0, 255.0])


def cover(poly, x0, y0, w, h, ss=4):
    """Coverage (h, w) of polygon `poly` ((n,2) image coords) over pixels [x0, x0+w) x [y0, y0+h)."""
    xa = poly[:, 0]; ya = poly[:, 1]
    xb = np.roll(xa, -1); yb = np.roll(ya, -1)
    H, Wd = h * ss, w * ss
    acc = np.zeros((H, Wd + 1), np.int32)
    for k in range(len(poly)):
        if ya[k] == yb[k]:
            continue
        lo, hi = (ya[k], yb[k]) if ya[k] < yb[k] else (yb[k], ya[k])
        m0 = max(int(np.ceil((lo - y0) * ss - 0.5)), 0)
        m1 = min(int(np.ceil((hi - y0) * ss - 0.5)), H)
        if m1 <= m0:
            continue
        yy = y0 + (np.arange(m0, m1) + 0.5) / ss
        xx = xa[k] + (yy - ya[k]) * (xb[k] - xa[k]) / (yb[k] - ya[k])
        col = np.clip(np.ceil((xx - x0) * ss - 0.5).astype(np.int64), 0, Wd)
        acc[np.arange(m0, m1), col] += 1 if yb[k] > ya[k] else -1
    inside = np.cumsum(acc[:, :-1], axis=1) != 0
    return inside.reshape(h, ss, w, ss).mean((1, 3), dtype=np.float32)


def seg_intersect(p1, p2, p3, p4):
    """Proper intersection test of segments p1p2 and p3p4 (shared endpoints excluded by caller)."""
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def signed_area(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


class Model:
    def __init__(self, img, verts, facets, box, ss=4):
        self.O = img[box[1]:box[3], box[0]:box[2]].astype(np.float64)
        self.box = box
        self.x0, self.y0 = box[0], box[1]
        self.h, self.w = self.O.shape[:2]
        self.V = np.array(verts, float)
        self.F = [list(f) for f in facets]
        self.ss = ss
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.px = xx + self.x0 + 0.5
        self.py = yy + self.y0 + 0.5
        self.rebuild()

    # ------------------------------------------------------------ incidence
    def incidence(self):
        self.inc = {}
        for fi, f in enumerate(self.F):
            for v in f:
                self.inc.setdefault(v, set()).add(fi)

    def poly(self, fi, V=None):
        V = self.V if V is None else V
        return V[self.F[fi]]

    # ------------------------------------------------------------ colours
    def full_cov(self, fi):
        return cover(self.poly(fi), self.x0, self.y0, self.w, self.h, self.ss)

    def fit_colors(self, model='affine'):
        self.C = []
        self.params = []
        for fi in range(len(self.F)):
            c = self.cov[fi]
            m = c >= 0.999
            # stay off edges: pixels whose 3x3 neighbourhood is fully inside
            mm = m.copy()
            mm[1:] &= m[:-1]; mm[:-1] &= m[1:]; mm[:, 1:] &= m[:, :-1]; mm[:, :-1] &= m[:, 1:]
            if mm.sum() < 12:
                mm = m if m.sum() >= 3 else (c > 0.5)
            X = np.stack([np.ones(mm.sum()), self.px[mm] - self.px[mm].mean(), self.py[mm] - self.py[mm].mean()], 1)
            cx, cy = self.px[mm].mean(), self.py[mm].mean()
            Y = self.O[mm]
            coef, *_ = np.linalg.lstsq(X, Y, rcond=None)    # (3, 3): rows = [const, gx, gy]
            self.params.append((cx, cy, coef))
            self.C.append(None)

    def color_field(self, fi, ys=slice(None), xs=slice(None)):
        cx, cy, coef = self.params[fi]
        px = self.px[ys, xs]; py = self.py[ys, xs]
        return coef[0] + (px - cx)[..., None] * coef[1] + (py - cy)[..., None] * coef[2]

    # ------------------------------------------------------------ render / error
    def rebuild(self):
        self.incidence()
        self.cov = [self.full_cov(fi) for fi in range(len(self.F))]
        self.fit_colors()
        self.render()

    def render(self):
        R = np.broadcast_to(WHITE, self.O.shape).copy()
        for fi in range(len(self.F)):
            R += self.cov[fi][..., None] * (self.color_field(fi) - WHITE)
        self.R = R
        return R

    def error(self):
        return float(((self.R - self.O) ** 2).sum())

    # ------------------------------------------------------------ local moves
    def _box_for(self, v, cand):
        pts = [self.V[v], cand]
        for fi in self.inc[v]:
            f = self.F[fi]
            k = f.index(v)
            pts.append(self.V[f[k - 1]]); pts.append(self.V[f[(k + 1) % len(f)]])
        pts = np.array(pts)
        x0 = int(np.floor(pts[:, 0].min())) - 1; x1 = int(np.ceil(pts[:, 0].max())) + 2
        y0 = int(np.floor(pts[:, 1].min())) - 1; y1 = int(np.ceil(pts[:, 1].max())) + 2
        x0 = max(x0, self.x0); y0 = max(y0, self.y0)
        x1 = min(x1, self.x0 + self.w); y1 = min(y1, self.y0 + self.h)
        return x0, y0, x1, y1

    def valid_move(self, v, cand):
        V2 = self.V.copy(); V2[v] = cand
        for fi in self.inc[v]:
            f = self.F[fi]
            P0, P1 = self.poly(fi), V2[f]
            a0, a1 = signed_area(P0), signed_area(P1)
            if a0 * a1 <= 0 or abs(a1) < 0.5:
                return False
            k = f.index(v); n = len(f)
            prev, nxt = f[k - 1], f[(k + 1) % n]
            new_edges = [(prev, v), (v, nxt)]
            for (a, b) in new_edges:
                for j in range(n):
                    c, d = f[j], f[(j + 1) % n]
                    if len({a, b, c, d}) < 4:
                        continue
                    if seg_intersect(V2[a], V2[b], V2[c], V2[d]):
                        return False
        return True

    def delta(self, v, cand, commit=False):
        bx0, by0, bx1, by1 = self._box_for(v, cand)
        if bx1 <= bx0 or by1 <= by0:
            return 0.0
        ys = slice(by0 - self.y0, by1 - self.y0); xs = slice(bx0 - self.x0, bx1 - self.x0)
        V2 = self.V.copy(); V2[v] = cand
        Rb = self.R[ys, xs]
        dR = np.zeros_like(Rb)
        news = {}
        for fi in self.inc[v]:
            cn = cover(V2[self.F[fi]], bx0, by0, bx1 - bx0, by1 - by0, self.ss)
            news[fi] = cn
            dR += (cn - self.cov[fi][ys, xs])[..., None] * (self.color_field(fi, ys, xs) - WHITE)
        Ob = self.O[ys, xs]
        d = float(((Rb + dR - Ob) ** 2).sum() - ((Rb - Ob) ** 2).sum())
        if commit:
            self.V[v] = cand
            for fi, cn in news.items():
                self.cov[fi][ys, xs] = cn
            self.R[ys, xs] = Rb + dR
        return d

    def optimize(self, steps=(2.0, 1.0, 0.5, 0.25, 0.125), sweeps=6, verts=None, fixed=(), log=print, refit=True):
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]
        verts = list(range(len(self.V))) if verts is None else list(verts)
        for h in steps:
            for sw in range(sweeps):
                moved = 0; gain = 0.0
                for v in verts:
                    if v in fixed or v not in self.inc:
                        continue
                    best, bd = None, -1e-6
                    for dx, dy in dirs:
                        cand = self.V[v] + (dx * h, dy * h)
                        if not self.valid_move(v, cand):
                            continue
                        d = self.delta(v, cand)
                        if d < bd:
                            best, bd = cand, d
                    if best is not None:
                        self.delta(v, best, commit=True)
                        moved += 1; gain += bd
                log(f'  step {h} sweep {sw}: moved {moved} gain {gain:.0f} err {self.error():.0f}')
                if moved == 0:
                    break
            if refit:  # refresh colours after each step size (geometry changed)
                self.fit_colors(); self.render()

    # ------------------------------------------------------------ topology edits
    def neighbors(self, v):
        nb = set()
        for fi in self.inc.get(v, ()):
            f = self.F[fi]; k = f.index(v)
            nb.add(f[k - 1]); nb.add(f[(k + 1) % len(f)])
        return nb

    def removable(self, v):
        return v in self.inc and len(self.neighbors(v)) == 2 and all(len(self.F[fi]) > 3 for fi in self.inc[v])

    def chord_dev(self, v):
        a, b = sorted(self.neighbors(v))
        A, B, P = self.V[a], self.V[b], self.V[v]
        ab = B - A
        return abs(ab[0] * (P[1] - A[1]) - ab[1] * (P[0] - A[0])) / max(1e-9, np.hypot(*ab))

    def remove_delta(self, v, commit=False):
        F2 = {fi: [u for u in self.F[fi] if u != v] for fi in self.inc[v]}
        R2 = self.R.copy()
        news = {}
        for fi, f in F2.items():
            cn = cover(self.V[f], self.x0, self.y0, self.w, self.h, self.ss)
            news[fi] = cn
            R2 += (cn - self.cov[fi])[..., None] * (self.color_field(fi) - WHITE)
        d = float(((R2 - self.O) ** 2).sum()) - self.error()
        if commit:
            for fi, f in F2.items():
                self.F[fi] = f; self.cov[fi] = news[fi]
            self.R = R2
            self.incidence()
        return d

    def collapse_delta(self, u, v, commit=False):
        """Merge vertex u into v (u's facets now use v)."""
        F2 = {}
        for fi in self.inc[u]:
            f = [v if w == u else w for w in self.F[fi]]
            g = [w for k, w in enumerate(f) if w != f[k - 1]]
            if len(g) < 3:
                return None
            F2[fi] = g
        R2 = self.R.copy(); news = {}
        for fi, f in F2.items():
            P = self.V[f]
            if abs(signed_area(P)) < 0.5:
                return None
            cn = cover(P, self.x0, self.y0, self.w, self.h, self.ss)
            news[fi] = cn
            R2 += (cn - self.cov[fi])[..., None] * (self.color_field(fi) - WHITE)
        d = float(((R2 - self.O) ** 2).sum()) - self.error()
        if commit:
            for fi, f in F2.items():
                self.F[fi] = f; self.cov[fi] = news[fi]
            self.R = R2
            self.incidence()
        return d


def snapshot(M):
    return (M.V.copy(), [f[:] for f in M.F], [c.copy() for c in M.cov], M.R.copy())


def restore(M, s):
    M.V, M.F, M.cov, M.R = s[0].copy(), [f[:] for f in s[1]], [c.copy() for c in s[2]], s[3].copy()
    M.incidence()


def try_collapse(M, u, v, thresh):
    """Merge u into v at the better of (u, v, midpoint), locally re-optimise, keep if error rises < thresh."""
    s = snapshot(M)
    e0 = M.error()
    best = None
    for pos in (M.V[v].copy(), M.V[u].copy(), 0.5 * (M.V[u] + M.V[v])):
        restore(M, s)
        M.V[v] = pos
        for fi in M.inc[v]:
            M.cov[fi] = M.full_cov(fi)
        M.render()
        d = M.collapse_delta(u, v, commit=True)
        if d is None:
            continue
        nb = set(M.neighbors(v)) | {v}
        M.optimize(steps=(1.0, 0.5, 0.25), sweeps=3, verts=sorted(nb), log=lambda *a: None, refit=False)
        e = M.error()
        if best is None or e < best[0]:
            best = (e, snapshot(M))
    if best is not None and best[0] - e0 < thresh:
        restore(M, best[1])
        return best[0] - e0
    restore(M, s)
    return None
