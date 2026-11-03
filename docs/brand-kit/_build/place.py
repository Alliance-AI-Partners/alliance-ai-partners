"""Place master marks onto the originals that reuse them (01, 13, 14, 17 and the 02 board slots) by silhouette
IoU, measure the colour error, and refit the stop colours from that original's pixels where the master's colours
are visibly off (fidelity rule for recreations: snap to the core palette only within dE2000 2).
Writes fit/placements.json, components/rec/<key>.svg and verify/placements.png.   Run: python place.py"""
import json
import re
import sys

import numpy as np

import fit
import kit

REC = kit.COMP / "rec"
HERO = json.loads((kit.COMP / "ap-hero.json").read_text(encoding="utf-8"))
DARK = json.loads((kit.COMP / "ap-hero-dark.json").read_text(encoding="utf-8"))
SHIELD = json.loads((kit.FIT / "shield-layout.json").read_text(encoding="utf-8"))
SLOTS = json.loads((kit.FIT / "board-slots.json").read_text(encoding="utf-8"))["slots"]
BOXES = json.loads((kit.FIT / "text-wordmark-master.json").read_text(encoding="utf-8"))["mark_boxes_px"]
REFIT_ABOVE = 3.0  # mean dE2000 inside the mark above which the stops are refitted from the original


def inner(svg):
    return svg[svg.index(">", svg.index("<svg")) + 1: svg.rindex("</svg>")]


def comp(name):
    """Component SVG text; a flat mark's own background square is dropped (its tile is drawn by the board)."""
    return re.sub(r'<rect id="bg"[^>]*/>', "", (kit.COMP / name).read_text(encoding="utf-8"))


def xf_d(d, sx, sy, tx, ty):
    subs = kit.parse_d(d)
    t = lambda x, y: (x * sx + tx, y * sy + ty)
    for s in subs:
        s["start"] = t(*s["start"])
        s["segs"] = [("L",) + t(g[1], g[2]) if g[0] == "L" else ("C",) + t(g[1], g[2]) + t(g[3], g[4]) + t(g[5], g[6])
                     for g in s["segs"]]
    return kit.format_d(subs)


def bake(svg, W, H, sx, sy, tx, ty):
    """The component with x' = sx*x + tx, y' = sy*y + ty applied to every path and gradient vector, in a W x H
    viewBox (source space, identity placement)."""
    t = re.sub(r'\bd="([^"]+)"', lambda m: f'd="{xf_d(m.group(1), sx, sy, tx, ty)}"', svg)

    def grad(m):
        a = m.group(0)
        for k, s, o in (("x1", sx, tx), ("x2", sx, tx), ("y1", sy, ty), ("y2", sy, ty)):
            a = re.sub(r'\b%s="([-\d.eE]+)"' % k, lambda q: f'{k}="{float(q.group(1)) * s + o:.3f}"', a)
        return a
    t = re.sub(r"<linearGradient\b[^>]*>", grad, t)
    t = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m.group(1)) * (sx + sy) / 2:.3f}"', t)
    t = re.sub(r'(<svg\b[^>]*?)\swidth="[^"]*"', rf'\1 width="{W}"', t, count=1)
    t = re.sub(r'(<svg\b[^>]*?)\sheight="[^"]*"', rf'\1 height="{H}"', t, count=1)
    return re.sub(r'viewBox="[^"]*"', f'viewBox="0 0 {W} {H}"', t, count=1)


def refine_axes(ds, target, box, p, pad=24, steps=(2.0, 0.8, 0.3, 0.12)):
    """Refine a similarity fit to separate x / y scale (the originals are separately generated drawings, often the
    master reproportioned by a percent or two): coordinate search on IoU over (sx, sy, tx, ty)."""
    H, W = target.shape
    x0, y0 = max(0, int(box[0] - pad)), max(0, int(box[1] - pad))
    x1, y1 = min(W, int(box[2] + pad) + 1), min(H, int(box[3] + pad) + 1)
    tgt = target[y0:y1, x0:x1]
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2

    def score(v):
        sx, sy, tx, ty = v
        m = kit.raster([xf_d(d, sx, sy, tx - x0, ty - y0) for d in ds], x1 - x0, y1 - y0, ss=2) > 0.5
        return kit.iou(m, tgt)
    v = [p["s"], p["s"], p["tx"], p["ty"]]
    best = score(v)
    span = (box[2] - box[0], box[3] - box[1])
    for st in steps:
        improved = True
        while improved:
            improved = False
            for i, dlt in ((0, st / span[0]), (0, -st / span[0]), (1, st / span[1]), (1, -st / span[1]),
                           (2, st), (2, -st), (3, st), (3, -st)):
                w = list(v)
                if i < 2:  # scale about the box centre so a scale step does not also move the mark
                    f = 1 + dlt
                    w[i] *= f
                    w[i + 2] = (cx if i == 0 else cy) - ((cx if i == 0 else cy) - w[i + 2]) * f
                else:
                    w[i] += dlt
                sc = score(w)
                if sc > best + 1e-5:
                    best, v, improved = sc, w, True
    return {"sx": v[0], "sy": v[1], "tx": v[2], "ty": v[3], "iou": round(best, 4)}


def sil_paths(svg):
    return [d for d, a in kit.parse_svg_paths(svg) if a.get("fill", "none") not in ("", "none")]


def bbox(ds):
    pts = np.array([p for d in ds for poly in kit.flatten(kit.parse_d(d)) for p in poly])
    return [float(v) for v in (*pts.min(0), *pts.max(0))]


def box_mask(shape, box, pad):
    m = np.zeros(shape, bool)
    x0, y0, x1, y1 = box
    m[max(0, int(y0 - pad)):int(y1 + pad) + 1, max(0, int(x0 - pad)):int(x1 + pad) + 1] = True
    return m


def median_hex(rgb, mask):
    return kit.rgbhex(np.median(rgb[mask].astype(float), 0))


def border_hex(rgb):
    m = np.ones(rgb.shape[:2], bool)
    m[6:-6, 6:-6] = False
    return median_hex(rgb, m)


def placed_ds(ds, s, tx, ty):
    return [kit.transform_d(d, s, tx, ty) for d in ds]


def fit_on(ds, target, box, pad=24):
    """Similarity (s, tx, ty) of path set ds onto the bool mask `target`, searched in a crop around box."""
    H, W = target.shape
    x0, y0 = max(0, int(box[0] - pad)), max(0, int(box[1] - pad))
    x1, y1 = min(W, int(box[2] + pad) + 1), min(H, int(box[3] + pad) + 1)
    sv = kit.svg_doc(1024, 1024, "".join(f'<path d="{d}" fill="#000000"/>' for d in ds))
    f = fit.fit_similarity(sv, target[y0:y1, x0:x1], bbox(ds))
    return {"s": f["s"], "tx": f["tx"] + x0, "ty": f["ty"] + y0, "iou": f["iou"]}


def render(W, H, bg, layers):
    """layers: [(svg text, s, tx, ty)] bottom first -> RGB 0..255 composited over bg."""
    body = f'<rect width="{W}" height="{H}" fill="{bg}"/>' + "".join(
        f'<g transform="matrix({s} 0 0 {s} {tx} {ty})">{inner(svg)}</g>' for svg, s, tx, ty in layers)
    return kit.over(kit.render_svg(kit.svg_doc(W, H, body)), bg)


def measure(rgb, ren, sil):
    m = kit.compare(rgb, ren, kit.erode(sil, 1))
    return m["de_mean"], m["de_p95"]


def keyline_svg(d, width):
    return kit.svg_doc(1024, 1024, f'<path d="{d}" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="{width}" '
                                   f'stroke-linejoin="round"/>')


def main():
    REC.mkdir(exist_ok=True)
    out, sheet, labels = {}, [], []
    hero_ds = [HERO["silhouette_d"]]
    jobs = [(f"hero@{oid}", oid, ["ap-hero.svg"], "light", BOXES[oid]) for oid in ("01", "13", "14")]
    jobs.append(("hero@17", "17", ["ap-hero.svg"], "shield", SHIELD["ap_mark"]["bbox_tight"]))
    for slot, cands in (("slot-hero-stacked", ["ap-hero.svg"]), ("slot-hero-horizontal", ["ap-hero.svg"]),
                        ("slot-clearspace-mark", ["ap-hero.svg"]),
                        ("slot-tile-twotone", ["flat-11.svg", "ap-hero-dark.svg"]),
                        ("slot-tile-flat", ["flat-12.svg", "flat-16.svg"])):
        jobs.append((slot, "02", cands, "tile" if "tile" in slot else "board", SLOTS[slot]["mark"]))

    only = set(sys.argv[1:])  # optional: re-fit just these keys and keep the others from the last run
    if only:
        jobs = [j for j in jobs if j[0] in only]
        prev = kit.FIT / "placements.json"
        out = json.loads(prev.read_text(encoding="utf-8")) if prev.exists() else {}
    for key, oid, cands, kind, box in jobs:
        rgb = kit.load(oid)
        H, W = rgb.shape[:2]
        if kind == "tile":
            tb = SLOTS[key]["tile"]
            bg = median_hex(rgb, box_mask(rgb.shape[:2], [tb[0] + 6, tb[1] + 6, tb[2] - 6, tb[3] - 6], 0)
                            & ~box_mask(rgb.shape[:2], box, 4))
        else:
            bg = border_hex(rgb)
        fg = kit.bg_mask(rgb, bg, 18.0)
        under, pad = [], 10
        if kind == "board":  # the red clear-space grid, grey guides and the lockup's own wordmark sit right beside the slots
            c = rgb.astype(int)
            red = (c[..., 0] > c[..., 1] + 20) & (c[..., 0] > c[..., 2] + 20)
            grey = (np.abs(c[..., 0] - c[..., 1]) < 14) & (np.abs(c[..., 1] - c[..., 2]) < 14) & (c[..., 0] > 140)
            fg &= ~kit.dilate(red, 1) & ~grey
            for k, v in SLOTS[key].items():
                if k.startswith("wordmark"):
                    fg &= ~box_mask(rgb.shape[:2], v, 2)
            pad = 3
        if kind == "shield":
            frame = comp("shield-frame.svg")
            fr = kit.over(kit.render_svg(frame), "#FFFFFF")
            differs = kit.de2000(kit.srgb_to_lab(rgb.astype(float)), kit.srgb_to_lab(fr)) > 12
            fg = kit.bg_mask(rgb, "#FFFFFF", 18.0) & differs
            under = [(frame, 1.0, 0.0, 0.0)]
        target = fg & box_mask(rgb.shape[:2], box, pad)
        best = None
        for name in cands:
            svg = comp(name)
            ds = hero_ds if name == "ap-hero.svg" else sil_paths(svg)
            p = fit_on(ds, target, box)
            a = refine_axes(ds, target, box, p)
            p.update(iou_similarity=p["iou"], iou=a["iou"], affine=[a["sx"], a["sy"], a["tx"], a["ty"]])
            baked = bake(svg, W, H, a["sx"], a["sy"], a["tx"], a["ty"])  # source space from here on
            bds = [xf_d(d, a["sx"], a["sy"], a["tx"], a["ty"]) for d in ds]
            sil = kit.raster(bds, W, H, ss=2) > 0.5
            layers = list(under)
            if kind == "shield":  # the original cuts a white keyline (measured 10 px) into the frame around the mark
                p["keyline_width"] = 2 * SHIELD["ap_mark"]["keyline_px"]
                layers.append((keyline_svg(bds[0], p["keyline_width"]), 1.0, 0.0, 0.0))
            ren = render(W, H, bg, layers + [(baked, 1.0, 0.0, 0.0)])
            de, p95 = measure(rgb, ren, sil)
            out_svg = baked
            p.update(de_mean=de, de_p95=p95, refit=False, bg=bg)
            if de > REFIT_ABOVE:
                new = fit.refit_colors(baked, rgb, 1.0, 0.0, 0.0, erode_px=2, palette_snap=2.0)
                ren2 = render(W, H, bg, layers + [(new, 1.0, 0.0, 0.0)])
                de2, p952 = measure(rgb, ren2, sil)
                if de2 < de:
                    p.update(de_mean=de2, de_p95=p952, refit=True, de_before_refit=de)
                    out_svg, ren = new, ren2
            (REC / f"{key}.svg").write_text(out_svg, encoding="utf-8")
            p.update(component=f"rec/{key}.svg", source=name, s=1.0, tx=0.0, ty=0.0)
            print(key, name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in p.items()}, flush=True)
            if best is None or p["de_mean"] < best[0]["de_mean"]:
                best = (p, ren)
        p, ren = best
        out[key] = dict(oid=oid, **p)
        x0, y0 = max(0, int(box[0] - 30)), max(0, int(box[1] - 30))
        x1, y1 = min(W, int(box[2] + 30)), min(H, int(box[3] + 30))
        sheet += [rgb[y0:y1, x0:x1], ren[y0:y1, x0:x1]]
        labels += [f"{key} original", f"{key} {p['component']} IoU {p['iou']} dE {p['de_mean']}/{p['de_p95']}"]

    # ap-hero-dark.json gives its 04 placement in the pixel-centre convention; SVG space is +0.5 px.
    t = DARK["transform_to_04"]
    out["hero-dark@04"] = {"oid": "04", "component": "ap-hero-dark.svg", "s": t["scale"],
                           "tx": t["tx"] + 0.5 - 0.5 * t["scale"], "ty": t["ty"] + 0.5 - 0.5 * t["scale"],
                           "iou": t["iou_fit"], "refit": False}
    (kit.FIT / "placements.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    kit.contact(sheet, labels, kit.VERIFY / "placements.png", cols=2, width=520)


if __name__ == "__main__":
    main()
