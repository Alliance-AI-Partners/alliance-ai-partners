"""Scratch: sanity + speed test of textfit rasteriser (board agent)."""
import sys, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import textfit as tf
import kit
# 1) square check
sq = [np.array([[2.0, 2.0], [6.0, 2.0], [6.0, 6.0], [2.0, 6.0]])]
m = tf.fill_evenodd([s * 4 for s in sq], 40, 40)
print('square 4x4 px area at ss=4 ->', m.sum() / 16)
# 2) glyph vs VectorCraft
d = kit.text_paths('HEADLINE', 'Bold', 30, 0, 10.3, 40.6)
body = '<rect id="bg" x="0" y="0" width="200" height="60" fill="#FFFFFF"/>' + ''.join('<path d="%s" fill="#000000"/>' % s for s in d)
svg = kit.svg_doc(200, 60, body)
import subprocess, tempfile
from PIL import Image
from pathlib import Path
p = kit.WORK / 'board' / 't_vc.svg'; p.write_text(svg, encoding='utf-8')
png = kit.WORK / 'board' / 't_vc.png'
kit._vc(['convert', p, png, '--scale', 4])
im = Image.open(png).convert('L').reduce(4)
vc = 1 - np.asarray(im, float) / 255
t = time.time()
g = tf.run_glyphs('HEADLINE', 'Bold', 30, 0, 10.3, 40.6)
cov = tf.coverage(g, (0, 0, 200, 60), 4)
print('own raster time %.3f s' % (time.time() - t))
print('coverage sums own=%.2f vc=%.2f  max abs diff=%.3f  mean abs diff=%.4f  softIoU=%.4f' % (cov.sum(), vc.sum(), np.abs(cov - vc).max(), np.abs(cov - vc).mean(), tf.soft_iou(cov, vc)))
kr = kit.raster(d, 200, 60)
print('kit.raster sum=%.2f  softIoU vs vc=%.4f' % (kr.sum(), tf.soft_iou(kr, vc)))
