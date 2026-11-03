"""Smooth glow for the ribbon wave. Replaces the stepped glow (8 copies at 1:1 / 20 in the master, every
copy edge a dE2000 2.4-3.6 step, hard outer edge) in components/graphic-wave.svg and
graphic-wave-master.svg with a fine expanded blend. Every other byte of both files stays as it is.

Model, re-measured on original 02 (`fit`): glow alpha against distance d outside the fitted silhouette is
A(d) = A0/2 erfc((d - mu) / (sigma sqrt2)), least squares on the median profile of every top/bottom-edge
pixel 25 px clear of the ends. Past the vertical end cuts the original's halo is that profile shifted
~3 px (weaker), not cut off: it reaches ~18 px past each cut. So the copies are offsets of the
silhouette with both end cuts moved END_INSET px inward; clipping the glow at the cuts instead more
than doubles the dE there.

Bands: composite alpha levels T_1 < ... < T_N = A(D_IN), spaced so that over Off-White and over Deep
Navy no two adjacent bands differ by more than STEP dE2000. Copy k is the silhouette offset by the radius
where A crosses (T_k-1 + T_k) / 2, with fill-opacity 1 - (1 - T_k) / (1 - T_k-1), so the stack
composites to exactly T_k. Plain closed paths, one fill colour: Illustrator imports them as they are.

usage: python glow_smooth.py fit                 re-measure 02, print MODEL / END_INSET
       python glow_smooth.py build               rewrite the glow in both SVGs (+ fit json record)
       python glow_smooth.py verify [old1 oldM]  metrics, verify/graphic-wave_diff.png, _profile.png,
                                                 graphic-wave-master_check.png (old files: before/after)
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import kit
import wavegeom as g

SVG1, SVGM = kit.COMP / "graphic-wave.svg", kit.COMP / "graphic-wave-master.svg"
GLOW = "#17BEF2"
OW, NAVY = kit.PALETTE["Off-White"], kit.PALETTE["Deep Navy"]
BOARD_BG = "#F5F9FC"  # 02's measured background around panel 05 (verify_wave.BG)
MODEL = {"A0": 0.7826, "mu": 5.0994, "sigma": 6.6442}  # from `fit` (rms 0.004 alpha)
END_INSET = 3.0  # px, from `fit`
D_IN = 0.5  # innermost band level = A(D_IN): the first pixel outside the ribbon edge
STEP_1TO1, N_MASTER = 0.48, 96  # dE2000 cap per band step at 1:1 (72 copies); master: 96 copies
TOL = 0.05  # Bezier fit tolerance of each copy, 02 px
GLOW_RE = re.compile(r'<path id="wave-glow-\d+"[^\n]*\n')
erfc = np.vectorize(math.erfc)


def A(d, m=None):
    m = m or MODEL
    return m["A0"] * 0.5 * erfc((np.asarray(d, float) - m["mu"]) / (m["sigma"] * math.sqrt(2)))


def alpha(rgb, bg):
    """Glow alpha of colours over bg: projection of (rgb - bg) on (glow - bg)."""
    bg = kit.hexrgb(bg) if isinstance(bg, str) else np.asarray(bg, float)
    v = kit.hexrgb(GLOW) - bg
    return ((np.asarray(rgb, float) - bg) @ v) / (v @ v)


# ------------------------------------------------------------------ measurement

def station_map(box, inset=0.0, n=1404):
    """For pixel centres in box (x0, x1, y0, y1): signed distance to the silhouette (< 0 inside; end cuts
    moved in by `inset`), the foot's kind (0 top edge, 1 right cut, 2 bottom edge, 3 left cut) and x."""
    M = g.load()
    top, bot, _ = g.curves(M)
    xs = np.linspace(M["XL"] + inset, M["XR"] - inset, n)
    a = np.concatenate([np.stack([xs, top(xs)], -1), np.stack([xs[::-1], bot(xs[::-1])], -1)])
    ab = np.roll(a, -1, 0) - a
    kind = np.r_[np.zeros(n - 1), 1, np.full(n - 1, 2), 3].astype(int)
    x0, x1, y0, y1 = box
    yy, xx = np.mgrid[y0:y1, x0:x1]
    P = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], -1)
    dist, seg, fx = np.empty(len(P)), np.empty(len(P), int), np.empty(len(P))
    for i in range(0, len(P), 600):
        p = P[i:i + 600, None, :]
        t = np.clip(((p - a) * ab).sum(-1) / np.maximum((ab ** 2).sum(1), 1e-12), 0, 1)
        q = a + t[..., None] * ab
        d2 = ((p - q) ** 2).sum(-1)
        j = d2.argmin(1)
        r = np.arange(len(j))
        dist[i:i + 600], seg[i:i + 600], fx[i:i + 600] = np.sqrt(d2[r, j]), j, q[r, j, 0]
    poly = "M" + " L".join("%.3f %.3f" % tuple(p) for p in a) + " Z"
    inside = kit.raster(poly, 1376, 768)[y0:y1, x0:x1].ravel() > 0.5
    sh = yy.shape
    return np.where(inside, -dist, dist).reshape(sh), kind[seg].reshape(sh), fx.reshape(sh)


def nelder_mead(f, x0, step, iters=3000):
    S = [np.array(x0, float)] + [np.array(x0, float) + np.eye(len(x0))[i] * step[i] for i in range(len(x0))]
    F = [f(x) for x in S]
    for _ in range(iters):
        o = np.argsort(F)
        S, F = [S[i] for i in o], [F[i] for i in o]
        c = np.mean(S[:-1], 0)
        xr = 2 * c - S[-1]
        fr = f(xr)
        if fr < F[0]:
            xe = 3 * c - 2 * S[-1]
            fe = f(xe)
            S[-1], F[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < F[-2]:
            S[-1], F[-1] = xr, fr
        else:
            xc = (c + S[-1]) / 2
            fc = f(xc)
            if fc < F[-1]:
                S[-1], F[-1] = xc, fc
            else:
                S = [(s + S[0]) / 2 for s in S]
                F = [f(x) for x in S]
    return S[int(np.argmin(F))]


FIT_BOX = (995, 1360, 455, 635)


def fit():
    x0, x1, y0, y1 = FIT_BOX
    M = g.load()
    sd, kind, fx = station_map(FIT_BOX)
    im = kit.load('02').astype(float)[y0:y1, x0:x1]
    yy = np.mgrid[y0:y1, x0:x1][0]
    ok = (yy >= 480) & (yy < 610)  # clear of the panel title above and the caption bar below
    bg = np.median(im[ok & (sd > 30)], 0)
    Aim = alpha(im, bg)
    edge = ok & (kind % 2 == 0) & (fx > M["XL"] + 25) & (fx < M["XR"] - 25)
    dc = np.arange(0.75, 24, 0.5)
    med = np.array([np.median(Aim[edge & (np.abs(sd - d) < 0.25)]) for d in dc])
    p = nelder_mead(lambda p: float(((A(dc, dict(zip(("A0", "mu", "sigma"), p))) - med) ** 2).sum()),
                    [0.97, 3.0, 7.4], [0.05, 1.0, 0.5])
    m = dict(zip(("A0", "mu", "sigma"), np.round(p, 4)))
    print('background', kit.rgbhex(bg), '| model', m, '| rms alpha %.4f' % np.sqrt(((A(dc, m) - med) ** 2).mean()))
    print('station profiles, median alpha x100 at d = 0.5, 1.5, ... (rows: foot x +-10)')
    for kname, kv in (("top", 0), ("bottom", 2)):
        for xc in range(1050, 1311, 20):
            sel = ok & (kind == kv) & (np.abs(fx - xc) <= 10)
            print('  %-6s %d ' % (kname, xc) + ' '.join(
                '%3.0f' % (100 * np.median(Aim[sel & (sd >= d) & (sd < d + 1)])) for d in range(0, 20)))
    for kname, kv in (("right cut", 1), ("left cut", 3)):
        sel = ok & (kind == kv)
        print('  %-11s ' % kname + ' '.join('%3.0f' % (100 * np.median(Aim[sel & (sd >= d) & (sd < d + 1)])) for d in range(0, 20)))
    # end-cut inset: compare the model past each end against the original
    xx = np.mgrid[y0:y1, x0:x1][1] + 0.5
    zones = {"left": ok & (xx < M["XL"] + 12) & (sd > 0.6) & (sd < 24),
             "right": ok & (xx > M["XR"] - 12) & (sd > 0.6) & (sd < 24)}
    lab = kit.srgb_to_lab(im)
    for inset in (0, 1, 2, 3, 4, 5):
        di = station_map(FIT_BOX, inset)[0]
        col = bg + A(di, m)[..., None] * (kit.hexrgb(GLOW) - bg)
        de = kit.de2000(lab, kit.srgb_to_lab(col))
        print('  end inset %d px: end-zone dE mean left %.2f right %.2f' % (inset, de[zones["left"]].mean(), de[zones["right"]].mean()))
    out = (xx < M["XL"]) | (xx > M["XR"])
    col = bg + np.where(out, 0, A(sd, m))[..., None] * (kit.hexrgb(GLOW) - bg)
    de = kit.de2000(lab, kit.srgb_to_lab(col))
    print('  clipped at the cuts:  end-zone dE mean left %.2f right %.2f' % (de[zones["left"]].mean(), de[zones["right"]].mean()))


# ------------------------------------------------------------------ bands and paths

def max_step(t0, t1):
    """Largest dE2000 between glow bands of composite alpha t0 and t1, over Off-White and Deep Navy."""
    G = kit.hexrgb(GLOW)
    return max(float(kit.de2000(kit.srgb_to_lab(b + t0 * (G - b)), kit.srgb_to_lab(b + t1 * (G - b))))
               for b in (kit.hexrgb(OW), kit.hexrgb(NAVY)))


def levels(step, res=8000):
    """Composite alpha levels from 0 up to A(D_IN), each step as large as `step` dE allows (on a grid of res)."""
    grid = np.linspace(0, float(A(D_IN)), res + 1)
    G = kit.hexrgb(GLOW)
    labs = [kit.srgb_to_lab(b + grid[:, None] * (G - b)) for b in (kit.hexrgb(OW), kit.hexrgb(NAVY))]
    T = [0]
    while T[-1] < res:
        i = T[-1]
        over = np.nonzero(np.max([kit.de2000(L[i], L[i:]) for L in labs], 0) > step)[0]
        assert not len(over) or over[0] > 1, "step below the grid resolution"
        T.append(i + (over[0] - 1 if len(over) else res - i))
    return grid[T[1:]]


def layers(step=None, n=None):
    """[(offset radius, fill-opacity)] outermost first: `step` dE cap, or exactly n bands."""
    if n:
        lo, hi = 0.05, 2.0
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if len(levels(mid)) > n else (lo, mid)
        step = hi
    T = levels(step)
    assert not n or len(T) == n, (len(T), n)
    prev = np.r_[0.0, T[:-1]]
    dd = np.linspace(-2, 40, 42001)
    radii = np.interp(-(prev + T) / 2, -A(dd), dd)
    op = 1 - (1 - T) / (1 - prev)
    return [(round(float(r), 3), round(float(o), 5)) for r, o in zip(radii, op)]


def composite(L):
    """Band levels the rounded opacities actually produce, outermost first."""
    return 1 - np.cumprod([1 - o for _, o in L])


def min_concave_radius():
    M = g.load()
    top, bot, _ = g.curves(M)
    xs = np.linspace(M["XL"], M["XR"], 4000)
    out = []
    for c, sgn in ((top, -1), (bot, 1)):  # glow side is concave where top'' < 0 / bot'' > 0
        d1, d2 = c.d(xs), (c.d(xs + 1e-3) - c.d(xs - 1e-3)) / 2e-3
        out.append(np.min(np.where(sgn * d2 > 0, (1 + d1 ** 2) ** 1.5 / np.maximum(np.abs(d2), 1e-12), np.inf)))
    return float(min(out))


def master_frame():
    """(s, dx, dy) taking 02 px to master px, read off the face gradients both files share."""
    pat = r'<linearGradient id="[^"]+" x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)"'
    a, b = (np.array(re.findall(pat, p.read_text(encoding="utf-8")), float).reshape(-1, 2) for p in (SVG1, SVGM))
    s = float(((a - a.mean(0)) * (b - b.mean(0))).sum() / ((a - a.mean(0)) ** 2).sum())
    dx, dy = b.mean(0) - s * a.mean(0)
    assert np.abs(a * s + [dx, dy] - b).max() < 0.01, "master is not a scaled copy of the 1:1 wave"
    return s, float(dx), float(dy)


def glow_lines(L, xform, nl):
    M = g.load()
    Mi = dict(M, XL=M["XL"] + END_INSET, XR=M["XR"] - END_INSET)
    return [f'<path id="wave-glow-{k + 1}" d="{g.path_d(g.glow_segments(Mi, r, TOL), xform)}" fill="{GLOW}" '
            f'fill-opacity="{o:.5f}"/>{nl}' for k, (r, o) in enumerate(L)]


def patch(path, lines):
    """Swap the block of wave-glow paths for `lines`; the rest of the file is kept byte for byte."""
    s = path.read_bytes().decode("utf-8")
    ms = list(GLOW_RE.finditer(s))
    assert ms and all(p.end() == q.start() for p, q in zip(ms, ms[1:])), f"glow block not found in {path}"
    path.write_bytes((s[:ms[0].start()] + "".join(lines) + s[ms[-1].end():]).encode("utf-8"))


def build():
    L1, LM = layers(step=STEP_1TO1), layers(n=N_MASTER)
    assert max(L1[0][0], LM[0][0]) < min_concave_radius(), "outer copies would self-intersect"
    s, dx, dy = master_frame()
    nl = "\r\n" if b"\r\n" in SVG1.read_bytes() else "\n"
    patch(SVG1, glow_lines(L1, lambda p: np.asarray(p, float), nl))
    patch(SVGM, glow_lines(LM, lambda p: np.asarray(p, float) * s + [dx, dy], nl))
    M = g.load()
    M["colors"]["glow"] = {
        "color": GLOW, "model": MODEL, "form": "A0/2 erfc((d - mu) / (sigma sqrt2)), d = px outside the silhouette",
        "end_inset": END_INSET, "d_in": D_IN, "step_cap_de2000": {"1to1": STEP_1TO1, "master": round(max(
            max_step(a, b) for a, b in zip(np.r_[0, composite(LM)[:-1]], composite(LM))), 3)},
        "layers_1to1": L1, "layers_master_02px": LM, "master_frame": [s, dx, dy]}
    json.dump(M, open(g.FIT, "w"), indent=1)
    for name, L in (("1:1", L1), ("master", LM)):
        T = composite(L)
        st = [max_step(a, b) for a, b in zip(np.r_[0, T[:-1]], T)]
        print('%-6s %3d copies  r %.2f..%.2f px  opacity %.5f..%.5f  max band step %.3f dE2000 (OW / Navy)' % (
            name, len(L), L[-1][0], L[0][0], min(o for _, o in L), max(o for _, o in L), max(st)))
    print('sizes: %s %d B, %s %d B' % (SVG1.name, SVG1.stat().st_size, SVGM.name, SVGM.stat().st_size))


# ------------------------------------------------------------------ verification

def render_box(svg, box, scale):
    """Render the part (x0, y0, w, h) of an SVG file at `scale` (VectorCraft)."""
    x0, y0, w, h = box
    t = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"', f'width="{w}" height="{h}" viewBox="{x0} {y0} {w} {h}"',
               Path(svg).read_text(encoding="utf-8"), count=1)
    return kit.render_svg(t, scale=scale)


def bilinear(img, u, v):
    u0, v0 = np.clip(np.floor(u).astype(int), 0, img.shape[1] - 2), np.clip(np.floor(v).astype(int), 0, img.shape[0] - 2)
    fu, fv = (u - u0)[..., None], (v - v0)[..., None]
    return ((img[v0, u0] * (1 - fu) + img[v0, u0 + 1] * fu) * (1 - fv) + (img[v0 + 1, u0] * (1 - fu) + img[v0 + 1, u0 + 1] * fu) * fv)


def normals(xs_top, xs_bot):
    """Station base points and outward unit normals on the top and bottom edges."""
    M = g.load()
    top, bot, _ = g.curves(M)
    out = []
    for xs, c, side in ((xs_top, top, 1), (xs_bot, bot, -1)):
        for x in xs:
            t = float(c.d(x)[0])
            n = np.array([side * t, -side]) / math.hypot(1, t)
            out.append((np.array([x, float(c(x)[0])]), n))
    return out


STATIONS = normals(range(1060, 1301, 20), range(1060, 1301, 20))


def normal_steps(rgb, to_px, dists):
    """Max dE2000 between neighbouring samples along every station normal of a rendered image, per distance."""
    steps = []
    for p0, n in STATIONS:
        u, v = to_px(p0[None] + dists[:, None] * n)
        lab = kit.srgb_to_lab(bilinear(rgb, u, v))
        steps.append(kit.de2000(lab[1:], lab[:-1]))
    return np.max(steps, 0)


def fine_steps(svg, dists, scale=16):
    """normal_steps on VectorCraft renders of a small box around each station normal at `scale`."""
    steps = []
    for p0, n in STATIONS:
        q = p0[None] + dists[:, None] * n
        x0, y0 = np.floor(q.min(0)) - 2
        x1, y1 = np.ceil(q.max(0)) + 2
        rgb = kit.over(render_box(svg, (int(x0), int(y0), int(x1 - x0), int(y1 - y0)), scale), BOARD_BG)
        lab = kit.srgb_to_lab(bilinear(rgb, (q[:, 0] - x0) * scale - 0.5, (q[:, 1] - y0) * scale - 0.5))
        steps.append(kit.de2000(lab[1:], lab[:-1]))
    return np.max(steps, 0)


def metrics(ren, im, rib, near, core):
    de = kit.compare(im, ren)["de_map"]
    return {"de_mean_glow": round(float(de[near].mean()), 3), "de_p95_glow": round(float(np.percentile(de[near], 95)), 2),
            "de_mean_ribbon": round(float(de[core].mean()), 3), "de_mean_crop": round(float(de.mean()), 3)}


class Plot:
    """Minimal PIL line chart."""
    F = ImageFont.load_default(size=13)

    def __init__(self, sheet, box, xr, yr, title, xlabel, ylabel, yticks):
        self.d, (self.x0, self.y0, self.x1, self.y1), self.xr, self.yr = ImageDraw.Draw(sheet), box, xr, yr
        d = self.d
        d.rectangle(box, outline=(150, 150, 150))
        d.text((self.x0, self.y0 - 34), title, fill=(0, 0, 0), font=self.F)
        d.text(((self.x0 + self.x1) // 2 - 60, self.y1 + 18), xlabel, fill=(60, 60, 60), font=self.F)
        d.text((self.x0 - 4, self.y0 - 17), ylabel, fill=(60, 60, 60), font=self.F)
        for x in np.arange(xr[0], xr[1] + 1e-9, 5 if xr[1] - xr[0] > 12 else 1):
            d.line([(self.X(x), self.y1), (self.X(x), self.y1 + 4)], fill=(120, 120, 120))
            d.text((self.X(x) - 6, self.y1 + 4), "%g" % x, fill=(60, 60, 60), font=self.F)
        for y in yticks:
            d.line([(self.x0, self.Y(y)), (self.x1, self.Y(y))], fill=(232, 232, 232))
            d.text((self.x0 - 34, self.Y(y) - 7), "%g" % y, fill=(60, 60, 60), font=self.F)
        self.legend_y = self.y0 + 6

    def X(self, x):
        return self.x0 + (x - self.xr[0]) / (self.xr[1] - self.xr[0]) * (self.x1 - self.x0)

    def Y(self, y):
        return self.y1 - (np.clip(y, *self.yr) - self.yr[0]) / (self.yr[1] - self.yr[0]) * (self.y1 - self.y0)

    def line(self, xs, ys, color, label=None, width=2, dots=False):
        pts = [(self.X(x), self.Y(y)) for x, y in zip(xs, ys) if self.xr[0] <= x <= self.xr[1] and np.isfinite(y)]
        if dots:
            for x, y in pts:
                self.d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color)
        else:
            self.d.line(pts, fill=color, width=width)
        if label:
            self.d.line([(self.x1 - 230, self.legend_y + 7), (self.x1 - 205, self.legend_y + 7)], fill=color, width=3)
            self.d.text((self.x1 - 198, self.legend_y), label, fill=(0, 0, 0), font=self.F)
            self.legend_y += 17


def verify(old1=None, oldM=None):
    import verify_wave as vw
    m_new, ren_new = vw.main()  # writes verify/graphic-wave_diff.png
    X0, X1, Y0, Y1 = vw.X0, vw.X1, vw.Y0, vw.Y1
    im = kit.load('02').astype(float)
    M = g.load()
    rib = kit.raster(g.path_d(g.face_segments(g.faces(M)["ribbon"])), 1376, 768) > 0.5
    sl = (slice(Y0, Y1), slice(X0, X1))
    core, near = rib[sl], (kit.dilate(rib, 16) & ~rib)[sl]
    rens = {"new": ren_new}
    if old1:
        rens["old"] = kit.over(kit.render_svg(old1), BOARD_BG)
        for new, old in ((SVG1, old1), (SVGM, oldM)):
            same = GLOW_RE.sub("", new.read_bytes().decode()) == GLOW_RE.sub("", Path(old).read_bytes().decode())
            print('%s: everything but the glow byte-identical to the old file: %s' % (new.name, same))
    for k, r in rens.items():
        print(k, metrics(r[sl], im[sl], rib[sl], near, core))
    if old1:
        dr = kit.de2000(kit.srgb_to_lab(rens["new"][sl]), kit.srgb_to_lab(rens["old"][sl]))
        inner = kit.erode(rib, 2)[sl]
        print('ribbon (2 px inside the edge) old vs new render: max dE %.3f' % float(dr[inner].max()))
    # profiles: alpha vs distance, original against renders
    box = (X0 - 5, X1 + 5, Y0 - 2, Y1)
    sd, kind, fx = station_map(box)
    crop = (slice(box[2], box[3]), slice(box[0], box[1]))
    yy = np.mgrid[box[2]:box[3], box[0]:box[1]][0]
    ok = (yy >= 480) & (yy < 610)
    bg02 = np.median(im[crop][ok & (sd > 30)], 0)
    edge = ok & (kind % 2 == 0) & (fx > M["XL"] + 25) & (fx < M["XR"] - 25)
    ends = ok & (kind % 2 == 1)
    alph = {"orig": alpha(im[crop], bg02)}
    for k, r in rens.items():
        alph[k] = alpha(r[crop], BOARD_BG)
    de_bins = np.arange(0.25, 25, 0.25)

    def prof(a, sel, bins, w):
        return np.array([np.median(a[sel & (np.abs(sd - d) <= w)]) if (sel & (np.abs(sd - d) <= w)).sum() > 4 else np.nan for d in bins])

    # 1x pixel steps along vertical profiles through the glow (as in the audit), outside 1 px from the edge
    def px_steps(rgb):
        lab = kit.srgb_to_lab(rgb)
        st = kit.de2000(lab[1:], lab[:-1])
        both = (sd[1:] >= 1.0) & (sd[:-1] >= 1.0) & ok[1:]
        dmid = (sd[1:] + sd[:-1]) / 2
        return st, both, dmid

    pxs = {k: px_steps(v) for k, v in [("orig", im[crop])] + [(k, r[crop]) for k, r in rens.items()]}
    for k, (st, both, dmid) in pxs.items():
        print('1x vertical pixel steps in the glow (d >= 1 px): %-4s max %.2f  p99 %.2f  | beyond 8 px: max %.2f' % (
            k, st[both].max(), np.percentile(st[both], 99), st[both & (dmid > 8)].max()))
    col = lambda r, x, ys: ' '.join(kit.rgbhex(r[y, x]) for y in ys)
    print('x1150, y548-560 orig:', col(im, 1150, range(548, 561)))
    for k, r in rens.items():
        print('x1150, y548-560 %s: ' % k + col(r, 1150, range(548, 561)))
    # fine sampling: 1/16 px along every station normal, each rendered at x16
    dists = np.arange(1.0, 26.0, 1 / 16)
    fine = {"new": fine_steps(SVG1, dists)}
    if old1:
        fine["old"] = fine_steps(old1, dists)
    for k, v in fine.items():
        print('x16 renders, max dE2000 between samples 1/16 px apart on %d station normals: %s %.2f' % (len(STATIONS), k, v.max()))
    # master on Off-White and Deep Navy
    s, dx, dy = master_frame()
    rgbaM = kit.render_svg(SVGM)
    toM = lambda q: (q[:, 0] * s + dx - 0.5, q[:, 1] * s + dy - 0.5)
    mdist = np.arange(1.0, 24.0, 0.25 / s)
    mast = {}
    for name, bgc in (("Off-White", OW), ("Deep Navy", NAVY)):
        rgb = kit.over(rgbaM, bgc)
        al = []
        for p0, n in STATIONS:
            u, v = toM(p0[None] + mdist[:, None] * n)
            al.append(alpha(bilinear(rgb, u, v), bgc))
        mast[name] = (rgb, np.median(al, 0), normal_steps(rgb, toM, mdist))
        print('master on %-9s: max dE2000 between samples 1/4 master px apart %.2f; |alpha - model| max %.4f' % (
            name, mast[name][2].max(), np.abs(mast[name][1] - A(mdist)).max()))
    a = rgbaM[..., 3]
    print('master glow extent: alpha > 0 rows %d..%d of 400 (viewBox clips the faintest tail where it reaches the edge)' % (
        np.nonzero(a.max(1) > 0)[0].min(), np.nonzero(a.max(1) > 0)[0].max()))
    print('sizes: %s %d B, %s %d B' % (SVG1.name, SVG1.stat().st_size, SVGM.name, SVGM.stat().st_size))

    # ---- profile sheet
    C = {"orig": (0, 0, 0), "old": (230, 120, 20), "new": (20, 90, 220), "model": (150, 150, 150)}
    sheet = Image.new("RGB", (1640, 1290), "white")
    ImageDraw.Draw(sheet).text((20, 10), "graphic-wave glow: original 02 vs VectorCraft renders over %s (1:1), master on Off-White / Deep Navy" % BOARD_BG,
                               fill=(0, 0, 0), font=ImageFont.load_default(size=16))
    p = Plot(sheet, (70, 90, 790, 420), (0, 25), (0, 0.7), "Edge profile: median glow alpha, all top/bottom-edge pixels 25 px clear of the ends",
             "distance outside the ribbon (02 px)", "alpha", [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    p.line(de_bins, A(de_bins), C["model"], "model A(d) (erfc fit)")
    p.line(de_bins, prof(alph["orig"], edge, de_bins, 0.125), C["orig"], "original 02", dots=True)
    for k in ("old", "new"):
        if k in alph:
            p.line(de_bins, prof(alph[k], edge, de_bins, 0.125), C[k], "%s render" % k)
    p = Plot(sheet, (900, 90, 1620, 420), (0, 25), (0, 0.7), "Past the vertical end cuts: median alpha vs distance from the cut (both ends)",
             "distance past the end cut (02 px)", "alpha", [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    eb = np.arange(0.5, 25, 0.5)
    p.line(eb, A(eb + END_INSET), C["model"], "model A(d + %g)" % END_INSET)
    p.line(eb, prof(alph["orig"], ends, eb, 0.25), C["orig"], "original 02", dots=True)
    for k in ("old", "new"):
        if k in alph:
            p.line(eb, prof(alph[k], ends, eb, 0.25), C[k], "%s render" % k)
    p = Plot(sheet, (70, 510, 790, 830), (1, 25), (0, 4), "1x vertical pixel profiles (as in the audit): max dE2000 between neighbouring pixels",
             "distance outside the ribbon (02 px)", "dE2000", [0, 0.5, 1, 2, 3, 4])
    p.d.text((p.x0 + 6, p.y1 - 34), "a smooth falloff in light cyan moves 1-2 dE2000 per pixel; the original's own pixels step 2-4",
             fill=(90, 90, 90), font=Plot.F)
    sb = np.arange(1.25, 25, 0.5)
    for k, (st, both, dmid) in pxs.items():
        p.line(sb, [st[both & (np.abs(dmid - b) <= 0.25)].max() if (both & (np.abs(dmid - b) <= 0.25)).any() else np.nan for b in sb],
               C[k], {"orig": "original 02", "old": "old render", "new": "new render"}[k])
    p = Plot(sheet, (900, 510, 1620, 830), (1, 25), (0, 4), "Bands: renders at x16, samples 1/16 px apart on %d station normals, max step" % len(STATIONS),
             "distance outside the ribbon (02 px)", "dE2000", [0, 0.5, 1, 2, 3, 4])
    p.d.line([(p.x0, p.Y(1)), (p.x1, p.Y(1))], fill=(200, 0, 0))
    p.d.line([(p.x0, p.Y(0.5)), (p.x1, p.Y(0.5))], fill=(240, 160, 160))
    for k, v in fine.items():
        p.line(dists[1:], v, C[k], "%s render (max %.2f)" % (k, v.max()), width=1)
    p = Plot(sheet, (70, 930, 790, 1250), (0, 25), (0, 0.7), "Master (1600x400): median glow alpha on the station normals",
             "distance outside the ribbon (02 px; master px = x%.3f)" % s, "alpha", [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    p.line(de_bins, A(de_bins), C["model"], "model A(d)")
    p.line(mdist, mast["Off-White"][1], (20, 90, 220), "on Off-White")
    p.line(mdist, mast["Deep Navy"][1], (20, 160, 90), "on Deep Navy")
    p = Plot(sheet, (900, 930, 1620, 1250), (1, 24), (0, 1.2), "Master: max dE2000 between samples 1/4 master px apart",
             "distance outside the ribbon (02 px)", "dE2000", [0, 0.25, 0.5, 0.75, 1.0])
    p.d.line([(p.x0, p.Y(0.5)), (p.x1, p.Y(0.5))], fill=(240, 160, 160))
    p.line(mdist[1:], mast["Off-White"][2], (20, 90, 220), "on Off-White (max %.2f)" % mast["Off-White"][2].max(), width=1)
    p.line(mdist[1:], mast["Deep Navy"][2], (20, 160, 90), "on Deep Navy (max %.2f)" % mast["Deep Navy"][2].max(), width=1)
    sheet.save(kit.VERIFY / "graphic-wave_profile.png")

    # ---- master check sheet: full view on both backgrounds + x4 zooms (left end, crest, right end)
    rows = []
    srcs = [("new", rgbaM)] + ([("old", kit.render_svg(oldM))] if oldM else [])
    for tag, rgba in srcs:
        for name, bgc in (("Off-White", OW), ("Deep Navy", NAVY)):
            rgb = np.clip(kit.over(rgba, bgc), 0, 255).astype(np.uint8)
            full = Image.fromarray(rgb).resize((800, 200), Image.LANCZOS)
            zs = [Image.fromarray(rgb[y:y + 100, x:x + 100]).resize((200, 200), Image.NEAREST)
                  for x, y in ((300, 230), (560, 40), (1180, 60))]
            row = Image.new("RGB", (800 + 3 * 206, 222), "white")
            row.paste(full, (0, 22))
            for i, z in enumerate(zs):
                row.paste(z, (806 + 206 * i, 22))
            ImageDraw.Draw(row).text((4, 3), "%s master on %s: full (0.5x) | x2 zooms: left end, crest, right end" % (tag, name),
                                     fill=(200, 0, 0), font=Plot.F)
            rows.append(row)
    chk = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), "white")
    for i, r in enumerate(rows):
        chk.paste(r, (0, i * r.height))
    chk.save(kit.VERIFY / "graphic-wave-master_check.png")
    print('wrote verify/graphic-wave_diff.png, graphic-wave_profile.png, graphic-wave-master_check.png')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"fit": fit, "build": build, "verify": lambda: verify(*sys.argv[2:4])}[cmd]()
