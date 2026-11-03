"""Scratch: glow layers with a colour per layer (linear LSQ for colours given geometry), plus the
profile-only noise floor."""
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

# floor: per-distance-bin mean colour
bins = np.floor(d * 4).astype(int)
mean = np.zeros_like(c)
for b in np.unique(bins):
    m = bins == b
    mean[m] = c[m].mean(0)
print('profile-only floor dE mean %.2f' % kit.de2000(lab_c, kit.srgb_to_lab(mean)).mean())


def weights(r, a):
    """Composite = bg + sum_i w_i (G_i - bg), layers painted outermost first."""
    N = len(r)
    cov = [a[i] * np.clip(r[i] - d + 0.5, 0, 1) for i in range(N)]
    w = []
    for i in range(N):
        rest = np.ones(len(d))
        for j in range(i + 1, N):  # layers painted after i (inner ones) attenuate it
            rest *= 1 - cov[j]
        w.append(cov[i] * rest)
    return np.stack(w, -1)


def solve(r, a):
    w = weights(r, a)
    G, *_ = np.linalg.lstsq(w, c - bg, rcond=None)
    G = np.clip(G + bg, 0, 255)
    pred = bg + w @ (G - bg)
    return G, float(kit.de2000(lab_c, kit.srgb_to_lab(pred)).mean())


def fit(N, iters=400, seed=1):
    rng = np.random.default_rng(seed)
    r = np.linspace(4, 16, N) if N > 1 else np.array([10.0])
    a = np.full(N, 0.35)
    G, best = solve(r, a)
    sr, sa = 2.0, 0.12
    for it in range(iters):
        r2 = np.sort(np.clip(r + rng.normal(0, sr, N), 0.5, 30))[::-1]
        a2 = np.clip(a + rng.normal(0, sa, N), 0.05, 1)
        G2, l2 = solve(r2, a2)
        if l2 < best:
            r, a, G, best = r2, a2, G2, l2
        if it % 100 == 99:
            sr *= 0.6; sa *= 0.6
    return r, a, G, best


if __name__ == '__main__':
    for N in (1, 2, 3):
        r, a, G, l = fit(N)
        print('N %d dE %.2f r %s a %s G %s' % (N, l, np.round(r, 2), np.round(a, 3), [kit.rgbhex(g) for g in G]))
