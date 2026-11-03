"""Measure the interlace gaps of flat original 12 (cyan AP on navy): gap width profile along each cut,
relative to the mark height."""
import sys
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit

rgb = kit.load('12').astype(float)
bg = np.median(rgb[20:120, 20:120].reshape(-1, 3), 0)
fg = np.median(rgb[540:560, 400:440].reshape(-1, 3), 0)     # inside the crossbar
d = fg - bg
alpha = np.clip(((rgb - bg) @ d) / (d @ d), 0, 1)            # soft coverage by 2-colour unmixing
mask = alpha > 0.5
ys, xs = np.nonzero(mask[250:750, 150:900]); ys += 250; xs += 150
print('bg', kit.rgbhex(bg), 'fg', kit.rgbhex(fg), 'mark bbox x', xs.min(), xs.max(), 'y', ys.min(), ys.max())
# subpixel top / baseline of 12's mark
top = np.mean([320 - alpha[295:320, x].sum() for x in range(570, 640)])
base = np.mean([660 + alpha[660:690, x].sum() for x in range(230, 280)])
print('12 top ~ %.2f  base ~ %.2f  height %.2f' % (top, base, base - top))
np.save(kit.WORK / 'ap-' / 'alpha12.npy', alpha)


def profile(p0, p1, half=9, step=1.0):
    """gap width (sum of 1-alpha over perpendicular cross-sections) along the segment p0->p1"""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    t = (p1 - p0) / np.hypot(*(p1 - p0)); n = np.array([-t[1], t[0]])
    L = np.hypot(*(p1 - p0))
    out = []
    for s in np.arange(0, L, step):
        c = p0 + s * t
        q = c[None] + np.arange(-half, half + 0.01, 0.25)[:, None] * n[None]
        # bilinear sample alpha
        x, y = q[:, 0] - 0.5, q[:, 1] - 0.5
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); fx, fy = x - x0, y - y0
        a = (alpha[y0, x0] * (1 - fx) * (1 - fy) + alpha[y0, x0 + 1] * fx * (1 - fy) + alpha[y0 + 1, x0] * (1 - fx) * fy + alpha[y0 + 1, x0 + 1] * fx * fy)
        out.append((s, (1 - a).sum() * 0.25, c))
    return out


if __name__ == '__main__':
    for name, p0, p1 in (('left gap', (262, 566), (342, 530)), ('right gap', (508, 588), (618, 436))):
        pr = profile(p0, p1)
        w = np.array([q[1] for q in pr])
        k = int(w.argmax())
        print(name, 'max width %.2f at s=%.0f (%s); widths every 8px:' % (w.max(), pr[k][0], np.round(pr[k][2], 1)),
              ' '.join('%.1f' % v for v in w[::8]))
