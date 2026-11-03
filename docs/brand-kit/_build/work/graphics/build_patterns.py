"""Build the five seamless 240x240 pattern tiles (components/pattern-*.svg) and components/patterns.json.

Every tile starts with <rect id="bg">. Seamlessness is by construction: column/row pitches divide 240,
periodic functions have period 240, shapes that would cross a tile edge are either kept inside
(halftone, monograms), split exactly at the edge (data-mesh bars, facet polygons), or, for the stroked
wave lines, drawn with an opaque wrapped copy one tile up/down so the tile is complete when clipped
to its 240x240 bounds.
"""
import json
import math
import numpy as np
import kit
import meshlib as ml
import pathsimp as ps
from wavegeom import fit_beziers

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
COMP = B + r'\components'
T = 240
P = kit.PALETTE
f2 = lambda v: ("%.2f" % v).rstrip("0").rstrip(".")


def doc(body, defs=""):
    return kit.svg_doc(T, T, "\n".join(body), defs)


# ------------------------------------------------------------------ 1. data mesh (from graphic-datamesh)

def tile_datamesh(seed=7):
    fit = json.load(open(B + r'\fit\graphic-datamesh_fit.json'))
    tones = fit["tones"]
    dark, light = fit["bg"]["stops"][0], fit["bg"]["stops"][-1]  # field behind the blue / the cyan bars
    y0p, y1p = fit["panel"][1], fit["panel"][3]
    cols = {}
    for b in fit["bars"]:
        cols.setdefault(b["col"], []).append(b)
    runs, gaps, nseg = [], [], []
    for bs in cols.values():
        bs.sort(key=lambda b: b["y0"])
        rl, cur = [], [bs[0]]
        for b in bs[1:]:
            if b["y0"] - cur[-1]["y1"] < 0.6:
                cur.append(b)
            else:
                rl.append(cur); cur = [b]
        rl.append(cur)
        for i, r in enumerate(rl):
            if r[0]["y0"] > y0p + 0.5 and r[-1]["y1"] < y1p - 0.5:
                runs.append(r[-1]["y1"] - r[0]["y0"]); nseg.append(len(r))
            if i + 1 < len(rl):
                gaps.append(rl[i + 1][0]["y0"] - r[-1]["y1"])
    runs, gaps = np.array(runs), np.array(gaps)
    nseg_p = np.bincount(nseg, minlength=5)[1:5] / len(nseg)
    xs = np.array([b["x"] for b in fit["bars"]]); t = np.array([b["tone"] for b in fit["bars"]])
    w = np.array([b["y1"] - b["y0"] for b in fit["bars"]])
    share_blue = np.bincount(t[xs < 1178], weights=w[xs < 1178], minlength=8); share_blue /= share_blue.sum()
    share_cyan = np.bincount(t[xs >= 1178], weights=w[xs >= 1178], minlength=8); share_cyan /= share_cyan.sum()
    target_cov = fit["stats_original"]["coverage"] / (ml.BAR_W / ml.PITCH)  # coverage along a column
    long_gap_p = max(0.0, (runs.mean() * (1 - target_cov) / target_cov - gaps.mean()) / (40 - gaps.mean()))

    rng = np.random.default_rng(seed)
    n = int(round(T / ml.PITCH))  # 39 columns -> pitch 6.154 (measured 6.118)
    pitch = T / n
    # periodic field: dark at the tile edges (blue zone) -> lighter mid-tile (cyan zone), like the original
    defs = kit.lin_grad("datamesh-grad-field", 0, 0, T, 0, [(0, dark), (0.5, light), (1, dark)])
    body = [f'<rect id="bg" x="0" y="0" width="{T}" height="{T}" fill="url(#datamesh-grad-field)"/>', '<g id="datamesh-bars">']
    stats = {"cols": n, "pitch": round(pitch, 4), "bar_w": ml.BAR_W, "bars": 0, "covered": 0.0}
    for k in range(n):
        cx = (k + 0.5) * pitch
        cyan_p = 0.5 - 0.5 * math.cos(2 * math.pi * (k + 0.5) / n)  # blue zone at the tile edges, cyan mid-tile
        y = float(rng.uniform(0, T))
        end = y + T
        y += float(rng.choice(gaps)) * rng.uniform(0.5, 1.0)
        segs = []
        while True:
            L = float(rng.choice(runs)) * rng.uniform(0.9, 1.1)
            if y + L > end - 1.5:
                L = end - 1.5 - y
                if L < 2.0:
                    break
            ns = int(rng.choice([1, 2, 3, 4], p=nseg_p)) if L >= 6 else 1
            cuts = np.sort(rng.uniform(0.25, 0.75, ns - 1)) * L if ns > 1 else []
            edges = [0.0] + list(cuts) + [L]
            fam = share_cyan if rng.random() < cyan_p else share_blue
            prev = None
            for a, b in zip(edges[:-1], edges[1:]):
                p = fam.copy()
                if prev is not None:
                    p[prev] = 0; p /= p.sum()
                tone = int(rng.choice(8, p=p)); prev = tone
                segs.append((y + a, y + b, tone, b < L))  # last flag: touches the next segment
            y += L
            g = float(rng.choice(gaps)) * rng.uniform(0.9, 1.1)
            if rng.random() < long_gap_p:
                g = float(rng.uniform(20, 60))
            y += g
            if y >= end - 4:
                break
        idx = 0
        for (a, b, tone, touch) in segs:
            stats["covered"] += b - a
            stats["bars"] += 1
            bb = b + 0.4 if touch else b  # tuck under the next segment (no hairline)
            pieces = []
            a_m, b_m = a % T, a % T + (bb - a)
            if b_m <= T:
                pieces = [(a_m, b_m)]
            else:  # split exactly at the tile edge
                pieces = [(a_m, T), (0.0, b_m - T)]
            for (pa, pb) in pieces:
                idx += 1
                body.append(f'<rect id="dm-c{k:02d}-{idx:02d}" x="{f2(cx - ml.BAR_W / 2)}" y="{f2(pa)}" width="{ml.BAR_W}" '
                            f'height="{f2(pb - pa)}" fill="{tones[tone]}"/>')
    body.append('</g>')
    stats["coverage"] = round(stats["covered"] * ml.BAR_W / (T * T), 3)
    info = {"name": "datamesh", "file": "pattern-datamesh-tile.svg", "size": [T, T], "background": dark,
            "background_gradient": {"x1": 0, "x2": T, "stops": [[0, dark], [0.5, light], [1, dark]]},
            "colors": tones, "repeat": "grid", "seam": "bars split exactly at the top/bottom edge; columns at (k+0.5)*240/39",
            "source": "statistics of the data mesh in original 02 (pitch, bar width, run/gap lengths, segments per run, tone shares, coverage)",
            "stats": {"columns": n, "pitch": round(pitch, 3), "bar_width": ml.BAR_W, "segments": stats["bars"],
                      "coverage": stats["coverage"], "original_coverage": fit["stats_original"]["coverage"]}}
    return doc(body, defs), info


# ------------------------------------------------------------------ 2. halftone

def tile_halftone(d=12.0, r_max=3.0, r_min=0.35, gamma=1.15):
    """45-degree halftone screen (rows every d/2, alternate rows offset d/2). Dot radius follows a
    diagonal cosine fade with period 240 along x+y, so bands of large dots fade out and back in."""
    body = [f'<rect id="bg" x="0" y="0" width="{T}" height="{T}" fill="{P["Deep Navy"]}"/>', '<g id="halftone-dots">']
    nrow, ncol = int(T / (d / 2)), int(T / d)
    count = 0
    for j in range(nrow):
        for i in range(ncol):
            x = d / 4 + (i + 0.5 * (j % 2)) * d
            y = d / 4 + j * d / 2
            u = 0.5 + 0.5 * math.cos(2 * math.pi * (x + y) / T)
            r = r_max * u ** gamma
            if r < r_min:
                continue
            count += 1
            body.append(f'<circle id="ht-r{j:02d}-c{i:02d}" cx="{f2(x)}" cy="{f2(y)}" r="{f2(r)}" fill="{P["Bright Cyan"]}"/>')
    body.append('</g>')
    info = {"name": "halftone", "file": "pattern-halftone-tile.svg", "size": [T, T], "background": P["Deep Navy"],
            "colors": [P["Bright Cyan"]], "repeat": "grid",
            "seam": "dots stay inside the tile (centres >= 3 px from the edges, r <= 3); fade is periodic in x+y",
            "stats": {"dots": count, "screen_angle_deg": 45, "dot_pitch": round(d / math.sqrt(2), 3), "r_max": r_max,
                      "fade": "r = 3 * ((1 + cos(2 pi (x + y) / 240)) / 2)^1.15"}}
    return doc(body), info


# ------------------------------------------------------------------ 3. AP monogram

MONO_TONE = "#1E2D47"  # Deep Navy lifted toward Vibrant Blue: a quiet tone-on-tone monogram


def monogram_geometry():
    paths = kit.trace_image(kit.load('12'), [P["Deep Navy"], "#1EC8EE"], noise=4, ignore_white=True)
    cy = max((d for d, fcol in paths if fcol == "#1EC8EE"), key=len)
    S = ps.simplify_d(cy, tol=0.8)
    pts = np.concatenate([ps_to_pts(s) for s in S])
    x0, y0 = pts.min(0); x1, y1 = pts.max(0)
    return S, (float(x0), float(y0), float(x1), float(y1)), cy


def ps_to_pts(segs):
    out = []
    for s in segs:
        if s[0] == "L":
            out += [s[1], s[2]]
        else:
            u = np.linspace(0, 1, 12)[:, None]
            Pc = s[1]
            out += list((1 - u) ** 3 * Pc[0] + 3 * (1 - u) ** 2 * u * Pc[1] + 3 * (1 - u) * u ** 2 * Pc[2] + u ** 3 * Pc[3])
    return np.array(out)


def tile_monogram(height=22.0):
    S, (x0, y0, x1, y1), raw = monogram_geometry()
    s = height / (y1 - y0)
    wid = (x1 - x0) * s
    json.dump({"source": "kit.trace_image(original 12, ['#121B2A', '#1EC8EE'], noise=4) -> pathsimp tol 0.8 px",
               "bbox_in_12": [x0, y0, x1, y1], "d_in_12": ps.to_d(S, nd=2), "segments": [len(q) for q in S]},
              open(B + r'\fit\pattern-ap-monogram_fit.json', 'w'), indent=1)
    body = [f'<rect id="bg" x="0" y="0" width="{T}" height="{T}" fill="{P["Deep Navy"]}"/>', '<g id="monograms">']
    # diagonal (staggered) lattice: 3 per row at 80 px, 4 rows at 60 px, alternate rows offset by 40,
    # the whole lattice shifted a quarter step so no monogram crosses an edge
    k = 0
    for j in range(4):
        for i in range(3):
            cx = 20 + 80 * i + 40 * (j % 2)
            cy = 30 + 60 * j
            xf = lambda p, cx=cx, cy=cy: ((p[0] - (x0 + x1) / 2) * s + cx, (p[1] - (y0 + y1) / 2) * s + cy)
            k += 1
            body.append(f'<path id="ap-monogram-{k:02d}" d="{ps.to_d(S, xf, nd=2)}" fill="{MONO_TONE}" fill-rule="evenodd"/>')
    body.append('</g>')
    info = {"name": "ap-monogram", "file": "pattern-ap-monogram-tile.svg", "size": [T, T], "background": P["Deep Navy"],
            "colors": [MONO_TONE], "repeat": "grid",
            "seam": "staggered lattice (80 x 60 px, rows offset 40) shifted a quarter step; every monogram lies inside the tile",
            "stats": {"monograms": k, "monogram_size": [round(wid, 2), height], "segments_per_monogram": sum(len(q) for q in S),
                      "trace_segments": sum(len(q["segs"]) for q in kit.parse_d(raw))}}
    return doc(body), info


# ------------------------------------------------------------------ 4. low-poly facets

FACET_RAMP = [P["Deep Navy"], "#192B48", "#1A449D", "#3A5072", P["Vibrant Blue"], "#1794E1", P["Bright Cyan"]]


def clip_poly(poly, x0=0.0, y0=0.0, x1=float(T), y1=float(T)):
    """Sutherland-Hodgman clip of a polygon to the tile box."""
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(inter(a, b))
                out.append(b)
            elif ia:
                out.append(inter(a, b))
        return out

    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def iy(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)
    pts = list(poly)
    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            break
        pts = clip(pts, inside, inter)
    return pts


def tile_facets(n=8, jitter=0.32, height=14.0, seed=2, band_w=0.3):
    rng = np.random.default_rng(seed)
    c = T / n
    J = rng.uniform(-jitter, jitter, (n, n, 2)) * c
    H = rng.uniform(-1, 1, (n, n)) * height
    diag = rng.integers(0, 2, (n, n))

    def V3(i, j):
        ii, jj = i % n, j % n
        return np.array([ii * c + J[ii, jj, 0] + (i - ii) * c, jj * c + J[ii, jj, 1] + (j - jj) * c, H[ii, jj]])

    light = np.array([-0.45, -0.55, 0.70]); light /= np.linalg.norm(light)
    tris = []
    for j in range(-1, n + 1):
        for i in range(-1, n + 1):
            a, b, cc, d = V3(i, j), V3(i + 1, j), V3(i, j + 1), V3(i + 1, j + 1)
            pair = [(a, b, d), (a, d, cc)] if diag[i % n, j % n] else [(a, b, cc), (b, d, cc)]
            for t3 in pair:
                tris.append(t3)
    shade = []
    for p1, p2, p3 in tris:
        nrm = np.cross(p2 - p1, p3 - p1)
        if nrm[2] < 0:
            nrm = -nrm
        shade.append(float(np.dot(nrm / np.linalg.norm(nrm), light)))
    shade = np.array(shade)
    s_lo, s_hi = np.percentile(shade, 3), np.percentile(shade, 97)
    body = [f'<rect id="bg" x="0" y="0" width="{T}" height="{T}" fill="{FACET_RAMP[2]}"/>', '<g id="facets">']
    k = 0
    used = set()
    for (p1, p2, p3), sh in zip(tris, shade):
        cen = (p1 + p2 + p3)[:2] / 3
        band = 0.5 + 0.5 * math.cos(2 * math.pi * (cen[0] + cen[1]) / T)  # periodic diagonal light band
        v = (1 - band_w) * np.clip((sh - s_lo) / (s_hi - s_lo), 0, 1) + band_w * band
        tone = FACET_RAMP[int(np.clip(round(v * (len(FACET_RAMP) - 1)), 0, len(FACET_RAMP) - 1))]
        poly = clip_poly([tuple(p1[:2]), tuple(p2[:2]), tuple(p3[:2])])
        if len(poly) < 3:
            continue
        area = 0.5 * abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly))))
        if area < 0.05:
            continue
        k += 1
        used.add(tone)
        dd = "M" + " L".join(f"{f2(x)} {f2(y)}" for x, y in poly) + " Z"
        body.append(f'<path id="facet-{k:03d}" d="{dd}" fill="{tone}"/>')
    body.append('</g>')
    info = {"name": "facets", "file": "pattern-facets-tile.svg", "size": [T, T], "background": FACET_RAMP[2],
            "colors": [t for t in FACET_RAMP if t in used], "repeat": "grid",
            "seam": "periodic jittered 8x8 vertex lattice; facets of the neighbouring periods are clipped exactly to the tile",
            "stats": {"facets": k, "lattice": [n, n], "cell": c, "jitter": jitter,
                      "shading": f"flat-shaded relief (vertex heights +-{height:g} px, light from top-left) + periodic diagonal band ({band_w:g}), quantised to the ramp"},
            "ramp": FACET_RAMP}
    return doc(body), info


# ------------------------------------------------------------------ 5. ribbon lines

def tile_ribbon_lines(n=30, amp=18.0, w_min=0.45, w_max=1.6):
    """n parallel cosine waves (period 240, so slope 0 at x=0 and x=240: butt ends meet flush). Stroke
    width swells and thins periodically across the stack, like light running along a ribbon."""
    s = T / n
    body = [f'<rect id="bg" x="0" y="0" width="{T}" height="{T}" fill="{P["Deep Navy"]}"/>', '<g id="ribbon-lines">']
    # one cosine period fitted with cubic Beziers (analytic tangents, max error 0.01 px)
    xs = np.linspace(0, T, 961)
    ys = amp * np.cos(2 * np.pi * xs / T)
    tv = np.stack([np.ones_like(xs), -amp * 2 * np.pi / T * np.sin(2 * np.pi * xs / T)], -1)
    tv /= np.linalg.norm(tv, axis=1, keepdims=True)
    bez = fit_beziers(np.stack([xs, ys], -1), tv, tol=0.01)

    def wave_d(y0):
        out = [f"M0 {f2(y0 + amp)}"]
        for Pc in bez:
            out.append("C" + " ".join(f"{f2(v[0])} {f2(v[1] + y0)}" for v in Pc[1:]))
        return " ".join(out)
    k_id = 0
    for k in range(-3, n + 3):
        y0 = (k + 0.5) * s
        lo, hi = y0 - amp - w_max, y0 + amp + w_max
        if hi < 0 or lo > T:
            continue
        kk = k % n
        wdt = w_min + (w_max - w_min) * (0.5 + 0.5 * math.cos(2 * math.pi * kk / n)) ** 2
        k_id += 1
        body.append(f'<path id="wave-line-{k_id:02d}" d="{wave_d(y0)}" fill="none" stroke="{P["Bright Cyan"]}" '
                    f'stroke-width="{f2(wdt)}" stroke-linecap="butt"/>')
    body.append('</g>')
    info = {"name": "ribbon-lines", "file": "pattern-ribbon-lines-tile.svg", "size": [T, T], "background": P["Deep Navy"],
            "colors": [P["Bright Cyan"]], "repeat": "grid",
            "seam": "cosine period = 240 (flush butt ends at x=0/240); lines near the top/bottom edge are repeated one tile up/down (opaque, so overlaps are invisible); clip to the 240x240 tile",
            "stats": {"lines": n, "spacing": s, "amplitude": amp, "stroke_width": [w_min, w_max], "beziers_per_line": len(bez)}}
    return doc(body), info


if __name__ == '__main__':
    infos = []
    for fn in (tile_datamesh, tile_halftone, tile_monogram, tile_facets, tile_ribbon_lines):
        svg, info = fn()
        open(COMP + '\\' + info["file"], 'w', encoding='utf-8').write(svg)
        infos.append(info)
        print(info["name"], info["stats"])
    json.dump({"tile_size": [T, T], "units": "px (1 px = 1 px of original 02)", "tiles": infos,
               "notes": "Background is the first <rect id='bg'> of each tile. Make an Illustrator pattern with tile size 240x240 (Pattern Options, Size Tile to Art off)."},
              open(COMP + r'\patterns.json', 'w'), indent=1)
