"""Fit of the four clear-space 'x' labels with luma-based alpha (chroma of these 10 px red glyphs is
smeared by the 4:2:0 subsampling, luma is not) normalised by the shared clear-space red (board agent)."""
import json, sys, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import textfit as tf
from runs import RUNS
W = kit.WORK / 'board'
LUM = np.array([0.299, 0.587, 0.114])
red = np.array(json.loads((W / 'cs_joint.json').read_text())['ink'])
Ybg = tf.BG @ LUM
_img = kit.load('02').astype(float)
# apparent ink luma of the labels themselves: median luma of their 8 darkest pixels
Yink = float(np.median([np.sort((_img[y0:y1, x0:x1] @ LUM).ravel())[:8].mean()
                        for (x0, y0, x1, y1) in [(861, 514, 881, 533), (861, 681, 881, 700), (725, 579, 745, 598), (957, 579, 977, 598)]]))
print('apparent x-label luma', round(Yink, 1), ' shared red luma', round(float(red @ LUM), 1))
RUN = {r[0]: r for r in RUNS}
ids = ['cs-x-top', 'cs-x-bottom', 'cs-x-left', 'cs-x-right']
img = kit.load('02').astype(float)
runs = []
for rid in ids:
    _, s, box, ink, gi = RUN[rid]
    r = tf.Run(rid, s, box, [red], {})
    x0, y0, x1, y1 = box
    a = np.clip((Ybg - img[y0:y1, x0:x1] @ LUM) / (Ybg - Yink), 0, 1)
    r.alpha = np.where(a < r.cut, 0.0, a)
    runs.append(r)
res = {}
for st in ['Light', 'Regular', 'Medium', 'SemiBold']:
    free = [r.fit_style(st) for r in runs]
    size = float(np.median([f['size'] for f in free]))
    per = [r.fit_style(st, fix_size=size) for r in runs]
    res[st] = {'size': size, 'runs': per}
    print('%-9s size=%.2f bin=%s soft=%s' % (st, size, [round(p['iou'], 3) for p in per], [round(p['iou_soft'], 3) for p in per]), flush=True)
best = max(res, key=lambda k: np.mean([p['iou'] for p in res[k]['runs']]))
print('best', best)
(W / 'fit_x.json').write_text(json.dumps({'ink_luma': float(Yink), 'trials': res, 'best_style': best,
    '_runs': {rid: dict(p, group='csx', alpha='luma') for rid, p in zip(ids, res[best]['runs'])}}, indent=1))
