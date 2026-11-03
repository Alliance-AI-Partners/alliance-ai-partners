"""Tight bboxes of the board's logo-mark / graphic slots, measured from original 02's pixels (board agent).

Coverage of an object pixel is estimated as its RGB distance from the local backdrop divided by the largest
such distance in its 7x7 neighbourhood (the object's own full-coverage colour nearby); the bbox is where that
coverage reaches 0.5, refined to sub-pixel by the coverage of the extreme row / column."""
import json
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

a = kit.load('02').astype(float)
BG = np.array([245.2, 249.4, 252.6])
NAVY_TILE = np.array([18.0, 29.0, 48.5])


def local_max(m, r=3):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out = np.maximum(out, np.roll(np.roll(m, dy, 0), dx, 1))
    return out


def coverage(box, backdrop, keep=None, floor=18.0):
    x0, y0, x1, y1 = box
    reg = a[y0:y1, x0:x1]
    d = np.linalg.norm(reg - backdrop, axis=-1)
    if keep is not None:
        d = np.where(keep(reg), d, 0.0)
    d = np.where(d < floor, 0.0, d)          # JPEG noise / faint guides
    cov = np.clip(d / np.maximum(local_max(d), 1e-6), 0, 1)
    return cov


def bbox(box, backdrop, keep=None, floor=18.0, thr=0.5):
    x0, y0, x1, y1 = box
    cov = coverage(box, backdrop, keep, floor)
    m = cov >= thr
    ys, xs = np.nonzero(m)
    l, r, t, b = xs.min(), xs.max(), ys.min(), ys.max()
    # sub-pixel: the outermost covered row/column contributes its max coverage
    cl = cov[:, l - 1].max() if l > 0 else 0
    cr = cov[:, r + 1].max() if r + 1 < cov.shape[1] else 0
    ct = cov[t - 1].max() if t > 0 else 0
    cb = cov[b + 1].max() if b + 1 < cov.shape[0] else 0
    sub = [x0 + l - cl, y0 + t - ct, x0 + r + 1 + cr, y0 + b + 1 + cb]
    return [round(float(v), 2) for v in sub], [int(x0 + l), int(y0 + t), int(x0 + r + 1), int(y0 + b + 1)]


def bluish(reg):            # marks are blue / cyan / navy; excludes the red clear-space guides
    return (reg[..., 2] - reg[..., 0]) > 25


def not_gray(reg):          # excludes the light-grey layout guides
    return (reg.max(-1) - reg.min(-1) > 18) | (reg.mean(-1) < 150)


if __name__ == '__main__':
    S = {}
    def put(name, box, backdrop, keep=None, floor=18.0, note=''):
        sub, px = bbox(box, backdrop, keep, floor)
        S[name] = {"bbox": sub, "bbox_px": px, "search_box": list(box), "note": note}
        print('%-28s bbox=%s px=%s' % (name, sub, px))
    put('hero-stacked.mark', (100, 196, 340, 336), BG, not_gray, note='big gradient AP')
    put('hero-horizontal.mark', (396, 199, 506, 270), BG, not_gray, note='small gradient AP left of ALLIANCE / AI PARTNERS')
    put('tile-twotone.mark', (406, 298, 513, 406), NAVY_TILE, floor=30, note='white + cyan two-tone AP inside navy tile 1')
    put('tile-flat.mark', (543, 298, 650, 406), NAVY_TILE, floor=30, note='flat cyan AP inside navy tile 2')
    put('clearspace.mark', (745, 535, 960, 680), BG, bluish, note='gradient AP inside the clear-space grid')
    put('graphic-wave', (1022, 485, 1345, 606), BG, lambda r: (r @ np.array([0.299, 0.587, 0.114])) < 185, floor=40, note='ribbon wave core (glow excluded: luma < 185)')
    put('graphic-wave.glow', (1018, 480, 1350, 609), BG, floor=10, note='visible extent incl. cyan glow (RGB distance > 10)')
    put('graphic-datamesh', (1030, 605, 1325, 718), BG, floor=40, note='navy data-mesh panel')
    (kit.WORK / 'board' / 'slots_raw.json').write_text(json.dumps(S, indent=1))
