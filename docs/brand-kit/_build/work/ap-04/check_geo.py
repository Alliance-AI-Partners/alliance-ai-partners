"""Scratch check of geo04.json: silhouette IoU vs mask04 (whole and per face union) and an outline overlay."""
import json
import sys
import numpy as np
from PIL import Image, ImageDraw

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from build_hero import FACES
from seg04 import W4

COL = {'p-bowl-lower': (255, 0, 0), 'p-bowl-under': (255, 128, 0), 'a-right-outer': (255, 255, 0), 'a-right-inner': (0, 255, 0),
       'a-left-bevel': (0, 255, 255), 'a-left-outer': (255, 0, 255), 'p-bowl-top': (255, 255, 255), 'p-bowl-fold': (255, 0, 128),
       'ribbon-front-stem': (128, 255, 0), 'ribbon-front': (0, 128, 255), 'ribbon-back': (255, 200, 150), 'silhouette': (255, 255, 255)}


def overlay(rgb, geo, out, box, k=3, names=None):
    x0, y0, x1, y1 = box
    im = Image.fromarray(rgb[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.LANCZOS)
    dr = ImageDraw.Draw(im)
    for n in (names or geo):
        for poly in kit.flatten(kit.parse_d(geo[n]), tol=0.05):
            pts = [((x - x0) * k, (y - y0) * k) for x, y in poly]
            dr.line(pts + [pts[0]], fill=COL.get(n, (255, 255, 255)), width=1)
    im.save(out)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'geo04.json'
    g = json.load(open(W4 / src))
    geo, sil = g['geo'], g['silhouette']
    rgb = kit.load('04').astype(float)
    h, w = rgb.shape[:2]
    m04 = np.load(kit.WORK / 'ap-' / 'mask04.npy')
    rs = kit.raster(sil, w, h) > 0.5
    ru = kit.raster(list(geo.values()), w, h) > 0.5
    print('IoU silhouette %.4f   union of faces %.4f   |sil^faces| %d px' % (kit.iou(rs, m04), kit.iou(ru, m04), int((rs ^ ru).sum())))
    print('mask-only px %d   render-only px %d' % (int((m04 & ~ru).sum()), int((ru & ~m04).sum())))
    overlay(rgb, geo, W4 / 'ov_faces.png', (180, 252, 595, 515), 3)
    overlay(rgb, {'silhouette': sil}, W4 / 'ov_sil.png', (180, 252, 595, 515), 3)
    # where the silhouette disagrees with the mask
    x0, y0, x1, y1 = 180, 252, 595, 515
    v = rgb.copy() * 0.5
    v[m04 & ~ru] = [255, 0, 0]
    v[ru & ~m04] = [0, 255, 0]
    Image.fromarray(v[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * 3, (y1 - y0) * 3), Image.NEAREST).save(W4 / 'ov_iou.png')
