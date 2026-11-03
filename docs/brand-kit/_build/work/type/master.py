"""Stage 3: master wordmark spec (fit/text-wordmark-master.json) from the per-original fits fit/text-<id>.json
and the mark ink boxes measured here (dE2000 > 25 from the background, text and rule boxes excluded).
Usage: python work/type/master.py"""
import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import textfit as T  # noqa: E402

kit = T.kit
CAP = 0.70004  # Montserrat cap height / em, every weight (glyphs.json: flat tops at y = -70.004 at 100 pt)


def r(v, n=4):
    return round(float(v), n)


def med(xs):
    return float(st.median(xs))


def mark_box(oid):
    a = kit.load(oid)
    bgc = np.median(np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)]), 0)
    m = kit.de2000(kit.srgb_to_lab(a), kit.srgb_to_lab(bgc)) > 25
    for run in T.RUNS[oid]:
        x0, y0, x1, y1 = run["box"]
        m[y0 - 2:y1 + 2, x0 - 2:x1 + 2] = False
    if oid in T.RULES:
        x0, y0, x1, y1 = T.RULES[oid]["box"]
        m[y0 - 2:y1 + 2, x0 - 2:x1 + 2] = False
    rows, cols = np.nonzero(m.sum(1) >= 3)[0], np.nonzero(m.sum(0) >= 3)[0]
    return [int(cols.min()), int(rows.min()), int(cols.max() + 1), int(rows.max() + 1)]


def unit_width(s, style, tracking):
    """Ink width per pt of size: W(size) = size * unit_width."""
    bx0, by0, bx1, by1 = T.string_bbox(s, style)
    idx = kit.glyphs()["weights"][style]["strings"][s][-1][1]
    return (bx1 - bx0) / 100 + idx * tracking / 1000


def main():
    F = {oid: json.loads((kit.FIT / f"text-{oid}.json").read_text(encoding="utf-8")) for oid in T.RUNS}
    MB = {oid: mark_box(oid) for oid in T.RUNS}

    def run(oid, role):
        return next(x for x in F[oid]["runs"] if x["id"].endswith(role))

    def H(oid):
        return MB[oid][3] - MB[oid][1]

    # ---------------- one-line wordmark: light lockups 01, 13 (horizontal), 14 (stacked), 17 (badge)
    one = {}
    for oid in ("01", "13", "14", "17"):
        w = run(oid, "wordmark")
        mb, h, cap = MB[oid], H(oid), w["cap_height"]
        ink = w["ink_bbox"]
        rec = {"style": w["style"], "size_px": w["size"], "tracking": w["tracking"], "iou": w["iou"], "cap_px": cap,
               "mark_bbox": mb, "mark_height_px": h, "size_over_H": r(w["size"] / h), "cap_over_H": r(cap / h),
               "ink_width_over_cap": r((ink[2] - ink[0]) / cap)}
        if oid in ("01", "13"):
            rec["gap_mark_to_text_over_cap"] = r((ink[0] - mb[2]) / cap)
            rec["gap_mark_to_text_over_H"] = r((ink[0] - mb[2]) / h)
            rec["baseline_from_mark_top_over_H"] = r((w["baseline"] - mb[1]) / h)
        if oid == "14":
            rec["gap_mark_bottom_to_cap_top_over_cap"] = r((w["baseline"] - cap - mb[3]) / cap)
            rec["gap_mark_bottom_to_cap_top_over_H"] = r((w["baseline"] - cap - mb[3]) / h)
            rec["wordmark_width_over_mark_width"] = r((ink[2] - ink[0]) / (mb[2] - mb[0]))
            rec["center_offset_px"] = r((ink[0] + ink[2]) / 2 - (mb[0] + mb[2]) / 2, 2)
        if oid == "17":
            rec["note"] = "mark = the whole shield badge here; the wordmark sits on the banner, centered"
            rec["center_offset_px"] = r((ink[0] + ink[2]) / 2 - (mb[0] + mb[2]) / 2, 2)
        one[oid] = rec
    trk = [one[o]["tracking"] for o in one]
    one_tracking = round(med(trk))

    # text-block vertical centering in the horizontal one-line lockups (cap top of wordmark .. last baseline)
    tag, desc = run("01", "tagline"), run("13", "descriptor")
    w01, w13 = run("01", "wordmark"), run("13", "wordmark")
    blk01 = ((w01["baseline"] - w01["cap_height"]) + tag["baseline"]) / 2
    blk13 = ((w13["baseline"] - w13["cap_height"]) + desc["baseline"]) / 2
    one["01"]["text_block_center_minus_mark_center_over_H"] = r((blk01 - (MB["01"][1] + MB["01"][3]) / 2) / H("01"))
    one["13"]["text_block_center_minus_mark_center_over_H"] = r((blk13 - (MB["13"][1] + MB["13"][3]) / 2) / H("13"))

    # ---------------- two-line: "ALLIANCE" over "AI PARTNERS": 04, 10, 08 (horizontal), 05 (stacked)
    two = {}
    for oid in ("04", "10", "08", "05"):
        l1, l2 = run(oid, "line1"), run(oid, "line2")
        mb, h, c1 = MB[oid], H(oid), l1["cap_height"]
        i1, i2 = l1["ink_bbox"], l2["ink_bbox"]
        rec = {"line1": {"style": l1["style"], "size_px": l1["size"], "tracking": l1["tracking"], "iou": l1["iou"]},
               "line2": {"style": l2["style"], "size_px": l2["size"], "tracking": l2["tracking"], "iou": l2["iou"]},
               "mark_bbox": mb, "mark_height_px": h,
               "line2_size_over_line1_size": r(l2["size"] / l1["size"]),
               "baseline_to_baseline_over_cap1": r((l2["baseline"] - l1["baseline"]) / c1),
               "line1_baseline_to_line2_cap_top_over_cap1": r((l2["baseline"] - l2["cap_height"] - l1["baseline"]) / c1),
               "ink_left_px": [i1[0], i2[0]], "ink_right_px": [i1[2], i2[2]],
               "line1_size_over_H": r(l1["size"] / h), "cap1_over_H": r(c1 / h),
               "text_block_height_over_H": r((l2["baseline"] - (l1["baseline"] - c1)) / h)}
        blk = ((l1["baseline"] - c1) + l2["baseline"]) / 2
        if oid == "05":
            rec["gap_mark_bottom_to_cap_top_over_cap1"] = r((l1["baseline"] - c1 - mb[3]) / c1)
            rec["block_center_offset_px"] = r((min(i1[0], i2[0]) + max(i1[2], i2[2])) / 2 - (mb[0] + mb[2]) / 2, 2)
        else:
            rec["gap_mark_to_text_over_cap1"] = r((min(i1[0], i2[0]) - mb[2]) / c1)
            rec["text_block_center_minus_mark_center_over_H"] = r((blk - (mb[1] + mb[3]) / 2) / h)
        rec["mark"] = {"04": "gradient AP", "10": "flat cyan AP", "08": "faceted bird", "05": "faceted bird"}[oid]
        two[oid] = rec

    ratio = med([two[o]["line2_size_over_line1_size"] for o in two])
    t1 = round(med([two[o]["line1"]["tracking"] for o in two]))
    t2 = round(med([two[o]["line2"]["tracking"] for o in two]))
    # exact width match (both lines flush left and right) for Bold / Bold at the median trackings
    wm_ratio = unit_width("ALLIANCE", "Bold", t1) / unit_width("AI PARTNERS", "Bold", t2)
    # the "A" of both lines starts the line: same left side bearing, so equal x origins differ by lsb*(1-ratio)
    lsb = kit.glyphs()["weights"]["Bold"]["chars"]["A"]["left"] / 100

    # ---------------- tagline (01) and descriptor + rule (13)
    rule = F["13"]["rules"][0]
    i13 = w13["ink_bbox"]
    d_ink = desc["ink_bbox"]
    t_ink = tag["ink_bbox"]
    desc_cap_top = desc["baseline"] - desc["cap_height"]

    tones = json.loads((T.WORK / "supporting_tones.json").read_text(encoding="utf-8"))

    # master descriptor tracking: justify "ENTERPRISE AI CONSULTING" (Medium, at the 13 size ratio) to the master
    # one-line wordmark (Bold, consensus tracking)
    d_ratio = desc["size"] / w13["size"]
    d_idx = kit.glyphs()["weights"]["Medium"]["strings"][desc["string"]][-1][1]
    bx0, by0, bx1, by1 = T.string_bbox(desc["string"], "Medium")
    d_track = ((unit_width(w13["string"], "Bold", one_tracking) / d_ratio) - (bx1 - bx0) / 100) * 1000 / d_idx

    # self-check: the width matches hold on the actual outlines (ink widths at size 100)
    def ink_w(s, style, size, tr):
        pts = np.concatenate([np.array(p) for d in kit.text_paths(s, style, size, tr) for p in kit.flatten(kit.parse_d(d), 0.02)])
        return pts[:, 0].max() - pts[:, 0].min()
    assert abs(ink_w("ALLIANCE", "Bold", 100, t1) - ink_w("AI PARTNERS", "Bold", 100 * wm_ratio, t2)) < 0.05
    assert abs(ink_w(w13["string"], "Bold", 100, one_tracking) - ink_w(desc["string"], "Medium", 100 * d_ratio, d_track)) < 0.05

    spec = {
        "about": "Master wordmark spec for the Alliance AI Partners logo suite, derived from Montserrat fits of the originals "
                 "(fit/text-<id>.json). H = ink-bbox height of the mark in the source lockup; cap = Montserrat cap height "
                 "= 0.70004 x font size (all weights). Font size in pt: size = size_over_H x H. Tracking in Illustrator units "
                 "(1/1000 em), Auto (metrics) kerning. Consensus = median over the listed originals.",
        "font": {"family": "Montserrat", "cap_height_em": CAP, "kerning": "Auto (metrics)", "case": "all caps (wordmark, descriptor); sentence case (tagline)"},
        "one_line_wordmark": {
            "string": "ALLIANCE AI PARTNERS", "style": "Bold", "font": "Montserrat-Bold",
            "tracking": one_tracking,
            "tracking_note": f"median of {trk} (01, 13, 14, 17); the originals split into ~0 (01, 17) and ~-18 (13, 14)",
            "accent": {"chars": [9, 11], "text": "AI"},
            "horizontal_lockup": {
                "size_over_H": r(med([one["01"]["size_over_H"], one["13"]["size_over_H"]])),
                "cap_over_H": r(med([one["01"]["cap_over_H"], one["13"]["cap_over_H"]])),
                "gap_mark_to_text_over_cap": r(med([one["01"]["gap_mark_to_text_over_cap"], one["13"]["gap_mark_to_text_over_cap"]])),
                "text_align": "left; wordmark, tagline / descriptor share the same x origin",
                "vertical": "text block (wordmark cap top .. last baseline) centered on the mark: offsets "
                            f"{one['01']['text_block_center_minus_mark_center_over_H']} H (01), "
                            f"{one['13']['text_block_center_minus_mark_center_over_H']} H (13)",
                "sources": ["01", "13"]},
            "stacked_lockup": {
                "size_over_H": one["14"]["size_over_H"], "cap_over_H": one["14"]["cap_over_H"],
                "gap_mark_bottom_to_cap_top_over_cap": one["14"]["gap_mark_bottom_to_cap_top_over_cap"],
                "wordmark_width_over_mark_width": one["14"]["wordmark_width_over_mark_width"],
                "align": "centered on the mark's vertical axis (ink centers within %.1f px in 14)" % abs(one["14"]["center_offset_px"]),
                "sources": ["14"]},
            "sources": one},
        "two_line_wordmark": {
            "line1": {"string": "ALLIANCE", "style": "Bold", "tracking": t1},
            "line2": {"string": "AI PARTNERS", "style": "Bold", "tracking": t2,
                      "weight_note": "Bold in 08 and 05; 04 uses SemiBold and 10 Regular for line 2 (lighter variants)"},
            "line2_size_over_line1_size": r(wm_ratio),
            "line2_size_ratio_note": f"exact width match for Bold/Bold at these trackings (both lines flush left and right, as in all four "
                                     f"originals); measured ratios median {r(ratio)}",
            "baseline_to_baseline_over_cap1": r(med([two[o]["baseline_to_baseline_over_cap1"] for o in two])),
            "line1_baseline_to_line2_cap_top_over_cap1": r(med([two[o]["line1_baseline_to_line2_cap_top_over_cap1"] for o in two])),
            "alignment": "justified block: both lines share ink left and right edges (within 2 px in 04, 10, 08, 05); "
                         f"with left-aligned point text put line 2's x origin {r(-lsb, 4)} x (size1 - size2) px left of line 1's "
                         "(Bold 'A' starts at -0.009 em), i.e. practically the same origin",
            "horizontal_lockup": {
                "line1_size_over_H": r(med([two[o]["line1_size_over_H"] for o in ("04", "10", "08")])),
                "cap1_over_H": r(med([two[o]["cap1_over_H"] for o in ("04", "10", "08")])),
                "gap_mark_to_text_over_cap1": r(med([two[o]["gap_mark_to_text_over_cap1"] for o in ("04", "10", "08")])),
                "vertical": "text block (line 1 cap top .. line 2 baseline) centered on the mark (offsets "
                            + ", ".join(f"{two[o]['text_block_center_minus_mark_center_over_H']} H ({o})" for o in ("04", "10", "08")) + ")",
                "sources": ["04", "10", "08"]},
            "stacked_lockup": {"line1_size_over_H": two["05"]["line1_size_over_H"],
                               "gap_mark_bottom_to_cap_top_over_cap1": two["05"]["gap_mark_bottom_to_cap_top_over_cap1"],
                               "align": "centered", "sources": ["05"]},
            "sources": two},
        "tagline": {
            "string": "Partners in AI. Partners in growth.", "style": "Regular", "tracking": round(tag["tracking"], 1),
            "size_over_wordmark_size": r(tag["size"] / w01["size"]),
            "baseline_gap_over_wordmark_cap": r((tag["baseline"] - w01["baseline"]) / w01["cap_height"]),
            "align": "left, same x origin as the wordmark (01: %.2f vs %.2f px)" % (tag["x"], w01["x"]),
            "ink_width_over_wordmark_ink_width": r((t_ink[2] - t_ink[0]) / (w01["ink_bbox"][2] - w01["ink_bbox"][0])),
            "weight_note": "original strokes sit between Regular and Medium (stem 2.95 px vs Regular 3.0 / Medium 3.8 at 36.3 px); Regular fits best",
            "source": "01"},
        "descriptor": {
            "string": "ENTERPRISE AI CONSULTING", "style": "Medium", "tracking": round(desc["tracking"], 1),
            "size_over_wordmark_size": r(desc["size"] / w13["size"]),
            "baseline_gap_over_wordmark_cap": r((desc["baseline"] - w13["baseline"]) / w13["cap_height"]),
            "align": "justified to the wordmark: ink %.1f..%.1f vs wordmark %.1f..%.1f px" % (d_ink[0], d_ink[2], i13[0], i13[2]),
            "tracking_rule": "tracking chosen so the descriptor's ink width equals the wordmark's (73.2 against the 13 wordmark at "
                             "-17.9); against the master wordmark (Bold, tracking %d) at this size ratio it is %.1f" % (one_tracking, d_track),
            "tracking_for_master_wordmark": round(d_track, 1),
            "source": "13"},
        "rule": {
            "x_extent": "the wordmark's ink extents (13: rule %.2f..%.2f, wordmark ink %.1f..%.1f)" % (rule["x0"], rule["x1"], i13[0], i13[2]),
            "thickness_over_wordmark_cap": r(rule["thickness"] / w13["cap_height"]),
            "center_from_wordmark_baseline_over_cap": r((rule["y"] - w13["baseline"]) / w13["cap_height"]),
            "position_note": "centered between the wordmark baseline and the descriptor cap top (midpoint %.2f, rule center %.2f px)"
                             % ((w13["baseline"] + desc_cap_top) / 2, rule["y"]),
            "caps": "butt (square ends)", "color_light": "Bright Cyan #00D5FF", "measured_hex": rule["measured_hex"], "dE": rule["dE"],
            "source": "13"},
        "color_rule": {
            "light": {"text": "Deep Navy #121B2A", "accent_AI": "Vibrant Blue #1B56FF", "tagline": "Deep Navy #121B2A",
                      "descriptor": "Deep Navy #121B2A", "rule": "Bright Cyan #00D5FF",
                      "alt_accent": "08 sets 'AI' in Bright Cyan on Off-White (measured within dE 4 of #00D5FF)"},
            "dark": {"text": "Pure White #FFFFFF", "accent_AI": "Bright Cyan #00D5FF",
                     "note": "the dark originals (04, 07, 09, 10, 16) set 'AI' in white; Bright Cyan accent on dark is the brief's rule"},
            "mono_black": "all text #000000, no accent", "mono_white": "all text #FFFFFF, no accent",
            "measured_vs_core": "the originals' own text inks are off-palette supporting tones (listed below); the master uses the core "
                                "palette, the per-original recreations use the measured tones",
            "supporting_tones": tones},
        "other_arrangements": {
            "ALLIANCE AI / PARTNERS": {o: {"line1": {k: run(o, "line1")[k] for k in ("string", "style", "size", "tracking")},
                                           "line2": {k: run(o, "line2")[k] for k in ("string", "style", "size", "tracking")},
                                           "mark_height_px": H(o), "line1_size_over_H": r(run(o, "line1")["size"] / H(o)),
                                           "align": "left" if o == "07" else "center"} for o in ("07", "09", "16")}},
        "mark_boxes_px": MB,
    }
    (kit.FIT / "text-wordmark-master.json").write_text(json.dumps(spec, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: spec[k] for k in ("one_line_wordmark", "two_line_wordmark")}, indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
