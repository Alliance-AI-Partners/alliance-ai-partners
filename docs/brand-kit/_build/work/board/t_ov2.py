"""Scratch: overlay for second-pass fits (board agent)."""
import sys, json
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
from PIL import Image
import textfit as tf
from runs import RUNS
import kit
R = {}
for f in ['tf2_P1.json', 'tf2_P2.json', 'tf2_P3.json', 'tf2_P4.json']:
    try:
        R.update(json.load(open(f))['_runs'])
    except Exception:
        pass
inks = json.load(open('inks_apparent.json'))
RUN = {r[0]: r for r in RUNS}
s = int(sys.argv[-1])
ims = []
for rid in sys.argv[1:-1]:
    _, st, box, ink, gi = RUN[rid]
    b = R[rid]
    run = tf.Run(rid, st, box, inks[rid], {i: 1 for i in gi})
    cov = run.render(b['style'], [b['size'], b['tracking'], b['x'], b['baseline']], offs=b['offsets_px'])
    a = run.alpha
    o, q = np.clip(a, 0, 1), np.clip(cov, 0, 1)
    rgb = np.stack([255 * (1 - q), 255 * (1 - np.maximum(o, q)), 255 * (1 - o)], -1)
    ims.append(Image.fromarray(rgb.astype(np.uint8)).resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST))
    print(rid, b['style'], round(b['size'], 2), 'bin=%.3f soft=%.3f' % (b['iou'], b['iou_soft']))
W = max(i.width for i in ims); H = sum(i.height + 4 for i in ims)
sheet = Image.new('RGB', (W, H), 'white'); y = 0
for i in ims:
    sheet.paste(i, (0, y)); y += i.height + 4
sheet.save('ov2.png')
