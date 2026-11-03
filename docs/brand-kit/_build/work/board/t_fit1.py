"""Scratch: fit one run with all styles (board agent)."""
import sys, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import textfit as tf
from runs import RUNS, INK0
import kit
img = kit.load('02')
want = sys.argv[1:]
for rid, s, box, ink, gi in RUNS:
    if want and rid not in want:
        continue
    keys = [ink] + sorted(set(gi.values()))
    inks = [INK0[k] for k in keys]
    r = tf.Run(rid, s, box, inks, {i: keys.index(v) for i, v in gi.items()})
    t = time.time()
    print(rid, repr(s))
    b = r.fit()
    print('  BEST', b['style'], 'soft=%.4f bin=%.4f  (%.1fs)' % (b['iou_soft'], b['iou'], time.time() - t))
