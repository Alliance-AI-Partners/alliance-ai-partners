"""Scratch: fit the wave silhouette (top/bottom edges as least-squares natural cubic splines in x)
and the three internal face boundaries (clamped splines that leave/join the edges tangentially)."""
import json
import sys
import numpy as np

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
E = {int(k): v for k, v in json.load(open(W + r'\wave_edges.json')).items()}
XL, XR = 1037.5, 1318.2


def spline_basis(knots, xs, clamp=None):
    """Matrix B (len(xs), n) so that y(xs) = B @ vals for a natural cubic spline through the knot values.
    clamp=(d0, d1) gives a clamped spline with end slopes d0, d1 instead; returns (B, c) with y = B@vals + c."""
    n = len(knots)
    hk = np.diff(knots)
    A = np.zeros((n, n)); R = np.zeros((n, n)); rc = np.zeros(n)
    if clamp is None:
        A[0, 0] = A[-1, -1] = 1
    else:
        A[0, 0], A[0, 1] = 2 * hk[0], hk[0]
        R[0, 0], R[0, 1] = -6 / hk[0], 6 / hk[0]; rc[0] = -6 * clamp[0]
        A[-1, -2], A[-1, -1] = hk[-1], 2 * hk[-1]
        R[-1, -2], R[-1, -1] = 6 / hk[-1], -6 / hk[-1]; rc[-1] = 6 * clamp[1]
    for i in range(1, n - 1):
        A[i, i - 1], A[i, i], A[i, i + 1] = hk[i - 1], 2 * (hk[i - 1] + hk[i]), hk[i]
        R[i, i - 1], R[i, i], R[i, i + 1] = 6 / hk[i - 1], -6 / hk[i - 1] - 6 / hk[i], 6 / hk[i]
    Ai = np.linalg.inv(A)
    Mv, Mc = Ai @ R, Ai @ rc  # second derivatives M = Mv @ vals + Mc
    i = np.clip(np.searchsorted(knots, xs) - 1, 0, n - 2)
    a, b = (knots[i + 1] - xs) / hk[i], (xs - knots[i]) / hk[i]
    B = np.zeros((len(xs), n))
    B[np.arange(len(xs)), i] += a
    B[np.arange(len(xs)), i + 1] += b
    ca = ((a ** 3 - a) * hk[i] ** 2 / 6)[:, None]
    cb = ((b ** 3 - b) * hk[i] ** 2 / 6)[:, None]
    B += ca * Mv[i] + cb * Mv[i + 1]
    c = ca[:, 0] * Mc[i] + cb[:, 0] * Mc[i + 1]
    return B, c


def lsq_spline(xd, yd, knots):
    B, c = spline_basis(knots, xd)
    vals, *_ = np.linalg.lstsq(B, yd - c, rcond=None)
    r = B @ vals + c - yd
    return vals, r


def edges():
    xs = np.array([x for x in sorted(E) if XL + 0.6 < x + 0.5 < XR - 0.6 and E[x]["top"] and E[x]["bot"]])
    return xs + 0.5, np.array([E[x]["top"] for x in xs]), np.array([E[x]["bot"] for x in xs])


def deriv(knots, vals, x, eps=1e-3):
    B1, c1 = spline_basis(knots, np.array([x - eps, x + eps]))
    y = B1 @ vals + c1
    return (y[1] - y[0]) / (2 * eps)


def evaluate(knots, vals, xs, clamp=None):
    B, c = spline_basis(knots, np.asarray(xs, float), clamp)
    return B @ vals + c


if __name__ == '__main__':
    xd, yt, yb = edges()
    for nk in (8, 10, 12, 14, 16, 18):
        knots = np.linspace(XL, XR, nk)
        _, rt = lsq_spline(xd, yt, knots)
        _, rb = lsq_spline(xd, yb, knots)
        print(nk, 'top rms %.3f max %.3f | bot rms %.3f max %.3f' % (
            np.sqrt((rt ** 2).mean()), np.abs(rt).max(), np.sqrt((rb ** 2).mean()), np.abs(rb).max()))
