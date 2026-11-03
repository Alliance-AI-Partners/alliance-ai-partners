"""Scratch: fit the wave's centerline y_c(x) (natural cubic spline) and half-width h(x) (quadratic)
so that the normal offsets +-h reproduce the measured top/bottom edges of the ribbon in original 02."""
import json
import sys
import numpy as np

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
E = {int(k): v for k, v in json.load(open(W + r'\wave_edges.json')).items()}
XL, XR = 1037.5, 1318.2


def spline(knots, vals, xs):
    """Natural cubic spline through (knots, vals), evaluated with first derivative at xs."""
    n = len(knots)
    hk = np.diff(knots)
    A = np.zeros((n, n)); r = np.zeros(n)
    A[0, 0] = A[-1, -1] = 1
    for i in range(1, n - 1):
        A[i, i - 1], A[i, i], A[i, i + 1] = hk[i - 1], 2 * (hk[i - 1] + hk[i]), hk[i]
        r[i] = 6 * ((vals[i + 1] - vals[i]) / hk[i] - (vals[i] - vals[i - 1]) / hk[i - 1])
    M = np.linalg.solve(A, r)
    i = np.clip(np.searchsorted(knots, xs) - 1, 0, n - 2)
    x0, x1, h_ = knots[i], knots[i + 1], hk[i]
    a, b = (x1 - xs) / h_, (xs - x0) / h_
    y = a * vals[i] + b * vals[i + 1] + ((a ** 3 - a) * M[i] + (b ** 3 - b) * M[i + 1]) * h_ ** 2 / 6
    dy = (vals[i + 1] - vals[i]) / h_ + (-(3 * a ** 2 - 1) * M[i] + (3 * b ** 2 - 1) * M[i + 1]) * h_ / 6
    return y, dy


def model(p, knots, xs):
    nk = len(knots)
    yc, dy = spline(knots, p[:nk], xs)
    u = (xs - (XL + XR) / 2) / ((XR - XL) / 2)
    hw = p[nk] + p[nk + 1] * u + p[nk + 2] * u ** 2
    nrm = np.sqrt(1 + dy ** 2)
    nx, ny = dy / nrm, -1 / nrm  # unit normal pointing up (y down screen)
    top = np.stack([xs + hw * nx, yc + hw * ny], -1)
    bot = np.stack([xs - hw * nx, yc - hw * ny], -1)
    return yc, hw, top, bot


def residual(p, knots, data_t, data_b):
    xs = np.linspace(XL - 15, XR + 15, 1400)
    _, _, top, bot = model(p, knots, xs)
    rt = data_t[:, 1] - np.interp(data_t[:, 0], top[:, 0], top[:, 1])
    rb = data_b[:, 1] - np.interp(data_b[:, 0], bot[:, 0], bot[:, 1])
    return np.concatenate([rt, rb])


def fit(nk):
    knots = np.linspace(XL - 10, XR + 10, nk)
    dt = np.array([[x + 0.5, v["top"]] for x, v in E.items() if XL + 1 < x + 0.5 < XR - 1 and v["top"]])
    db = np.array([[x + 0.5, v["bot"]] for x, v in E.items() if XL + 1 < x + 0.5 < XR - 1 and v["bot"]])
    mid = np.interp(knots, dt[:, 0], (dt[:, 1] + np.interp(dt[:, 0], db[:, 0], db[:, 1])) / 2)
    p = np.concatenate([mid, [11.0, 0.0, 0.0]])
    lam = 1e-2
    for it in range(60):
        r = residual(p, knots, dt, db)
        J = np.zeros((len(r), len(p)))
        for j in range(len(p)):
            q = p.copy(); q[j] += 1e-4
            J[:, j] = (residual(q, knots, dt, db) - r) / 1e-4
        g = J.T @ r
        Hm = J.T @ J
        step = np.linalg.solve(Hm + lam * np.diag(np.diag(Hm) + 1e-9), -g)
        if (residual(p + step, knots, dt, db) ** 2).sum() < (r ** 2).sum():
            p = p + step; lam *= 0.5
        else:
            lam *= 4
    r = residual(p, knots, dt, db)
    return p, knots, r


if __name__ == '__main__':
    for nk in (6, 7, 8, 9, 10, 12):
        p, knots, r = fit(nk)
        print(nk, 'rms %.3f max %.3f' % (np.sqrt((r ** 2).mean()), np.abs(r).max()), 'h', np.round(p[nk:], 3))
    nk = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    p, knots, r = fit(nk)
    json.dump({"knots": knots.tolist(), "p": p.tolist(), "XL": XL, "XR": XR}, open(W + r'\center_fit.json', 'w'))
    print('saved nk', nk, 'knots', np.round(knots, 2), 'vals', np.round(p[:nk], 2))
