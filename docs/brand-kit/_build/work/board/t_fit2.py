"""Scratch: robust global fit + kerning on selected runs/styles (board agent)."""
import sys, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import textfit as tf
from runs import RUNS, INK0
rid = sys.argv[1]; styles = sys.argv[2].split(',')
for r_ in RUNS:
    if r_[0] == rid:
        _, s, box, ink, gi = r_
keys = [ink] + sorted(set(gi.values()) - {ink})
run = tf.Run(rid, s, box, [INK0[k] for k in keys], {i: keys.index(v) for i, v in gi.items()})
t = time.time()
for st in styles:
    r = run.fit_style(st)
    print('   %-9s size=%6.2f track=%7.1f x=%7.2f base=%7.2f  soft=%.4f bin=%.4f  (%.1fs)' % (st, r['size'], r['tracking'], r['x'], r['baseline'], r['iou_soft'], r['iou'], time.time() - t))
    k = run.fit_kerned(st, r)
    print('      offsets', k['offsets_px'])
    print('      (%.1fs)' % (time.time() - t))
