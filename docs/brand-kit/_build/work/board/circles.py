"""Scratch: palette circle geometry (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
a = kit.load('02').astype(float)
BG = np.array([245.2, 249.4, 252.6])
LUM = np.array([0.299, 0.587, 0.114])
def filled(x0, y0, x1, y1, fill, label):
    reg = a[y0:y1, x0:x1]
    v = np.asarray(fill, float) - BG
    al = np.clip(((reg - BG) @ v) / (v @ v), -0.2, 1.2)
    al0 = np.clip(al, 0, 1)
    ys, xs = np.mgrid[y0:y1, x0:x1] + 0.5
    A = al0.sum()
    cx, cy = (al0 * xs).sum() / A, (al0 * ys).sum() / A
    r = np.sqrt(A / np.pi)
    # radial profile
    rr = np.hypot(xs - cx, ys - cy)
    prof = [al[(rr >= q) & (rr < q + 0.5)].mean() for q in np.arange(r - 4, r + 4, 0.5)]
    # interior color
    inner = reg[rr < r - 3].reshape(-1, 3)
    med = np.median(inner, 0)
    print('%-8s cx=%.2f cy=%.2f r=%.2f  inner median=%s %s nearest=%s' % (label, cx, cy, r, med.round(1), kit.rgbhex(med), kit.nearest_palette(med)))
    print('    radial alpha r-4..r+4:', np.round(prof, 2))
    return cx, cy, r
filled(735, 215, 845, 325, (27, 90, 254), 'blue')
filled(855, 215, 965, 325, (0, 209, 242), 'cyan')
filled(975, 215, 1085, 325, (17, 28, 47), 'navy')
def ring(x0, y0, x1, y1, label):
    reg = a[y0:y1, x0:x1]
    d = (BG - reg) @ LUM
    dp = np.clip(d, 0, None)
    ys, xs = np.mgrid[y0:y1, x0:x1] + 0.5
    # iterate center from dark ring pixels
    m = dp > 0.3 * dp.max()
    cx, cy = (dp * m * xs).sum() / (dp * m).sum(), (dp * m * ys).sum() / (dp * m).sum()
    for _ in range(3):
        rr = np.hypot(xs - cx, ys - cy)
        r = (dp * m * rr).sum() / (dp * m).sum()
        band = (np.abs(rr - r) < 4)
        w8 = dp * band
        # refine center: fit circle by minimizing variance of rr weighted -> use algebraic fit
        X, Y, W = xs[band], ys[band], w8[band]
        A = np.stack([X, Y, np.ones_like(X)], 1) * W[:, None]
        b = (X ** 2 + Y ** 2) * W
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        cx, cy = sol[0] / 2, sol[1] / 2
        r = np.sqrt(sol[2] + cx ** 2 + cy ** 2)
    rr = np.hypot(xs - cx, ys - cy)
    band = np.abs(rr - r) < 4
    integ = (d * band).sum() / (2 * np.pi * r)          # luma darkness integral across ring (per unit length)
    chan = ((BG - reg) * band[..., None]).sum((0, 1)) / (2 * np.pi * r)
    inner = reg[rr < r - 4].reshape(-1, 3)
    med = np.median(inner, 0)
    prof = [d[(rr >= q) & (rr < q + 0.5)].mean() for q in np.arange(r - 4, r + 4, 0.5)]
    print('%-8s ring cx=%.2f cy=%.2f r=%.2f integL=%.1f chan=%s  inner=%s %s nearest=%s' % (label, cx, cy, r, integ, chan.round(1), med.round(1), kit.rgbhex(med), kit.nearest_palette(med)))
    print('    radial darkness r-4..r+4:', np.round(prof, 1))
ring(1095, 215, 1205, 325, 'white')
ring(1215, 215, 1325, 325, 'offwhite')
