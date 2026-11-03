# Shield geometry from edges.json: curve evaluation, intersections, Bezier conversion.
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
E = json.loads((HERE / 'edges.json').read_text())
AX = E['axis']

# common slope for the four parallel top-edge lines (they agree to 0.0004); keep each line through
# its own fitted value at the middle of its measured span (x = 540)
_ms = [E[k]['coef'][0] for k in ('T_o', 'T_b1', 'T_b2', 'T_b3')]
M_TOP = float(np.mean(_ms))
for k in ('T_o', 'T_b1', 'T_b2', 'T_b3'):
    y540 = np.polyval(E[k]['coef'], 540.0)
    E[k]['coef'] = [M_TOP, float(y540 - M_TOP * 540.0)]


def f(name, v):
    """Evaluate a fitted boundary: x_of_y -> x(v); y_of_x -> y(v)."""
    return float(np.polyval(E[name]['coef'], v))


def df(name, v):
    return float(np.polyval(np.polyder(E[name]['coef']), v))


def solve(fun, a, b, tol=1e-9):
    fa, fb = fun(a), fun(b)
    if fa * fb > 0:
        raise ValueError('no sign change in [%g, %g]: %g %g' % (a, b, fa, fb))
    for _ in range(200):
        m = 0.5 * (a + b)
        fm = fun(m)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
        if b - a < tol:
            break
    return 0.5 * (a + b)


def top_meets_side(t, s):
    """Intersection of top line t (y of x) with side curve s (x of y). Returns (x, y)."""
    x = solve(lambda x: f(s, f(t, x)) - x, 360, 450)
    return np.array([x, f(t, x)])


def side_meets_line(s, line, ya, yb):
    """Side curve s (x of y) meets line (y of x)."""
    y = solve(lambda y: f(line, f(s, y)) - y, ya, yb)
    return np.array([f(s, y), y])


def low_meets_y(d, y, xa, xb):
    x = solve(lambda x: f(d, x) - y, xa, xb)
    return np.array([x, y])


def low_meets_line(d, line, xa, xb):
    x = solve(lambda x: f(d, x) - f(line, x), xa, xb)
    return np.array([x, f(d, x)])


def at_axis(d):
    return np.array([AX, f(d, AX)])


def bez_x_of_y(name, y0, y1):
    """Exact cubic Bezier for x = cubic(y) on [y0, y1] (y linear in t). Returns 4 control points."""
    c = np.poly1d(E[name]['coef'])
    # x(t) = c(y0 + (y1-y0) t) as a cubic in t -> Bernstein coefficients
    h = y1 - y0
    pt = np.poly1d([h, y0])
    xt = c(pt)  # poly in t
    a = np.zeros(4)
    a[4 - len(xt.coeffs):] = xt.coeffs  # a0 t^3 + a1 t^2 + a2 t + a3
    p3, p2, p1, p0 = a  # power basis: x = p3 t^3 + p2 t^2 + p1 t + p0
    b0 = p0
    b1 = p0 + p1 / 3
    b2 = p0 + 2 * p1 / 3 + p2 / 3
    b3 = p0 + p1 + p2 + p3
    ys = [y0, y0 + h / 3, y0 + 2 * h / 3, y1]
    return [np.array([bx, by]) for bx, by in zip((b0, b1, b2, b3), ys)]


def bez_y_of_x(name, x0, x1):
    """Exact cubic Bezier for y = cubic(x) on [x0, x1]."""
    c = np.poly1d(E[name]['coef'])
    h = x1 - x0
    yt = c(np.poly1d([h, x0]))
    a = np.zeros(4)
    a[4 - len(yt.coeffs):] = yt.coeffs
    p3, p2, p1, p0 = a
    b = [p0, p0 + p1 / 3, p0 + 2 * p1 / 3 + p2 / 3, p0 + p1 + p2 + p3]
    xs = [x0, x0 + h / 3, x0 + 2 * h / 3, x1]
    return [np.array([bx, by]) for bx, by in zip(xs, b)]


def mirror(p):
    return np.array([2 * AX - p[0], p[1]])
