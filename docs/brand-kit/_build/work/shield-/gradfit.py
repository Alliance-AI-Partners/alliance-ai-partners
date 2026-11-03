# Linear-gradient fitting for one face: best direction + piecewise-linear stops (sRGB, pad spread).
import numpy as np
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit


def _hat(tb, offs):
    """Interpolation weights of bin positions tb (0..1) on stops at offs (pad outside)."""
    K = len(offs)
    A = np.zeros((len(tb), K))
    if K == 1:
        A[:, 0] = 1
        return A
    t = np.clip(tb, offs[0], offs[-1])
    k = np.clip(np.searchsorted(offs, t, side='right') - 1, 0, K - 2)
    w = (t - offs[k]) / np.maximum(offs[k + 1] - offs[k], 1e-9)
    A[np.arange(len(t)), k] = 1 - w
    A[np.arange(len(t)), k + 1] += w
    return A


def _solve(tb, nb, mb, offs):
    A = _hat(tb, offs)
    Aw = A * nb[:, None]
    M = A.T @ Aw + 1e-6 * np.eye(len(offs))
    C = np.linalg.solve(M, Aw.T @ mb)
    C = np.clip(C, 0, 255)
    sse = float((nb[:, None] * (A @ C - mb) ** 2).sum())
    return C, sse


def _bins(t, rgb, nbins):
    edges = np.linspace(0, 1, nbins + 1)
    idx = np.clip((t * nbins).astype(int), 0, nbins - 1)
    nb = np.bincount(idx, minlength=nbins).astype(float)
    mb = np.stack([np.bincount(idx, rgb[:, c], minlength=nbins) for c in range(3)], 1)
    keep = nb > 0
    mb = mb[keep] / nb[keep, None]
    tb = ((edges[:-1] + edges[1:]) / 2)[keep]
    return tb, nb[keep], mb


def _opt_offsets(tb, nb, mb, K):
    offs = np.linspace(0, 1, K)
    C, best = _solve(tb, nb, mb, offs)
    step = 0.08
    while step > 0.002:
        improved = False
        for i in range(K):
            for d in (-step, step):
                o = offs.copy()
                o[i] += d
                lo = o[i - 1] + 0.01 if i > 0 else 0.0
                hi = o[i + 1] - 0.01 if i < K - 1 else 1.0
                if not (lo <= o[i] <= hi):
                    continue
                C2, s = _solve(tb, nb, mb, o)
                if s < best - 1e-9:
                    offs, C, best, improved = o, C2, s, True
        if not improved:
            step /= 2
    return offs, C, best


def fit(xy, rgb, max_stops=5, theta_step=3.0, lab_tol=0.35):
    """xy (N,2) pixel centers, rgb (N,3) 0..255. Returns dict with p1, p2, stops [(off, rgb)], pred, de."""
    xy, rgb = np.asarray(xy, float), np.asarray(rgb, float)
    c0 = xy.mean(0)
    best = None

    sq = (rgb ** 2).sum(1)

    def eval_theta(th):
        """Score = within-bin SSE (residual of the best arbitrary colour profile along this direction)
        with bins of ~1 px, so the direction is chosen independently of the number of stops."""
        u = np.array([np.cos(th), np.sin(th)])
        t = (xy - c0) @ u
        t0, t1 = t.min(), t.max()
        tn = (t - t0) / max(t1 - t0, 1e-6)
        nbins = int(np.clip((t1 - t0), 8, 600))
        tb, nb, mb = _bins(tn, rgb, nbins)
        s = float(sq.sum() - (nb[:, None] * mb ** 2).sum())
        return s, (u, t0, t1, tn, tb, nb, mb)

    ths = np.deg2rad(np.arange(0, 180, theta_step))
    scores = [eval_theta(th)[0] for th in ths]
    th0 = ths[int(np.argmin(scores))]
    fine = th0 + np.deg2rad(np.arange(-theta_step, theta_step + 1e-9, 0.25))
    th = fine[int(np.argmin([eval_theta(t)[0] for t in fine]))]
    _, (u, t0, t1, tn, tb, nb, mb) = eval_theta(th)
    lab = kit.srgb_to_lab(rgb)
    results = []
    for K in range(1, max_stops + 1):
        offs, C, s = _opt_offsets(tb, nb, mb, K)
        pred = _hat(tn, offs) @ C
        de = float(kit.de2000(lab, kit.srgb_to_lab(pred)).mean())
        results.append((K, offs, C, de, pred))
    # smallest K whose mean dE is within lab_tol of the best (more stops only when they clearly help)
    bde = min(r[3] for r in results)
    K, offs, C, de, pred = next(r for r in results if r[3] <= bde + lab_tol)
    p1 = c0 + t0 * u
    p2 = c0 + t1 * u
    return {'theta_deg': float(np.rad2deg(th)), 'p1': p1, 'p2': p2, 'u': u, 't0': t0, 't1': t1, 'c0': c0,
            'offs': offs, 'cols': C, 'de': de, 'pred': pred, 'all': [(r[0], r[3]) for r in results]}


def eval_grad(xy, p1, p2, offs, cols):
    v = np.asarray(p2, float) - np.asarray(p1, float)
    t = (np.asarray(xy, float) - p1) @ v / max(v @ v, 1e-9)
    return _hat(t, np.asarray(offs, float)) @ np.asarray(cols, float)
