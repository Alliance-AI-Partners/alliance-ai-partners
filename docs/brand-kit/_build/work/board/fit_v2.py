"""Second-pass text fit (board agent).

* alpha is normalised by each run's own apparent ink (median of the pixels the first-pass fit covers > 0.9),
  so thin charcoal / navy runs are not under- or over-estimated;
* runs that are obviously one typographic setting (section labels, palette names, hex codes, the specimen
  lines, the clear-space 'x' labels) share style and size; tracking, position and kerning stay per run.
usage: python fit_v2.py <out.json> <group> [<group> ...]"""
import json
import sys
import time

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import textfit as tf
from runs import RUNS

W = kit.WORK / 'board'
GROUPS = {
    "labels": ["label-01", "label-02", "label-03", "label-04", "label-05"],
    "names": ["name-vibrant", "name-blue", "name-cyan", "name-navy", "name-white", "name-offwhite"],
    "hex": ["hex-blue", "hex-cyan", "hex-navy", "hex-white", "hex-offwhite"],
    "spec": ["spec-1", "spec-2", "spec-3", "spec-4", "spec-5"],
    "csx": ["cs-x-top", "cs-x-bottom", "cs-x-left", "cs-x-right"],
}
SINGLES = ["title", "subtitle", "hero-wordmark", "hero-tagline", "horiz-line1", "horiz-line2", "headline",
           "headline-note", "subheader", "subheader-note", "body", "body-note"]
for s in SINGLES:
    GROUPS[s] = [s]
RUN = {r[0]: r for r in RUNS}


def first_pass():
    R = {}
    for f in ['tf_A.json', 'tf_B.json', 'tf_C.json', 'tf_D.json']:
        R.update(json.loads((W / f).read_text()))
    return R


def apparent_inks(R, img):
    """{run id: [main ink, other ink?]} = median colour of pixels covered > 0.9 by the first-pass fit."""
    out = {}
    for rid, s, box, ink, gi in RUNS:
        b = R[rid]["best"]
        g = tf.run_glyphs(s, b["style"], b["size"], b["tracking"], b["x"], b["baseline"], b.get("offsets_px"))
        x0, y0, x1, y1 = box
        rgb = img[y0:y1, x0:x1].astype(float)
        cov = tf.coverage([gg for gg in g if gg[1] not in gi], box)
        inks = [np.median(rgb[cov > 0.9], 0).tolist()]
        if gi:
            cov2 = tf.coverage([gg for gg in g if gg[1] in gi], box)
            inks.append(np.median(rgb[cov2 > 0.9], 0).tolist())
        out[rid] = inks
    return out


def make_run(rid, inks):
    _, s, box, ink, gi = RUN[rid]
    return tf.Run(rid, s, box, inks[rid], {i: 1 for i in gi})


if __name__ == '__main__':
    out = W / sys.argv[1]
    groups = sys.argv[2:]
    img = kit.load('02')
    R = first_pass()
    ink_path = W / 'inks_apparent.json'
    if ink_path.exists():
        inks = json.loads(ink_path.read_text())
    else:
        inks = apparent_inks(R, img)
        ink_path.write_text(json.dumps(inks, indent=1))
    res = json.loads(out.read_text()) if out.exists() else {}
    for gname in groups:
        ids = GROUPS[gname]
        t = time.time()
        runs = [make_run(r, inks) for r in ids]
        # candidate styles: best three by mean first-pass global soft IoU over the group
        score = {}
        for st in tf.STYLES:
            score[st] = np.mean([next(x["iou_soft"] for x in R[r]["global"] if x["style"] == st) for r in ids])
        cands = sorted(score, key=lambda k: -score[k])[:3]
        print(gname, ids, 'candidates', cands, flush=True)
        trials = {}
        for st in cands:
            free = [run.fit_style(st) for run in runs]
            size = float(np.median([f["size"] for f in free]))
            per = []
            for run, fr in zip(runs, free):
                fx = run.fit_style(st, fix_size=size) if len(runs) > 1 else fr
                k = run.fit_kerned(st, fx, verbose=False, fix_size=size if len(runs) > 1 else None)
                per.append({"free": fr, "fixed": fx, "kerned": k})
            m = float(np.mean([p["kerned"]["iou_soft"] for p in per]))
            trials[st] = {"size": size, "runs": per, "mean_soft": m,
                          "mean_bin": float(np.mean([p["kerned"]["iou"] for p in per]))}
            print('   %-9s size=%.2f mean kerned soft=%.4f bin=%.4f  per-run bin=%s' % (
                st, size, m, trials[st]["mean_bin"], [round(p["kerned"]["iou"], 3) for p in per]), flush=True)
        best = max(trials, key=lambda k: trials[k]["mean_soft"])
        res[gname] = {"runs": ids, "candidates": cands, "trials": trials, "best_style": best}
        for rid, p in zip(ids, trials[best]["runs"]):
            res.setdefault("_runs", {})[rid] = dict(p["kerned"], group=gname, ink_apparent=inks[rid])
        print('  BEST %s (%.1fs)' % (best, time.time() - t), flush=True)
        out.write_text(json.dumps(res, indent=1))
    print('done ->', out)
