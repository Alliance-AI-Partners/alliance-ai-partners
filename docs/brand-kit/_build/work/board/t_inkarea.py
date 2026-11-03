"""Scratch: ink-area ratio (sum render coverage / sum original alpha) per style for contested runs (board agent)."""
import sys, json
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit, textfit as tf
from runs import RUNS
RUN = {r[0]: r for r in RUNS}
inks = json.load(open('inks_apparent.json'))
D = {}
for f in ['tf2_P1.json', 'tf2_P2.json', 'tf2_P3.json', 'tf2_P4.json']:
    d = json.load(open(f))
    for g, v in d.items():
        if g != '_runs':
            D[g] = v
for g in ['names', 'hex', 'hero-tagline', 'subheader-note', 'body', 'body-note', 'subheader', 'labels', 'spec', 'subtitle', 'title', 'headline-note']:
    v = D[g]
    line = []
    for st, t in v['trials'].items():
        ratios = []
        for rid, p in zip(v['runs'], t['runs']):
            k = p['kerned']
            _, s, box, ink, gi = RUN[rid]
            run = tf.Run(rid, s, box, inks[rid], {i: 1 for i in gi})
            cov = run.render(st, [k['size'], k['tracking'], k['x'], k['baseline']], offs=k['offsets_px'])
            ratios.append(cov.sum() / run.alpha.sum())
        line.append('%s area=%.3f bin=%.3f soft=%.3f' % (st, np.mean(ratios), t['mean_bin'], t['mean_soft']))
    print('%-15s ' % g + ' | '.join(line))
