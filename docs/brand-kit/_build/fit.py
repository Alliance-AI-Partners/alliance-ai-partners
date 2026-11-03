"""Fit a master component onto an original: similarity transform by mask IoU, then optional per-original
re-fit of every face's gradient stop colors from that original's pixels (same geometry, same gradient
vectors, only the stop colors change).

Used by build.py to place the master AP / bird into each original's recreation."""
import re

import numpy as np

import kit


def faces(svg_text):
    """[(id, d, fill)] in document order (= z-order, bottom first)."""
    return [(a.get("id", ""), d, a.get("fill", "")) for d, a in kit.parse_svg_paths(svg_text)]


def gradients(svg_text):
    """{id: {'x1','y1','x2','y2', 'stops': [(offset, hex)]}} for every linearGradient."""
    out = {}
    for m in re.finditer(r"<linearGradient\b([^>]*)>(.*?)</linearGradient>", svg_text, re.S):
        a = dict(re.findall(r'([\w:-]+)="([^"]*)"', m.group(1)))
        stops = [(float(o), c.upper()) for o, c in re.findall(r'<stop[^>]*offset="([^"]+)"[^>]*stop-color="([^"]+)"', m.group(2))]
        out[a["id"]] = {k: float(a[k]) for k in ("x1", "y1", "x2", "y2")}
        out[a["id"]]["stops"] = stops
    return out


def silhouette(svg_text, w, h, s=1.0, tx=0.0, ty=0.0, ss=2):
    ds = [kit.transform_d(d, s, tx, ty) for _, d, f in faces(svg_text) if f and f != "none"]
    return kit.raster(ds, w, h, ss=ss)


def fit_similarity(svg_text, target_mask, src_bbox, region=None, steps=(8, 3, 1, 0.4)):
    """Find (s, tx, ty) mapping the component (whose artwork bbox in its own space is src_bbox = x0,y0,x1,y1)
    onto the boolean target_mask. Starts from the bbox match, then coordinate search with shrinking steps (px)."""
    h, w = target_mask.shape
    tgt = target_mask if region is None else (target_mask & region)
    ys, xs = np.where(tgt)
    tx0, ty0, tx1, ty1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    sx0, sy0, sx1, sy1 = src_bbox
    s = ((tx1 - tx0) / (sx1 - sx0) + (ty1 - ty0) / (sy1 - sy0)) / 2
    tx, ty = tx0 - sx0 * s, ty0 - sy0 * s

    def score(s_, tx_, ty_):
        m = silhouette(svg_text, w, h, s_, tx_, ty_) > 0.5
        if region is not None:
            m &= region
        return kit.iou(m, tgt)

    best = score(s, tx, ty)
    cx, cy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    for step in steps:
        improved = True
        while improved:
            improved = False
            for ds_, dx, dy in ((step / (sx1 - sx0), 0, 0), (-step / (sx1 - sx0), 0, 0), (0, step, 0), (0, -step, 0), (0, 0, step), (0, 0, -step)):
                s2 = s * (1 + ds_)
                # scale about the target center so a scale step does not also shift the mark
                tx2 = cx - (cx - tx) * (1 + ds_) + dx
                ty2 = cy - (cy - ty) * (1 + ds_) + dy
                v = score(s2, tx2, ty2)
                if v > best + 1e-5:
                    best, s, tx, ty, improved = v, s2, tx2, ty2, True
    return {"s": s, "tx": tx, "ty": ty, "iou": round(best, 4)}


def refit_colors(svg_text, orig_rgb, s, tx, ty, erode_px=2, palette_snap=4.0):
    """Re-estimate every face's fill from orig_rgb under the transform. Solid fills take the median color of the
    face's visible pixels; gradient stops are solved by least squares with the stop offsets and gradient vector
    kept. Stops within palette_snap dE2000 of a core palette color snap to it. Returns new SVG text."""
    h, w = orig_rgb.shape[:2]
    fs = faces(svg_text)
    grads = gradients(svg_text)
    masks = [kit.raster(kit.transform_d(d, s, tx, ty), w, h, ss=2) > 0.5 for _, d, f in fs]
    covered = np.zeros((h, w), bool)
    visible = [None] * len(fs)
    for i in range(len(fs) - 1, -1, -1):  # top face first
        visible[i] = masks[i] & ~covered
        covered |= masks[i]
    pal = [(kit.hexrgb(v), v) for v in kit.PALETTE.values()]

    def snap(c):
        lab = kit.srgb_to_lab(c)
        for rgbv, hx in pal:
            if float(kit.de2000(lab, kit.srgb_to_lab(rgbv))) <= palette_snap:
                return hx
        return kit.rgbhex(c)

    new = svg_text
    for (fid, d, fill), vis in zip(fs, visible):
        core = kit.erode(vis, erode_px) if vis.sum() > 400 else vis
        if core.sum() < 30:
            continue
        px = orig_rgb[core].astype(float)
        m = re.match(r"url\(#([^)]+)\)", fill or "")
        if not m:
            new = re.sub(r'(<path\b[^>]*id="%s"[^>]*fill=")[^"]*"' % re.escape(fid), r'\g<1>%s"' % snap(np.median(px, 0)), new)
            continue
        g = grads[m.group(1)]
        offs = np.array([o for o, _ in g["stops"]])
        x1, y1, x2, y2 = (g["x1"] * s + tx, g["y1"] * s + ty, g["x2"] * s + tx, g["y2"] * s + ty)
        yy, xx = np.where(core)
        vx, vy = x2 - x1, y2 - y1
        t = np.clip(((xx - x1) * vx + (yy - y1) * vy) / (vx * vx + vy * vy), 0, 1)
        # hat-function basis on the stop offsets, flat beyond the end stops
        basis = np.zeros((len(t), len(offs)))
        for k in range(len(offs)):
            if k > 0:
                seg = (t >= offs[k - 1]) & (t <= offs[k])
                basis[seg, k] = (t[seg] - offs[k - 1]) / max(1e-6, offs[k] - offs[k - 1])
            if k < len(offs) - 1:
                seg = (t >= offs[k]) & (t <= offs[k + 1])
                basis[seg, k] = np.maximum(basis[seg, k], (offs[k + 1] - t[seg]) / max(1e-6, offs[k + 1] - offs[k]))
        basis[t <= offs[0], 0] = 1
        basis[t >= offs[-1], -1] = 1
        sol, *_ = np.linalg.lstsq(basis, px, rcond=None)
        block = re.search(r'<linearGradient\b[^>]*id="%s"[^>]*>.*?</linearGradient>' % re.escape(m.group(1)), new, re.S).group(0)
        nb = block
        for st, c in zip(re.findall(r"<stop\b[^>]*/>", block), sol):
            nb = nb.replace(st, re.sub(r'stop-color="[^"]+"', 'stop-color="%s"' % snap(np.clip(c, 0, 255)), st), 1)
        new = new.replace(block, nb)
    return new
