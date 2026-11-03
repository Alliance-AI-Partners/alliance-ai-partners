"""Scratch: dE breakdown (silhouette edge band vs interior, per visible face) and a 3x heatmap with face outlines."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from build_hero import FACES
from seg04 import W4
from color04 import visible_labels

if __name__ == '__main__':
    tag = sys.argv[1]
    gsrc = sys.argv[2] if len(sys.argv) > 2 else 'geo04.json'
    de = np.load(W4 / f'de_{tag}.npy').astype(float)
    m04 = np.load(kit.WORK / 'ap-' / 'mask04.npy')
    g = json.load(open(W4 / gsrc))
    geo = g['geo']
    FACES = g.get('order', FACES)
    rgb = kit.load('04').astype(float)
    lab = visible_labels(geo, rgb.shape[:2], FACES)
    edge = m04 & ~kit.erode(m04, 2)
    tot = de[m04].sum()
    print('mask px %d  mean %.2f | edge band (2px) px %d mean %.2f share %.0f%% | interior mean %.2f' % (
        m04.sum(), de[m04].mean(), edge.sum(), de[edge].mean(), 100 * de[edge].sum() / tot, de[m04 & ~edge].mean()))
    for i, n in enumerate(FACES):
        r = (lab == i) & m04 & ~edge
        print('  %-18s px %5d mean %5.2f p95 %5.2f  share of total %4.1f%%' % (n, r.sum(), de[r].mean(), np.percentile(de[r], 95), 100 * de[r].sum() / tot))
    r = m04 & (lab < 0)
    print('  %-18s px %5d mean %5.2f' % ('(no face)', r.sum(), de[r].mean() if r.any() else 0))
    x0, y0, x1, y1 = (176, 252, 596, 514)
    k = 3
    t = np.clip(de / 10.0, 0, 1)[..., None]
    heat = (np.array([255, 255, 255]) * (1 - t) + np.array([220, 30, 30]) * t)
    heat[~m04] = heat[~m04] * 0.6 + 40
    im = Image.fromarray(heat[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    for n in FACES:
        for poly in kit.flatten(kit.parse_d(geo[n]), tol=0.05):
            pts = [((x - x0) * k, (y - y0) * k) for x, y in poly]
            dr.line(pts + [pts[0]], fill=(0, 90, 200), width=1)
    im.save(W4 / f'heat_{tag}.png')
