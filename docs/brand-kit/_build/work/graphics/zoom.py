"""Scratch: labelled zoom crops of original 02 (or any RGB png) for visual inspection."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
from PIL import Image, ImageDraw
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'


def crop(im, x0, x1, y0, y1, s, name, step=10):
    c = Image.fromarray(np.asarray(im, np.uint8)[y0:y1, x0:x1]).resize(((x1 - x0) * s, (y1 - y0) * s), Image.BICUBIC)
    d = ImageDraw.Draw(c)
    for x in range(x0 - x0 % step + step, x1, step):
        d.line([((x - x0) * s, 0), ((x - x0) * s, 8)], fill=(255, 0, 0))
        d.text(((x - x0) * s + 2, 10), str(x), fill=(255, 0, 0))
    for y in range(y0 - y0 % step + step, y1, step):
        d.line([(0, (y - y0) * s), (8, (y - y0) * s)], fill=(255, 0, 0))
        d.text((10, (y - y0) * s - 5), str(y), fill=(255, 0, 0))
    c.save(W + '\\' + name)


if __name__ == '__main__':
    im = kit.load('02')
    crop(im, 1030, 1135, 495, 595, 9, 'z_a.png')
    crop(im, 1100, 1210, 495, 595, 9, 'z_b.png')
    crop(im, 1200, 1325, 495, 595, 9, 'z_c.png')
