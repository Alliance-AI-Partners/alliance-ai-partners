"""Alliance AI Partners signature icon set: geometry source of truth.

Writes components/icons/icon-<slug>.svg (duotone), icon-<slug>-mono.svg (Deep Navy), icons.json, and
renders verify/icon-sheet.png. Run:  python work/icons/build_icons.py [draft-tag]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build")
import kit  # noqa: E402

OUT = kit.COMP / "icons"
WORKDIR = kit.WORK / "icons"
BLUE, CYAN, NAVY, WHITE = kit.PALETTE["Vibrant Blue"], kit.PALETTE["Bright Cyan"], kit.PALETTE["Deep Navy"], kit.PALETTE["Pure White"]
GRID, PAD, SW = 48, 4, 3.0
A_LEG = 65.0  # A monogram leg angle from horizontal, measured on original 12 (64.7 deg both legs)


# ---------------------------------------------------------------- geometry

def f(v):
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def arc_segs(cx, cy, r, a0, a1):
    """Cubic segments for a circular arc a0 -> a1 (degrees, y down: increasing = clockwise on screen)."""
    n = max(1, math.ceil(abs(a1 - a0) / 90 - 1e-9))
    out = []
    for i in range(n):
        t0, t1 = (math.radians(a0 + (a1 - a0) * j / n) for j in (i, i + 1))
        k = 4 / 3 * math.tan((t1 - t0) / 4)
        x0, y0 = cx + r * math.cos(t0), cy + r * math.sin(t0)
        x3, y3 = cx + r * math.cos(t1), cy + r * math.sin(t1)
        out.append((x0 - k * r * math.sin(t0), y0 + k * r * math.cos(t0),
                    x3 + k * r * math.sin(t1), y3 - k * r * math.cos(t1), x3, y3))
    return out


def polar(cx, cy, r, a):
    return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))


class Pen:
    """Absolute M/L/C/Z path builder; arcs become cubics so every consumer (Illustrator, kit.parse_d) reads it."""

    def __init__(self):
        self.ops, self.cur = [], None

    def M(self, x, y):
        self.ops.append(["M", x, y]); self.cur = (x, y); return self

    def L(self, x, y):
        self.ops.append(["L", x, y]); self.cur = (x, y); return self

    def H(self, x):
        return self.L(x, self.cur[1])

    def V(self, y):
        return self.L(self.cur[0], y)

    def C(self, x1, y1, x2, y2, x, y):
        self.ops.append(["C", x1, y1, x2, y2, x, y]); self.cur = (x, y); return self

    def A(self, cx, cy, r, a0, a1):
        sx, sy = polar(cx, cy, r, a0)
        if self.cur is None:
            self.M(sx, sy)
        elif math.hypot(sx - self.cur[0], sy - self.cur[1]) > 1e-6:
            self.L(sx, sy)
        for s in arc_segs(cx, cy, r, a0, a1):
            self.C(*s)
        return self

    def Z(self):
        self.ops.append(["Z"]); return self

    def map(self, fn):
        for op in self.ops:
            for i in range(1, len(op), 2):
                op[i], op[i + 1] = fn(op[i], op[i + 1])
        return self

    def d(self):
        return " ".join(op[0] + " ".join(f(v) for v in op[1:]) for op in self.ops)


def swoosh(pen, p0, pm, p1, a0, a1, k=(0.5, 0.5, 0.5, 0.5)):
    """The brand ribbon: rises from p0 at a0 deg, runs level through pm, lifts into p1 at a1 deg
    (two cubics, tangent-continuous at pm). Measured on original 06: ~50 deg in, level middle, ~80 deg out."""
    if pen.cur is None:
        pen.M(*p0)
    c1 = math.dist(p0, pm)
    c2 = math.dist(pm, p1)
    t0 = (math.cos(math.radians(a0)), -math.sin(math.radians(a0)))
    t1 = (math.cos(math.radians(a1)), -math.sin(math.radians(a1)))
    pen.C(p0[0] + k[0] * c1 * t0[0], p0[1] + k[0] * c1 * t0[1], pm[0] - k[1] * c1, pm[1], *pm)
    pen.C(pm[0] + k[2] * c2, pm[1], p1[0] - k[3] * c2 * t1[0], p1[1] - k[3] * c2 * t1[1], *p1)
    return pen


def chevron(tip, ang, size=5.5, spread=40):
    """Open arrowhead at `tip` pointing along `ang` (deg above horizontal) as a 3-point polyline."""
    pts = []
    for s in (-spread, spread):
        a = math.radians(ang + 180 + s)
        pts.append((tip[0] + size * math.cos(a), tip[1] - size * math.sin(a)))
    return pts[0], tip, pts[1]


def rot(cx, cy, deg, tx=0.0, ty=0.0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda x, y: (cx + tx + (x - cx) * c - (y - cy) * s, cy + ty + (x - cx) * s + (y - cy) * c)


# element constructors: (tag, part, role, attrs)
def path(part, d, role="primary"):
    return ("path", part, role, {"d": d})


def circle(part, cx, cy, r, role="primary"):
    return ("circle", part, role, {"cx": cx, "cy": cy, "r": r})


def dot(part, cx, cy, r):
    return ("dot", part, "accent", {"cx": cx, "cy": cy, "r": r})


def solid(part, d):
    return ("solid", part, "accent", {"d": d})


def line(part, x1, y1, x2, y2, role="primary"):
    return ("line", part, role, {"x1": x1, "y1": y1, "x2": x2, "y2": y2})


def rect(part, x, y, w, h, rx=4, role="primary"):
    return ("rect", part, role, {"x": x, "y": y, "width": w, "height": h, "rx": rx})


# ---------------------------------------------------------------- the twelve icons

GAP = 2.0                      # visible gap where a stroke passes behind another stroke
CLEAR = SW / 2 + GAP + SW / 2  # centreline distance at which an interrupted stroke's round cap stops


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def ring_window(c, r, ang, obstacles, clear=CLEAR, step=0.1):
    """Angular window (lo, hi) around `ang` where the ring at radius r comes closer than `clear` to the
    obstacle polylines; the ring is drawn outside it, so it ducks behind the obstacle with a clean gap."""
    def dmin(a):
        p = polar(*c, r, a)
        return min(seg_dist(p, q0, q1) for poly in obstacles for q0, q1 in zip(poly, poly[1:]))
    lo = hi = ang
    while dmin(lo) < clear:
        lo -= step
    while dmin(hi) < clear:
        hi += step
    return lo, hi


def edge(a, b, ra, rb):
    """Segment between two node centres trimmed to the node radii (caps tuck under the rings)."""
    d = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
    return a[0] + ra * ux, a[1] + ra * uy, b[0] - rb * ux, b[1] - rb * uy


def cw_tangent(a):
    """Direction of travel (deg above horizontal) of a clockwise arc at angle a (y-down degrees)."""
    return -(a + 90.0)


def rounded_poly(pts, r):
    """Closed polygon whose corners are rounded by tangent arcs of radius r (echoes the round stroke joins)."""
    p, n = Pen(), len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        u = (a[0] - b[0], a[1] - b[1]); lu = math.hypot(*u); u = (u[0] / lu, u[1] / lu)
        v = (c[0] - b[0], c[1] - b[1]); lv = math.hypot(*v); v = (v[0] / lv, v[1] / lv)
        ang = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))
        t = r / math.tan(ang / 2)
        p1 = (b[0] + u[0] * t, b[1] + u[1] * t)
        p2 = (b[0] + v[0] * t, b[1] + v[1] * t)
        bis = (u[0] + v[0], u[1] + v[1]); lb = math.hypot(*bis)
        cc = (b[0] + bis[0] / lb * r / math.sin(ang / 2), b[1] + bis[1] / lb * r / math.sin(ang / 2))
        a0 = math.degrees(math.atan2(p1[1] - cc[1], p1[0] - cc[0]))
        a1 = math.degrees(math.atan2(p2[1] - cc[1], p2[0] - cc[0]))
        (p.M if i == 0 else p.L)(*p1)
        p.A(*cc, r, a0, a0 + (a1 - a0 + 540) % 360 - 180)
    return p.Z()


def ai_strategy():
    # target with an arrow home in the bullseye; both rings open where the arrow enters
    c, s = (21.0, 27.0), 5.5
    k = (c[0] + 10.5, c[1] - 10.5)  # shaft end / fletching corner on the 45 deg diagonal
    fl = [(k[0], k[1] - s), k, (k[0] + s, k[1]), (k[0] + 2 * s, k[1] - s), (k[0] + s, k[1] - s),
          (k[0] + s, k[1] - 2 * s), (k[0], k[1] - s)]
    arrow = Pen().M(*c).L(*k).M(*fl[0])
    for q in fl[1:-1]:
        arrow.L(*q)
    arrow.Z()
    obst = [[c, k], fl]
    rings = []
    for part, r in (("ring-outer", 14.5), ("ring-inner", 7.0)):
        lo, hi = ring_window(c, r, -45.0, obst)
        rings.append(path(part, Pen().A(*c, r, hi, lo + 360).d()))
    return rings + [path("arrow", arrow.d(), "accent")]


def machine_learning():
    # 1-3-1 network: one input fans out to a hidden layer that converges on the (cyan) prediction
    r, ro = 3.5, 5.0
    inp, hidden, out = (9.0, 24.0), [(24.0, 9.5), (24.0, 24.0), (24.0, 38.5)], (39.0, 24.0)
    els = [line("edge-in-%d" % (i + 1), *edge(inp, h, r, r)) for i, h in enumerate(hidden)]
    els += [line("edge-out-%d" % (i + 1), *edge(h, out, r, ro - SW / 2)) for i, h in enumerate(hidden)]
    els.append(circle("node-input", *inp, r))
    els += [circle("node-hidden-%d" % (i + 1), *h, r) for i, h in enumerate(hidden)]
    els.append(dot("output", *out, ro))
    return els


def gear_path(cx, cy, n, rt, rr, at, ar, phase=-90.0):
    g = Pen()
    for i in range(n):
        c = phase + i * 360 / n
        if i == 0:
            g.M(*polar(cx, cy, rr, c - ar))
        g.L(*polar(cx, cy, rt, c - at))
        g.A(cx, cy, rt, c - at, c + at)
        g.L(*polar(cx, cy, rr, c + ar))
        g.A(cx, cy, rr, c + ar, c + 360 / n - ar)
    return g.Z()


def automation():
    # the process (gear) with a run button at its heart
    g = gear_path(24.0, 24.0, 8, 16.5, 12.5, 8.0, 11.5, phase=-90 + 22.5)
    tri = rounded_poly([(20.2, 17.0), (31.7, 24.0), (20.2, 31.0)], 1.5)
    return [path("gear", g.d()), solid("run", tri.d())]


def data_analytics():
    # the pulled slice clears the pie by 1.5 units between the 3-unit strokes (its corner at 26.5, 21.5 and
    # radius 13.5 keep the outer extents at x 40 / y 8), so the mono icon does not fuse the two into one bar
    c, r = (22.0, 26.0), 15.0
    pie = Pen().M(*c).L(c[0] + r, c[1]).A(*c, r, 0, 270).Z()
    w, rw = (26.5, 21.5), 13.5
    wedge = Pen().M(*w).L(w[0], w[1] - rw).A(*w, rw, -90, 0).Z()
    return [path("pie", pie.d()), path("slice", wedge.d(), "accent")]


def partnership():
    # two rings on a vesica piscis (each centre on the other ring), woven over-under
    r, ca, cb = 12.0, (18.0, 24.0), (30.0, 24.0)
    up = (24.0, 24.0 - math.sqrt(r * r - 36))
    lo = (24.0, 24.0 + math.sqrt(r * r - 36))

    def window(c_under, c_over, cross):
        ang = math.degrees(math.atan2(cross[1] - c_under[1], cross[0] - c_under[0]))
        over = [polar(*c_over, r, a) for a in np.arange(0, 361, 2.0)]
        return ring_window(c_under, r, ang, [over])

    a_lo, a_hi = window(ca, cb, lo)   # left ring passes under the right one at the lower crossing
    b_lo, b_hi = window(cb, ca, up)   # right ring passes under the left one at the upper crossing
    return [path("ring-left", Pen().A(*ca, r, a_hi, a_lo + 360).d()),
            path("ring-right", Pen().A(*cb, r, b_hi, b_lo + 360).d(), "accent")]


def security_governance():
    s = Pen().M(24, 42.5).C(31.5, 39, 39, 32.5, 39, 24).V(11).L(24, 5.5).L(9, 11).V(24) \
        .C(9, 32.5, 16.5, 39, 24, 42.5).Z()
    chk = Pen().M(16.5, 23).L(21.5, 28).L(31.5, 17.5)  # sits on the shield's optical centre, 1 unit above geometric
    return [path("shield", s.d()), path("check", chk.d(), "accent")]


def growth():
    xs, tops = (9.5, 19.0, 28.5, 38.0), (34.0, 29.5, 25.0, 20.5)
    bars = [line("bar-%d" % (i + 1), x, 41.5, x, t) for i, (x, t) in enumerate(zip(xs, tops))]
    tip, ang = (41.0, 6.5), 55.0
    s = swoosh(Pen(), (6.5, 23.5), (19.5, 16.5), tip, 40, ang, k=(0.45, 0.5, 0.5, 0.45))
    h0, t, h1 = chevron(tip, ang, 6.0, 40)
    s.M(*h0).L(*t).L(*h1)
    return bars + [path("trend", s.d(), "accent")]


def cloud_shape(bc, br, sc, sr, base):
    d = math.dist(bc, sc)
    a = (br * br - sr * sr + d * d) / (2 * d)
    h = math.sqrt(br * br - a * a)
    ux, uy = (sc[0] - bc[0]) / d, (sc[1] - bc[1]) / d
    ix, iy = bc[0] + a * ux + h * uy, bc[1] + a * uy - h * ux
    ang_b = math.degrees(math.atan2(iy - bc[1], ix - bc[0]))
    ang_s = math.degrees(math.atan2(iy - sc[1], ix - sc[0]))
    return Pen().M(sc[0], base).H(bc[0]).A(*bc, br, 90, 360 + ang_b).A(*sc, sr, ang_s, 90).Z()


def cloud_integration():
    base = 27.5
    cl = cloud_shape((18.5, 17.5), 10.0, (32.5, 20.5), 7.0, base)
    r, ny = 3.5, 37.5
    left = Pen().M(17, base).V(ny - r).A(17, ny, r, -90, 270)
    right = Pen().M(31, base).V(ny - r).A(31, ny, r, -90, 270)
    # links first: the cloud's base stroke covers their caps, so no cyan bump shows on the blue line
    return [path("link-left", left.d()), path("link-right", right.d(), "accent"), path("cloud", cl.d())]


def advisory():
    head = circle("head", 16, 19.5, 6)
    sh = Pen().A(16, 42, 10, 180, 360)  # the shoulders are the P bowl: a true semicircle
    b = Pen().M(31, 6).H(38).A(38, 10, 4, -90, 0).V(15.5).A(38, 15.5, 4, 0, 90).H(32) \
        .L(27, 24).V(10).A(31, 10, 4, 180, 270).Z()
    return [head, path("shoulders", sh.d()), path("bubble", b.d(), "accent")]


def training_enablement():
    dy = 2.0  # drop the whole cap so its bounding box centres on the grid (it sat 2.25 units high)
    board = Pen().M(24, 9 + dy).L(42, 16.5 + dy).L(24, 24 + dy).L(6, 16.5 + dy).Z()
    cap = Pen().M(12.5, 19.5 + dy).V(28.5 + dy).C(12.5, 31.5 + dy, 17.5, 34.5 + dy, 24, 34.5 + dy) \
        .C(30.5, 34.5 + dy, 35.5, 31.5 + dy, 35.5, 28.5 + dy).V(19.5 + dy)
    tassel = Pen().M(39, 17.8 + dy).V(31.5 + dy)
    # cap and tassel first: the board's lower edges cover their top caps
    return [path("cap", cap.d(), "accent"), path("tassel", tassel.d()), path("board", board.d())]


def research_insights():
    # the lens finds the signal: the brand ribbon, seen through the glass
    c, r = (20.5, 20.5), 13.5
    p = polar(*c, r, 45)
    s = swoosh(Pen(), (14.5, 26.3), (20.5, 21.0), (26.5, 14.5), 50, 75, k=(0.45, 0.5, 0.5, 0.45))
    return [circle("lens", *c, r), line("handle", *p, 41, 41), path("signal", s.d(), "accent")]


def launch():
    # rocket drawn pointing up in local space, turned 45 deg; the ribbon is its exhaust trail
    body = Pen().M(-6, 9).V(-3).C(-6, -9.5, -3, -14, 0, -17).C(3, -14, 6, -9.5, 6, -3).V(9).Z()
    fin_l = Pen().M(-6, 1).L(-11.5, 7.5).V(11.5).L(-6, 9)
    fin_r = Pen().M(6, 1).L(11.5, 7.5).V(11.5).L(6, 9)
    place = rot(0, 0, 45, 28.0, 20.0)
    for p in (body, fin_l, fin_r):
        p.map(place)
    tail = place(0, 13.0)
    trail = swoosh(Pen(), (6.5, 41.5), (12.5, 35.0), tail, 60, 45, k=(0.4, 0.5, 0.5, 0.4))
    return [path("trail", trail.d(), "accent"), path("body", body.d()), path("fin-left", fin_l.d()),
            path("fin-right", fin_r.d()), circle("window", *place(0, -4), 3)]




ICONS = [
    ("ai-strategy", "AI Strategy", ai_strategy),
    ("machine-learning", "Machine Learning", machine_learning),
    ("automation", "Automation", automation),
    ("data-analytics", "Data & Analytics", data_analytics),
    ("partnership", "Partnership", partnership),
    ("security-governance", "Security & Governance", security_governance),
    ("growth", "Growth", growth),
    ("cloud-integration", "Cloud Integration", cloud_integration),
    ("advisory", "Advisory", advisory),
    ("training-enablement", "Training & Enablement", training_enablement),
    ("research-insights", "Research & Insights", research_insights),
    ("launch", "Launch", launch),
]


# ---------------------------------------------------------------- SVG output

def svg_text(slug, els, primary, accent, variant):
    sid = "icon-" + slug + ("" if variant == "duotone" else "-" + variant)
    stroke = 'stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" fill="none"' % f(SW)
    rows = []
    for tag, part, role, a in els:
        col = accent if role == "accent" else primary
        eid = "%s-%s" % (sid, part)
        if tag == "path":
            rows.append('  <path id="%s" d="%s" stroke="%s" %s/>' % (eid, a["d"], col, stroke))
        elif tag == "circle":
            rows.append('  <circle id="%s" cx="%s" cy="%s" r="%s" stroke="%s" %s/>' % (eid, f(a["cx"]), f(a["cy"]), f(a["r"]), col, stroke))
        elif tag == "line":
            rows.append('  <line id="%s" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" %s/>' % (
                eid, f(a["x1"]), f(a["y1"]), f(a["x2"]), f(a["y2"]), col, stroke))
        elif tag == "rect":
            rows.append('  <rect id="%s" x="%s" y="%s" width="%s" height="%s" rx="%s" stroke="%s" %s/>' % (
                eid, f(a["x"]), f(a["y"]), f(a["width"]), f(a["height"]), f(a["rx"]), col, stroke))
        elif tag == "dot":
            rows.append('  <circle id="%s" cx="%s" cy="%s" r="%s" fill="%s"/>' % (eid, f(a["cx"]), f(a["cy"]), f(a["r"]), col))
        elif tag == "solid":
            rows.append('  <path id="%s" d="%s" fill="%s"/>' % (eid, a["d"], col))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" id="%s" width="%d" height="%d" viewBox="0 0 %d %d">\n'
            '%s\n</svg>\n') % (sid, GRID, GRID, GRID, GRID, "\n".join(rows))


# ---------------------------------------------------------------- notes shipped in icons.json

INFO = {
    "ai-strategy": (
        "Target with an arrow home in the bullseye: a clear objective and the plan that reaches it.",
        "Concentric rings r 14.5 and r 7 on centre (21, 27), both opened where the arrow enters (2-unit gap "
        "rule). The arrow runs at 45 deg from the centre to a two-feather fletching built on a 5.5-unit module "
        "in the top-right corner of the live area.", "arrow"),
    "machine-learning": (
        "A 1-3-1 neural network: one input fans out to a hidden layer that converges on a single prediction.",
        "Node rings r 3.5 at x 9 / 24 / 39 (hidden layer at y 9.5 / 24 / 38.5). Edges are trimmed to the ring "
        "centrelines so their caps tuck under the rings. The prediction is the set's only solid dot (r 5, the "
        "same outer size as a ring).", "output node"),
    "automation": (
        "A gear with a run button at its heart: processes that run themselves.",
        "8-tooth gear on (24, 24): tip radius 16.5, root radius 12.5, teeth 16 deg wide at the tip and 23 deg "
        "at the root, rotated 22.5 deg so a gap sits at 12 o'clock. Run button = small solid triangle with "
        "1.5-unit corner radius (matching the round joins), centroid on the gear centre.", "run button"),
    "data-analytics": (
        "A pie chart with its key slice pulled out: the number that matters, separated from the rest.",
        "Three-quarter pie r 15 on (22, 26), closed through its centre; the remaining quarter is offset "
        "3 units up and right. Both are circular arcs (the P bowl construction).", "slice"),
    "partnership": (
        "Two rings woven through each other: an alliance in which each partner sits at the centre of the other.",
        "Rings r 12 with centres 12 apart, so each centre lies on the other ring (vesica piscis). "
        "Over-under weave: each ring breaks once, 2 units clear of the ring that crosses over it.", "right ring"),
    "security-governance": (
        "A shield with a check: protected, compliant, approved.",
        "Shield 30 x 37 (x 9-39, y 5.5-42.5): peaked top at 20 deg, vertical sides, mirrored curves to the "
        "point. The check is raised 1 unit to the shield's optical centre.", "check"),
    "growth": (
        "Rising bars under the brand ribbon, which lifts into an arrow.",
        "Four bars on a 9.5-unit pitch, bottoms on y 41.5, each 4.5 units taller than the last. The trend is "
        "the ribbon (40 deg entry, level middle, 55 deg exit) ending in a 6-unit chevron.", "trend"),
    "cloud-integration": (
        "A cloud with two systems plugged in beneath it, one connection highlighted.",
        "Two-lobe cloud from circles r 10 and r 7 tangent to a flat base at y 27.5. Two drop links end in "
        "r 3.5 nodes; the links are drawn beneath the cloud so its base covers their caps.", "right link"),
    "advisory": (
        "An advisor and a speech bubble: guidance, conversation, counsel.",
        "Head r 6 over semicircular shoulders r 10 (the P bowl). The bubble is a 4-radius rounded rectangle "
        "whose lower-left corner becomes the tail, pointing back at the advisor.", "speech bubble"),
    "training-enablement": (
        "A mortarboard: training, certification, capability building.",
        "Board rhombus 36 x 15, cap band 23 wide with a rounded base, tassel on the right. Cap and tassel are "
        "drawn beneath the board so its edges cover their caps; the whole cap is centred on the grid.", "cap band"),
    "research-insights": (
        "A magnifier that has found the signal: the brand ribbon, seen through the lens.",
        "Lens r 13.5 on (20.5, 20.5), 45 deg handle to (41, 41). The ribbon inside (50 deg entry, level "
        "middle, 75 deg exit) is held 2 units clear of the lens.", "signal"),
    "launch": (
        "A rocket on its way, riding the ribbon as its exhaust trail.",
        "Rocket built upright (12-unit body, ogive nose, swept fins, r 3 window), then turned 45 deg. The "
        "ribbon trail rises from the bottom-left corner and stops short of the tail.", "trail"),
}


# ---------------------------------------------------------------- rendering, checks, sheet

def render(svg, px):
    return kit.render_svg(svg, px / GRID)


def checks(slug, els, rgba48):
    acc = [e for e in els if e[2] == "accent"]
    assert len(acc) == 1, "%s: expected exactly one accent element, got %d" % (slug, len(acc))
    a = rgba48[..., 3]
    live = np.zeros_like(a, bool)
    live[PAD:GRID - PAD, PAD:GRID - PAD] = True
    spill = float(a[~live].max()) if (~live).any() else 0.0
    ys, xs = np.where(a > 0.5)
    return {"ink": round(float(a.sum()), 1), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
            "spill_outside_live_area": round(spill, 3)}


def validate_svg(path, allowed, n_accent):
    """Structural check of a written icon file: Illustrator-safe elements only, ids everywhere and unique,
    exact palette colours, the stroke spec on every stroked element, M/L/C/Z path data, one accent."""
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    assert root.tag == ns + "svg" and root.get("viewBox") == "0 0 48 48", path
    ids, accents = set(), 0
    for el in root:
        tag = el.tag.replace(ns, "")
        assert tag in ("path", "circle", "line", "rect"), (path, tag)
        eid = el.get("id")
        assert eid and eid not in ids, (path, eid)
        ids.add(eid)
        for bad in ("filter", "mask", "clip-path", "style", "transform", "opacity"):
            assert el.get(bad) is None, (path, eid, bad)
        stroke, fill = el.get("stroke"), el.get("fill")
        assert (stroke or fill) and (stroke in allowed or stroke is None) and (fill in allowed or fill in (None, "none")), (path, eid)
        if stroke:
            assert (el.get("stroke-width"), el.get("stroke-linecap"), el.get("stroke-linejoin"), fill) == ("3", "round", "round", "none"), (path, eid)
        accents += (stroke or fill) == CYAN
        if tag == "path":
            kit.parse_d(el.get("d"))  # raises on anything but M/L/H/V/C/S/Q/T/Z
            assert not set(el.get("d")) & set("Aa"), (path, eid)
    assert accents == n_accent, (path, accents)
    return len(ids)


def rel_lum(h):
    c = kit.hexrgb(h) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(a, b):
    la, lb = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def font(sz):
    for name in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except OSError:
            pass
    return ImageFont.load_default()


PANELS = [(WHITE, NAVY, "light", "duotone  #1B56FF + #00D5FF on #FFFFFF"),
          (NAVY, WHITE, "dark", "dark  #FFFFFF + #00D5FF on #121B2A (Vibrant Blue swapped to white)"),
          (WHITE, NAVY, "mono", "mono  #121B2A on #FFFFFF (icon-<slug>-mono.svg)")]


def sheet(renders, out, title, panels=PANELS[:2]):
    """renders[slug][(panel_key, px)] -> RGB uint8; one panel per colourway, rows 96 / 48 / 24 px."""
    cell, lab, left = 112, 18, 64
    slugs = list(renders)
    W = left + len(slugs) * cell + 8
    rows = (96, 48, 24)
    panel_h = 28 + sum(r + 22 for r in rows) + lab
    H = 40 + len(panels) * panel_h + 10
    im = Image.new("RGB", (W, H), "#DADFE6")
    d = ImageDraw.Draw(im)
    d.text((12, 10), title, fill="#121B2A", font=font(16))
    for k, (bg, fg, key, name) in enumerate(panels):
        y0 = 40 + k * panel_h
        d.rectangle([8, y0, W - 8, y0 + panel_h - 8], fill=bg)
        d.text((20, y0 + 6), name, fill=fg, font=font(13))
        y = y0 + 28
        for px in rows:
            for i, slug in enumerate(slugs):
                im.paste(Image.fromarray(renders[slug][(key, px)]), (left + i * cell + (cell - px) // 2, y))
            d.text((20, y + px // 2 - 7), "%d px" % px, fill=fg, font=font(12))
            y += px + 22
        for i, slug in enumerate(slugs):
            tw = d.textlength(slug, font=font(11))
            d.text((left + i * cell + (cell - tw) // 2, y - 6), slug, fill=fg, font=font(11))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


def zoom24(renders, out):
    """24 px renders blown up 6x with nearest neighbour, to judge real pixel legibility."""
    z = 6
    W = len(renders) * (24 * z + 12) + 12
    im = Image.new("RGB", (W, 2 * (24 * z + 12) + 12), "#DADFE6")
    for k, key in enumerate(("light", "dark")):
        for i, slug in enumerate(renders):
            t = Image.fromarray(renders[slug][(key, 24)]).resize((24 * z, 24 * z), Image.NEAREST)
            im.paste(t, (12 + i * (24 * z + 12), 12 + k * (24 * z + 12)))
    im.save(out)


def render_set(svgs):
    """svgs: {key: svg path or text} for light / dark / mono -> {(key, px): RGB uint8}."""
    out = {}
    for key, src in svgs.items():
        bg = NAVY if key == "dark" else WHITE
        for px in (24, 48, 96):
            out[(key, px)] = kit.over(render(src, px), bg).round().astype(np.uint8)
    return out


def write_json(stats):
    inks = [stats[s]["ink"] for s, _, _ in ICONS]
    doc = {
        "set": "Alliance AI Partners signature icons",
        "version": "1.0.0",
        "generator": "docs/brand-kit/_build/work/icons/build_icons.py (geometry source of truth; re-run to regenerate)",
        "files": {"duotone": "icon-<slug>.svg", "mono": "icon-<slug>-mono.svg",
                  "dark": "not shipped as files: use the duotone file with #1B56FF swapped to #FFFFFF"},
        "grid": {"viewBox": "0 0 48 48", "size": GRID, "padding": PAD, "live_area": [PAD, PAD, GRID - PAD, GRID - PAD],
                 "keylines_outer_edge": {"circle_diameter": 40, "square": 36, "portrait": [32, 40], "landscape": [40, 32]},
                 "render_sizes": [24, 48, 96]},
        "stroke": {"width": SW, "linecap": "round", "linejoin": "round", "fill": "none"},
        "corner_radius": 4,
        "colors": {"primary": BLUE, "accent": CYAN, "mono": NAVY,
                   "dark_mode": {"primary": WHITE, "accent": CYAN, "background": NAVY}},
        "contrast_wcag": {"vibrant_blue_on_white": contrast(BLUE, WHITE), "bright_cyan_on_white": contrast(CYAN, WHITE),
                          "white_on_deep_navy": contrast(WHITE, NAVY), "bright_cyan_on_deep_navy": contrast(CYAN, NAVY),
                          "deep_navy_on_white": contrast(NAVY, WHITE),
                          "note": "Bright Cyan on white is below the 3:1 non-text guideline, so on light backgrounds "
                                  "the accent is emphasis only: every icon is identifiable from its Vibrant Blue "
                                  "strokes alone. On Deep Navy both colours pass."},
        "rules": [
            "48 x 48 grid, 4-unit safe padding: no ink outside 4..44 (checked on every render).",
            "One stroke weight: 3 units, round caps, round joins, no fill.",
            "Exactly one Bright Cyan accent element per icon; everything else Vibrant Blue.",
            "Fills only for small accent solids (machine-learning output dot, automation run button).",
            "Straight strokes and circular arcs only (the monogram's straight legs and round P bowl); the ribbon "
            "is the only free curve.",
            "Rounded rectangles use a 4-unit corner radius.",
            "A stroke that passes behind another stops 2 units short of it (round cap included).",
            "A stroke that ends on another stroke is drawn beneath it, so the joint never shows a cap.",
            "Path data is M/L/C/Z only (arcs converted to cubics) so Illustrator and kit.parse_d read it exactly.",
        ],
        "motifs": {
            "ribbon": "The AP monogram's swoosh, rebuilt as two tangent-continuous cubics with a level middle "
                      "(swoosh() in the generator). Fitted to the swoosh centreline measured on original 11 the "
                      "construction lands within 2.2 px mean (0.38% of the 583 px chord) with a 58 deg entry and a "
                      "90 deg exit into the P stem (verify/icon-ribbon-check.png). The icons keep the level middle "
                      "but exit at 45-75 deg so the ribbon reads as forward motion at 24 px: growth (trend, 40/55), "
                      "research-insights (signal, 50/75), launch (trail, 60/45).",
            "bowl": "Circular arcs from the P bowl: target rings, pie, woven rings, cloud lobes, lens, shoulders.",
            "legs": "Straight, uniform-weight strokes like the A legs: bars, check, gear flanks, network edges. The "
                    "monogram's leg angle (%.0f deg, measured 64.7 deg on original 12) is not imposed; icon "
                    "diagonals run at 45 deg, which renders cleaner on the pixel grid." % A_LEG,
        },
        "optical_balance": {"metric": "rendered ink coverage at 48 px (sum of alpha, px^2)",
                            "min": min(inks), "max": max(inks), "mean": round(float(np.mean(inks)), 1),
                            "max_over_min": round(max(inks) / min(inks), 2),
                            "note": "dense glyphs (target, network, gear, pie) carry up to 42% more ink than open "
                                    "ones (growth, research); outer size is held by the keylines instead."},
        "verification": {k: v for k, v in VER.items()},
        "icons": [],
    }
    for slug, name, _ in ICONS:
        desc, cons, acc = INFO[slug]
        doc["icons"].append({"slug": slug, "name": name, "description": desc, "construction": cons, "accent": acc,
                             "files": {"duotone": "icon-%s.svg" % slug, "mono": "icon-%s-mono.svg" % slug},
                             "ink_48px": stats[slug]["ink"], "ink_bbox_48px": stats[slug]["bbox"],
                             "elements": stats[slug]["elements"]})
    (OUT / "icons.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


VER = {}


def main(tag="final"):
    OUT.mkdir(parents=True, exist_ok=True)
    WORKDIR.mkdir(parents=True, exist_ok=True)
    final = tag == "final"
    renders, stats = {}, {}
    for slug, name, fn in ICONS:
        els = fn()
        duo = svg_text(slug, els, BLUE, CYAN, "duotone")
        mono = svg_text(slug, els, NAVY, NAVY, "mono")
        dark = svg_text(slug, els, WHITE, CYAN, "dark")
        src = {"light": duo, "dark": dark, "mono": mono}
        if final:
            for key, txt in (("", duo), ("-mono", mono)):
                (OUT / ("icon-%s%s.svg" % (slug, key))).write_text(txt, encoding="utf-8")
            n = validate_svg(OUT / ("icon-%s.svg" % slug), {BLUE, CYAN}, 1)
            assert validate_svg(OUT / ("icon-%s-mono.svg" % slug), {NAVY}, 0) == n
            src["light"], src["mono"] = OUT / ("icon-%s.svg" % slug), OUT / ("icon-%s-mono.svg" % slug)
        renders[slug] = render_set(src)
        stats[slug] = checks(slug, els, render(src["light"], 48))
        stats[slug]["elements"] = len(els)
        assert stats[slug]["spill_outside_live_area"] == 0.0, slug
        # colour and geometry fidelity of what is on disk, at 96 px
        light, monor = render(src["light"], 96), render(src["mono"], 96)
        solid_px = light[..., 3] > 0.999
        lab = kit.srgb_to_lab(light[..., :3] * 255)
        de_b, de_c = (kit.de2000(lab, kit.srgb_to_lab(kit.hexrgb(h))) for h in (BLUE, CYAN))
        de = np.minimum(de_b, de_c)
        contact = kit.dilate(solid_px & (de_b < 1), 2) & kit.dilate(solid_px & (de_c < 1), 2)  # blue meets cyan
        off = solid_px & (de > 1.0)
        stats[slug]["solid_px"] = int(solid_px.sum())
        stats[slug]["solid_px_off_palette"] = int(off.sum())
        stats[slug]["solid_px_off_palette_away_from_contact"] = int((off & ~contact).sum())
        stats[slug]["solid_px_max_de2000"] = round(float(de[solid_px].max()), 2)
        stats[slug]["mono_iou"] = round(kit.iou(light[..., 3] > 0.5, monor[..., 3] > 0.5), 4)
    VER["opaque_pixels_96px"] = {
        "exactly_on_palette_dE_le_1": "%.2f%%" % (100 - 100 * sum(s["solid_px_off_palette"] for s in stats.values())
                                              / sum(s["solid_px"] for s in stats.values())),
        "off_palette_count": {k: s["solid_px_off_palette"] for k, s in stats.items() if s["solid_px_off_palette"]},
        "off_palette_away_from_blue_cyan_contact": sum(s["solid_px_off_palette_away_from_contact"] for s in stats.values()),
        "max_de2000": max(s["solid_px_max_de2000"] for s in stats.values()),
        "note": "the only off-palette opaque pixels are anti-aliased blends where a blue stroke meets the cyan "
                "accent (machine-learning edges into the output dot, the cap band under the mortarboard); "
                "everywhere else rendered colour is the exact hex (dE2000 0.0)."}
    VER["mono_vs_duotone_geometry_iou_min"] = min(s["mono_iou"] for s in stats.values())
    VER["ink_outside_live_area"] = max(s["spill_outside_live_area"] for s in stats.values())
    VER["svg_structure"] = ("all 24 files parsed: only path/circle/line elements, unique ids on every element, "
                            "palette hex only, stroke 3/round/round, M/L/C/Z path data, one cyan element per duotone "
                            "file, none in mono")
    VER["ribbon_vs_monogram"] = "mean centreline error 2.22 px = 0.38% of chord (work/icons/ribbon_check.py)"
    out = (kit.VERIFY / "icon-sheet.png") if final else (WORKDIR / ("sheet-%s.png" % tag))
    sheet(renders, out, "Alliance AI Partners - signature icons (%s)   48 grid, 4 px padding, 3 px round strokes, "
                        "one cyan accent" % tag, PANELS if final else PANELS[:2])
    zoom24(renders, WORKDIR / ("zoom24-%s.png" % tag))
    for slug, s in stats.items():
        print("%-20s ink %6.1f  bbox %-18s spill %.3f" % (slug, s["ink"], s["bbox"], s["spill_outside_live_area"]))
    inks = [s["ink"] for s in stats.values()]
    print("ink min %.1f max %.1f mean %.1f  (max/min %.2f)" % (min(inks), max(inks), np.mean(inks), max(inks) / min(inks)))
    if final:
        write_json(stats)
        print("wrote", OUT, "and", out)
    return renders, stats


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "final")
