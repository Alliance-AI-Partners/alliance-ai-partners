"""hero-01: vector recreation of the 3D gradient AP mark exactly as drawn in original 01 (light horizontal logo).

Step 1 (affine.py) showed 01 is the master AP (components/ap-hero.svg, built from 06) under a full affine map
(silhouette IoU 0.988 against 0.968 for the best similarity), so this keeps the master's 11 faces, z-order, shared
silhouette and under-tucks, bakes the affine into the coordinates (01 pixel space, identity placement) and refits
every face's linear gradient from 01's pixels (least squares in sRGB, <= 5 stops on visible pixels; the faces cut
from one band are solved jointly so the cuts stay invisible).  Colours: measured, snapped to kit.PALETTE only
within dE2000 2, near-identical tones merged within dE2000 2.
Run: python work/ap-01/hero01.py  ->  components/rec/hero-01.svg/.json, verify/hero-01_diff.png"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "ap-"))
import kit
import fit
import gradfit
from soft import box as boxsum
import edges
from affine import BOX, coverage, nelder_mead, target

REC = kit.COMP / "rec"
MASTER = (kit.COMP / "ap-hero.svg").read_text(encoding="utf-8")
HERO = json.loads((kit.COMP / "ap-hero.json").read_text(encoding="utf-8"))
LN06 = json.loads((kit.WORK / "ap-" / "lines06.json").read_text(encoding="utf-8"))
SNAP, MERGE, THR = 2.0, 2.0, 18.0
CROP = (BOX[0] - 20, BOX[1] - 20, BOX[2] + 21, BOX[3] + 21)
C06 = np.array([512.0, 512.0])
# where the master cuts one band into several faces (06 space, build_hero.G): seam point sets
SEAMS06 = [("p-bowl-top", "ribbon-front-stem", np.stack([np.linspace(542.4, 579, 40), np.full(40, 352.5)], 1)),
           ("ribbon-front-stem", "ribbon-front", np.stack([np.linspace(520, 590, 80), np.full(80, 480.0)], 1)),
           ("p-bowl-under", "p-bowl-lower", np.stack([np.full(40, 760.0), np.linspace(539.23, 575, 40)], 1))]
PAD = {"p-bowl-top": 0, "ribbon-front": 1}   # face kept flat along seam k (as make_hero.py does)


def affine_d(d, A, t, nd=3):
    subs = kit.parse_d(d)
    f = lambda x, y: tuple(A @ (x, y) + t)
    for s in subs:
        s["start"] = f(*s["start"])
        s["segs"] = [("L",) + f(g[1], g[2]) if g[0] == "L" else ("C",) + f(g[1], g[2]) + f(g[3], g[4]) + f(g[5], g[6])
                     for g in s["segs"]]
    return kit.format_d(subs, nd)


def alpha_map(rgb, T, bg):
    """Per pixel, the coverage at which a render edge of the local mark colour crosses kit.bg_mask's dE 18."""
    E = kit.erode(T, 2).astype(float)
    col = None
    for r in (3, 6, 12, 40):
        den = boxsum(E, r)
        c = boxsum(rgb * E[..., None], r) / np.maximum(den, 1e-9)[..., None]
        col = np.where((den > 0)[..., None], c, np.nan) if col is None else np.where(np.isnan(col), c, col)
    bgc, bgl = kit.hexrgb(bg), kit.srgb_to_lab(kit.hexrgb(bg))
    lo, hi = np.zeros(T.shape), np.ones(T.shape)
    for _ in range(22):
        mid = (lo + hi) / 2
        de = kit.de2000(kit.srgb_to_lab(mid[..., None] * col + (1 - mid[..., None]) * bgc), bgl)
        hi, lo = np.where(de > THR, mid, hi), np.where(de > THR, lo, mid)
    return (lo + hi) / 2


def fit_affine(rgb, T, bg, A0, t0):
    """Hard-IoU fit of the master silhouette (coverage > per-pixel alpha threshold) onto 01's mark mask."""
    x0, y0, x1, y1 = CROP
    Tc = T[y0:y1, x0:x1]
    am = alpha_map(rgb, T, bg)[y0:y1, x0:x1]
    polys = [np.asarray(p) for p in kit.flatten(kit.parse_d(HERO["silhouette_d"]), tol=0.03)]

    def unpack(x):
        dA = np.array([[x[0], x[1]], [x[2], x[3]]])
        return A0 + dA, t0 + x[4:6] - dA @ C06

    def f(x):
        m = coverage(polys, *unpack(x), CROP) > am
        return -(m & Tc).sum() / max(1, (m | Tc).sum())
    best, steps = (np.zeros(6), f(np.zeros(6))), [0.003, 0.003, 0.003, 0.003, 0.8, 0.8]
    for _ in range(4):
        x, v = nelder_mead(f, best[0], steps)
        if v < best[1]:
            best = (x, v)
        steps = [s / 2 for s in steps]
    A, t = unpack(best[0])
    return A, t, -best[1]


def tone_family(hx):
    L, a, b = kit.srgb_to_lab(kit.hexrgb(hx))
    h, C = np.degrees(np.arctan2(b, a)) % 360, np.hypot(a, b)
    fam = "Navy" if L < 22 else "Slate" if C < 35 else "Cyan" if h < 230 else "Azure" if h < 272 else "Blue"
    return fam, float(L)


def merge_tones(hexes, thr):
    """Minimax-linkage agglomeration in dE2000 -> {hex: representative hex}: clusters merge while one member
    (the representative) stays within thr of every member, so no stop moves more than thr from its measured colour."""
    hs = sorted(set(hexes))
    lab = np.array([kit.srgb_to_lab(kit.hexrgb(h)) for h in hs])
    D = kit.de2000(lab[:, None], lab[None])

    def radius(c):
        r = D[np.ix_(c, c)].max(1)
        return float(r.min()), c[int(np.argmin(r))]
    cl = [[i] for i in range(len(hs))]
    while True:
        best = None
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                r = radius(cl[i] + cl[j])[0]
                if r <= thr and (best is None or r < best[0]):
                    best = (r, i, j)
        if best is None:
            break
        cl[best[1]] += cl.pop(best[2])
    return {hs[i]: hs[radius(c)[1]] for c in cl for i in c}


def drop_flat_stops(f):
    """Remove stops that repeat their neighbours' colour (an end run is continued by the pad, so the vector shrinks)."""
    st = f["stops"]
    k = 1
    while k < len(st) - 1:
        if st[k - 1]["hex"] == st[k]["hex"] == st[k + 1]["hex"]:
            st.pop(k)
        else:
            k += 1
    while len(st) > 2 and st[-1]["hex"] == st[-2]["hex"]:
        st.pop()
    while len(st) > 2 and st[0]["hex"] == st[1]["hex"]:
        st.pop(0)
    p1, p2 = np.array([f["x1"], f["y1"]]), np.array([f["x2"], f["y2"]])
    o0, o1 = st[0]["offset"], st[-1]["offset"]
    q1, q2 = p1 + o0 * (p2 - p1), p1 + o1 * (p2 - p1)
    for s in st:
        s["offset"] = round((s["offset"] - o0) / (o1 - o0), 4)
    f.update(x1=round(float(q1[0]), 3), y1=round(float(q1[1]), 3), x2=round(float(q2[0]), 3), y2=round(float(q2[1]), 3))


def grad_at(fl, pts):
    p1, p2 = np.array([fl["x1"], fl["y1"]]), np.array([fl["x2"], fl["y2"]])
    v = p2 - p1
    t = np.clip(((np.asarray(pts) - p1) @ v) / (v @ v), 0, 1)
    offs = np.array([s["offset"] for s in fl["stops"]])
    cols = np.array([kit.hexrgb(s["hex"]) for s in fl["stops"]])
    return np.stack([np.interp(t, offs, cols[:, c]) for c in range(3)], 1)


def main():
    rgb = kit.load("01").astype(float)
    H, W = rgb.shape[:2]
    bgmask = np.ones((H, W), bool)
    bgmask[BOX[1] - 30:BOX[3] + 31, BOX[0] - 30:BOX[2] + 31] = False
    bg = kit.rgbhex(np.median(rgb[bgmask[:, :] & ~kit.dilate(kit.bg_mask(rgb, "#FFFFFF", THR), 4)], 0))
    T = target(rgb)
    prev = json.loads((HERE / "affine.json").read_text(encoding="utf-8"))["affine_thr0.35"]
    A, t, iou_fit = fit_affine(rgb, T, bg, np.array(prev["A"]), np.array(prev["t"]))
    print("affine", A.round(6).tolist(), t.round(4).tolist(), "fit IoU", round(iou_fit, 4), flush=True)

    faces = [(fid[5:], affine_d(d, A, t)) for fid, d, _ in fit.faces(MASTER)]
    names = [n for n, _ in faces]
    sil = affine_d(HERO["silhouette_d"], A, t)
    x0, y0, x1, y1 = CROP
    cov = [kit.raster(kit.transform_d(d, 1.0, -x0, -y0, nd=4), x1 - x0, y1 - y0, ss=4) for _, d in faces]
    vis, above = [None] * len(cov), np.ones_like(cov[0])
    for k in range(len(cov) - 1, -1, -1):
        vis[k] = cov[k] * above
        above = above * (1 - cov[k])
    Tc = T[y0:y1, x0:x1]
    core = {n: kit.erode(vis[k] > 0.98, 2) & kit.erode(Tc, 2) for k, n in enumerate(names)}

    def px(n):
        ys, xs = np.nonzero(core[n])
        return np.stack([xs + x0 + 0.5, ys + y0 + 0.5], 1), rgb[ys + y0, xs + x0]

    def inside(pts, a, b):
        ia, ib = names.index(a), names.index(b)
        q = np.floor(pts - (x0, y0)).astype(int)
        return pts[(vis[ia][q[:, 1], q[:, 0]] + vis[ib][q[:, 1], q[:, 0]]) > 0.9]
    seams = [(a, b, inside(p @ A.T + t, a, b)) for a, b, p in SEAMS06]
    axis = {s: np.degrees(np.arctan2(*(A @ (LN06[k]["a"], 1.0))[::-1])) for s, k in (("a-left", "LL_crease"), ("a-right", "RL_internal"))}

    fits = {}
    for n in names:
        xy, c = px(n)
        pad = seams[PAD[n]][2] if n in PAD else None
        if n.startswith("a-"):
            ax = axis[n[:6] if n.startswith("a-left") else n[:7]]
            g = gradfit.fit(xy, c, Kmax=5, angles=np.arange(ax - 15, ax + 15.01, 3.0), improve=0.85)
        else:
            g = gradfit.fit(xy, c, Kmax=5, improve=0.8, pad=pad)
        g["center"] = xy.mean(0)
        fits[n] = (xy, c, g)
        print(f"{n:18s} px {len(xy):5d} K{g['K']} angle {g['angle']:6.1f}", flush=True)
    J = gradfit.joint({n: fits[n] for n in {a for s in seams for a in s[:2]}}, seams, lam=3.0)

    # colours: measured; palette only within SNAP; then near-identical tones merged within MERGE
    raw, fills = {}, {}
    for n in names:
        xy, c, g = fits[n]
        cols = np.clip(J.get(n, g["colors"]), 0, 255)
        p1, p2, offs = gradfit.svg_vector(g, g["center"])
        stops = []
        for o, col in zip(offs, cols):
            pname, phex, pde = kit.nearest_palette(kit.rgbhex(col))
            stops.append({"offset": round(float(o), 4), "hex": phex if pde <= SNAP else kit.rgbhex(col),
                          "palette": pname if pde <= SNAP else None, "measured": kit.rgbhex(col)})
        fills[n] = {"type": "linear", "x1": round(float(p1[0]), 3), "y1": round(float(p1[1]), 3),
                    "x2": round(float(p2[0]), 3), "y2": round(float(p2[1]), 3), "stops": stops}
    rep = merge_tones([s["hex"] for f in fills.values() for s in f["stops"] if not s["palette"]], MERGE)
    usage = {}
    for n, f in fills.items():
        for s in f["stops"]:
            if not s["palette"]:
                s["hex"] = rep[s["hex"]]
        drop_flat_stops(f)
        for k, s in enumerate(f["stops"]):
            usage.setdefault(s["hex"], []).append(f"face-{n}#{k}")
    fam = {}
    for hx in usage:
        if not any(s["hex"] == hx and s["palette"] for f in fills.values() for s in f["stops"]):
            fm, L = tone_family(hx)
            fam.setdefault(fm, []).append((L, hx))
    tname, order = {}, {}
    for fm, lst in sorted(fam.items()):
        for i, (L, hx) in enumerate(sorted(lst, reverse=True)):
            tname[hx] = f"AP01 {fm} {i + 1}" if len(lst) > 1 else f"AP01 {fm}"
            order[hx] = (fm, i)
    master_tones = [(m["name"], m["hex"]) for m in HERO["supporting_tones"]]

    def near_master(hx):
        lab = kit.srgb_to_lab(kit.hexrgb(hx))
        nm, mh = min(master_tones, key=lambda v: float(kit.de2000(lab, kit.srgb_to_lab(kit.hexrgb(v[1])))))
        return {"name": nm, "hex": mh, "de2000": round(float(kit.de2000(lab, kit.srgb_to_lab(kit.hexrgb(mh)))), 2)}
    tones = []
    for hx in sorted(usage, key=lambda h: order.get(h, ("", 0))):
        pal = next((s["palette"] for f in fills.values() for s in f["stops"] if s["hex"] == hx and s["palette"]), None)
        pn, ph, pde = kit.nearest_palette(hx)
        tones.append({"name": pal or tname[hx], "hex": hx, "palette": bool(pal), "used_in": usage[hx],
                      "nearest_palette": {"name": pn, "hex": ph, "de2000": round(pde, 2)}, "nearest_master_tone": near_master(hx)})
    for f in fills.values():
        for s in f["stops"]:
            s["tone"] = s["palette"] or tname[s["hex"]]

    # SVG in 01's pixel space, identity placement
    defs, body = [], []
    for n, d in faces:
        f = fills[n]
        defs.append(kit.lin_grad("grad-" + n, f["x1"], f["y1"], f["x2"], f["y2"], [(s["offset"], s["hex"]) for s in f["stops"]]))
        body.append(f'<path id="face-{n}" d="{d}" fill="url(#grad-{n})" fill-rule="evenodd"/>')
    svg = kit.svg_doc(W, H, "\n".join(body), "\n".join(defs))
    REC.mkdir(exist_ok=True)
    (REC / "hero-01.svg").write_text(svg, encoding="utf-8")

    # verify: VectorCraft render over 01's measured background
    ren = kit.over(kit.render_svg(REC / "hero-01.svg"), bg)
    box = np.zeros((H, W), bool)
    box[BOX[1] - 10:BOX[3] + 11, BOX[0] - 10:BOX[2] + 11] = True
    rm = kit.bg_mask(ren, bg, THR) & box
    m = kit.compare(rgb, ren, T)
    mi = kit.compare(rgb, ren, kit.erode(T, 1))
    de = m["de_map"]
    per_face = {}
    for n in names:
        reg = np.zeros((H, W), bool)
        reg[y0:y1, x0:x1] = core[n]
        per_face[n] = {"de_mean": round(float(de[reg].mean()), 2), "de_p95": round(float(np.percentile(de[reg], 95)), 2),
                       "pixels": int(reg.sum()), "stops": len(fills[n]["stops"])}
    edge = T & ~kit.erode(T, 1)
    cores = np.zeros((H, W), bool)
    cores[y0:y1, x0:x1] = np.any([core[n] for n in names], 0)
    internal = np.zeros((H, W), bool)
    internal[y0:y1, x0:x1] = kit.erode(Tc, 1)
    internal &= ~cores
    seam_rep = []
    for a, b, pts in seams:
        dd = kit.de2000(kit.srgb_to_lab(grad_at(fills[a], pts)), kit.srgb_to_lab(grad_at(fills[b], pts)))
        seam_rep.append({"faces": [a, b], "de_max": round(float(dd.max()), 2), "de_mean": round(float(dd.mean()), 2), "points": len(pts)})
    met = {"iou": round(kit.iou(T, rm), 4), "de_mean": m["de_mean"], "de_p95": m["de_p95"],
           "de_mean_interior": mi["de_mean"], "de_p95_interior": mi["de_p95"],
           "de_mean_outer_edge_px": round(float(de[edge].mean()), 2),
           "de_mean_internal_edge_band": round(float(de[internal].mean()), 2),
           "de_mean_face_cores": round(float(de[cores].mean()), 2),
           "background": bg, "per_face": per_face, "seams": seam_rep,
           "edge_offsets_px": dict(edges.offsets(rgb, ren, bg), note="01 edge minus render edge along probe scanlines "
                                   "(dE 18 crossing, sub-pixel); + = 01's mark is smaller there, - = 01's mark reaches further"),
           "reference_master_colours": {k: {q: v[q] for q in ("iou", "de_mean", "de_p95")} for k, v in
                                        json.loads((HERE / "affine.json").read_text(encoding="utf-8")).items()},
           "method": ("VectorCraft render (kit.render_svg, 1x) composited over 01's measured background; IoU of kit.bg_mask "
                      "(dE2000 > 18 from the background) of render vs 01 inside the mark box [117,270,486,490] padded 10 px "
                      "(wordmark and tagline excluded); dE2000 over 01's mark mask")}
    print({k: v for k, v in met.items() if k not in ("per_face", "seams", "method")}, flush=True)
    for n, v in per_face.items():
        print(f"  {n:18s} {v}")
    for s in seam_rep:
        print("  seam", s)
    xa, ya, xb, yb = CROP
    kit.diff_sheet(rgb[ya:yb, xa:xb], ren[ya:yb, xa:xb], kit.VERIFY / "hero-01_diff.png", de[ya:yb, xa:xb],
                   "hero-01 vs 01  IoU %.4f  dE mean %.2f p95 %.2f" % (met["iou"], met["de_mean"], met["de_p95"]))
    z = lambda a: np.repeat(np.repeat(np.asarray(a), 3, 0), 3, 1)
    kit.diff_sheet(z(rgb[ya:yb, xa:xb]), z(ren[ya:yb, xa:xb]), HERE / "hero-01_diff_x3.png", z(de[ya:yb, xa:xb]), "hero-01 x3")

    P = np.vstack([np.asarray(p) for p in kit.flatten(kit.parse_d(sil), tol=0.05)])
    out = {"component": "hero-01", "source": "01", "viewBox": [0, 0, W, H],
           "source_space": "original 01 pixel space (y down), identity placement",
           "construction": ("master ap-hero faces (built from 06) under the full affine p01 = A p06 + t fitted to 01's silhouette, "
                            "baked into every coordinate; gradients refit from 01"),
           "affine_from_master": {"A": A.round(7).tolist(), "t": t.round(4).tolist(),
                                  "svg_matrix": [round(float(v), 7) for v in (A[0, 0], A[1, 0], A[0, 1], A[1, 1], t[0], t[1])],
                                  "fit_iou": round(iou_fit, 4), "similarity_iou": 0.968},
           "bbox": [round(float(v), 2) for v in (*P.min(0), *P.max(0))], "silhouette_d": sil,
           "z_order": "faces listed bottom to top; each lower face reaches ~1.4 px (2.5 px in 06) under the face stacked above it; all faces are cut by one shared silhouette",
           "faces": [{"id": "face-" + n, "z": z_, "fill": fills[n], "anchors": sum(len(q["segs"]) for q in kit.parse_d(d))}
                     for z_, (n, d) in enumerate(faces)],
           "tones": tones, "palette_used": sorted({t_["name"] for t_ in tones if t_["palette"]}),
           "colour_rule": (f"measured colours; snapped to kit.PALETTE within dE2000 {SNAP} (no stop was that close); near-identical "
                           f"tones merged within dE2000 {MERGE} (minimax linkage: no stop moves more than {MERGE} from its measured colour)"),
           "known_deviations": ("01 is a separately drawn copy: the A matches the master within 0.3 px, but under one affine these "
                                "edges stay off: " + "; ".join(f"{k} {v['mean']:+.2f} px" for k, v in met["edge_offsets_px"].items()
                                                              if isinstance(v, dict) and abs(v["mean"]) > 0.5)
                                + " (- = 01's shape reaches further). Closing them needs the faces re-measured on 01."),
           "metrics": met}
    (REC / "hero-01.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote", REC / "hero-01.svg", REC / "hero-01.json", kit.VERIFY / "hero-01_diff.png")


if __name__ == "__main__":
    main()
