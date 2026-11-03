"""Silhouette mask of a mark on a dark background with glow: dE from the background > lo, then peel the
outer glow layers (boundary pixels much fainter than the face pixels right inside them)."""
import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit


def maxf(a, r):
    out = a.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out = np.maximum(out, np.roll(np.roll(a, dy, 0), dx, 1))
    return out


def mark_mask(rgb, bg, lo=7.0, ratio=0.5, peel=5):
    de = kit.de2000(kit.srgb_to_lab(rgb), kit.srgb_to_lab(kit.hexrgb(bg)))
    m = de > lo
    m = kit.erode(kit.dilate(m, 1), 1)            # close pinholes
    for _ in range(peel):
        inner = np.where(m, de, 0)
        ref = maxf(np.where(kit.erode(m, 1), de, 0), 2)
        border = m & ~kit.erode(m, 1)
        drop = border & (de < ratio * ref)
        if not drop.any():
            break
        m &= ~drop
    return m, de


if __name__ == '__main__':
    from PIL import Image
    rgb = kit.load('04').astype(float)
    m, de = mark_mask(rgb, '#132031')
    box = (150, 230, 620, 540)
    sub = np.zeros_like(m); sub[box[1]:box[3], box[0]:box[2]] = m[box[1]:box[3], box[0]:box[2]]
    np.save(kit.WORK / 'ap-' / 'mask04.npy', sub)
    ov = rgb.copy(); e = sub ^ kit.erode(sub, 1); ov[e] = [255, 255, 0]
    Image.fromarray(ov.astype(np.uint8)).crop(box).resize(((box[2]-box[0])*2, (box[3]-box[1])*2), Image.NEAREST).save(kit.WORK / 'ap-' / 'mask04_ov.png')
    print('area', int(sub.sum()))
