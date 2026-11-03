"""Step 1 for hero-01: is original 01 just the master AP (components/ap-hero.svg, 06 space) under an affine map?
Fits p01 = A (p06 - c) + c' + t by maximising silhouette IoU against 01's mark mask, then measures the real
metric (VectorCraft render composited on white, kit.bg_mask on both sides).   Run: python work/ap-01/affine.py"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import kit

OUT = Path(__file__).resolve().parent
BOX = (117, 270, 486, 490)
HERO = json.loads((kit.COMP / "ap-hero.json").read_text(encoding="utf-8"))
SVG = (kit.COMP / "ap-hero.svg").read_text(encoding="utf-8")


def target(rgb, pad=10):
    m = kit.bg_mask(rgb, "#FFFFFF", 18.0)
    box = np.zeros(m.shape, bool)
    x0, y0, x1, y1 = BOX
    box[y0 - pad:y1 + pad + 1, x0 - pad:x1 + pad + 1] = True
    return m & box


def coverage(polys, A, t, crop, ss=4):
    """even-odd fill of the master polylines mapped by p -> A p + t into crop (x0, y0, x1, y1), ss x ss AA."""
    x0, y0, x1, y1 = crop
    w, h = x1 - x0, y1 - y0
    acc = np.zeros((h * ss, w * ss), bool)
    for P in polys:
        q = (P @ A.T + t - (x0, y0)) * ss
        im = Image.new("1", (w * ss, h * ss), 0)
        ImageDraw.Draw(im).polygon([tuple(v) for v in q], fill=1)
        acc ^= np.asarray(im, bool)
    return acc.reshape(h, ss, w, ss).mean((1, 3))


def nelder_mead(f, x0, steps, iters=400, tol=1e-7):
    n = len(x0)
    pts = [np.array(x0, float)] + [np.array(x0, float) + np.eye(n)[i] * steps[i] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        o = np.argsort(vals)
        pts, vals = [pts[i] for i in o], [vals[i] for i in o]
        if abs(vals[-1] - vals[0]) < tol:
            break
        c = np.mean(pts[:-1], 0)
        xr = c + (c - pts[-1]); fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


def main():
    rgb = kit.load("01")
    H, W = rgb.shape[:2]
    T = target(rgb)
    crop = (BOX[0] - 20, BOX[1] - 20, BOX[2] + 21, BOX[3] + 21)
    Tc = T[crop[1]:crop[3], crop[0]:crop[2]].astype(float)
    polys = [np.asarray(p) for p in kit.flatten(kit.parse_d(HERO["silhouette_d"]), tol=0.03)]
    s0, tx0, ty0 = 0.5476137534239645, 20.449370369448076, 99.8746627241303   # fit/placements.json hero@01
    c06 = np.array([515.0, 512.0])

    def unpack(x):
        A = np.array([[x[0], x[1]], [x[2], x[3]]])
        t = s0 * c06 + (tx0, ty0) + x[4:6] - A @ c06
        return A, t

    res = {}
    for thr in (0.5, 0.35):
        def f(x):
            cov = coverage(polys, *unpack(x), crop)
            m = cov > thr
            return -(m & (Tc > 0)).sum() / max(1, (m | (Tc > 0)).sum())
        x0 = np.array([s0, 0, 0, s0, 0, 0])
        steps = [0.004, 0.004, 0.004, 0.004, 1.0, 1.0]
        best = None
        for rnd in range(3):
            x, v = nelder_mead(f, x0 if best is None else best[0], steps)
            if best is None or v < best[1]:
                best = (x, v)
            steps = [s / 2 for s in steps]
        A, t = unpack(best[0])
        res[thr] = (A, t, -best[1])
        print(f"thr {thr}: A={A.round(5).tolist()} t={t.round(3).tolist()} IoU(cov>{thr})={-best[1]:.4f}", flush=True)
    sim = coverage(polys, np.eye(2) * s0, np.array([tx0, ty0]), crop) > 0.5
    print("similarity IoU(cov>0.5)", round(float((sim & (Tc > 0)).sum() / (sim | (Tc > 0)).sum()), 4))

    # the real metric: render the master under each affine, composite on white, bg_mask vs bg_mask
    inner = SVG[SVG.index(">", SVG.index("<svg")) + 1:SVG.rindex("</svg>")]
    report = {}
    for key, (A, t) in [("similarity", (np.eye(2) * s0, np.array([tx0, ty0])))] + [(f"affine_thr{k}", v[:2]) for k, v in res.items()]:
        body = (f'<g transform="matrix({A[0,0]:.7f} {A[1,0]:.7f} {A[0,1]:.7f} {A[1,1]:.7f} {t[0]:.4f} {t[1]:.4f})">'
                f"{inner}</g>")
        ren = kit.over(kit.render_svg(kit.svg_doc(W, H, body)), "#FFFFFF")
        rm = kit.bg_mask(ren, "#FFFFFF", 18.0)
        box = np.zeros(rm.shape, bool); box[BOX[1] - 10:BOX[3] + 11, BOX[0] - 10:BOX[2] + 11] = True
        rm &= box
        m = kit.compare(rgb.astype(float), ren, T)
        report[key] = {"A": A.round(6).tolist(), "t": t.round(4).tolist(), "iou": round(kit.iou(T, rm), 4),
                       "de_mean": m["de_mean"], "de_p95": m["de_p95"]}
        print(key, report[key], flush=True)
        if key != "similarity":
            x0_, y0_, x1_, y1_ = crop
            kit.diff_sheet(rgb[y0_:y1_, x0_:x1_], ren[y0_:y1_, x0_:x1_], OUT / f"{key}_diff.png",
                           m["de_map"][y0_:y1_, x0_:x1_], f"master under {key} IoU {report[key]['iou']}")
            # silhouette disagreement map: red = only in 01, blue = only in the master
            vis = np.full((y1_ - y0_, x1_ - x0_, 3), 255, np.uint8)
            a, b = T[y0_:y1_, x0_:x1_], rm[y0_:y1_, x0_:x1_]
            vis[a & b] = (200, 200, 200); vis[a & ~b] = (220, 0, 0); vis[~a & b] = (0, 60, 230)
            Image.fromarray(vis).resize((vis.shape[1] * 2, vis.shape[0] * 2), Image.NEAREST).save(OUT / f"{key}_sil.png")
    (OUT / "affine.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
