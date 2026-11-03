"""Scratch: median of all fitted-coverage>0.9 pixels per run; calibration check vs big-text interior (board agent)."""
import json, sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import textfit as tf
from runs import RUNS
R = {}
for f in ['tf_A.json', 'tf_B.json', 'tf_C.json', 'tf_D.json']:
    R.update(json.load(open(f)))
img = kit.load('02').astype(float)
ref = kit.srgb_to_lab(np.array([21.5, 25, 54]))
for thr in (0.9, 0.98):
    print('--- coverage >', thr)
    for rid, s, box, ink, gi in RUNS:
        b = R[rid]['best']
        g = tf.run_glyphs(s, b['style'], b['size'], b['tracking'], b['x'], b['baseline'], b.get('offsets_px'))
        cov = tf.coverage([gg for gg in g if gg[1] not in gi], box)
        x0, y0, x1, y1 = box
        sel = img[y0:y1, x0:x1][cov > thr]
        m = np.median(sel, 0); mn = sel.mean(0)
        lab = kit.srgb_to_lab(mn)
        print('%-15s n=%4d median=%s mean=%s %s L=%.1f a=%.1f b=%.1f  dE(mean vs ink0)=%.1f' % (rid, len(sel), m.round(0), mn.round(1), kit.rgbhex(mn), lab[0], lab[1], lab[2], kit.de2000(lab, ref)))
