"""Clean path rebuild: dense contour (from a trace) -> corners + straight runs on known lines ->
exact snapped lines and minimal cubic Beziers (Schneider least-squares fitting, G1 joins)."""
import sys
import numpy as np

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit


class Line:
    """n . p = d with |n| = 1 (n is the normal)."""

    def __init__(self, n, d, name=''):
        n = np.asarray(n, float)
        k = np.hypot(*n)
        self.n, self.d, self.name = n / k, d / k, name
        self.t = np.array([-self.n[1], self.n[0]])

    @staticmethod
    def h(y, name=''):
        return Line((0, 1), y, name)

    @staticmethod
    def v(x, name=''):
        return Line((1, 0), x, name)

    @staticmethod
    def xy(a, b, name=''):
        """x = a*y + b"""
        return Line((1, -a), b, name)

    def dist(self, p):
        return np.asarray(p) @ self.n - self.d

    def project(self, p):
        p = np.asarray(p, float)
        return p - self.dist(p) * self.n

    def meet(self, o):
        A = np.array([self.n, o.n])
        if abs(np.linalg.det(A)) < 1e-6:
            return None
        return np.linalg.solve(A, np.array([self.d, o.d]))


def resample(poly, step=0.5):
    p = np.asarray(poly, float)
    if np.hypot(*(p[0] - p[-1])) > 1e-9:
        p = np.vstack([p, p[:1]])
    seg = np.hypot(*np.diff(p, axis=0).T)
    p = p[np.concatenate([[True], seg > 1e-9])]
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(8, int(np.ceil(s[-1] / step)))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)


def turning(p, h):
    a = p - np.roll(p, h, 0)
    b = np.roll(p, -h, 0) - p
    return np.degrees(np.arctan2(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0], (a * b).sum(1)))


def find_corners(p, h=6, thresh=28.0):
    ang = np.abs(turning(p, h))
    n = len(p)
    cand = [i for i in range(n) if ang[i] > thresh and ang[i] >= ang[(i - 1) % n] and ang[i] >= ang[(i + 1) % n]]
    cand.sort(key=lambda i: -ang[i])
    keep = []
    for i in cand:
        if all(min(abs(i - j), n - abs(i - j)) > 2 * h for j in keep):
            keep.append(i)
    return sorted(keep)


def smooth_open(p, sigma):
    if sigma <= 0 or len(p) < 5:
        return p
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    out = p.copy()
    n = len(p)
    for i in range(1, n - 1):
        rr = min(i, n - 1 - i, r)
        kk = k[r - rr:r + rr + 1]
        out[i] = (p[i - rr:i + rr + 1] * kk[:, None]).sum(0) / kk.sum()
    return out


# ---------------------------------------------------------------- Schneider fitting

def bez(ctrl, t):
    t = t[:, None]
    return (1 - t) ** 3 * ctrl[0] + 3 * (1 - t) ** 2 * t * ctrl[1] + 3 * (1 - t) * t ** 2 * ctrl[2] + t ** 3 * ctrl[3]


def bez_d1(ctrl, t):
    t = t[:, None]
    return 3 * ((1 - t) ** 2 * (ctrl[1] - ctrl[0]) + 2 * (1 - t) * t * (ctrl[2] - ctrl[1]) + t ** 2 * (ctrl[3] - ctrl[2]))


def bez_d2(ctrl, t):
    t = t[:, None]
    return 6 * ((1 - t) * (ctrl[2] - 2 * ctrl[1] + ctrl[0]) + t * (ctrl[3] - 2 * ctrl[2] + ctrl[1]))


def chord_params(p):
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    return d / max(d[-1], 1e-12)


def gen_bezier(p, u, t1, t2):
    a1 = np.outer(3 * (1 - u) ** 2 * u, t1)
    a2 = np.outer(3 * (1 - u) * u ** 2, t2)
    C = np.array([[(a1 * a1).sum(), (a1 * a2).sum()], [(a1 * a2).sum(), (a2 * a2).sum()]])
    b0 = (1 - u) ** 3 + 3 * (1 - u) ** 2 * u
    b1 = 3 * (1 - u) * u ** 2 + u ** 3
    tmp = p - np.outer(b0, p[0]) - np.outer(b1, p[-1])
    X = np.array([(a1 * tmp).sum(), (a2 * tmp).sum()])
    det = C[0, 0] * C[1, 1] - C[0, 1] * C[1, 0]
    seg = np.hypot(*(p[-1] - p[0]))
    if abs(det) > 1e-12:
        al1 = (X[0] * C[1, 1] - X[1] * C[0, 1]) / det
        al2 = (C[0, 0] * X[1] - C[1, 0] * X[0]) / det
    else:
        al1 = al2 = seg / 3
    if al1 < 1e-6 * seg or al2 < 1e-6 * seg or al1 > 2 * seg or al2 > 2 * seg:
        al1 = al2 = seg / 3
    return np.array([p[0], p[0] + al1 * t1, p[-1] + al2 * t2, p[-1]])


def reparam(ctrl, p, u):
    q = bez(ctrl, u) - p
    d1 = bez_d1(ctrl, u)
    d2 = bez_d2(ctrl, u)
    num = (q * d1).sum(1)
    den = (d1 * d1).sum(1) + (q * d2).sum(1)
    un = np.clip(u - np.where(np.abs(den) > 1e-12, num / den, 0), 0, 1)
    un[0], un[-1] = 0, 1
    return np.maximum.accumulate(un)


def max_err(ctrl, p, u):
    d = np.hypot(*(bez(ctrl, u) - p).T)
    i = int(np.argmax(d))
    return float(d[i]), i


def unitv(v):
    n = np.hypot(*v)
    return v / n if n > 1e-12 else v


def fit_cubic(p, t1, t2, err, min_pts=12):
    n = len(p)
    if n <= 3:
        seg = np.hypot(*(p[-1] - p[0]))
        return [np.array([p[0], p[0] + t1 * seg / 3, p[-1] + t2 * seg / 3, p[-1]])]
    u = chord_params(p)
    ctrl = gen_bezier(p, u, t1, t2)
    e, split = max_err(ctrl, p, u)
    if e < err:
        return [ctrl]
    if e < err * 6:
        for _ in range(20):
            u = reparam(ctrl, p, u)
            ctrl = gen_bezier(p, u, t1, t2)
            e, split = max_err(ctrl, p, u)
            if e < err:
                return [ctrl]
    if n < 2 * min_pts and e < 2.5 * err:
        return [ctrl]
    split = int(np.clip(split, min(min_pts, n // 2), n - 1 - min(min_pts, n // 2)))
    tc = unitv(p[min(split + 3, n - 1)] - p[max(split - 3, 0)])
    return fit_cubic(p[:split + 1], t1, -tc, err, min_pts) + fit_cubic(p[split:], tc, t2, err, min_pts)


def is_line(p, tol):
    a, b = p[0], p[-1]
    v = b - a
    L = np.hypot(*v)
    if L < 1e-9:
        return True
    return (np.abs((p[:, 0] - a[0]) * v[1] - (p[:, 1] - a[1]) * v[0]) / L).max() <= tol


# ---------------------------------------------------------------- rebuild

def line_runs(p, lines, step, dtol=0.8, atol=5.0, min_len=10.0):
    """[(i0, i1, line)] maximal cyclic index runs of p lying on a known line and running along it."""
    n = len(p)
    h = max(2, int(2.0 / step))
    tang = np.roll(p, -h, 0) - np.roll(p, h, 0)
    tang /= np.maximum(np.hypot(*tang.T), 1e-9)[:, None]
    runs = []
    for L in lines:
        on = (np.abs(L.dist(p)) < dtol) & (np.abs(tang @ L.n) < np.sin(np.radians(atol)))
        if not on.any():
            continue
        if on.all():
            runs.append((0, n - 1, L)); continue
        start = int(np.argmin(on))  # an index that is off
        i = 0
        while i < n:
            k = (start + i) % n
            if on[k]:
                j = i
                while j + 1 < n and on[(start + j + 1) % n]:
                    j += 1
                if (j - i + 1) * step >= min_len:
                    runs.append(((start + i) % n, (start + j) % n, L))
                i = j + 1
            else:
                i += 1
    return runs


def rebuild(d, lines=(), err=0.3, line_tol=0.3, corner_deg=28.0, sigma=2.0, step=0.5, min_area=4.0,
            snap_px=6.0, merge_px=8.0, meet_px=5.0):
    """Refit every closed subpath: straight runs on known lines become exact snapped lines (meeting at
    their exact intersection where two lines form a corner), the rest minimal G1 cubic Beziers."""
    out = []
    for poly in kit.flatten(kit.parse_d(d), tol=0.05):
        if len(poly) < 4:
            continue
        P = np.asarray(poly)
        area = 0.5 * abs(np.dot(P[:-1, 0], P[1:, 1]) - np.dot(P[1:, 0], P[:-1, 1]))
        if area < min_area:
            continue
        p = resample(poly, step)
        n = len(p)
        hc = max(3, int(3.0 / step))
        corners = sorted(find_corners(p, h=hc, thresh=corner_deg))
        runs = line_runs(p, lines, step)
        snap = int(snap_px / step)
        ext_runs = []
        for i0, i1, L in runs:
            for c in corners:
                if 0 < (i0 - c) % n <= snap:
                    i0 = c
                if 0 < (c - i1) % n <= snap:
                    i1 = c
            ext_runs.append((i0, i1, L))
        bset = set(corners) | {r[0] for r in ext_runs} | {r[1] for r in ext_runs}
        if not bset:
            bset = {0, n // 2}
        order = sorted(bset)
        kind = {i: ('corner' if i in corners else ('join' if any(i in r[:2] for r in ext_runs) else 'smooth')) for i in order}
        pieces = []
        for k, i0 in enumerate(order):
            i1 = order[(k + 1) % len(order)]
            idx = np.arange(i0, i1 + (n if i1 <= i0 else 0) + 1) % n
            L = None
            for r0, r1, RL in ext_runs:
                span = np.arange(r0, r1 + (n if r1 < r0 else 0) + 1) % n
                if np.isin(idx, span).mean() > 0.8:
                    L = RL
            pieces.append({'i0': i0, 'i1': i1, 'idx': idx, 'L': L})
        # drop short free pieces between two different lines that meet nearby -> exact corner
        changed = True
        while changed and len(pieces) > 2:
            changed = False
            for k in range(len(pieces)):
                a, b, c = pieces[k - 1], pieces[k], pieces[(k + 1) % len(pieces)]
                # a short bump (one or more free pieces) between two runs of the same line: one line
                if a['L'] is not None and b['L'] is None:
                    j, free = k, []
                    while pieces[j % len(pieces)]['L'] is None and len(free) < 4:
                        free.append(j % len(pieces)); j += 1
                    c2 = pieces[j % len(pieces)]
                    pts = np.concatenate([pieces[f]['idx'] for f in free])
                    if (c2['L'] is a['L'] and len(pieces) - len(free) > 2 and len(pts) * step < 3 * merge_px
                            and np.abs(a["L"].dist(p[pts])).max() < 2.0):
                        a['i1'] = c2['i1']
                        a['idx'] = np.concatenate([a['idx'], pts, c2['idx']])
                        drop = set(free) | {j % len(pieces)}
                        pieces[:] = [q for t, q in enumerate(pieces) if t not in drop]
                        changed = True
                        break
                if (b['L'] is None and a['L'] is not None and c['L'] is not None and a['L'] is not c['L']
                        and len(b['idx']) * step < merge_px):
                    q = a['L'].meet(c['L'])
                    mid = p[b['idx'][len(b['idx']) // 2]]
                    if q is not None and np.hypot(*(q - mid)) < meet_px:
                        c['i0'] = a['i1']
                        kind[a['i1']] = 'corner'
                        pieces.pop(k)
                        changed = True
                        break
        m = len(pieces)
        anchor = []
        for k in range(m):
            prv, cur = pieces[k - 1], pieces[k]
            i = cur['i0']
            q = p[i].copy()
            if prv['L'] is not None and cur['L'] is not None and prv['L'] is not cur['L']:
                x = prv['L'].meet(cur['L'])
                if x is not None and np.hypot(*(x - p[i])) < meet_px:
                    q = x
                else:
                    q = cur['L'].project(p[i])
            elif cur['L'] is not None:
                q = cur['L'].project(p[i])
            elif prv['L'] is not None:
                q = prv['L'].project(p[i])
            anchor.append(q)
        segs = []
        for k in range(m):
            cur = pieces[k]
            a0, a1 = anchor[k], anchor[(k + 1) % m]
            if cur['L'] is not None:
                segs.append(('L', a1[0], a1[1]))
                continue
            run = smooth_open(p[cur['idx']].copy(), sigma / step)
            run[0], run[-1] = a0, a1
            if len(run) < 4 or is_line(run, line_tol):
                segs.append(('L', a1[0], a1[1]))
                continue
            prvL, nxtL = pieces[k - 1]['L'], pieces[(k + 1) % m]['L']
            i0, i1 = cur['i0'], pieces[(k + 1) % m]['i0']

            def tan(i, sign, Lnb):
                if kind.get(i) != 'corner' and Lnb is not None:
                    return unitv(Lnb.t * np.sign((p[(i + sign * 4) % n] - p[i]) @ Lnb.t))
                if kind.get(i) == 'smooth':
                    return unitv(p[(i + 4) % n] - p[(i - 4) % n]) * sign
                kk = min(8, len(run) - 1)
                return unitv(run[kk] - run[0]) if sign > 0 else unitv(run[-1 - kk] - run[-1])
            for c in fit_cubic(run, tan(i0, +1, prvL), tan(i1, -1, nxtL), err):
                segs.append(('C', c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1]))
        out.append({'start': tuple(anchor[0]), 'segs': segs, 'closed': True})
    return kit.format_d(out, 3)


def count_anchors(d):
    return sum(len(s['segs']) for s in kit.parse_d(d))


def micro_cleanup(d, min_len=2.5, near=None, radius=6.0):
    """Remove micro segments (chord < min_len px) that Pathfinder leaves where shapes meet: next to a
    straight line the line's end is kept and the curve re-attached to it; between curves the two anchors
    merge at their midpoint (neighbouring handles move with them); line-line corners are kept exact."""
    out = []
    for sp in kit.parse_d(d):
        pts = [np.array(sp['start'], float)]
        segs = []
        for g in sp['segs']:
            if g[0] == 'L':
                segs.append(['L', None, None])
            else:
                segs.append(['C', np.array(g[1:3], float), np.array(g[3:5], float)])
            pts.append(np.array(g[-2:], float))
        closed = sp['closed']
        if closed and np.hypot(*(pts[-1] - pts[0])) < 1e-6:
            pts = pts[:-1]            # anchors 0..m-1, segment k goes pts[k] -> pts[k+1 mod m]
        else:
            if closed:
                segs.append(['L', None, None])
        changed = True
        while changed and len(segs) > 3:
            changed = False
            m = len(segs)
            for k in range(m):
                a, b = pts[k], pts[(k + 1) % m]
                if np.hypot(*(b - a)) >= min_len:
                    continue
                if near is not None and min(np.hypot(*(a - np.asarray(q))) for q in near) > radius:
                    continue
                prv, nxt = segs[k - 1], segs[(k + 1) % m]
                if prv[0] == 'L' and nxt[0] == 'L':
                    continue
                if k == m - 1:           # rotate so the micro segment is not the closing one
                    segs[:] = segs[1:] + segs[:1]
                    pts[:] = pts[1:] + pts[:1]
                    k = m - 2
                    a, b = pts[k], pts[k + 1]
                    prv, nxt = segs[k - 1], segs[k + 1]
                if prv[0] == 'L':        # keep a (end of the line), pull b onto it
                    keep, delta_i = a, (k + 1) % m
                    if nxt[0] == 'C':
                        nxt[1] = nxt[1] + (a - b)
                    pts[delta_i] = a
                elif nxt[0] == 'L':      # keep b (start of the line), pull a onto it
                    if prv[0] == 'C':
                        prv[2] = prv[2] + (b - a)
                    pts[k] = b
                else:
                    mid = (a + b) / 2
                    prv[2] = prv[2] + (mid - a)
                    nxt[1] = nxt[1] + (mid - b)
                    pts[k] = mid; pts[(k + 1) % m] = mid
                # drop segment k and the duplicated anchor k+1
                del segs[k]
                del pts[(k + 1) % m]
                changed = True
                break
        m = len(segs)
        new = {'start': tuple(pts[0]), 'segs': [], 'closed': True}
        for k in range(m):
            e = pts[(k + 1) % m]
            if segs[k][0] == 'L':
                new['segs'].append(('L', e[0], e[1]))
            else:
                new['segs'].append(('C', segs[k][1][0], segs[k][1][1], segs[k][2][0], segs[k][2][1], e[0], e[1]))
        out.append(new)
    return kit.format_d(out, 3)
