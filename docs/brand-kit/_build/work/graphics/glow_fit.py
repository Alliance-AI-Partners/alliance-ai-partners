"""Scratch: fit N stacked offset copies (offset r_i, opacity a_i, one colour G) to the measured glow
profile of the wave: pixel = bg + (1 - prod(1 - a_i [d < r_i])) * (G - bg)."""
import numpy as np
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
im = kit.load('02').astype(float)
dist = np.load(W + r'\glow_dist.npy')
X0, Y0 = 1000, 470
rgb = im[Y0:Y0 + dist.shape[0], X0:X0 + dist.shape[1]]
bg = np.array([245.0, 249.0, 252.0])
sel = (dist > 0.0) & (dist < 30)
d = dist[sel]
c = rgb[sel]
lab_c = kit.srgb_to_lab(c)


def comp(r, a, G):
    """Composite colour at distances d, with 1-px box anti-aliasing of each layer edge."""
    keep = np.ones(len(d))
    for ri, ai in zip(r, a):
        cov = np.clip(ri - d + 0.5, 0, 1)
        keep *= 1 - ai * cov
    return bg + (1 - keep)[:, None] * (G - bg)[None]


def loss(r, a, G):
    p = comp(r, a, G)
    return float(kit.de2000(lab_c, kit.srgb_to_lab(p)).mean())


def fit(N, G, iters=2500, seed=0):
    rng = np.random.default_rng(seed)
    r = np.linspace(3, 18, N) if N > 1 else np.array([8.0])
    a = np.full(N, 0.6 / N + 0.1)
    best = loss(r, a, G)
    step_r, step_a = 2.0, 0.1
    for it in range(iters):
        r2 = np.clip(r + rng.normal(0, step_r, N) * (rng.random(N) < 0.5), 0.3, 30)
        a2 = np.clip(a + rng.normal(0, step_a, N) * (rng.random(N) < 0.5), 0.01, 1)
        l2 = loss(r2, a2, G)
        if l2 < best:
            r, a, best = r2, a2, l2
        if it % 500 == 499:
            step_r *= 0.6; step_a *= 0.6
    o = np.argsort(r)
    return r[o], a[o], best


if __name__ == '__main__':
    dirn = np.array([-0.965, -0.255, -0.045])
    for k in (230, 250):
        G = np.clip(bg + k * dirn, 0, 255)
        for N in (1, 2, 3, 4, 5):
            r, a, l = fit(N, G)
            print('G %s k %d N %d  dE mean %.2f  r %s  a %s' % (kit.rgbhex(G), k, N, l, np.round(r, 2), np.round(a, 3)))
