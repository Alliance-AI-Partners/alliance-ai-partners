"""hero-04 verification: SVG from geo + fills, VectorCraft render (kit.render_svg) composited over 04's
measured background; silhouette IoU against 04's mark mask (mask04.py: dE2000 > 7 from the background,
outer glow peeled, wordmark excluded) and dE2000 mean / p95 inside that mask."""
import json
import sys
import numpy as np

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from build_hero import FACES
from make_hero import svg_for
from seg04 import W4, BOX

DIFF_BOX = (170, 248, 600, 518)


def measured_background(rgb, m04):
    """median of 04 away from the mark and its glow (> 30 px) and away from the wordmark (x < 610)."""
    far = ~kit.dilate(m04, 30)
    far[:, 610:] = False
    return kit.rgbhex(np.median(rgb[far], 0)), int(far.sum())


def score(svg_text, rgb, m04, bg_hex, geo, extra_paths=()):
    h, w = rgb.shape[:2]
    rgba = kit.render_svg(svg_text)
    comp = kit.over(rgba, bg_hex)
    sil = rgba[..., 3] > 0.5   # VectorCraft render coverage of the mark faces
    met = kit.compare(rgb, comp, m04)
    met2 = kit.compare(rgb, comp, kit.erode(m04, 2))
    return {'iou': round(kit.iou(sil, m04), 4), 'de_mean': met['de_mean'], 'de_p95': met['de_p95'],
            'de_mean_interior2px': met2['de_mean'], 'de_p95_interior2px': met2['de_p95']}, comp, met['de_map']


if __name__ == '__main__':
    gsrc = sys.argv[1] if len(sys.argv) > 1 else 'geo04.json'
    fsrc = sys.argv[2] if len(sys.argv) > 2 else 'fills04.json'
    tag = sys.argv[3] if len(sys.argv) > 3 else 'v1'
    rgb = kit.load('04').astype(float)
    h, w = rgb.shape[:2]
    m04 = np.load(kit.WORK / 'ap-' / 'mask04.npy')
    bg, nbg = measured_background(rgb, m04)
    g = json.load(open(W4 / gsrc))
    geo, order = g['geo'], g.get('order', FACES)
    fills = json.load(open(W4 / fsrc))['fills']
    svg = svg_for(geo, fills, order, w, h)
    (W4 / f'hero04_{tag}.svg').write_text(svg, encoding='utf-8')
    met, comp, de = score(svg, rgb, m04, bg, geo)
    print('background', bg, '(%d px)' % nbg, met)
    x0, y0, x1, y1 = DIFF_BOX
    kit.diff_sheet(rgb[y0:y1, x0:x1], comp[y0:y1, x0:x1], W4 / f'diff_{tag}.png', de[y0:y1, x0:x1],
                   'hero-04 %s  IoU %.4f  dE mean %.2f p95 %.2f' % (tag, met['iou'], met['de_mean'], met['de_p95']))
    np.save(W4 / f'de_{tag}.npy', de.astype(np.float32))
