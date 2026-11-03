"""Seeded watershed segmentation of the hero AP mark in original 14 into its 3D faces (same scheme as
work/ap-/seg.py for 06). Writes work/hero-14/labels14.npy and seg_preview.png."""
import numpy as np
from PIL import Image
from common import kit, W14, CROP, REGION_Y1, to14
from seg import watershed  # noqa: F401  (06 pipeline)
import seg as seg06

# seeds: the 06 seeds mapped by the master similarity, then corrected on 14's own pixels
SEEDS = {n: [[tuple(round(v, 1) for v in to14(x, y)) for x, y in pl] for pl in pls] for n, pls in seg06.SEEDS.items()}
# background lines that landed within a pixel of 14's edges (top 303.2, base 611.9, crossbar bottom 551.4)
SEEDS['bg'][0] = [(254.4, 297.0), (515.4, 297.0)]
SEEDS['bg'][1] = [(247.0, 619.0), (768.9, 619.0)]
SEEDS['bg'][3] = [(425.9, 561.0), (485.6, 561.0)]
# ribbon near the left tip (bands measured per column: upper/lower boundary at x 340 525.5, 330 528.5,
# 320 532.5, 310 539, 300 546.5, 290 556.5; lower band / leg boundary 552.5, 554.5, 557.5, 561.5, 567, 573):
# the mapped lower-band seed started inside the upper band at x 314; both bands get seeds down to the tip
SEEDS['ribbon-lower'][0] = [(290.0, 565.0), (300.0, 557.0), (318.0, 548.0), (340.0, 539.5), (400.0, 535.5), (470.6, 530.6)]
SEEDS['ribbon-upper'].append([(330.0, 517.0), (310.0, 527.0), (300.0, 536.0), (290.0, 548.0)])
# the bowl's dark lower face shows as a thin wedge between the lower band and the counter's left edge
# (x 583-590, y ~410-447); without a seed the band floods it down to y ~419
SEEDS['p-bowl-lower'].append([(588.2, 421.0), (586.5, 432.0), (584.5, 444.0)])
NAMES = list(SEEDS)


def seeds_mask(shape):
    from PIL import ImageDraw
    lab = np.full(shape, -1, np.int32)
    for k, name in enumerate(NAMES):
        im = Image.new('L', (shape[1], shape[0]), 0)
        d = ImageDraw.Draw(im)
        for pl in SEEDS[name]:
            d.line(pl, fill=255, width=3)
        lab[np.asarray(im) > 0] = k
    return lab


def lab_gradient(rgb):
    lab3 = kit.srgb_to_lab(rgb)
    H, W = lab3.shape[:2]
    pad = np.pad(lab3, ((1, 1), (1, 1), (0, 0)), mode='edge')
    sm = sum(pad[dy:dy + H, dx:dx + W] for dy in range(3) for dx in range(3)) / 9.0
    gx = np.zeros(sm.shape[:2]); gy = np.zeros(sm.shape[:2])
    gx[:, 1:-1] = np.linalg.norm(sm[:, 2:] - sm[:, :-2], axis=-1)
    gy[1:-1] = np.linalg.norm(sm[2:] - sm[:-2], axis=-1)
    return np.hypot(gx, gy)


def segment(rgb):
    grad = lab_gradient(rgb)
    lab = seeds_mask(grad.shape)
    x0, y0, x1, y1 = CROP
    y1 = min(y1, REGION_Y1)
    sub = seg06.watershed(grad[y0:y1, x0:x1], lab[y0:y1, x0:x1])
    full = np.zeros(grad.shape, np.int32)
    full[y0:y1, x0:x1] = sub
    return full


def preview(rgb, full, out, sc=2):
    prev = np.zeros_like(rgb)
    for k in range(len(NAMES)):
        m = full == k
        if m.any():
            prev[m] = np.median(rgb[m], 0)
    edge = np.zeros(full.shape, bool)
    edge[:, 1:] |= full[:, 1:] != full[:, :-1]
    edge[1:] |= full[1:] != full[:-1]
    prev[edge] = [255, 0, 0]
    x0, y0, x1, y1 = CROP
    Image.fromarray(prev.astype(np.uint8)).crop((x0, y0, x1, y1)).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST).save(out)


if __name__ == '__main__':
    rgb = kit.load('14').astype(float)
    full = segment(rgb)
    np.save(W14 / 'labels14.npy', full)
    preview(rgb, full, W14 / 'seg_preview.png')
    for k, n in enumerate(NAMES):
        print(k, n, int((full == k).sum()))
