"""Scratch: fit silhouette splines + the three face boundaries B1..B3 of the wave; saves wave_model.json."""
import json
import numpy as np
from wavefit import E, XL, XR, spline_basis, lsq_spline, edges, evaluate, W

NK_EDGE = 16


def fit_edges():
    xd, yt, yb = edges()
    w = np.ones_like(xd)
    w[(xd > 1284) & (xd < 1300)] = 0.25  # glow-merged cyan edge there; trust the spline instead
    knots = np.linspace(XL, XR, NK_EDGE)
    out = {}
    for name, yd in (("top", yt), ("bot", yb)):
        B, c = spline_basis(knots, xd)
        vals, *_ = np.linalg.lstsq(B * w[:, None], (yd - c) * w, rcond=None)
        r = B @ vals + c - yd
        print(name, 'rms %.3f max %.3f' % (np.sqrt((r[w == 1] ** 2).mean()), np.abs(r[w == 1]).max()))
        out[name] = vals
    return knots, out


def slope(knots, vals, x, eps=1e-3):
    y = evaluate(knots, vals, [x - eps, x + eps])
    return (y[1] - y[0]) / (2 * eps)


GUIDE = {  # rough (x, fraction-from-top) path of each boundary, read off the measurements, to pick its points
    "B1": [(1038, .467), (1050, .516), (1071, .539), (1083, .467), (1092, .374), (1101, .36), (1110, .304), (1119, .23),
           (1131, .135), (1143, .104)],
    "B2": [(1119, .894), (1131, .834), (1140, .73), (1149, .609), (1158, .516), (1167, .469), (1179, .494), (1188, .541),
           (1200, .494), (1209, .415), (1218, .325), (1227, .235), (1236, .091)],
    "B3": [(1224, .902), (1233, .831), (1242, .733), (1251, .661), (1260, .609), (1269, .558), (1278, .478), (1287, .417),
           (1293, .40), (1305, .476), (1311, .511), (1317, .553)],
}


def boundary_points(name, tol=0.08):
    g = np.array(GUIDE[name])
    pts = []
    for x, v in E.items():
        if not (g[0, 0] - 2 <= x <= g[-1, 0] + 2) or not v["top"] or not v["bot"]:
            continue
        fg = np.interp(x, g[:, 0], g[:, 1])
        for p in v["peaks"]:
            f = (p[0] - v["top"]) / (v["bot"] - v["top"])
            if abs(f - fg) < tol and p[1] >= 4:
                pts.append((x + 0.5, p[0], p[1]))
    return np.array(pts)


def fit_boundary(pts, ek, ev, x0, x1, start, end, n_int):
    """Clamped spline from x0 to x1. start/end: 'top'/'bot' (tangent to that edge) or None (free end).
    Returns knots, vals, rms."""
    knots = np.linspace(x0, x1, n_int + 2)
    d0 = slope(ek, ev[start], x0) if start else None
    d1 = slope(ek, ev[end], x1) if end else None
    fixed = {}
    if start:
        fixed[0] = float(evaluate(ek, ev[start], [x0])[0])
    if end:
        fixed[len(knots) - 1] = float(evaluate(ek, ev[end], [x1])[0])
    xs, ys, ws = pts[:, 0], pts[:, 1], np.sqrt(np.minimum(pts[:, 2], 20) / 20)
    m = (xs >= x0) & (xs <= x1)
    xs, ys, ws = xs[m], ys[m], ws[m]
    if start and end:
        B, c = spline_basis(knots, xs, clamp=(d0, d1))
    else:
        # one free end: natural on the free side is not expressible with this clamp helper; use a slope
        # estimated from the data at the free end instead (fitted below by a 1-D search)
        B, c = None, None
    best = None
    if B is not None:
        cand = [(d0, d1)]
    else:
        base = np.polyfit(xs[:8] if not start else xs[-8:], ys[:8] if not start else ys[-8:], 1)[0]
        cand = [((base + s) if not start else d0, (base + s) if not end else d1) for s in np.linspace(-1.5, 1.5, 61)]
    for dd in cand:
        B, c = spline_basis(knots, xs, clamp=dd)
        free = [k for k in range(len(knots)) if k not in fixed]
        cf = c + sum(B[:, k] * v for k, v in fixed.items())
        vf, *_ = np.linalg.lstsq(B[:, free] * ws[:, None], (ys - cf) * ws, rcond=None)
        vals = np.zeros(len(knots))
        for k, v in fixed.items():
            vals[k] = v
        vals[free] = vf
        r = (B @ vals + c - ys)
        rms = float(np.sqrt((r ** 2 * ws ** 2).sum() / (ws ** 2).sum()))
        if best is None or rms < best[2]:
            best = (knots, vals, rms, dd, float(np.abs(r).max()))
    return best


if __name__ == '__main__':
    ek, ev = fit_edges()
    model = {"XL": XL, "XR": XR, "edge_knots": ek.tolist(), "top": ev["top"].tolist(), "bot": ev["bot"].tolist(), "bounds": {}}
    specs = {
        "B1": dict(lo=XL, hi=1150, fmin=0.02, fmax=0.75, start=None, end="top"),
        "B2": dict(lo=1100, hi=1245, fmin=0.05, fmax=0.97, start="bot", end="top"),
        "B3": dict(lo=1205, hi=XR, fmin=0.05, fmax=0.97, start="bot", end=None),
    }
    for name, s in specs.items():
        pts = boundary_points(name)
        print(name, len(pts), "points")
        best = None
        x0s = [XL] if s["start"] is None else np.arange(1098, 1124, 1.0) if name == "B2" else np.arange(1200, 1226, 1.0)
        x1s = [XR] if s["end"] is None else np.arange(1140, 1162, 1.0) if name == "B1" else np.arange(1234, 1256, 1.0)
        for n_int in (3, 4, 5):
            for x0 in x0s:
                for x1 in x1s:
                    r = fit_boundary(pts, ek, ev, float(x0), float(x1), s["start"], s["end"], n_int)
                    score = r[2] + 0.004 * n_int  # mild preference for fewer knots
                    if best is None or score < best[0]:
                        best = (score, n_int, x0, x1, r)
        score, n_int, x0, x1, (knots, vals, rms, dd, mx) = best
        print(name, 'n_int', n_int, 'x0 %.1f x1 %.1f rms %.3f max %.3f slopes %s' % (x0, x1, rms, mx, np.round(dd, 3)))
        model["bounds"][name] = {"knots": knots.tolist(), "vals": vals.tolist(), "clamp": [float(dd[0]), float(dd[1])],
                                 "start": s["start"], "end": s["end"]}
    json.dump(model, open(W + r'\wave_model.json', 'w'), indent=1)
