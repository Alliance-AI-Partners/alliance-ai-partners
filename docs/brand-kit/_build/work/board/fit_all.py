"""Fit text runs of the board: global fit in all Montserrat styles, then per-glyph kerning for the top two.
usage: python fit_all.py <out.json> [run ids...]   (board agent)"""
import json
import sys
import time

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import kit
import textfit as tf
from runs import RUNS, INK0

out = kit.WORK / 'board' / sys.argv[1]
only = sys.argv[2:]
inks = dict(INK0)
ink_file = kit.WORK / 'board' / 'inks_est.json'
if ink_file.exists():
    inks.update({k: tuple(v) for k, v in json.loads(ink_file.read_text()).items()})
res = json.loads(out.read_text()) if out.exists() else {}
for rid, s, box, ink, gi in RUNS:
    if only and rid not in only:
        continue
    keys = [ink] + sorted(set(gi.values()) - {ink})
    run = tf.Run(rid, s, box, [inks[k] for k in keys], {i: keys.index(v) for i, v in gi.items()})
    t = time.time()
    print(rid, repr(s), flush=True)
    run.fit()
    top = sorted(run.all, key=lambda r: -r["iou_soft"])[:2]
    kerned = [run.fit_kerned(r["style"], r) for r in top]
    best = max(kerned, key=lambda r: r["iou_soft"])
    res[rid] = {"string": s, "box": list(box), "ink": ink, "glyph_inks": {str(k): v for k, v in gi.items()},
                "global": run.all, "kerned": kerned, "best": best}
    print('  BEST %s soft=%.4f bin=%.4f (%.1fs)' % (best['style'], best['iou_soft'], best['iou'], time.time() - t), flush=True)
    out.write_text(json.dumps(res, indent=1))
print('done ->', out)
