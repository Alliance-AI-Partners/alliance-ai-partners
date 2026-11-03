# Face construction for the shield frame: polynomial boundary curves -> exact Bezier paths.
# Measurement coordinates (pixel centers at integers); SVG space = measurement + 0.5.
import numpy as np
from geom import E, AX, top_meets_side

OV = 0.6  # overlap of a lower face under the face stacked above it (px)


class Curve:
    """kind 'x': x = p(y);  kind 'y': y = p(x)."""

    def __init__(self, kind, coef):
        self.kind, self.p = kind, np.poly1d(coef)

    def shift(self, d):
        return Curve(self.kind, (self.p + d).coeffs)

    def mirror(self):
        if self.kind == 'x':
            return Curve('x', (2 * AX - self.p).coeffs)
        return Curve('y', self.p(np.poly1d([-1.0, 2 * AX])).coeffs)

    @staticmethod
    def through(a, b):
        a, b = np.asarray(a, float), np.asarray(b, float)
        dx, dy = b - a
        if abs(dx) >= abs(dy):
            s = dy / dx
            return Curve('y', [s, a[1] - s * a[0]])
        s = dx / dy
        return Curve('x', [s, a[0] - s * a[1]])


def const_x(x):
    return Curve('x', [x])


def const_y(y):
    return Curve('y', [y])


def _pick(roots, target):
    r = roots[np.abs(roots.imag) < 1e-7].real
    if not len(r):
        raise ValueError('no real intersection')
    return r[np.argmin(np.abs(r - target))]


def intersect(c1, c2, guess):
    if c1.kind == c2.kind:
        d = c1.p - c2.p
        v = _pick(np.roots(d.coeffs), guess[1] if c1.kind == 'x' else guess[0])
        return np.array([c1.p(v), v]) if c1.kind == 'x' else np.array([v, c1.p(v)])
    a, b = (c1, c2) if c1.kind == 'x' else (c2, c1)
    y = _pick(np.roots((b.p(a.p) - np.poly1d([1.0, 0.0])).coeffs), guess[1])
    return np.array([a.p(y), y])


def _bez(p, u0, u1):
    """Cubic Bezier ordinates for polynomial p (deg <= 3) on [u0, u1]."""
    h = u1 - u0
    q = p(np.poly1d([h, u0]))
    a = np.zeros(4)
    a[4 - len(q.coeffs):] = q.coeffs
    p3, p2, p1, p0 = a
    return [p0, p0 + p1 / 3, p0 + 2 * p1 / 3 + p2 / 3, p0 + p1 + p2 + p3], [u0, u0 + h / 3, u0 + 2 * h / 3, u1]


def segment(c, a, b):
    """Path segment from a to b along curve c -> ('L', b) or ('C', c1, c2, b)."""
    if c.p.order <= 1:
        return ('L', b)
    if c.kind == 'x':
        xs, ys = _bez(c.p, a[1], b[1])
    else:
        ys, xs = _bez(c.p, a[0], b[0])
    return ('C', np.array([xs[1], ys[1]]), np.array([xs[2], ys[2]]), b)


class Face:
    def __init__(self, fid, curves, guesses):
        self.id = fid
        self.curves = curves
        self.verts = [intersect(curves[i], curves[(i + 1) % len(curves)], guesses[i]) for i in range(len(curves))]
        for v, g in zip(self.verts, guesses):
            if np.hypot(*(v - np.asarray(g))) > 8:
                raise ValueError(f'{fid}: vertex {v} far from guess {g}')

    def segs(self):
        n = len(self.curves)
        out = []
        for i in range(n):
            out.append(segment(self.curves[i], self.verts[i - 1], self.verts[i]))
        return self.verts[-1], out

    def d(self, off=0.5, nd=3):
        f = lambda v: ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
        P = lambda p: f'{f(p[0] + off)} {f(p[1] + off)}'
        start, segs = self.segs()
        s = ['M' + P(start)]
        for g in segs:
            s.append(('L' + P(g[1])) if g[0] == 'L' else ('C' + P(g[1]) + ' ' + P(g[2]) + ' ' + P(g[3])))
        return ' '.join(s) + ' Z'

    def n_anchors(self):
        return len(self.curves)


def mirrored(fid, face_curves, guesses, axis_index=None):
    """Right-half face: mirror every curve; the axis curve (if any) stays exactly on the axis."""
    cs = [c.mirror() for c in face_curves]
    if axis_index is not None:
        cs[axis_index] = const_x(AX)
    gs = [np.array([2 * AX - g[0], g[1]]) for g in guesses]
    return Face(fid, cs, gs)


def build():
    C = {}
    for k in ('T_o', 'T_b1', 'T_b2', 'T_b3', 'D_o', 'D_b1', 'D_b2', 'D_b3', 'C_t', 'C_b', 'UW', 'LW'):
        C[k] = Curve('y', E[k]['coef'])
    for k in ('S_o', 'S_b1', 'S_b2', 'S_b3'):
        C[k] = Curve('x', E[k]['coef'])
    U_top, U_bot, L_top, L_bot = E['U_top'], E['U_bot'], E['L_top'], E['L_botin']
    Ko, K1 = top_meets_side('T_o', 'S_o'), top_meets_side('T_b1', 'S_b1')
    K2, K3 = top_meets_side('T_b2', 'S_b2'), top_meets_side('T_b3', 'S_b3')
    MIT_o, MIT_i = Curve.through(Ko, K1), Curve.through(K2, K3)
    AXL = const_x(AX + OV)
    Y_SB = const_y(U_top + 2.0)  # side faces run 2 px under the upper bar
    yT = lambda k, x: float(C[k].p(x))
    xS = lambda k, y: float(C[k].p(y))
    yD = lambda k, x: float(C[k].p(x))
    faces = []

    def pair(name, curves, guesses, axis_index):
        faces.append(Face(name + '-L', curves, guesses))
        faces.append(mirrored(name + '-R', curves, guesses, axis_index))

    # ---- white fields (bottom of the stack)
    T3o, S3o = C['T_b3'].shift(-OV), C['S_b3'].shift(-OV)
    yF = U_top + OV
    faces.append(Face('field-upper', [T3o, T3o.mirror(), S3o.mirror(), const_y(yF), S3o],
                      [(AX, yT('T_b3', AX)), (2 * AX - K3[0], K3[1]), (2 * AX - xS('S_b3', yF), yF),
                       (xS('S_b3', yF), yF), K3]))
    tipU = np.array([(U_bot - C['UW'].p.coeffs[1]) / C['UW'].p.coeffs[0], U_bot])
    tipL = np.array([(L_top - C['LW'].p.coeffs[1]) / C['LW'].p.coeffs[0], L_top])
    END = Curve.through(tipU, tipL)
    faces.append(Face('field-banner', [const_y(U_bot - OV), END.mirror(), const_y(L_top + OV), END],
                      [(2 * AX - tipU[0], U_bot), (2 * AX - tipL[0], L_top), tipL, tipU]))
    D3o = C['D_b3'].shift(OV)
    yLF = L_bot - OV
    x3 = 556.6
    faces.append(Face('field-lower', [const_y(yLF), D3o.mirror(), D3o],
                      [(2 * AX - x3, yLF), (AX, yD('D_b3', AX)), (x3, yLF)]))

    # ---- upper frame: outer band (side under top), cyan rim, inner band (side under top)
    # Below J (where the bar's wing meets the outer edge) the outer band steps 3 px left, under the
    # wing, so the short bar/band boundary along S_o has the lower face underneath (no hairline seam).
    J = intersect(C['S_o'], C['UW'], (417.9, 464.57))
    UWd, XJ = C['UW'].shift(OV), const_x(J[0] - 3.0)
    pair('outer-side', [C['S_o'], UWd, XJ, Y_SB, C['S_b1'].shift(OV), MIT_o.shift(-OV)],
         [J + (0.1, OV), (J[0] - 3.0, float(UWd.p(J[0] - 3.0))), (J[0] - 3.0, U_top + 2),
          (xS('S_b1', U_top + 2), U_top + 2), K1, Ko], None)
    pair('outer-top', [C['T_o'], AXL, C['T_b1'].shift(OV), MIT_o],
         [(AX, yT('T_o', AX)), (AX, yT('T_b1', AX)), K1, Ko], 1)
    pair('rim-upper', [C['T_b1'], AXL, C['T_b2'].shift(OV), C['S_b2'].shift(OV), Y_SB, C['S_b1']],
         [(AX, yT('T_b1', AX)), (AX, yT('T_b2', AX)), K2, (xS('S_b2', U_top + 2), U_top + 2),
          (xS('S_b1', U_top + 2), U_top + 2), K1], 1)
    pair('inner-side', [C['S_b2'], Y_SB, C['S_b3'], MIT_i.shift(-OV)],
         [(xS('S_b2', U_top + 2), U_top + 2), (xS('S_b3', U_top + 2), U_top + 2), K3, K2], None)
    pair('inner-top', [C['T_b2'], AXL, C['T_b3'], MIT_i],
         [(AX, yT('T_b2', AX)), (AX, yT('T_b3', AX)), K3, K2], 1)

    # ---- upper banner bar (in front of the side bands)
    So, Sor, UW, UWr = C['S_o'], C['S_o'].mirror(), C['UW'], C['UW'].mirror()
    faces.append(Face('bar-upper', [UW, So, const_y(U_top), Sor, UWr, const_y(U_bot)],
                      [J, (xS('S_o', U_top), U_top), (2 * AX - xS('S_o', U_top), U_top), (2 * AX - J[0], J[1]),
                       (2 * AX - tipU[0], U_bot), tipU]))

    # ---- lower frame
    pair('inner-lower', [const_y(yLF), C['D_b3'], AXL, C['D_b2'].shift(OV)],
         [(x3, yLF), (AX, yD('D_b3', AX)), (AX, yD('D_b2', AX)), (523.4, yLF)], 2)
    faces.append(Face('bar-lower', [const_y(L_top), C['D_b1'].mirror(), const_y(L_bot), C['D_b1']],
                      [(2 * AX - 493.5, L_top), (2 * AX - 513.6, L_bot), (513.6, L_bot), (493.5, L_top)]))
    pair('rimwing-lower', [const_y(L_top), C['D_b1'].shift(-OV), AXL, C['D_o'], C['LW']],
         [(493.5, L_top), (AX, yD('D_b1', AX)), (AX, yD('D_o', AX)), (482.5, 593.0), tipL], 2)
    pair('rim-lower', [const_y(L_top), C['D_b2'], AXL, C['D_b1']],
         [(502.7, L_top), (AX, yD('D_b2', AX)), (AX, yD('D_b1', AX)), (493.5, L_top)], 2)
    pair('chevron', [C['C_t'], AXL, C['C_b']],
         [(AX, yD('C_t', AX)), (AX, yD('C_b', AX)), (584.4, 595.5)], 1)
    return faces
