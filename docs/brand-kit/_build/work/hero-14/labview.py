"""Label map in distinct colours, blended 50% with original 14. usage: python labview.py x0 y0 x1 y1 scale out.png [labels.npy]"""
import sys
import numpy as np
from PIL import Image
from common import kit, W14

COLS = np.array([[255, 255, 255], [145, 30, 180], [245, 130, 49], [67, 99, 216], [255, 225, 25], [70, 240, 240],
                 [0, 128, 128], [240, 50, 230], [230, 25, 75], [60, 180, 75], [188, 246, 12], [250, 190, 190],
                 [128, 128, 0], [0, 0, 128]], float)

if __name__ == '__main__':
    x0, y0, x1, y1, sc = (int(v) for v in sys.argv[1:6])
    out = sys.argv[6]
    lab = np.load(sys.argv[7] if len(sys.argv) > 7 else W14 / 'labels14.npy')
    im = kit.load('14').astype(float)
    v = 0.45 * im + 0.55 * COLS[lab % len(COLS)]
    Image.fromarray(v[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST).save(out)
