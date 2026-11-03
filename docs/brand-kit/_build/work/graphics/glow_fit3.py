"""Scratch: smooth glow as N nested offset copies (an expanded blend). Radii put at equal alpha steps
of the measured falloff; opacities refined by coordinate descent on the pixels around the wave."""
import sys
import numpy as np
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
im = kit.load('02').astype(float)
dist = np.load(W + r'\glow_dist.npy')
X0, Y0 = 1000, 470
rgb = im[Y0:Y0 + dist.shape[0], X0:X0 + dist.shape[1]]
bg = np.array([245.0, 249.0, 252.0])
sel = (dist > 0.0) & (dist < 28)
d = dist[sel]
c = rgb[sel]
lab_c = kit.srgb_to_lab(c)


def composite(r, a, G):
    out = np.tile(bg, (len(d), 1))
    for ri, ai, gi in zip(r, a, G):  # outermost first
        cov = (ai * np.clip(ri - d + 0.5, 0, 1))[:, None]
        out = out * (1 - cov) + np.asarray(gi)[None] * cov
    return out


def run(N, G_hex):
    G = kit.hexrgb(G_hex)
    span = np.linalg.norm(G - bg)
    # measured alpha profile (projection on the bg->G direction), binned
    u = (G - bg) / span
    A = np.clip(((c - bg) @ u) / span, 0, 1)
    edges = np.arange(0, 28.5, 0.5)
    mids = (edges[:-1] + edges[1:]) / 2
    prof = np.array([A[(d >= lo) & (d < hi)].mean() if ((d >= lo) & (d < hi)).any() else 0 for lo, hi in zip(edges[:-1], edges[1:])])
    prof = np.minimum.accumulate(prof)  # monotone
    A0 = prof[0]
    levels = A0 * np.arange(1, N) / N  # ring boundaries at equal alpha steps
    radii = [float(np.interp(-lv, -prof, mids)) for lv in levels[::-1]]  # increasing alpha -> decreasing d
    r_out = float(np.interp(-A0 / (2 * N), -prof, mids))
    r = np.array([r_out] + radii)  # outermost first, decreasing
    targets = A0 * (np.arange(N) + 0.5) / N
    a = np.empty(N)
    prev = 0.0
    for k in range(N):
        a[k] = 1 - (1 - targets[k]) / (1 - prev)
        prev = targets[k]
    Gs = [G] * N

    def loss(a):
        p = composite(r, a, Gs)
        return float(((p - c) ** 2).sum(1).mean())

    best = loss(a)
    for sweep in range(6):
        for k in range(N):
            for step in (0.02, 0.005, 0.001):
                for sgn in (1, -1):
                    while True:
                        t = a.copy(); t[k] = np.clip(t[k] + sgn * step, 0.001, 1)
                        l = loss(t)
                        if l < best - 1e-9:
                            a, best = t, l
                        else:
                            break
    p = composite(r, a, Gs)
    de = kit.de2000(lab_c, kit.srgb_to_lab(p))
    return r, a, float(de.mean()), float(np.percentile(de, 95))


if __name__ == '__main__':
    for G in sys.argv[1:] or ['#17BEF2']:
        for N in (2, 6, 8, 10, 12):
            r, a, m, p95 = run(N, G)
            print(G, 'N', N, 'dE mean %.2f p95 %.2f' % (m, p95), 'r', np.round(r, 2).tolist(), 'a', np.round(a, 4).tolist())
