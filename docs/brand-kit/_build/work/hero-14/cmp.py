"""original | render | dE heat for a crop, scaled. usage: python cmp.py comp_tag x0 y0 x1 y1 scale out.png [vertical]"""
import sys
import numpy as np
from PIL import Image
from common import kit, W14

if __name__ == '__main__':
    tag = sys.argv[1]
    x0, y0, x1, y1, sc = (int(v) for v in sys.argv[2:7])
    out = sys.argv[7]
    vert = len(sys.argv) > 8
    o = kit.load('14').astype(float)
    r = np.load(W14 / f'comp_{tag}.npy').astype(float)
    de = kit.de2000(kit.srgb_to_lab(o[y0:y1, x0:x1]), kit.srgb_to_lab(r[y0:y1, x0:x1]))
    t = np.clip(de / 10.0, 0, 1)[..., None]
    heat = np.array([255, 255, 255]) * (1 - t) + np.array([220, 30, 30]) * t
    tiles = [o[y0:y1, x0:x1], r[y0:y1, x0:x1], heat]
    ims = [Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST) for a in tiles]
    w, h = ims[0].size
    sheet = Image.new('RGB', (w, h * 3 + 8) if vert else (w * 3 + 8, h), 'black')
    for k, im in enumerate(ims):
        sheet.paste(im, (0, k * (h + 4)) if vert else (k * (w + 4), 0))
    sheet.save(out)
    print('dE mean %.2f p95 %.2f max %.1f' % (de.mean(), np.percentile(de, 95), de.max()))
