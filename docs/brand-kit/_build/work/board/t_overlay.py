"""Scratch: overlay original alpha vs fitted render for a run (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
from PIL import Image
import textfit as tf
from runs import RUNS, INK0
import kit

def overlay(r, style, p, out, s=4):
    cov = r.render(style, p)
    a = r.alpha
    rgb = np.ones(a.shape + (3,)) * 255
    # original only -> red, render only -> blue, both -> dark
    o, q = np.clip(a, 0, 1), np.clip(cov, 0, 1)
    rgb[..., 0] = 255 * (1 - q)
    rgb[..., 1] = 255 * (1 - np.maximum(o, q))
    rgb[..., 2] = 255 * (1 - o)
    im = Image.fromarray(rgb.astype(np.uint8)).resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)
    im.save(out)

if __name__ == '__main__':
    rid, style = sys.argv[1], sys.argv[2]
    p = list(map(float, sys.argv[3:7]))
    for r_ in RUNS:
        if r_[0] == rid:
            _, s, box, ink, gi = r_
    keys = [ink] + sorted(set(gi.values()))
    r = tf.Run(rid, s, box, [INK0[k] for k in keys], {i: keys.index(v) for i, v in gi.items()})
    overlay(r, style, p, kit.WORK / 'board' / ('ov_%s.png' % rid), int(sys.argv[7]) if len(sys.argv) > 7 else 3)
