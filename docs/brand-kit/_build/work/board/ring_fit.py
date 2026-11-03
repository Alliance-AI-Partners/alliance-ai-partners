"""Outline rings of the Pure White / Off-White swatches (board agent): centre, stroke radius, width and true
colour, with the swatch fill underneath (pixel = fill/bg base, ring composited on top), via the JPEG model."""
import json
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import jpegsim as J
import textfit as tf
import thin

IMG, BG = thin.IMG, thin.BG


def disk(cx, cy, r, box, ss=8):
    t = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    return thin.cover_polys([np.column_stack([cx + r * np.cos(t), cy + r * np.sin(t)])], box, ss)


def ring_ls(p, fill, box):
    cx, cy, r, w = p
    x0, y0, x1, y1 = box
    dfill = disk(cx, cy, r, box)
    base = BG + dfill[..., None] * (np.asarray(fill, float) - BG)
    ring = np.clip(disk(cx, cy, r + w / 2, box) - disk(cx, cy, r - w / 2, box), 0, 1)
    J0 = J.jpeg420(base * (1 - ring[..., None]), x0, y0, clip=False)
    zero = J.jpeg420(np.zeros(base.shape), x0, y0, clip=False)
    B = []
    for k in range(3):
        e = np.zeros(3); e[k] = 1.0
        B.append(J.jpeg420(ring[..., None] * e, x0, y0, clip=False) - zero)
    orig = IMG[y0:y1, x0:x1]
    A = np.stack([b.reshape(-1) for b in B], 1)
    y = (orig - J0).reshape(-1)
    ink, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = J0 + sum(ink[k] * B[k] for k in range(3))
    return ink, float(np.sqrt(((np.clip(pred, 0, 255) - orig) ** 2).mean()))


if __name__ == '__main__':
    out = {}
    for name, (cx, cy, r, fill) in {'swatch-pure-white': (1147.07, 268.73, 44.63, '#FFFFFF'),
                                    'swatch-off-white': (1266.28, 268.78, 44.65, '#F4F7FB')}.items():
        box = (int(cx - r - 6), int(cy - r - 6), int(cx + r + 7), int(cy + r + 7))
        f = lambda p: ring_ls(p, kit.hexrgb(fill), box)[1]
        p, v = tf.nelder_mead(f, np.array([cx, cy, r, 1.4]), [0.15, 0.15, 0.15, 0.2], 120)
        ink, rms = ring_ls(p, kit.hexrgb(fill), box)
        out[name] = {"cx": p[0], "cy": p[1], "r_stroke": p[2], "width": p[3], "ink": ink.tolist(), "rms": rms, "fill": fill}
        print('%-18s c=(%.2f, %.2f) r=%.2f w=%.2f outer=%.2f ink=%s %s nearest=%s rms=%.2f' % (
            name, p[0], p[1], p[2], p[3], p[2] + p[3] / 2, ink.round(1), kit.rgbhex(np.clip(ink, 0, 255)),
            kit.nearest_palette(np.clip(ink, 0, 255)), rms))
    (kit.WORK / 'board' / 'ring_fit.json').write_text(json.dumps(out, indent=1))
