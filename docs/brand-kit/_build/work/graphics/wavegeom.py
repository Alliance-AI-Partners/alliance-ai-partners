"""Wave geometry from the fitted model (fit/graphic-wave_fit.json): edge / boundary curves as cubic
splines in x, face outlines, glow offsets with round caps, and cubic-Bezier conversion with known
tangents (few anchors)."""
import json
import numpy as np
from wavefit import evaluate

FIT = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\fit\graphic-wave_fit.json'


def load(path=FIT):
    return json.load(open(path))


class Curve:
    """y(x) on [x0, x1] given by a (natural or clamped) cubic spline."""

    def __init__(self, knots, vals, clamp=None):
        self.k, self.v, self.c = np.asarray(knots, float), np.asarray(vals, float), clamp
        self.x0, self.x1 = float(self.k[0]), float(self.k[-1])

    def __call__(self, xs):
        return evaluate(self.k, self.v, np.atleast_1d(np.asarray(xs, float)), clamp=self.c)

    def d(self, xs, eps=1e-4):
        xs = np.atleast_1d(np.asarray(xs, float))
        return (self(xs + eps) - self(xs - eps)) / (2 * eps)


def curves(M):
    ek = M["edge_knots"]
    top, bot = Curve(ek, M["top"]), Curve(ek, M["bot"])
    B = {n: Curve(b["knots"], b["vals"], tuple(b["clamp"])) for n, b in M["bounds"].items()}
    return top, bot, B


class Piece:
    """A run of curve y(x) from xa to xb, optionally offset by r along the normal on side +1 (up, -y)
    or -1 (down, +y)."""

    def __init__(self, curve, xa, xb, r=0.0, side=1):
        self.cv, self.xa, self.xb, self.r, self.side = curve, float(xa), float(xb), float(r), side

    def sample(self, n=None):
        n = n or max(30, int(abs(self.xb - self.xa) * 2.5))
        xs = np.linspace(self.xa, self.xb, n)
        y, dy = self.cv(xs), self.cv.d(xs)
        nrm = np.sqrt(1 + dy ** 2)
        nx, ny = self.side * dy / nrm, -self.side / nrm
        q = np.stack([xs + self.r * nx, y + self.r * ny], -1)
        sgn = 1.0 if self.xb > self.xa else -1.0
        tv = np.stack([np.full_like(xs, sgn), sgn * dy], -1) / nrm[:, None]
        return q, tv

    def pts(self):
        return self.sample()[0]


def faces(M):
    """Face name -> list of pieces forming a closed outline (clockwise on screen)."""
    top, bot, B = curves(M)
    XL, XR = M["XL"], M["XR"]
    b1, b2, b3 = B["B1"], B["B2"], B["B3"]
    return {
        "A": [Piece(top, XL, b1.x1), Piece(b1, b1.x1, XL)],
        "B": [Piece(b1, XL, b1.x1), Piece(top, b1.x1, b2.x1), Piece(b2, b2.x1, b2.x0), Piece(bot, b2.x0, XL)],
        "C": [Piece(b2, b2.x0, b2.x1), Piece(top, b2.x1, XR), Piece(b3, XR, b3.x0), Piece(bot, b3.x0, b2.x0)],
        "D": [Piece(b3, b3.x0, XR), Piece(bot, XR, b3.x0)],
        "ribbon": [Piece(top, XL, XR), Piece(bot, XR, XL)],
    }


def outline(pieces):
    return np.concatenate([p.pts() for p in pieces])


# ------------------------------------------------------------- Bezier fitting with known end tangents

def _bez(P, u):
    u = u[:, None]
    return ((1 - u) ** 3) * P[0] + 3 * ((1 - u) ** 2) * u * P[1] + 3 * (1 - u) * u ** 2 * P[2] + u ** 3 * P[3]


def _fit1(q, t0, t1, iters=5):
    """One cubic through q[0], q[-1] with unit tangents t0 (forward at start) and t1 (backward at end)."""
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
    L = d[-1]
    u = d / L
    P = None
    for _ in range(iters):
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
        A1, A2 = b1[:, None] * t0, b2[:, None] * t1
        rhs = q - (b0 + b1)[:, None] * q[0] - (b2 + b3)[:, None] * q[-1]
        C = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
        X = np.array([np.sum(A1 * rhs), np.sum(A2 * rhs)])
        try:
            a, b = np.linalg.solve(C, X)
        except np.linalg.LinAlgError:
            a = b = L / 3
        if not (1e-3 * L < a < 2 * L) or not (1e-3 * L < b < 2 * L):
            a = b = L / 3
        P = np.array([q[0], q[0] + a * t0, q[-1] + b * t1, q[-1]])
        Bq = _bez(P, u) - q
        d1 = (3 * ((1 - u) ** 2)[:, None] * (P[1] - P[0]) + 6 * ((1 - u) * u)[:, None] * (P[2] - P[1])
              + 3 * (u ** 2)[:, None] * (P[3] - P[2]))
        d2 = 6 * (1 - u)[:, None] * (P[2] - 2 * P[1] + P[0]) + 6 * u[:, None] * (P[3] - 2 * P[2] + P[1])
        num = np.sum(Bq * d1, 1)
        den = np.sum(d1 * d1, 1) + np.sum(Bq * d2, 1)
        u = np.clip(u - np.where(np.abs(den) > 1e-12, num / den, 0), 0, 1)
        u[0], u[-1] = 0, 1
        u = np.maximum.accumulate(u)
    err = np.linalg.norm(_bez(P, u) - q, axis=1)
    return P, float(err.max())


def fit_beziers(q, tv, tol=0.1):
    """Few cubic segments with max error <= tol: greedy longest feasible segment from each anchor,
    found by binary search (fit error grows with span). q: dense samples, tv: unit forward tangents."""
    n = len(q)
    out, i = [], 0
    while i < n - 1:
        lo, hi = i + 1, n - 1
        P, e = _fit1(q[i:hi + 1], tv[i], -tv[hi])
        if e <= tol:
            out.append(P)
            break
        bestP = _fit1(q[i:lo + 1], tv[i], -tv[lo])[0]
        while hi - lo > 1:
            mid = (lo + hi) // 2
            P, e = _fit1(q[i:mid + 1], tv[i], -tv[mid])
            if e <= tol:
                lo, bestP = mid, P
            else:
                hi = mid
        out.append(bestP)
        i = lo
    return out


def piece_beziers(piece, tol=0.1):
    q, tv = piece.sample()
    return fit_beziers(q, tv, tol)


def arc_beziers(c, r, a0, a1):
    """Circular arc around c from angle a0 to a1 (radians, screen coords), as cubic Beziers (<= 90 deg each)."""
    n = max(1, int(np.ceil(abs(a1 - a0) / (np.pi / 2) - 1e-9)))
    out = []
    for k in range(n):
        s, e = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
        h = 4 / 3 * np.tan((e - s) / 4) * r
        p0 = c + r * np.array([np.cos(s), np.sin(s)])
        p3 = c + r * np.array([np.cos(e), np.sin(e)])
        t0 = np.array([-np.sin(s), np.cos(s)])
        t3 = np.array([-np.sin(e), np.cos(e)])
        out.append(np.array([p0, p0 + h * t0, p3 - h * t3, p3]))
    return out


def line_bezier(p, q):
    p, q = np.asarray(p, float), np.asarray(q, float)
    return ("L", p, q)


def glow_segments(M, r, tol=0.12):
    """Outline of the ribbon silhouette offset outward by r (Minkowski sum with a disk): offset edges,
    straight offset end cuts and round corners. Returns a list of ('C', P) / ('L', p, q) segments."""
    top, bot, _ = curves(M)
    XL, XR = M["XL"], M["XR"]
    segs = []

    def ang(v):
        return float(np.arctan2(v[1], v[0]))

    def nrm_top(x):
        t = float(top.d(x)[0]); v = np.array([t, -1.0]); return v / np.linalg.norm(v)

    def nrm_bot(x):
        t = float(bot.d(x)[0]); v = np.array([-t, 1.0]); return v / np.linalg.norm(v)

    pTL, pTR = np.array([XL, top(XL)[0]]), np.array([XR, top(XR)[0]])
    pBL, pBR = np.array([XL, bot(XL)[0]]), np.array([XR, bot(XR)[0]])
    segs += [("C", P) for P in piece_beziers(Piece(top, XL, XR, r, +1), tol)]
    # top-right corner: from the top normal round to +x
    a0, a1 = ang(nrm_top(XR)), 0.0
    if a1 < a0:
        a1 += 2 * np.pi
    segs += [("C", P) for P in arc_beziers(pTR, r, a0, a1)]
    segs.append(line_bezier(pTR + [r, 0], pBR + [r, 0]))
    a0, a1 = 0.0, ang(nrm_bot(XR))
    segs += [("C", P) for P in arc_beziers(pBR, r, a0, a1)]
    segs += [("C", P) for P in piece_beziers(Piece(bot, XR, XL, r, -1), tol)]
    a0, a1 = ang(nrm_bot(XL)), np.pi
    segs += [("C", P) for P in arc_beziers(pBL, r, a0, a1)]
    segs.append(line_bezier(pBL - [r, 0], pTL - [r, 0]))
    a0, a1 = np.pi, ang(nrm_top(XL))
    if a1 < a0:
        a1 += 2 * np.pi
    segs += [("C", P) for P in arc_beziers(pTL, r, a0, a1)]
    return segs


def inset_segments(M, r, tol=0.1):
    """Ribbon silhouette shrunk by r on every side (edges offset inward, end cuts moved in)."""
    top, bot, _ = curves(M)
    XL, XR = M["XL"] + r, M["XR"] - r
    return face_segments([Piece(top, XL, XR, -r, +1), Piece(bot, XR, XL, -r, -1)], tol)


def face_segments(pieces, tol=0.1):
    segs = []
    for pc in pieces:
        segs += [("C", P) for P in piece_beziers(pc, tol)]
    return segs


def path_d(segs, xform=lambda p: p, nd=2):
    f = lambda v: ("%.*f" % (nd, v)).rstrip("0").rstrip(".")
    fp = lambda p: "%s %s" % (f(p[0]), f(p[1]))
    out, last = [], None
    for s in segs:
        if s[0] == "C":
            P = np.array([xform(p) for p in s[1]])
            p0 = P[0]
        else:
            p0, p1 = xform(s[1]), xform(s[2])
        if last is None:
            out.append("M" + fp(p0))
        elif np.linalg.norm(np.asarray(p0) - last) > 1e-3:
            out.append("L" + fp(p0))
        if s[0] == "C":
            out.append("C" + " ".join(fp(p) for p in P[1:]))
            last = P[3]
        else:
            out.append("L" + fp(p1))
            last = np.asarray(p1)
    out.append("Z")
    return " ".join(out)


def segs_polyline(segs, n=24):
    pts = []
    for s in segs:
        if s[0] == "C":
            u = np.linspace(0, 1, n)
            pts.append(_bez(s[1], u))
        else:
            pts.append(np.array([s[1], s[2]]))
    return np.concatenate(pts)
