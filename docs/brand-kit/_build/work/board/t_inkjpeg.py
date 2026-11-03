"""Scratch: per-run true ink via JPEG-4:2:0 model least squares on fitted geometry (board agent)."""
import json, sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import textfit as tf
import jpegsim as J
from runs import RUNS

def fit_inks(covs, orig, bg, x0, y0):
    base = J.jpeg420(np.broadcast_to(bg, covs[0].shape + (3,)), x0, y0, clip=False)
    B = []
    for cov in covs:
        for k in range(3):
            e = np.zeros(3); e[k] = 1.0
            B.append(J.jpeg420(bg + cov[..., None] * e, x0, y0, clip=False) - base)
    w = np.ones(orig.shape, bool)
    for _ in range(4):
        A = np.stack([b[w] for b in B], 1)
        d, *_ = np.linalg.lstsq(A, (orig - base)[w], rcond=None)
        pred = base + sum(d[i] * B[i] for i in range(len(B)))
        w = ~(((pred > 255) & (orig >= 254)) | ((pred < 0) & (orig <= 1)))
    return [bg + d[3 * i:3 * i + 3] for i in range(len(covs))]

if __name__ == '__main__':
    R = {}
    for f in ['tf_A.json', 'tf_B.json', 'tf_C.json', 'tf_D.json']:
        R.update(json.load(open(f)))
    img = kit.load('02').astype(float)
    out = {}
    for rid, s, box, ink, gi in RUNS:
        b = R[rid]['best']
        g = tf.run_glyphs(s, b['style'], b['size'], b['tracking'], b['x'], b['baseline'], b.get('offsets_px'))
        x0, y0, x1, y1 = box
        covs = [tf.coverage([gg for gg in g if gg[1] not in gi], box)]
        if gi:
            covs.append(tf.coverage([gg for gg in g if gg[1] in gi], box))
        inks = fit_inks(covs, img[y0:y1, x0:x1], tf.BG, x0, y0)
        out[rid] = [c.tolist() for c in inks]
        txt = '  '.join('%s %s (L%.1f a%.1f b%.1f) nearest %s %.1f' % (np.round(c, 1), kit.rgbhex(c), *kit.srgb_to_lab(np.clip(c, 0, 255)), kit.nearest_palette(np.clip(c, 0, 255))[0], kit.nearest_palette(np.clip(c, 0, 255))[2]) for c in inks)
        print('%-15s %-9s %s' % (rid, b['style'], txt))
    json.dump(out, open('inks_jpeg.json', 'w'), indent=1)
