"""Scratch: zoomed crops of original 02 for visual inspection (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from PIL import Image

W = kit.WORK / 'board'
a = kit.load('02')


def crop(name, x0, y0, x1, y1, s, src=None):
    src = a if src is None else src
    Image.fromarray(np.asarray(src[y0:y1, x0:x1], np.uint8)).resize(((x1 - x0) * s, (y1 - y0) * s), Image.NEAREST).save(W / (name + '.png'))


if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        n, x0, y0, x1, y1, s = args[0], *map(int, args[1:6])
        crop(n, x0, y0, x1, y1, s)
    else:
        crop('c_title', 360, 30, 1020, 130, 2)
        crop('c_logo', 20, 150, 690, 440, 2)
        crop('c_pal', 690, 150, 1360, 440, 2)
        crop('c_typo', 20, 440, 690, 750, 2)
        crop('c_clear', 690, 440, 1010, 750, 3)
        crop('c_graph', 1010, 440, 1376, 768, 2)
        for (x, y) in [(5, 5), (1370, 5), (5, 760), (1370, 760), (688, 300), (200, 600), (1200, 400), (688, 30), (688, 760)]:
            print((x, y), a[y, x], a[max(0, y - 3):y + 4, max(0, x - 3):x + 4].reshape(-1, 3).mean(0).round(1))
