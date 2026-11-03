"""Scratch: per-run ink estimate by the integral method using fitted geometry (board agent).
ink = bg - sum(bg - pix) / sum(coverage), over the run box (pixels of other inks excluded)."""
import json, sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import textfit as tf
from runs import RUNS, INK0
R = {}
for f in ['tf_A.json', 'tf_B.json', 'tf_C.json', 'tf_D.json']:
    R.update(json.load(open(f)))
img = kit.load('02').astype(float)
BG = tf.BG
inkL = kit.srgb_to_lab(np.array(INK0['ink']))
for rid, s, box, ink, gi in RUNS:
    b = R[rid]['best']
    x0, y0, x1, y1 = box
    g = tf.run_glyphs(s, b['style'], b['size'], b['tracking'], b['x'], b['baseline'], b.get('offsets_px'))
    main = [gg for gg in g if gg[1] not in gi]
    cov = tf.coverage(main, box)
    # exclude pixels near other-ink glyphs
    if gi:
        other = tf.coverage([gg for gg in g if gg[1] in gi], box)
        ex = kit.dilate(other > 0, 2)
        covo = other
    else:
        ex = np.zeros(cov.shape, bool)
    rgb = img[y0:y1, x0:x1]
    keep = ~ex
    dark = ((BG - rgb) * keep[..., None]).sum((0, 1))
    c = BG - dark / (cov * keep).sum()
    core = rgb[(cov > 0.99) & keep]
    corem = np.median(core, 0) if len(core) else np.array([np.nan] * 3)
    de = float(kit.de2000(kit.srgb_to_lab(c), inkL))
    nm, hx, dp = kit.nearest_palette(c)
    line = '%-15s integral ink=%s %s (dE vs INK0 %.1f; nearest %s %.1f)  core(n=%d)=%s' % (rid, c.round(1), kit.rgbhex(c), de, nm, dp, len(core), kit.rgbhex(corem) if len(core) else '-')
    if gi:
        dark2 = ((BG - rgb) * kit.dilate(other > 0, 2)[..., None]).sum((0, 1))
        c2 = BG - dark2 / other.sum()
        line += '  | other-ink=%s %s nearest=%s' % (c2.round(1), kit.rgbhex(c2), kit.nearest_palette(c2))
    print(line)
