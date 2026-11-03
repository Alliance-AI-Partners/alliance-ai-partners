"""Stage 1: fit every text run (style by best IoU, then local search with restarts), per-glyph spacing
diagnostic and per-glyph color measurement. Writes work/type/res_<id>.json.
Usage: python work/type/run_fit.py [ids...]"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import textfit as T  # noqa: E402

kit = T.kit


def glyph_colors(oid, run, style, p):
    """Median original color inside each glyph (coverage 1 after a 1 px erosion, so no anti-aliasing)."""
    rgb = kit.load(oid).astype(float)
    x0, y0, x1, y1 = run["box"]
    crop = rgb[y0:y1, x0:x1]
    out = []
    for ch, idx, ox in T.layout(run["s"], style, *p):
        g = T.render(run["s"], style, *p, run["box"], only={idx})
        core = kit.erode(g >= 0.999, 1)
        if core.sum() < 8:
            core = g >= 0.999
        out.append({"ch": ch, "i": idx, "rgb": [round(float(v), 1) for v in np.median(crop[core], 0)], "n": int(core.sum())})
    return out


def main(ids):
    for oid in ids:
        res = {"id": oid, "runs": []}
        for run in T.RUNS[oid]:
            t = time.time()
            r = T.fit_run(oid, run, log=lambda m: None)
            b = r["fine"][0]
            style, p, M = b["style"], b["p"], r["M"]
            rk = T.kit_render(run["s"], style, p, run["box"]) > 0.5
            offs = T.glyph_offsets(run["s"], style, p, M, run["box"])
            rs = T.render(run["s"], style, *p, run["box"], shifts={o["i"]: o["dx"] for o in offs}) > 0.5
            res["runs"].append({
                "s": run["s"], "box": run["box"], "align": run["align"], "style": style, "chosen_by": b["chosen_by"],
                "size": p[0], "tracking": p[1], "x": p[2], "baseline": p[3], "iou": b["iou"], "soft_iou": b["soft"],
                "edge_err_px": T.edge_err(rk, M > 0.5), "iou_with_glyph_dx": kit.iou(rs, M > 0.5),
                "stem_px_orig": b["stem_orig"], "stem_px_render": b["stem_render"],
                "styles_coarse": r["coarse"],
                "candidates": [{"style": f["style"], "iou": round(f["iou"], 4), "soft": round(f["soft"], 4),
                                "stem_render": f["stem_render"], "p": [round(v, 3) for v in f["p"]]} for f in r["fine"]],
                "fg_measured": [kit.rgbhex(f) for f in r["fgs"]], "bg_measured": kit.rgbhex(np.median(r["bg"].reshape(-1, 3), 0)),
                "glyph_dx": offs, "glyph_colors": glyph_colors(oid, run, style, p), "secs": round(time.time() - t, 1)})
            R = res["runs"][-1]
            print(f"{oid} '{run['s']}' -> {style} ({b['chosen_by']}) size {p[0]:.3f} tr {p[1]:.2f} x {p[2]:.3f} base {p[3]:.3f}"
                  f" IoU {b['iou']:.4f} (glyph-dx {R['iou_with_glyph_dx']:.4f}) edge {R['edge_err_px']:.3f}px"
                  f" stems {b['stem_orig']:.2f}/{b['stem_render']:.2f}" if b["stem_orig"] else "",
                  f"| cands {[(c['style'], c['iou'], c['stem_render'] and round(c['stem_render'], 2)) for c in R['candidates']]}"
                  f"\n    dx {[g['dx'] for g in offs]}  ({time.time() - t:.0f}s)", flush=True)
        (T.WORK / f"res_{oid}.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:] or list(T.RUNS))
