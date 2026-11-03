"""Flat-mark rebuild helpers (agent prefix flat-): clean resynthesis, trace, refit to clean line/curve
geometry, ring geometry and verification. Used only by work/flat-/build_flat.py."""
import os
import sys

BUILD = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path.insert(0, BUILD)
import kit  # noqa: E402
import numpy as np  # noqa: E402

WORK = os.path.join(BUILD, 'work', 'flat-')
NAVY_HEX, CYAN_HEX, WHITE_HEX = '#121B2A', '#00D5FF', '#FFFFFF'
NAVY, CYAN, WHITE = kit.hexrgb(NAVY_HEX), kit.hexrgb(CYAN_HEX), kit.hexrgb(WHITE_HEX)


# ------------------------------------------------------------------ measurement

def frame_mask(h, w, m=30):
    f = np.zeros((h, w), bool)
    f[:m] = f[-m:] = True
    f[:, :m] = f[:, -m:] = True
    return f


def lab_chroma(a):
    lab = kit.srgb_to_lab(a)
    return lab[..., 0], np.hypot(lab[..., 1], lab[..., 2])


def box_of(mask, pad=0):
    ys, xs = np.nonzero(mask)
    return [int(xs.min()) - pad, int(ys.min()) - pad, int(xs.max()) + 1 + pad, int(ys.max()) + 1 + pad]


def cov2(a, c0, c1):
    """Coverage of colour c1 over c0 per pixel: projection on the c0->c1 line, clipped to 0..1."""
    d = np.asarray(c1, float) - np.asarray(c0, float)
    return np.clip(((a - c0) @ d) / (d @ d), 0, 1)


def cov3(a, n, c, w):
    """Barycentric weights (u for c, v for w) of each pixel in the navy/cyan/white plane (least squares)."""
    M = np.stack([c - n, w - n], 1)  # 3x2
    pinv = np.linalg.pinv(M)  # 2x3
    uv = (a - n) @ pinv.T
    u, v = np.clip(uv[..., 0], 0, 1), np.clip(uv[..., 1], 0, 1)
    s = np.maximum(u + v, 1.0)
    return u / s, v / s


def gauss_blur(img, sigma):
    """Separable Gaussian blur (numpy only, edge-replicated)."""
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = img
    for ax in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[ax] = (r, r)
        p = np.pad(out, pad, mode='edge')
        n = out.shape[ax]
        acc = np.zeros_like(out)
        for i, w in enumerate(k):
            acc += w * (p[i:i + n] if ax == 0 else p[:, i:i + n])
        out = acc
    return out


def soft_offset(cov, d, sigma=2.0):
    """Coverage map offset by d px (outward > 0) with a smooth ~1 px anti-aliased edge: Gaussian-blur the
    coverage and re-threshold at the level a straight edge reaches d px away."""
    from math import erf, sqrt
    b = gauss_blur(np.clip(cov, 0, 1).astype(float), sigma)
    lvl = 0.5 * (1 + erf(-d / (sigma * sqrt(2))))   # Phi(-d/sigma)
    # slope of the blurred profile at the iso-level -> map to a ~1 px wide ramp
    slope = np.exp(-0.5 * (d / sigma) ** 2) / (sigma * sqrt(2 * np.pi))
    return np.clip((b - lvl) / slope + 0.5, 0, 1)


def snap01(al, lo=0.1, hi=0.9):
    return np.where(al < lo, 0.0, np.where(al > hi, 1.0, al))


# ------------------------------------------------------------------ geometry helpers

def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def bez(p0, p1, p2, p3, u):
    u = np.asarray(u, float)[:, None]
    m = 1 - u
    return m ** 3 * p0 + 3 * m * m * u * p1 + 3 * m * u * u * p2 + u ** 3 * p3


def bez_d1(p0, p1, p2, p3, u):
    u = np.asarray(u, float)[:, None]
    m = 1 - u
    return 3 * m * m * (p1 - p0) + 6 * m * u * (p2 - p1) + 3 * u * u * (p3 - p2)


def bez_d2(p0, p1, p2, p3, u):
    u = np.asarray(u, float)[:, None]
    return 6 * (1 - u) * (p2 - 2 * p1 + p0) + 6 * u * (p3 - 2 * p2 + p1)


def flat_seg(p0, g, tol=0.02):
    if g[0] == 'L':
        return [np.array(g[1:3])]
    pts = kit.flatten([{'start': tuple(p0), 'segs': [g], 'closed': False}], tol=tol)[0]
    return [np.array(p) for p in pts[1:]]


def poly_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def point_in_poly(pt, poly):
    x, y = pt
    xs, ys = poly[:, 0], poly[:, 1]
    xs2, ys2 = np.roll(xs, -1), np.roll(ys, -1)
    cond = (ys > y) != (ys2 > y)
    xint = xs + (y - ys) * (xs2 - xs) / np.where(ys2 - ys == 0, 1e-12, ys2 - ys)
    return bool(np.sum(cond & (x < xint)) % 2)


def resample(pts, ds=0.5):
    """Polyline (open, list of arrays) -> uniformly spaced points including both ends."""
    p = np.array(pts, float)
    if len(p) < 2:
        return p
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    keep = np.concatenate([[True], seg > 1e-9])
    p = p[keep]
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    n = max(2, int(np.ceil(L / ds)) + 1)
    t = np.linspace(0, L, n)
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)


def snap_run(q, alpha, ds=0.5, max_shift=1.0, sigma_px=2.0):
    """Move the interior points of a dense run onto the alpha = 0.5 iso-line of the coverage map (sampled
    bilinearly along each point's normal, nearest crossing within max_shift). The per-point shifts are
    smoothed along the run (Gaussian, sigma_px) so the correction removes the tracer's edge bias without
    adding JPEG noise. Endpoints are left for the caller. Returns (q_new, shifts)."""
    n = len(q)
    if n < 5:
        return q.copy(), np.zeros(n)
    k = 2
    idx = np.arange(n)
    t = q[np.clip(idx + k, 0, n - 1)] - q[np.clip(idx - k, 0, n - 1)]
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    s = np.arange(-max_shift - 0.3, max_shift + 0.3001, 0.05)
    P = q[:, None, :] + s[None, :, None] * nrm[:, None, :]
    prof = bilinear(alpha, P[..., 0] - 0.5, P[..., 1] - 0.5) - 0.5
    shift = np.zeros(n)
    w = np.zeros(n)
    sgn = np.sign(prof)
    for i in range(1, n - 1):
        cr = np.nonzero(sgn[i, :-1] * sgn[i, 1:] < 0)[0]
        if not len(cr):
            continue
        f = prof[i, cr] / (prof[i, cr] - prof[i, cr + 1])
        pos = s[cr] + f * 0.05
        j = int(np.argmin(np.abs(pos)))
        if abs(pos[j]) <= max_shift:
            shift[i], w[i] = pos[j], 1.0
    r = int(np.ceil(3 * sigma_px / ds))
    g = np.exp(-0.5 * (np.arange(-r, r + 1) * ds / sigma_px) ** 2)
    num = np.convolve(np.pad(shift * w, r), g, mode='valid')
    den = np.convolve(np.pad(w, r), g, mode='valid')
    sm = np.where(den > 0.3, num / np.maximum(den, 1e-9), 0.0)
    sm[0] = sm[-1] = 0.0
    return q + sm[:, None] * nrm, sm


def _gauss_pts(q, sigma, ds):
    """Gaussian smoothing of an open polyline along arc length; point-reflection padding keeps both
    endpoints and their tangent lines fixed."""
    if sigma <= 0.05 or len(q) < 3:
        return q.copy()
    r = int(np.ceil(3 * sigma / ds))
    r = min(r, len(q) - 1)
    head = 2 * q[0] - q[r:0:-1]
    tail = 2 * q[-1] - q[-2:-r - 2:-1]
    p = np.vstack([head, q, tail])
    g = np.exp(-0.5 * (np.arange(-r, r + 1) * ds / sigma) ** 2)
    g /= g.sum()
    out = np.stack([np.convolve(p[:, 0], g, mode='valid'), np.convolve(p[:, 1], g, mode='valid')], 1)
    out[0], out[-1] = q[0], q[-1]
    return out


def smooth_curve_points(q, ds=0.5, eps=0.06, smax=4.0):
    """Curvature-adaptive smoothing of a curve piece: each point is smoothed with sigma = sqrt(2 R eps)
    (capped at smax), so a curve of radius R shrinks by at most ~eps px while JPEG/tracer wobble on gentle
    curves is removed. Tight features (crescent tips) are barely touched."""
    q = np.asarray(q, float)
    if len(q) < 7:
        return q.copy()
    levels = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, smax]
    sm = [_gauss_pts(q, s, ds) for s in levels]
    ref = sm[-2] if len(sm) > 2 else q
    # curvature of the reference (moderately smoothed) curve
    k = 3
    a, b, c = ref[:-2 * k], ref[k:-k], ref[2 * k:]
    ab, bc, ca = np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1), np.linalg.norm(a - c, axis=1)
    cross = np.abs((b - a)[:, 0] * (c - a)[:, 1] - (b - a)[:, 1] * (c - a)[:, 0])
    kap = 2 * cross / np.maximum(ab * bc * ca, 1e-9)
    kap = np.concatenate([np.full(k, kap[0]), kap, np.full(k, kap[-1])])
    # take the max curvature over the local window so tight spots are protected
    w = int(np.ceil(smax / ds))
    kp = np.pad(kap, w, mode='edge')
    kmax = np.max(np.stack([kp[i:i + len(kap)] for i in range(2 * w + 1)]), 0)
    R = 1.0 / np.maximum(kmax, 1e-6)
    sig = np.clip(np.sqrt(2 * R * eps), 0, smax)
    out = np.empty_like(q)
    lv = np.array(levels)
    for i in range(len(q)):
        j = int(np.searchsorted(lv, sig[i]))
        if j <= 0:
            out[i] = sm[0][i]
        elif j >= len(lv):
            out[i] = sm[-1][i]
        else:
            t = (sig[i] - lv[j - 1]) / (lv[j] - lv[j - 1])
            out[i] = (1 - t) * sm[j - 1][i] + t * sm[j][i]
    out[0], out[-1] = q[0], q[-1]
    return out


def line_fit(q):
    c = q.mean(0)
    _, _, vt = np.linalg.svd(q - c, full_matrices=False)
    d = vt[0]
    if d @ (q[-1] - q[0]) < 0:
        d = -d
    nrm = np.array([-d[1], d[0]])
    dist = (q - c) @ nrm
    t = (q - c) @ d
    return c, d, dist, t


def line_ok(q, maxdev, sag):
    if len(q) < 3:
        return True
    c, d, dist, t = line_fit(q)
    if np.abs(dist).max() > maxdev:
        return False
    L = t.max() - t.min()
    if L < 1e-6:
        return True
    A = np.stack([t * t, t, np.ones_like(t)], 1)
    co = np.linalg.lstsq(A, dist, rcond=None)[0]
    return abs(co[0]) * (L / 2) ** 2 < sag


def sag_limit(L, sag):
    """Allowed systematic bow for a line of length L: strict on short runs (a short arc must stay a curve),
    looser on long edges where JPEG wobble averages out but a real curve would bow far more."""
    return float(np.clip(sag + (L - 40.0) * (0.12 / 110.0), sag, 0.2))


def line_ok2(q, ds, maxdev, sag):
    L = ds * (len(q) - 1)
    return line_ok(q, maxdev, sag_limit(L, sag))


def dp_indices(q, tol):
    keep = {0, len(q) - 1}
    stack = [(0, len(q) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        p0, d = q[a], q[b] - q[a]
        L = np.linalg.norm(d)
        r = q[a + 1:b] - p0
        dist = np.linalg.norm(r, axis=1) if L < 1e-9 else np.abs(d[0] * r[:, 1] - d[1] * r[:, 0]) / L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            m = a + 1 + k
            keep.add(m)
            stack += [(a, m), (m, b)]
    return sorted(keep)


def find_lines(q, ds, line_min, maxdev, sag):
    """Maximal straight sub-runs of an open polyline q: Douglas-Peucker edges seed candidates that are
    shrunk until they pass the line test, then grown while they still pass; overlaps go to the longer line."""
    N = len(q)
    m = int(round(line_min / ds))
    idx = dp_indices(q, 0.4)
    cands = []
    for k in range(len(idx) - 1):
        a, b = idx[k], idx[k + 1]
        if b - a < m:
            continue
        while b - a >= m and not line_ok2(q[a:b + 1], ds, maxdev, sag):
            dist = line_fit(q[a:b + 1])[2]
            if np.abs(dist[:4]).max() > np.abs(dist[-4:]).max():
                a += 2
            else:
                b -= 2
        if b - a < m:
            continue
        while a >= 2 and line_ok2(q[a - 2:b + 1], ds, maxdev, sag):
            a -= 2
        while b <= N - 3 and line_ok2(q[a:b + 3], ds, maxdev, sag):
            b += 2
        cands.append((a, b))
    cands = sorted(set(cands), key=lambda ab: ab[0] - ab[1])
    acc = []
    for a, b in cands:
        for a2, b2 in acc:
            if a < b2 and b > a2:  # overlap: keep the part outside the accepted line
                if a >= a2 and b <= b2:
                    a = b = -1
                    break
                if a < a2:
                    b = min(b, a2)
                else:
                    a = max(a, b2)
        if a >= 0 and b - a >= m and line_ok2(q[a:b + 1], ds, maxdev, sag):
            acc.append((a, b))
    return sorted(acc)


def intersect(c1, d1, c2, d2):
    A = np.array([d1, -d2]).T
    if abs(np.linalg.det(A)) < 1e-9:
        return None
    s = np.linalg.solve(A, c2 - c1)
    return c1 + s[0] * d1


def project(p, c, d):
    return c + ((p - c) @ d) * d


# ------------------------------------------------------------------ cubic fitting (Schneider-style, free or G1 ends)

def _solve(q, u, P0, P3, t0, t1):
    m = 1 - u
    b0, b1, b2, b3 = m ** 3, 3 * m * m * u, 3 * m * u * u, u ** 3
    R = q - np.outer(b0, P0) - np.outer(b3, P3)
    cols = []
    if t0 is not None:
        R -= np.outer(b1, P0)
        cols.append(np.concatenate([b1 * t0[0], b1 * t0[1]]))
    else:
        z = np.zeros_like(b1)
        cols += [np.concatenate([b1, z]), np.concatenate([z, b1])]
    if t1 is not None:
        R -= np.outer(b2, P3)
        cols.append(np.concatenate([-b2 * t1[0], -b2 * t1[1]]))
    else:
        z = np.zeros_like(b2)
        cols += [np.concatenate([b2, z]), np.concatenate([z, b2])]
    A = np.array(cols).T
    rhs = np.concatenate([R[:, 0], R[:, 1]])
    sol = np.linalg.lstsq(A, rhs, rcond=None)[0]
    chord = max(np.linalg.norm(P3 - P0), 0.3 * float(np.sum(np.linalg.norm(np.diff(q, axis=0), axis=1))))
    k = 0
    if t0 is not None:
        a1 = sol[k]; k += 1
        if not (1e-3 * chord < a1 < 2.0 * chord):
            a1 = chord / 3
        P1 = P0 + a1 * t0
    else:
        P1 = np.array([sol[k], sol[k + 1]]); k += 2
    if t1 is not None:
        a2 = sol[k]; k += 1
        if not (1e-3 * chord < a2 < 2.0 * chord):
            a2 = chord / 3
        P2 = P3 - a2 * t1
    else:
        P2 = np.array([sol[k], sol[k + 1]]); k += 2
    return P1, P2


def _reparam(q, u, P0, P1, P2, P3):
    B = bez(P0, P1, P2, P3, u)
    d1 = bez_d1(P0, P1, P2, P3, u)
    d2 = bez_d2(P0, P1, P2, P3, u)
    f = np.sum((B - q) * d1, 1)
    fp = np.sum(d1 * d1, 1) + np.sum((B - q) * d2, 1)
    un = u - np.where(np.abs(fp) > 1e-12, f / fp, 0)
    un = np.clip(un, 0, 1)
    un[0], un[-1] = 0.0, 1.0
    return np.maximum.accumulate(un)


def fit_one(q, t0=None, t1=None, tol=0.25):
    """Single cubic through q[0], q[-1] (least squares, Newton reparameterisation). -> (P0..P3, emax, imax)"""
    q = np.asarray(q, float)
    P0, P3 = q[0], q[-1]
    n = len(q)
    if n <= 4:
        ch = np.linalg.norm(P3 - P0)
        d = unit(P3 - P0)
        return (P0, P0 + (t0 if t0 is not None else d) * ch / 3, P3 - (t1 if t1 is not None else d) * ch / 3, P3), 0.0, 0
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    u = np.concatenate([[0], np.cumsum(seg)])
    u /= u[-1]
    best = None
    for _ in range(12):
        P1, P2 = _solve(q, u, P0, P3, t0, t1)
        u = _reparam(q, u, P0, P1, P2, P3)
        err = np.linalg.norm(bez(P0, P1, P2, P3, u) - q, axis=1)
        if best is None or err.max() < best[0]:
            best = (float(err.max()), int(np.argmax(err)), P1, P2)
        if err.max() < tol:
            break
    emax, imax, P1, P2 = best
    return (P0, P1, P2, P3), emax, imax


def _split_fit(q, i0, t0, t1, tol, depth):
    n = len(q)
    c, emax, imax = fit_one(q, t0, t1, tol)
    if emax < tol or n < 14 or depth > 12:
        return [dict(c=c, i0=i0, i1=i0 + n - 1, t0=t0, t1=t1)]
    imax = int(np.clip(imax, 6, n - 7))
    lo, hi = max(0, imax - 3), min(n - 1, imax + 3)
    tm = unit(q[hi] - q[lo])
    return (_split_fit(q[:imax + 1], i0, t0, tm, tol, depth + 1)
            + _split_fit(q[imax:], i0 + imax, tm, t1, tol, depth + 1))


# ------------------------------------------------------------------ C2 spline fit (smooth curvature)

def bs_basis(t, U, p=3):
    """B-spline basis matrix (len(t) x (len(U)-p-1)), Cox-de Boor; t=1 maps to the last basis."""
    t = np.asarray(t, float)
    m = len(U) - p - 1
    N = np.zeros((len(t), len(U) - 1))
    for j in range(len(U) - 1):
        N[:, j] = (U[j] <= t) & (t < U[j + 1])
    last = np.nonzero(U < U[-1])[0][-1]
    N[t >= U[-1], :] = 0
    N[t >= U[-1], last] = 1
    for d in range(1, p + 1):
        Nn = np.zeros((len(t), len(U) - 1 - d))
        for j in range(len(U) - 1 - d):
            a = U[j + d] - U[j]
            b = U[j + d + 1] - U[j + 1]
            if a > 0:
                Nn[:, j] += (t - U[j]) / a * N[:, j]
            if b > 0:
                Nn[:, j] += (U[j + d + 1] - t) / b * N[:, j + 1]
        N = Nn
    return N[:, :m]


def _spline_solve(q, t, U, t0, t1, lam):
    m = len(U) - 4
    B = bs_basis(t, U)
    P0, P3 = q[0], q[-1]
    # unknown layout: [c1 (1 or 2)] [c2..c_{m-3} (2 each)] [c_{m-2} (1 or 2)]; m >= 4
    cols = []  # each column: (m x 2) contribution of one unknown to the control points
    base = np.zeros((m, 2))
    base[0], base[-1] = P0, P3

    def unitcol(j, axis):
        c = np.zeros((m, 2)); c[j, axis] = 1.0
        return c
    if t0 is not None:
        base[1] = P0
        c = np.zeros((m, 2)); c[1] = t0; cols.append(c)
    else:
        cols += [unitcol(1, 0), unitcol(1, 1)]
    for j in range(2, m - 2):
        cols += [unitcol(j, 0), unitcol(j, 1)]
    if m - 2 > 1:
        if t1 is not None:
            base[m - 2] = P3
            c = np.zeros((m, 2)); c[m - 2] = -t1; cols.append(c)
        else:
            cols += [unitcol(m - 2, 0), unitcol(m - 2, 1)]
    K = len(cols)
    A = np.zeros((2 * len(q), K))
    for k, c in enumerate(cols):
        v = B @ c
        A[:, k] = np.concatenate([v[:, 0], v[:, 1]])
    r0 = q - B @ base
    rhs = np.concatenate([r0[:, 0], r0[:, 1]])
    if lam > 0 and m >= 4:
        # third differences of control points (curvature variation), weighted per data point
        D = np.zeros((m - 3, m))
        for i in range(m - 3):
            D[i, i:i + 4] = [-1, 3, -3, 1]
        w = np.sqrt(lam * len(q) / max(1, m - 3))
        Ar = np.zeros((2 * (m - 3), K))
        for k, c in enumerate(cols):
            v = D @ c
            Ar[:, k] = np.concatenate([v[:, 0], v[:, 1]])
        rb = -(D @ base)
        A = np.vstack([A, w * Ar])
        rhs = np.concatenate([rhs, w * np.concatenate([rb[:, 0], rb[:, 1]])])
    z = np.linalg.lstsq(A, rhs, rcond=None)[0]
    ctrl = base + sum(zk * c for zk, c in zip(z, cols))
    return ctrl


def _spline_eval(ctrl, U, t):
    return bs_basis(t, U) @ ctrl


def spline_to_bezier(ctrl, U):
    """Exact Bezier segments of a clamped cubic B-spline, one per knot span (Hermite conversion)."""
    # derivative spline: degree 2, control points 3 (c_{j+1}-c_j)/(U_{j+4}-U_{j+1}), knots U[1:-1]
    m = len(ctrl)
    dc = np.array([3 * (ctrl[j + 1] - ctrl[j]) / (U[j + 4] - U[j + 1]) for j in range(m - 1)])
    U2 = U[1:-1]
    knots = np.unique(U)
    segs = []
    for a, b in zip(knots[:-1], knots[1:]):
        P0 = _spline_eval(ctrl, U, [a])[0]
        P3 = _spline_eval(ctrl, U, [b])[0]
        d0 = bs_basis([a], U2, 2) @ dc
        d1 = bs_basis([min(b, U[-1])], U2, 2) @ dc
        h = b - a
        segs.append((P0, P0 + d0[0] * h / 3, P3 - d1[0] * h / 3, P3))
    return segs


def fit_spline(q, t0=None, t1=None, tol=0.3, span=45.0, min_span=10.0, lam=1e-3, iters=4):
    """C2 cubic spline through q[0], q[-1] (optional G1 end tangents), least squares with a small
    curvature-variation penalty; spans are added until the max error is below tol. Returns Bezier list."""
    q = np.asarray(q, float)
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
    L = float(seg.sum())
    if len(q) < 5 or L < 4:
        c, _, _ = fit_one(q, t0, t1, tol)
        return [c], 0.0
    n = max(1, int(round(L / span)))
    nmax = max(1, int(L / min_span))
    best = None
    while True:
        U = np.concatenate([[0, 0, 0], np.linspace(0, 1, n + 1), [1, 1, 1]])
        t = np.concatenate([[0], np.cumsum(seg)]) / L
        for _ in range(iters):
            ctrl = _spline_solve(q, t, U, t0, t1, lam)
            # reparameterise: nearest point on a dense sampling of the curve
            ts = np.linspace(0, 1, int(min(3000, max(300, 30 * n))))
            cs = _spline_eval(ctrl, U, ts)
            dd = ((q[:, None, :] - cs[None, :, :]) ** 2).sum(-1)
            k = np.argmin(dd, 1)
            t = ts[k]
            t[0], t[-1] = 0.0, 1.0
            t = np.maximum.accumulate(t)
        ctrl = _spline_solve(q, t, U, t0, t1, lam)
        cs = _spline_eval(ctrl, U, np.linspace(0, 1, int(min(4000, max(400, 60 * n)))))
        err = float(np.sqrt(((q[:, None, :] - cs[None, :, :]) ** 2).sum(-1).min(1)).max())
        if best is None or err < best[0]:
            best = (err, ctrl, U)
        if err < tol or n >= nmax:
            break
        n = min(nmax, n + max(1, n // 3))
    return spline_to_bezier(best[1], best[2]), best[0]


def merge_beziers(segs, tol=0.15, n=16):
    """Greedy longest-run merge of consecutive G1 cubics (e.g. a C2 spline's spans) into single cubics
    that stay within tol of them; end tangents are kept, so joints stay G1. Returns the shorter list."""
    def tan0(c):
        v = c[1] - c[0]
        return unit(v if np.linalg.norm(v) > 1e-6 else c[2] - c[0])

    def tan1(c):
        v = c[3] - c[2]
        return unit(v if np.linalg.norm(v) > 1e-6 else c[3] - c[1])
    out, i = [], 0
    u = np.linspace(0, 1, n)
    while i < len(segs):
        j, best = i, segs[i]
        while j + 1 < len(segs):
            pts = np.vstack([bez(*segs[k], u)[:-1] for k in range(i, j + 2)] + [segs[j + 1][3][None]])
            c, emax, _ = fit_one(pts, tan0(segs[i]), tan1(segs[j + 1]), tol)
            if emax >= tol:
                break
            best, j = c, j + 1
        out.append(best)
        i = j + 1
    return out


def fit_cubic(q, t0=None, t1=None, tol=0.25, tiny=4.0, merge_tol=0.45):
    """Fit G1-joined cubic(s) to points q (endpoints fixed). t0/t1: unit tangents in travel direction, or
    None (free). Tiny segments left by a split next to an end are merged into their neighbour when the
    merged fit stays within merge_tol. Returns list of (P0, P1, P2, P3)."""
    q = np.asarray(q, float)
    segs = _split_fit(q, 0, t0, t1, tol, 0)
    changed = True
    while changed and len(segs) > 1:
        changed = False
        for k, s in enumerate(segs):
            if np.linalg.norm(s['c'][3] - s['c'][0]) >= tiny:
                continue
            for nb in ([k + 1, k - 1] if k == 0 else [k - 1, k + 1]):
                if not 0 <= nb < len(segs):
                    continue
                a, b = (segs[k], segs[nb]) if nb > k else (segs[nb], segs[k])
                c, emax, _ = fit_one(q[a['i0']:b['i1'] + 1], a['t0'], b['t1'], merge_tol)
                if emax < merge_tol:
                    lo = min(k, nb)
                    segs[lo:lo + 2] = [dict(c=c, i0=a['i0'], i1=b['i1'], t0=a['t0'], t1=b['t1'])]
                    changed = True
                    break
            if changed:
                break
    return [s['c'] for s in segs]


# ------------------------------------------------------------------ refit of one closed traced subpath

def subpath_nodes(sub):
    """(node points, corner flags) for a parsed closed subpath; corner = tangent break > 20 deg."""
    segs = sub['segs']
    cur = np.array(sub['start'], float)
    tin, tout, ends, flats = [], [], [], []
    for g in segs:
        if g[0] == 'L':
            e = np.array(g[1:3]); a0 = a1 = unit(e - cur)
        else:
            p1, p2, e = np.array(g[1:3]), np.array(g[3:5]), np.array(g[5:7])
            a0 = unit(p1 - cur) if np.linalg.norm(p1 - cur) > 1e-6 else unit(p2 - cur)
            a1 = unit(e - p2) if np.linalg.norm(e - p2) > 1e-6 else unit(e - p1)
        flats.append(flat_seg(cur, g))
        tin.append(a1); tout.append(a0); ends.append(e); cur = e
    n = len(segs)
    if np.linalg.norm(ends[-1] - np.array(sub['start'])) > 1e-6:
        # implicit closing line
        e = np.array(sub['start'], float)
        a = unit(e - ends[-1])
        flats.append([e]); tin.append(a); tout.append(a); ends.append(e); n += 1
    corner = []
    for k in range(n):
        ang = np.degrees(np.arccos(np.clip(tin[k] @ tout[(k + 1) % n], -1, 1)))
        corner.append(ang > 20)
    # node k = end of seg k; flats[k] = points of seg k (excluding its start)
    return ends, corner, flats


def refit_subpath(sub, ds=0.5, line_min=30.0, maxdev=0.4, sag=0.08, run_line_dev=0.3, trim_dev=0.05,
                  round_corner_gap=10.0, round_corner_ang=25.0, tiny=3.5, absorb_len=15.0, absorb_dev=0.5,
                  tol=0.3, fixed_corners=(), alpha=None, snap_sigma=3.0, smooth_eps=0.0, spline=True, merge_tol=0.2):
    """Refit a traced closed subpath into clean geometry: true lines for straight edges, sharp corners,
    G1 cubics elsewhere. Returns (elements, stats); elements = list of ('L', p0, p1) | ('C', p0, p1, p2, p3)."""
    ends, corner, flats = subpath_nodes(sub)
    n = len(ends)
    for fc in fixed_corners:  # force extra corners near given points
        k = int(np.argmin([np.linalg.norm(e - np.array(fc)) for e in ends]))
        corner[k] = True
    ck = [k for k in range(n) if corner[k]]
    cyclic = not ck
    if cyclic:
        ck = [n - 1]
    # runs between consecutive corners: run j from node ck[j] to node ck[j+1]
    runs = []
    for j in range(len(ck)):
        a, b = ck[j], ck[(j + 1) % len(ck)]
        pts = [ends[a]]
        k = (a + 1) % n
        while True:
            pts += flats[k]
            if k == b:
                break
            k = (k + 1) % n
        runs.append(resample(pts, ds))
    if alpha is not None:
        # snap to the coverage map's 0.5 iso-line (removes the tracer's ~0.1-0.2 px outward bias)
        moved = []
        for j, q in enumerate(runs):
            qn, _ = snap_run(q, alpha, ds, sigma_px=snap_sigma)
            moved.append(qn)
        R = len(runs)
        for j in range(R):  # corner shared by the end of run j-1 and the start of run j
            a_, b_ = moved[j - 1], moved[j]
            disp = np.vstack([(a_ - runs[j - 1])[-4:-1], (b_ - runs[j])[1:4]]).mean(0)
            b_[0] = runs[j][0] + disp
            a_[-1] = b_[0]
        runs = moved
    # classify each run into line/curve pieces: list of [kind, q]
    pieces = []  # (kind, q, start_is_corner)
    for j, q in enumerate(runs):
        L = ds * (len(q) - 1)
        if line_ok(q, run_line_dev, max(sag, 0.15)) and L >= 1.0:
            pieces.append(['L', q, True])
            continue
        lines = find_lines(q, ds, line_min, maxdev, sag)
        N = len(q)
        # build pieces in order
        cur = 0
        first = True
        for (s, e) in lines:
            if s > cur:
                pieces.append(['C', q[cur:s + 1], first])
                first = False
            pieces.append(['L', q[s:e + 1], first])
            first = False
            cur = e
        if cur < N - 1:
            pieces.append(['C', q[cur:], first])
    # each piece: [kind, points, corner_before]; corner_before = a tracer corner sits at the piece's start
    if cyclic:
        for pc in pieces:
            pc[2] = False

    def _drop(x):
        del pieces[next(i for i, p in enumerate(pieces) if p is x)]

    def _merge_pass(fn):
        while len(pieces) >= 2 and fn():
            pass

    def _round_corners():  # L, short C, L with a big angle -> L, L meeting at a sharp corner
        P = len(pieces)
        if P < 3:
            return False
        for j in range(P):
            a, b, c = pieces[j], pieces[(j + 1) % P], pieces[(j + 2) % P]
            if a[0] == 'L' and b[0] == 'C' and c[0] == 'L' and not b[2] and not c[2]:
                ca, da = line_fit(a[1])[:2]
                cc, dc = line_fit(c[1])[:2]
                ang = np.degrees(np.arccos(np.clip(da @ dc, -1, 1)))
                if ang < round_corner_ang:
                    continue
                gap = ds * (len(b[1]) - 1)
                X = intersect(ca, da, cc, dc)
                hug = False
                if X is not None and gap <= 60.0:
                    # the curve only rounds the corner of the two lines: it stays on them except near X
                    q = b[1]
                    na, nc = np.array([-da[1], da[0]]), np.array([-dc[1], dc[0]])
                    dist = np.minimum(np.abs((q - ca) @ na), np.abs((q - cc) @ nc))
                    near = np.linalg.norm(q - X, axis=1) < 5.0
                    hug = bool(np.all(dist[~near] < absorb_dev) and np.all(dist[near] < 2.0)
                               and np.min(np.linalg.norm(q - X, axis=1)) < 3.0)
                if gap <= round_corner_gap or hug:
                    q = b[1]
                    if X is not None:
                        k = int(np.argmin(np.linalg.norm(q - X, axis=1)))
                        m4 = int(round(4.0 / ds))
                        if k - m4 > 0:
                            a[1] = np.vstack([a[1], q[1:k - m4 + 1]])
                        if k + m4 < len(q) - 1:
                            c[1] = np.vstack([q[k + m4:-1], c[1]])
                    c[2] = True
                    _drop(b)
                    return True
        return False

    def _tiny_curves():  # short curve between a line and a corner (tracer rounding at a line end) -> into the line
        P = len(pieces)
        if P < 3:
            return False
        for j in range(P):
            a, b, c = pieces[j - 1], pieces[j], pieces[(j + 1) % P]
            blen = ds * (len(b[1]) - 1)
            if b[0] != 'C' or blen >= absorb_len:
                continue
            if a[0] == 'L' and c[2] and not b[2]:
                qq = np.vstack([a[1], b[1][1:]])
                if blen < tiny or line_ok(qq, absorb_dev, 0.15):
                    a[1] = qq
                    _drop(b)
                    return True
            if c[0] == 'L' and b[2] and not c[2]:
                qq = np.vstack([b[1], c[1][1:]])
                if blen < tiny or line_ok(qq, absorb_dev, 0.15):
                    c[1] = qq
                    c[2] = True
                    _drop(b)
                    return True
        return False

    def _trim_lines():  # a line that runs on into a tangent curve keeps only its truly straight part
        P = len(pieces)
        for j in range(P):
            a = pieces[j]
            if a[0] != 'L' or len(a[1]) < 16:
                continue
            prv, nxt = pieces[j - 1], pieces[(j + 1) % P]
            c, dvec, _, _ = line_fit(a[1])
            dist = np.abs((a[1] - c) @ np.array([-dvec[1], dvec[0]]))
            thr = max(trim_dev, 2.0 * float(np.median(dist)))
            k0, k1 = 0, len(dist) - 1
            if prv[0] == 'C' and not a[2]:
                while k0 < k1 - 12 and dist[k0:k0 + 6].max() > thr:
                    k0 += 1
            if nxt[0] == 'C' and not nxt[2]:
                while k1 > k0 + 12 and dist[k1 - 5:k1 + 1].max() > thr:
                    k1 -= 1
            if k0 > 0:
                prv[1] = np.vstack([prv[1], a[1][1:k0 + 1]])
            if k1 < len(dist) - 1:
                nxt[1] = np.vstack([a[1][k1:-1], nxt[1]])
            a[1] = a[1][k0:k1 + 1]

    def _line_pairs():  # consecutive lines with no corner between: one line if they fit together, else a corner
        P = len(pieces)
        for j in range(P):
            a, b = pieces[j - 1], pieces[j]
            if a is not b and a[0] == 'L' and b[0] == 'L' and not b[2]:
                qq = np.vstack([a[1], b[1][1:]])
                if line_ok2(qq, ds, maxdev, sag):
                    a[1] = qq
                    _drop(b)
                else:
                    b[2] = True
                return True
        return False

    _merge_pass(_round_corners)
    _merge_pass(_tiny_curves)
    _merge_pass(_line_pairs)
    _trim_lines()
    P = len(pieces)
    jcorner = [pc[2] for pc in pieces]
    # line parameters
    linep = [line_fit(pc[1])[:2] if pc[0] == 'L' else None for pc in pieces]
    # junction points and tangent constraints
    jpt, jtan = [], []
    for j in range(P):
        prev, nxt = pieces[j - 1], pieces[j]
        lp, ln = linep[j - 1], linep[j]
        node = nxt[1][0]
        if jcorner[j]:
            if lp is not None and ln is not None:
                x = intersect(lp[0], lp[1], ln[0], ln[1])
                ang = np.degrees(np.arccos(np.clip(lp[1] @ ln[1], -1, 1)))
                pt = x if (x is not None and ang > 5 and np.linalg.norm(x - node) < (15 if ang > 20 else 6)) else node
            elif lp is not None:
                pt = project(node, *lp)
            elif ln is not None:
                pt = project(node, *ln)
            else:
                pt = node
            tan = None
        else:
            if lp is not None:
                pt, tan = project(node, *lp), lp[1]
            elif ln is not None:
                pt, tan = project(node, *ln), ln[1]
            else:
                lo, hi = max(0, len(prev[1]) - 4), min(len(nxt[1]) - 1, 3)
                pt, tan = node, unit(nxt[1][hi] - prev[1][lo])
        jpt.append(np.asarray(pt, float))
        jtan.append(tan)
    els = []
    for j in range(P):
        kind, q = pieces[j][0], pieces[j][1]
        p0, p1 = jpt[j], jpt[(j + 1) % P]
        if kind == 'L':
            els.append(('L', p0, p1))
        else:
            qq = np.array(q, float).copy()
            qq[0], qq[-1] = p0, p1
            if smooth_eps > 0:
                qq = smooth_curve_points(qq, ds, smooth_eps)
            t0 = jtan[j]
            t1 = jtan[(j + 1) % P]
            cubics = merge_beziers(fit_spline(qq, t0, t1, tol)[0], merge_tol) if spline else fit_cubic(qq, t0, t1, tol)
            for c in cubics:
                els.append(('C',) + tuple(c))
    return els


def els_to_d(els, nd=3):
    f = lambda v: ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
    out = ['M%s %s' % (f(els[0][1][0]), f(els[0][1][1]))]
    for e in els:
        if e[0] == 'L':
            out.append('L%s %s' % (f(e[2][0]), f(e[2][1])))
        else:
            out.append('C' + ' '.join('%s %s' % (f(p[0]), f(p[1])) for p in e[2:5]))
    out.append('Z')
    return ' '.join(out)


def els_poly(els):
    pts = [els[0][1]]
    for e in els:
        if e[0] == 'L':
            pts.append(e[2])
        else:
            u = np.linspace(0, 1, 24)[1:]
            pts += list(bez(*e[1:5], u))
    return np.array(pts)


def reverse_els(els):
    out = []
    for e in reversed(els):
        if e[0] == 'L':
            out.append(('L', e[2], e[1]))
        else:
            out.append(('C', e[4], e[3], e[2], e[1]))
    return out


def refit_path(d, min_area=30.0, **kw):
    """Refit every subpath of a traced path; drop specks; orient outers CW / holes CCW (screen space)
    so nonzero and evenodd agree. Returns (d_string, info)."""
    subs = kit.parse_d(d)
    items = []
    dropped = []
    for s in subs:
        poly = np.array(kit.flatten([s], tol=0.1)[0])
        A = poly_area(poly)
        if abs(A) < min_area:
            dropped.append(round(abs(A), 1))
            continue
        els = refit_subpath(s, **kw)
        items.append((els, els_poly(els)))
    # nesting depth
    out = []
    for i, (els, poly) in enumerate(items):
        depth = sum(point_in_poly(poly[0], p2) for j, (_, p2) in enumerate(items) if j != i)
        want_pos = depth % 2 == 0
        if (poly_area(poly) > 0) != want_pos:
            els = reverse_els(els)
        out.append(els)
    nanch = sum(len(e) for e in out)
    nlines = sum(1 for els in out for e in els if e[0] == 'L')
    return ' '.join(els_to_d(e) for e in out), {'subpaths': len(out), 'anchors': nanch, 'line_segs': nlines,
                                                 'curve_segs': nanch - nlines, 'specks_dropped_area': dropped}


# ------------------------------------------------------------------ rounded-rect ring

KAPPA = 0.5522847498


def rrect_els(x0, y0, x1, y1, r, cw=True):
    """Rounded rectangle as line + cubic elements, clockwise on screen (y down) when cw."""
    k = KAPPA * r
    P = lambda x, y: np.array([x, y], float)
    els = [('L', P(x0 + r, y0), P(x1 - r, y0)),
           ('C', P(x1 - r, y0), P(x1 - r + k, y0), P(x1, y0 + r - k), P(x1, y0 + r)),
           ('L', P(x1, y0 + r), P(x1, y1 - r)),
           ('C', P(x1, y1 - r), P(x1, y1 - r + k), P(x1 - r + k, y1), P(x1 - r, y1)),
           ('L', P(x1 - r, y1), P(x0 + r, y1)),
           ('C', P(x0 + r, y1), P(x0 + r - k, y1), P(x0, y1 - r + k), P(x0, y1 - r)),
           ('L', P(x0, y1 - r), P(x0, y0 + r)),
           ('C', P(x0, y0 + r), P(x0, y0 + r - k), P(x0 + r - k, y0), P(x0 + r, y0))]
    return els if cw else reverse_els(els)


def fit_circle(pts):
    pts = np.asarray(pts, float)
    x, y = pts[:, 0], pts[:, 1]
    A = np.stack([2 * x, 2 * y, np.ones_like(x)], 1)
    b = x * x + y * y
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]
    r = np.sqrt(c + cx * cx + cy * cy)
    res = np.hypot(x - cx, y - cy) - r
    return cx, cy, r, float(np.abs(res).max())


def bilinear(img, x, y):
    h, w = img.shape
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def crossings(profile, pos, level=0.5):
    """Sub-pixel positions where a sampled profile crosses `level` (linear interpolation)."""
    s = profile - level
    idx = np.nonzero(np.sign(s[:-1]) != np.sign(s[1:]))[0]
    out = []
    for i in idx:
        if s[i] == s[i + 1]:
            continue
        f = s[i] / (s[i] - s[i + 1])
        out.append((pos[i] + f * (pos[i + 1] - pos[i]), 1 if s[i] < 0 else -1))
    return out


# ------------------------------------------------------------------ verification

def render_rgb(svg_path, bg_hex=NAVY_HEX, ss=4):
    """VectorCraft render at ss x, box-filtered back to 1x (VectorCraft's own 1x anti-aliasing quantises
    coverage to quarters, which flips whole pixel rows at the 0.5 threshold). -> float RGB 0..255"""
    import subprocess
    import tempfile
    from PIL import Image
    with tempfile.TemporaryDirectory(dir=WORK) as td:
        png = os.path.join(td, 'r.png')
        r = subprocess.run([kit.VC, 'convert', str(svg_path), png, '--scale', str(ss)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)
        im = Image.open(png).convert('RGBA')
        im.load()
    im = im.reduce(ss)
    return kit.over(np.asarray(im, float) / 255.0, bg_hex)
