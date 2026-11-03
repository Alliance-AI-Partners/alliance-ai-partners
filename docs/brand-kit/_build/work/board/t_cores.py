"""Scratch: apparent core ink per run = median of the darkest-luma 20% of fitted-coverage>0.9 pixels (board agent)."""
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
LUM = np.array([0.299, 0.587, 0.114])
out = {}
for rid, s, box, ink, gi in RUNS:
    b = R[rid]['best']
    x0, y0, x1, y1 = box
    g = tf.run_glyphs(s, b['style'], b['size'], b['tracking'], b['x'], b['baseline'], b.get('offsets_px'))
    cov = tf.coverage([gg for gg in g if gg[1] not in gi], box)
    rgb = img[y0:y1, x0:x1]
    sel = rgb[cov > 0.9]
    lum = sel @ LUM
    core = sel[lum <= np.percentile(lum, 50)]
    m = np.median(core, 0)
    out[rid] = m.tolist()
    lab = kit.srgb_to_lab(m)
    print('%-15s n=%4d core50=%s %s  L=%.1f a=%.1f b=%.1f  B-R=%.1f' % (rid, len(core), m.round(1), kit.rgbhex(m), lab[0], lab[1], lab[2], m[2] - m[0]))
    if gi:
        cov2 = tf.coverage([gg for gg in g if gg[1] in gi], box)
        sel2 = rgb[cov2 > 0.9]
        m2 = np.median(sel2, 0)
        out[rid + ':other'] = m2.tolist()
        print('%-15s   other-ink core=%s %s nearest=%s' % ('', m2.round(1), kit.rgbhex(m2), kit.nearest_palette(m2)))
json.dump(out, open('cores.json', 'w'), indent=1)
