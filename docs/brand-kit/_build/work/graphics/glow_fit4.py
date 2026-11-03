"""Scratch: fit a Gaussian-edge falloff A(d) = A0/2 erfc((d-mu)/(sigma sqrt2)) to the wave's glow and
sample it into N nested offset copies at equal alpha steps (an expanded Illustrator blend)."""
import math
import sys
import numpy as np
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
bg = np.array([245.0, 249.0, 252.0])
erfc = np.vectorize(math.erfc)


def A_model(d, A0, mu, sig):
    return A0 * 0.5 * erfc((d - mu) / (sig * math.sqrt(2)))


def load_samples():
    im = kit.load('02').astype(float)
    dist = np.load(W + r'\glow_dist.npy')
    rgb = im[470:470 + dist.shape[0], 1000:1000 + dist.shape[1]]
    sel = (dist > 0.0) & (dist < 28)
    return dist[sel], rgb[sel]


def fit_profile(d, c, G):
    span = np.linalg.norm(G - bg)
    u = (G - bg) / span
    A = np.clip(((c - bg) @ u) / span, 0, 1)
    best = None
    for A0 in np.linspace(0.6, 1.0, 41):
        for mu in np.linspace(0, 10, 51):
            for sig in np.linspace(3, 10, 36):
                e = float(((A_model(np.array([0.5, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]), A0, mu, sig) -
                            np.array([np.mean(A[np.abs(d - x) < 0.5]) for x in (0.5, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20)])) ** 2).sum())
                if best is None or e < best[0]:
                    best = (e, A0, mu, sig)
    return best[1:]


def layers(A0, mu, sig, N, d_in=0.5):
    """N nested copies: returns [(radius, opacity)] outermost first. The composite alpha inside ring k
    equals the model at the ring's middle, so each step adds the same alpha."""
    dd = np.linspace(-5, 40, 9001)
    Am = A_model(dd, A0, mu, sig)
    a_in = float(A_model(np.array([d_in]), A0, mu, sig)[0])
    lv = a_in * np.arange(1, N + 1) / N  # alpha at ring boundaries, outer..inner reached at d=0
    # boundary radius for level l: where the model crosses l (model decreases with d)
    radii = [float(np.interp(-l, -Am, dd)) for l in (a_in * (np.arange(N) + 0.5) / N)]
    radii = sorted(radii, reverse=True)
    targets = [a_in * (k + 1) / N for k in range(N)]
    out, prev = [], 0.0
    for r, t in zip(radii, targets):
        out.append((max(r, 0.4), 1 - (1 - t) / (1 - prev)))
        prev = t
    return out


def evaluate(d, c, G, L):
    out = np.tile(bg, (len(d), 1))
    for r, a in L:
        cov = (a * np.clip(r - d + 0.5, 0, 1))[:, None]
        out = out * (1 - cov) + G[None] * cov
    de = kit.de2000(kit.srgb_to_lab(c), kit.srgb_to_lab(out))
    return float(de.mean()), float(np.percentile(de, 95))


if __name__ == '__main__':
    d, c = load_samples()
    G = kit.hexrgb(sys.argv[1] if len(sys.argv) > 1 else '#17BEF2')
    A0, mu, sig = fit_profile(d, c, G)
    print('A0 %.3f mu %.2f sigma %.2f' % (A0, mu, sig))
    for N in (6, 8, 10):
        L = layers(A0, mu, sig, N)
        print(N, 'dE mean %.2f p95 %.2f' % evaluate(d, c, G, L), [(round(r, 2), round(a, 4)) for r, a in L])
