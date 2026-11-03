"""Stage 2: from work/type/res_<id>.json build the deliverables
  fit/text-<id>.json, fit/text-<id>.svg (fitted outlines, source px space),
  verify/text-<id>_overlay.png, verify/text-<id>_diff.png, verify/text_sheet.png.
Usage: python work/type/build_out.py"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import textfit as T  # noqa: E402

kit = T.kit
FIT, VER = kit.FIT, kit.VERIFY
ROLE = {"ALLIANCE AI PARTNERS": "wordmark", "ALLIANCE": "line1", "ALLIANCE AI": "line1", "AI PARTNERS": "line2",
        "PARTNERS": "line2", "Partners in AI. Partners in growth.": "tagline", "ENTERPRISE AI CONSULTING": "descriptor"}
SNAP_DE, MERGE_DE = 4.0, 3.0


def load_res(oid):
    return json.loads((T.WORK / f"res_{oid}.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ per-glyph spacing (faithful mode)

def refine_dx(s, style, p, M, box, dx0, passes=2, win=2.0, step=0.125):
    """Refine the per-glyph shifts with the other glyphs at their shifted positions (Gauss-Seidel passes)."""
    x0, y0, x1, y1 = box
    sh = dict(dx0)
    for _ in range(passes):
        for ch, idx, ox in T.layout(s, style, *p):
            g = T.render(s, style, *p, box, only={idx}, shifts=sh)
            xs = np.nonzero(g.max(0) > 0)[0]
            gx0, gx1 = max(int(xs.min() - win - 3), 0), min(int(xs.max() + win + 4), x1 - x0)
            sub = (x0 + gx0, y0, x0 + gx1, y1)
            best = (-1.0, sh[idx])
            for d in np.arange(sh[idx] - win, sh[idx] + win + 1e-9, step):
                v = T.soft_iou(T.render(s, style, *p, sub, shifts={**sh, idx: d}), M[:, gx0:gx1])
                if v > best[0] + 1e-9:
                    best = (v, float(d))
            sh[idx] = round(best[1], 3)
    return sh


def shifted_paths(s, style, size, tracking, x, base, shifts):
    """kit.text_paths with an extra per-glyph x shift (px)."""
    w = kit.glyphs()["weights"][style]
    k = size / 100.0
    return [kit.transform_d(w["chars"][ch]["d"], k, x + dx * k + idx * tracking / 1000.0 * size + shifts.get(idx, 0.0), base)
            for ch, idx, dx in w["strings"][s]]


def per_char_tracking(s, style, size, tracking, shifts):
    """Illustrator per-character tracking (1/1000 em, added after each character) that moves every glyph by its
    shift while Auto kerning stays untouched; the first glyph's shift goes into x. Spaces keep the base value."""
    lay = kit.glyphs()["weights"][style]["strings"][s]
    tr = [tracking] * len(s)
    for (c0, i0, _), (c1, i1, _) in zip(lay, lay[1:]):
        tr[i0] = tracking + (shifts[i1] - shifts[i0]) * 1000.0 / size
    return [round(v, 1) for v in tr], shifts[lay[0][1]]


# ------------------------------------------------------------------ color

def char_ranges(s, glyph_colors, fg_hex):
    """Group the string into ranges of one ink color: each glyph goes to the nearest measured foreground
    (k-means center); a space takes its neighbors' color when they agree, else the run's base (majority)
    color, so an accent range is exactly the accented word. [[start, end_exclusive, group]]"""
    labs = kit.srgb_to_lab(np.array([kit.hexrgb(h) for h in fg_hex]))
    grp = [None] * len(s)
    for g in glyph_colors:
        grp[g["i"]] = int(np.argmin(kit.de2000(kit.srgb_to_lab(np.array(g["rgb"])), labs)))
    inked = [g for g in grp if g is not None]
    base = max(set(inked), key=inked.count)
    for i in range(len(s)):
        if grp[i] is None:
            nb = {grp[j] for j in (i - 1, i + 1) if 0 <= j < len(s) and grp[j] is not None}
            grp[i] = nb.pop() if len(nb) == 1 else base
    out = []
    for i, g in enumerate(grp):
        if out and out[-1][2] == g:
            out[-1][1] = i + 1
        else:
            out.append([i, i + 1, g])
    return out


def range_color(crop, s, style, p, box, i0, i1):
    idxs = {idx for ch, idx, ox in T.layout(s, style, *p) if i0 <= idx < i1}
    g = T.render(s, style, *p, box, only=idxs)
    core = kit.erode(g >= 0.999, 1)
    if core.sum() < 20:
        core = g >= 0.999
    return np.median(crop[core], 0), int(core.sum())


# ------------------------------------------------------------------ rule (13)

def measure_rule(oid):
    rb = T.RULES[oid]
    x0, y0, x1, y1 = rb["box"]
    crop = kit.load(oid).astype(float)[y0:y1, x0:x1]
    bg, b0 = T.bg_field(crop)
    fg = T.measure_fg(crop, bg, [rb["fg"]])
    a, k = T.coverage(crop, bg, fg)
    w = x1 - x0
    prof = np.median(a[:, int(0.1 * w):int(0.9 * w)], 1)
    thick = float(prof.sum())
    yc = float((prof * (np.arange(len(prof)) + 0.5)).sum() / thick) + y0
    col = a.sum(0) / thick
    full = np.nonzero(col >= 0.95)[0]
    cf, cl = full.min(), full.max()
    xa = x0 + cf - float(col[:cf].sum())
    xb = x0 + cl + 1 + float(col[cl + 1:].sum())
    # fill color from the rows well inside the bar: its edge rows carry the original's sharpening ring
    rows = np.abs(np.arange(len(prof)) + 0.5 + y0 - yc) <= thick / 2 - 2
    core = np.zeros_like(a, bool)
    core[rows, cf + 2:cl - 1] = True
    return {"x0": round(xa, 2), "x1": round(xb, 2), "y": round(yc, 2), "thickness": round(thick, 2),
            "top": round(yc - thick / 2, 2), "bottom": round(yc + thick / 2, 2), "caps": "butt (square ends)",
            "rgb": np.median(crop[core], 0), "n": int(core.sum()), "box": rb["box"]}


# ------------------------------------------------------------------ SVG

def clean_d(d):
    """Retracted-handle cubics (how the outline export writes straight segments) become true lines, and a
    closing line back onto the start point is dropped (Z closes it), so no duplicate anchor is imported."""
    subs = kit.parse_d(d)
    for sp in subs:
        cur, segs = sp["start"], []
        for g in sp["segs"]:
            if g[0] == "C" and np.allclose(g[1:3], cur, atol=1e-3) and np.allclose(g[3:5], g[5:7], atol=1e-3):
                segs.append(("L", g[5], g[6]))
            else:
                segs.append(g)
            cur = (g[-2], g[-1])
        if sp["closed"] and segs and segs[-1][0] == "L" and np.allclose(segs[-1][1:3], sp["start"], atol=1e-3):
            segs.pop()
        sp["segs"] = segs
    return kit.format_d(subs, 3)


def outline_bbox(ds):
    pts = np.concatenate([np.array(p) for d in ds for p in kit.flatten(kit.parse_d(d), 0.02)])
    return [float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max())]


def anchor_count(d):
    return sum(len(sp["segs"]) for sp in kit.parse_d(d))


# ------------------------------------------------------------------ main

def main():
    ids = list(T.RUNS)
    data = {}
    all_ranges = []  # for the cross-original supporting-tone merge
    for oid in ids:
        res = load_res(oid)
        rgb = kit.load(oid).astype(float)
        runs = []
        for run, R in zip(T.RUNS[oid], res["runs"]):
            s, st, box = R["s"], R["style"], tuple(R["box"])
            p = [R["size"], R["tracking"], R["x"], R["baseline"]]
            crop, bg, fgs, a, M = T.prep(oid, run)
            cache = T.WORK / f"shifts_{oid}_{ROLE[s]}.json"
            key = [st] + [round(v, 4) for v in p]
            cached = json.loads(cache.read_text()) if cache.exists() else None
            if cached and cached["key"] == key:
                sh = {int(k): v for k, v in cached["shifts"].items()}
            else:
                sh = refine_dx(s, st, p, M, box, {g["i"]: g["dx"] for g in R["glyph_dx"]})
                cache.write_text(json.dumps({"key": key, "shifts": sh}))
            x0, y0, x1, y1 = box
            rf = kit.raster(shifted_paths(s, st, p[0], p[1], p[2] - x0, p[3] - y0, sh), x1 - x0, y1 - y0)
            ru = kit.raster(kit.text_paths(s, st, p[0], p[1], p[2] - x0, p[3] - y0), x1 - x0, y1 - y0)
            pct, xshift = per_char_tracking(s, st, p[0], p[1], sh)
            ranges = []
            for i0, i1, gi in char_ranges(s, R["glyph_colors"], R["fg_measured"]):
                c, n = range_color(crop, s, st, p, box, i0, i1)
                rec = {"oid": oid, "role": ROLE[s], "start": i0, "end": i1, "text": s[i0:i1], "rgb": c, "n": n}
                ranges.append(rec)
                all_ranges.append(rec)
            runs.append({"run": run, "R": R, "p": p, "box": box, "M": M, "ru": ru, "rf": rf, "shifts": sh,
                         "pct": pct, "xshift": xshift, "ranges": ranges, "bg": bg,
                         "ink": outline_bbox(kit.text_paths(s, st, *p))})
            print(oid, s, "uniform IoU %.4f  faithful IoU %.4f" % (kit.iou(ru > 0.5, M > 0.5), kit.iou(rf > 0.5, M > 0.5)), flush=True)
        rule = measure_rule(oid) if oid in T.RULES else None
        if rule:
            all_ranges.append({"oid": oid, "role": "rule", "rgb": rule["rgb"], "n": rule["n"], "rule": rule})
        data[oid] = {"runs": runs, "rule": rule}

    # ---- colors: snap within dE 4 of the core palette, otherwise merge into few supporting tones (dE <= 3)
    tones = []
    for rec in sorted(all_ranges, key=lambda r: -r["n"]):
        name, hx, de = kit.nearest_palette(rec["rgb"])
        rec["measured_hex"], rec["dE"], rec["nearest"] = kit.rgbhex(rec["rgb"]), round(de, 2), name
        if de <= SNAP_DE:
            rec["hex"], rec["swatch"] = hx, name
            continue
        lab = kit.srgb_to_lab(rec["rgb"])
        for t in tones:
            if float(kit.de2000(lab, kit.srgb_to_lab(t["rgb"]))) <= MERGE_DE:
                t["members"].append(rec)
                w = np.array([m["n"] for m in t["members"]], float)
                t["rgb"] = (np.array([m["rgb"] for m in t["members"]]) * w[:, None]).sum(0) / w.sum()
                break
        else:
            tones.append({"rgb": np.array(rec["rgb"], float), "members": [rec], "family": name})
    fam_name = {"Deep Navy": "Ink Navy", "Vibrant Blue": "Accent Blue", "Bright Cyan": "Accent Cyan",
                "Pure White": "Text White", "Off-White": "Text White"}
    counts = {}
    for t in tones:
        f = fam_name[t["family"]]
        counts[f] = counts.get(f, 0) + 1
        t["name"] = f"{f} {chr(64 + counts[f])}"
    for t in tones:
        t["hex"] = kit.rgbhex(t["rgb"])
        for m in t["members"]:
            m["hex"], m["swatch"] = t["hex"], t["name"]
    tone_list = [{"name": t["name"], "hex": t["hex"], "nearest_core": t["family"],
                  "dE_to_core": round(float(kit.de2000(kit.srgb_to_lab(t["rgb"]), kit.srgb_to_lab(kit.hexrgb(kit.PALETTE[t["family"]])))), 2),
                  "where": sorted({f"{m['oid']} {m['role']}" + (f" '{m['text']}'" if 'text' in m else "") for m in t["members"]})}
                 for t in tones]
    (T.WORK / "supporting_tones.json").write_text(json.dumps(tone_list, indent=1), encoding="utf-8")
    print(json.dumps(tone_list, indent=1))

    # ---- per original outputs
    sheet_imgs, sheet_labels = [], []
    for oid in ids:
        D = data[oid]
        rgb = kit.load(oid)
        H, W = rgb.shape[:2]
        out_runs, body = [], []
        for k, rr in enumerate(D["runs"]):
            R, p, s, st = rr["R"], rr["p"], rr["R"]["s"], rr["R"]["style"]
            role = ROLE[s]
            rid = f"text-{oid}-{role}"
            iou_u = kit.iou(rr["ru"] > 0.5, rr["M"] > 0.5)
            iou_f = kit.iou(rr["rf"] > 0.5, rr["M"] > 0.5)
            colors = [{"start": c["start"], "end": c["end"], "text": c["text"], "hex": c["hex"], "swatch": c["swatch"],
                       "measured_hex": c["measured_hex"], "dE": c["dE"], "nearest_core": c["nearest"]} for c in rr["ranges"]]
            ink = [round(float(v), 2) for v in rr["ink"]]
            out_runs.append({
                "id": rid, "string": s, "font": f"Montserrat-{st}", "style": st,
                "size": round(p[0], 3), "tracking": round(p[1], 2), "x": round(p[2], 3), "baseline": round(p[3], 3),
                "align": R["align"], "kerning": "Auto (metrics)",
                "cap_height": round(0.70004 * p[0], 3), "ink_bbox": ink, "ink_center_x": round((ink[0] + ink[2]) / 2, 2),
                "colors": colors,
                "iou": round(iou_u, 4), "edge_err_px": round(T.edge_err(rr["ru"] > 0.5, rr["M"] > 0.5), 3),
                "style_check": {"chosen_by": R["chosen_by"], "candidates": R["candidates"],
                                "stem_px_original": R["stem_px_orig"] and round(R["stem_px_orig"], 2),
                                "stem_px_fit": R["stem_px_render"] and round(R["stem_px_render"], 2)},
                "faithful_spacing": {
                    "note": "optional: reproduces the original's own (irregular, AI-made) letter spacing. Set x to this x and give "
                            "each character its own tracking (1/1000 em after that character); Auto kerning unchanged.",
                    "x": round(p[2] + rr["xshift"], 3), "tracking_per_char": rr["pct"],
                    "glyph_shift_px": {str(i): v for i, v in sorted(rr["shifts"].items())}, "iou": round(iou_f, 4)},
                "measured": {"bg": R["bg_measured"], "fg_kmeans": R["fg_measured"]},
            })
            # SVG body: one path per glyph, grouped per run, uniform-tracking setting
            fill_of = {}
            for c in rr["ranges"]:
                for i in range(c["start"], c["end"]):
                    fill_of[i] = c["hex"]
            lay = kit.glyphs()["weights"][st]["strings"][s]
            ds = kit.text_paths(s, st, *p)
            g = [f'<g id="{rid}">']
            for (ch, idx, dx), d in zip(lay, ds):
                nm = ch if ch.isalnum() else {".": "period"}.get(ch, "glyph")
                g.append(f'<path id="{rid}-{idx:02d}-{nm}" fill="{fill_of[idx]}" fill-rule="evenodd" d="{clean_d(d)}"/>')
            g.append("</g>")
            body.append("\n".join(g))
        rules = []
        if D["rule"]:
            ru = D["rule"]
            rec = next(r for r in all_ranges if r.get("rule") is ru)
            rules.append({"id": f"text-{oid}-rule", "x0": ru["x0"], "x1": ru["x1"], "y": ru["y"], "thickness": ru["thickness"],
                          "top": ru["top"], "bottom": ru["bottom"], "caps": ru["caps"], "hex": rec["hex"], "swatch": rec["swatch"],
                          "measured_hex": rec["measured_hex"], "dE": rec["dE"], "nearest_core": rec["nearest"]})
            body.append(f'<path id="text-{oid}-rule" fill="{rec["hex"]}" d="M{ru["x0"]} {ru["top"]} L{ru["x1"]} {ru["top"]} '
                        f'L{ru["x1"]} {ru["bottom"]} L{ru["x0"]} {ru["bottom"]} Z"/>')
        svg = kit.svg_doc(W, H, "\n".join(body))
        svg_path = FIT / f"text-{oid}.svg"
        svg_path.write_text(svg, encoding="utf-8")

        # ---- verification: VectorCraft render of the SVG over the original's own background estimate
        rgba = kit.render_svg(svg_path)
        bgimg = rgb.astype(float).copy()
        for rr in D["runs"]:
            x0, y0, x1, y1 = rr["box"]
            bgimg[y0:y1, x0:x1] = rr["bg"]
        if D["rule"]:
            x0, y0, x1, y1 = D["rule"]["box"]
            bgimg[y0:y1, x0:x1] = T.bg_field(rgb[y0:y1, x0:x1].astype(float))[0]
        a_ = rgba[..., 3:4]
        comp = rgba[..., :3] * 255 * a_ + bgimg * (1 - a_)
        region = np.zeros((H, W), bool)
        for rr in D["runs"]:
            x0, y0, x1, y1 = rr["box"]
            region[y0:y1, x0:x1] = True
        if D["rule"]:
            x0, y0, x1, y1 = D["rule"]["box"]
            region[y0:y1, x0:x1] = True
        cmp_ = kit.compare(rgb.astype(float), comp, region)
        for o, rr in zip(out_runs, D["runs"]):
            x0, y0, x1, y1 = rr["box"]
            o["iou_svg_render"] = round(kit.iou(rgba[y0:y1, x0:x1, 3] > 0.5, rr["M"] > 0.5), 4)
            o["svg_render_dE"] = kit.compare(rgb[y0:y1, x0:x1].astype(float), comp[y0:y1, x0:x1])
            o["svg_render_dE"].pop("de_map")
        ys, xs = np.nonzero(region)
        ux0, uy0, ux1, uy1 = max(xs.min() - 8, 0), max(ys.min() - 8, 0), min(xs.max() + 9, W), min(ys.max() + 9, H)
        kit.diff_sheet(rgb[uy0:uy1, ux0:ux1], comp[uy0:uy1, ux0:ux1], VER / f"text-{oid}_diff.png",
                       de_map=cmp_["de_map"][uy0:uy1, ux0:ux1], label=f"text-{oid}  dE mean {cmp_['de_mean']} p95 {cmp_['de_p95']} (text boxes)")

        doc = {"id": oid, "source": kit.ORIGINALS[oid][0], "description": kit.ORIGINALS[oid][1],
               "space": "source image pixels, y down; size in pt = px; x = first glyph origin (pen position) on the baseline; "
                        "tracking in Illustrator units (1/1000 em after every character); colors ranges are [start, end) char indices",
               "image_size": [W, H], "svg": f"fit/text-{oid}.svg",
               "svg_render_check": {"de_mean": cmp_["de_mean"], "de_p95": cmp_["de_p95"], "region": "union of the text boxes"},
               "runs": out_runs, "rules": rules}
        (FIT / f"text-{oid}.json").write_text(json.dumps(doc, indent=1, default=float), encoding="utf-8")

        # ---- overlay (2x): original + fitted outlines in magenta
        S = 2
        ov = Image.fromarray(rgb).resize((W * S, H * S), Image.LANCZOS)
        dr = ImageDraw.Draw(ov)
        for rr in D["runs"]:
            for d in kit.text_paths(rr["R"]["s"], rr["R"]["style"], *rr["p"]):
                for poly in kit.flatten(kit.parse_d(d), 0.1):
                    pts = [(x * S, y * S) for x, y in poly]
                    dr.line(pts + [pts[0]], fill=(255, 0, 255), width=1)
        if D["rule"]:
            ru = D["rule"]
            dr.rectangle([ru["x0"] * S, ru["top"] * S, ru["x1"] * S, ru["bottom"] * S], outline=(255, 0, 255), width=1)
        head = Image.new("RGB", (W * S, 36), "white")
        ImageDraw.Draw(head).text((8, 10), f"text-{oid}: " + "   ".join(f"{o['string'][:24]} {o['style']} {o['size']:.2f}px tr {o['tracking']:.1f} IoU {o['iou']:.3f}" for o in out_runs), fill="black")
        full = Image.new("RGB", (W * S, H * S + 36), "white")
        full.paste(head, (0, 0))
        full.paste(ov, (0, 36))
        full.save(VER / f"text-{oid}_overlay.png")

        # ---- sheet cells: zoomed overlay + mask diff per run
        for o, rr in zip(out_runs, D["runs"]):
            x0, y0, x1, y1 = rr["box"]
            Z = 2
            c = Image.fromarray(rgb[y0:y1, x0:x1]).resize(((x1 - x0) * Z, (y1 - y0) * Z), Image.LANCZOS)
            dr = ImageDraw.Draw(c)
            for d in kit.text_paths(rr["R"]["s"], rr["R"]["style"], *rr["p"]):
                for poly in kit.flatten(kit.parse_d(d), 0.1):
                    pts = [((x - x0) * Z, (y - y0) * Z) for x, y in poly]
                    dr.line(pts + [pts[0]], fill=(255, 0, 255), width=1)
            Mb, Rb = rr["M"] > 0.5, rr["ru"] > 0.5
            dimg = np.full(Mb.shape + (3,), 255, np.uint8)
            dimg[Mb & Rb] = (90, 90, 90)
            dimg[Mb & ~Rb] = (230, 40, 40)
            dimg[~Mb & Rb] = (40, 90, 230)
            dimg = Image.fromarray(dimg).resize(c.size, Image.NEAREST)
            cell = Image.new("RGB", (c.width, c.height * 2 + 4), (200, 200, 200))
            cell.paste(c, (0, 0))
            cell.paste(dimg, (0, c.height + 4))
            sheet_imgs.append(cell)
            sheet_labels.append(f"{oid} {o['string'][:26]} | {o['style']} {o['size']:.1f}px tr {o['tracking']:.1f} | IoU {o['iou']:.3f}"
                                f" (faithful {o['faithful_spacing']['iou']:.3f}) | red=orig only blue=fit only")
        print(oid, "written", flush=True)
    kit.contact(sheet_imgs, sheet_labels, VER / "text_sheet.png", cols=2, width=760)


if __name__ == "__main__":
    main()
