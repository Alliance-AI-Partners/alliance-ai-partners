"""Re-fit a traced closed path with few anchors: flatten, find corners, then straight runs become lines
and curved runs become a minimal number of cubic Beziers (wavegeom.fit_beziers)."""
import numpy as np
import kit
from wavegeom import fit_beziers


def resample(poly, step):
    p = np.asarray(poly, float)
    if np.linalg.norm(p[0] - p[-1]) > 1e-9:
        p = np.vstack([p, p[:1]])
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    n = max(16, int(s[-1] / step))
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], -1)


def corners(q, win, ang_deg):
    n = len(q)
    idx = np.arange(n)
    a = q[(idx - win) % n] - q
    b = q[(idx + win) % n] - q
    cosang = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-12)
    turn = 180 - np.degrees(np.arccos(np.clip(cosang, -1, 1)))  # 0 = straight
    c = []
    for i in range(n):
        if turn[i] >= ang_deg and turn[i] == max(turn[(i + k) % n] for k in range(-win, win + 1)):
            if not c or i - c[-1] > win:
                c.append(i)
    return c, turn


def simplify_subpath(sub, tol=0.6, step=0.5, win=6, ang_deg=28.0):
    poly = kit.flatten([sub], tol=0.05)[0]
    q = resample(poly, step)
    n = len(q)
    cs, _ = corners(q, win, ang_deg)
    if not cs:
        cs = [0]
    segs = []
    for k, i in enumerate(cs):
        j = cs[(k + 1) % len(cs)]
        run = np.array([q[(i + t) % n] for t in range(((j - i) % n or n) + 1)])
        a, b = run[0], run[-1]
        chord = b - a
        L = np.linalg.norm(chord)
        if L > 1e-9:
            dev = np.abs(np.cross(chord / L, run - a)).max()
        else:
            dev = np.inf
        if dev <= tol:
            segs.append(("L", a, b))
            continue
        # tangents from the data near the run ends
        m = min(max(3, win // 2), len(run) // 3)
        tv = np.gradient(run, axis=0)
        tv[:m + 1] = (run[m] - run[0]) / (np.linalg.norm(run[m] - run[0]) + 1e-12)
        tv[-m - 1:] = (run[-1] - run[-1 - m]) / (np.linalg.norm(run[-1] - run[-1 - m]) + 1e-12)
        tv = tv / (np.linalg.norm(tv, axis=1, keepdims=True) + 1e-12)
        for P in fit_beziers(run, tv, tol):
            segs.append(("C", P))
    return segs


def to_d(subpath_segs, xform=lambda p: p, nd=2):
    f = lambda v: ("%.*f" % (nd, v)).rstrip("0").rstrip(".")
    out = []
    for segs in subpath_segs:
        first = segs[0][1] if segs[0][0] == "L" else segs[0][1][0]
        p = xform(first)
        out.append("M%s %s" % (f(p[0]), f(p[1])))
        for s in segs:
            if s[0] == "L":
                p = xform(s[2]); out.append("L%s %s" % (f(p[0]), f(p[1])))
            else:
                P = [xform(v) for v in s[1][1:]]
                out.append("C" + " ".join("%s %s" % (f(v[0]), f(v[1])) for v in P))
        out.append("Z")
    return " ".join(out)


def simplify_d(d, **kw):
    return [simplify_subpath(s, **kw) for s in kit.parse_d(d)]
