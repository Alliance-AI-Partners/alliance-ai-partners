"""Montserrat text-run fitting for the brand board (original 02).

For every text run of the board: estimate the original's ink coverage (alpha) by unmixing each pixel
between the background and the run's ink(s), then search Montserrat style / size / tracking / x /
baseline (kit.text_paths geometry) to maximise mask IoU against it. Rasterisation is our own exact
centre-sampled even-odd scanline fill (PIL's polygon fill fattens shapes by one sub-pixel).
"""
import json
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

STYLES = ["Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"]
G = kit.glyphs()
BG = np.array([245.2, 249.4, 252.6])          # measured board background (median of flat blocks)

_polys = {}


def glyph_polys(style, ch):
    """Glyph contours at 100 pt as float arrays (closed polylines), cached."""
    key = (style, ch)
    if key not in _polys:
        subs = kit.parse_d(G["weights"][style]["chars"][ch]["d"])
        _polys[key] = [np.asarray(p, float) for p in kit.flatten(subs, tol=0.03) if len(p) >= 3]
    return _polys[key]


def layout(string, style):
    return G["weights"][style]["strings"][string]


def fill_evenodd(contours, W, H):
    """Exact centre-sampled even-odd fill of polygons (list of (n,2) arrays, canvas units) -> bool (H, W)."""
    out = np.zeros((H, W), bool)
    if not contours:
        return out
    P = np.concatenate([np.stack([c, np.roll(c, -1, 0)], 1) for c in contours], 0)  # (E, 2, 2)
    x0, y0, x1, y1 = P[:, 0, 0], P[:, 0, 1], P[:, 1, 0], P[:, 1, 1]
    keep = y0 != y1
    x0, y0, x1, y1 = x0[keep], y0[keep], x1[keep], y1[keep]
    ylo, yhi = np.minimum(y0, y1), np.maximum(y0, y1)
    j0 = np.clip(np.ceil(ylo - 0.5).astype(int), 0, H)
    j1 = np.clip(np.ceil(yhi - 0.5).astype(int), 0, H)
    n = np.maximum(j1 - j0, 0)
    tot = int(n.sum())
    if tot == 0:
        return out
    e = np.repeat(np.arange(len(x0)), n)
    j = j0[e] + (np.arange(tot) - (np.cumsum(n) - n)[e])
    ys = j + 0.5
    xc = x0[e] + (ys - y0[e]) * (x1[e] - x0[e]) / (y1[e] - y0[e])
    k = np.clip(np.ceil(xc - 0.5).astype(int), 0, W)
    diff = np.bincount(j * (W + 1) + k, minlength=H * (W + 1)).reshape(H, W + 1)
    return (np.cumsum(diff, 1)[:, :W] & 1).astype(bool)


def run_glyphs(string, style, size, track, x, base, offs=None):
    """[(char, idx, contours at final position in image px)] for a run (same geometry as kit.text_paths),
    optionally with an extra x offset per glyph (manual kerning, px)."""
    k = size / 100.0
    out = []
    for n, (ch, idx, dx) in enumerate(layout(string, style)):
        sx = x + dx * k + idx * track / 1000.0 * size + (0.0 if offs is None else offs[n])
        out.append((ch, idx, [np.column_stack([p[:, 0] * k + sx, p[:, 1] * k + base]) for p in glyph_polys(style, ch)]))
    return out


def coverage(glyphs, box, ss=4, only=None):
    """Union of the glyphs' even-odd fills as a coverage map over box=(x0,y0,x1,y1), ss x ss samples per px."""
    bx0, by0, bx1, by1 = box
    W, H = (bx1 - bx0) * ss, (by1 - by0) * ss
    canvas = np.zeros((H, W), bool)
    for ch, idx, cons in glyphs:
        if only is not None and idx not in only:
            continue
        cs = [(c - [bx0, by0]) * ss for c in cons]
        allp = np.concatenate(cs, 0)
        gx0, gy0 = max(0, int(np.floor(allp[:, 0].min())) - 1), max(0, int(np.floor(allp[:, 1].min())) - 1)
        gx1, gy1 = min(W, int(np.ceil(allp[:, 0].max())) + 2), min(H, int(np.ceil(allp[:, 1].max())) + 2)
        if gx1 <= gx0 or gy1 <= gy0:
            continue
        m = fill_evenodd([c - [gx0, gy0] for c in cs], gx1 - gx0, gy1 - gy0)
        canvas[gy0:gy1, gx0:gx1] |= m
    return canvas.reshape(H // ss, ss, W // ss, ss).mean((1, 3))


def unmix(rgb, inks, bg=BG):
    """Per-pixel coverage of the best-fitting ink (line bg->ink in RGB) -> (alpha, ink index)."""
    rgb = np.asarray(rgb, float)
    best_r, alpha, which = None, None, None
    for i, ink in enumerate(inks):
        v = np.asarray(ink, float) - bg
        t = np.clip(((rgb - bg) @ v) / (v @ v), 0, 1)
        r = np.linalg.norm(rgb - (bg + t[..., None] * v), axis=-1)
        if best_r is None:
            best_r, alpha, which = r, t, np.zeros(t.shape, int)
        else:
            sel = r < best_r
            best_r = np.where(sel, r, best_r)
            alpha = np.where(sel, t, alpha)
            which = np.where(sel, i, which)
    return alpha, which


def soft_iou(a, b):
    return float(np.minimum(a, b).sum() / max(1e-9, np.maximum(a, b).sum()))


def bin_iou(a, b):
    return kit.iou(a >= 0.5, b >= 0.5)


def bbox_of(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def glyph_extent(glyphs):
    allp = np.concatenate([c for _, _, cons in glyphs for c in cons], 0)
    return allp[:, 0].min(), allp[:, 1].min(), allp[:, 0].max(), allp[:, 1].max()


def nelder_mead(f, x0, steps, iters=220, tol=1e-6):
    n = len(x0)
    pts = [np.asarray(x0, float)] + [np.asarray(x0, float) + np.eye(n)[i] * steps[i] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = np.argsort(vals)
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol:
            break
        c = np.mean(pts[:-1], 0)
        xr = c + (c - pts[-1]); fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1]); fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    i = int(np.argmin(vals))
    return pts[i], vals[i]


class Run:
    def __init__(self, rid, string, box, inks, ink_of=None, styles=STYLES, cut=0.25):
        """inks: list of RGB inks; ink_of: {glyph idx: ink index} (default ink 0)."""
        self.rid, self.string, self.box = rid, string, tuple(box)
        self.inks = [np.asarray(i, float) for i in inks]
        self.ink_of = ink_of or {}
        self.styles = styles
        self.cut = cut
        self.refresh()

    def refresh(self, img=None):
        img = kit.load('02') if img is None else img
        x0, y0, x1, y1 = self.box
        self.rgb = img[y0:y1, x0:x1].astype(float)
        a, w = unmix(self.rgb, self.inks)
        a = np.where(a < self.cut, 0.0, a)
        self.alpha, self.which = a, w

    def params_for_size(self, style, size):
        """x / baseline / tracking that put the run's ink bbox on the original's for a given size."""
        m = self.alpha >= 0.5
        mx0, my0, mx1, my1 = bbox_of(m)
        mx0 += self.box[0]; mx1 += self.box[0]; my0 += self.box[1]; my1 += self.box[1]
        g = run_glyphs(self.string, style, 100, 0, 0, 0)
        gx0, gy0, gx1, gy1 = glyph_extent(g)
        k = size / 100
        last = max(idx for _, idx, _ in g)
        track = ((mx1 - mx0) - (gx1 - gx0) * k) / max(1, last) / size * 1000 if last else 0.0
        base = (my0 + my1) / 2 - (gy0 + gy1) / 2 * k
        return np.array([size, track, mx0 - gx0 * k, base])

    def init_params(self, style):
        m = self.alpha >= 0.5
        _, my0, _, my1 = bbox_of(m)
        gy0, gy1 = glyph_extent(run_glyphs(self.string, style, 100, 0, 0, 0))[1::2]
        return self.params_for_size(style, 100 * (my1 - my0) / (gy1 - gy0))

    def render(self, style, p, ss=4, offs=None):
        g = run_glyphs(self.string, style, p[0], p[1], p[2], p[3], offs)
        return coverage(g, self.box, ss)

    def fit_style(self, style, iters=200, offs=None, fix_size=None):
        if fix_size is not None:
            # size shared with the run's group: search tracking / x / baseline only
            f3 = lambda q: 1 - soft_iou(self.alpha, self.render(style, [fix_size, q[0], q[1], q[2]], offs=offs))
            q0 = self.params_for_size(style, fix_size)[1:]
            q, v = nelder_mead(f3, q0, [6.0, 0.5, 0.5], iters)
            q, v = nelder_mead(f3, q, [2.0, 0.15, 0.15], iters // 2)
            p = np.array([fix_size, *q])
            r = self.render(style, p, offs=offs)
            return {"style": style, "size": float(p[0]), "tracking": float(p[1]), "x": float(p[2]), "baseline": float(p[3]),
                    "iou_soft": 1 - float(v), "iou": bin_iou(self.alpha, r)}
        f = lambda p: 1 - soft_iou(self.alpha, self.render(style, p, offs=offs))
        p0 = self.init_params(style)
        # coarse size grid (bbox-consistent x / tracking / baseline for each size), keep the best three starts
        grid = sorted(((f(q), tuple(q)) for q in (self.params_for_size(style, p0[0] * s) for s in np.arange(0.92, 1.0801, 0.01))))
        best = None
        for v0, q in grid[:3]:
            q = np.array(q)
            steps = [q[0] * 0.015, 6.0, 0.5, 0.5]
            p, v = nelder_mead(f, q, steps, iters)
            p, v = nelder_mead(f, p, [s * 0.3 for s in steps], iters // 2)
            if best is None or v < best[1]:
                best = (p, v)
        p, v = best
        r = self.render(style, p, offs=offs)
        return {"style": style, "size": float(p[0]), "tracking": float(p[1]), "x": float(p[2]), "baseline": float(p[3]),
                "iou_soft": 1 - float(v), "iou": bin_iou(self.alpha, r)}

    def fit(self, styles=None, verbose=True):
        res = []
        for st in (styles or self.styles):
            r = self.fit_style(st)
            res.append(r)
            if verbose:
                print('   %-9s size=%6.2f track=%7.1f x=%7.2f base=%7.2f  soft=%.4f bin=%.4f' % (
                    st, r["size"], r["tracking"], r["x"], r["baseline"], r["iou_soft"], r["iou"]))
        best = max(res, key=lambda r: r["iou_soft"])
        self.best, self.all = best, res
        return best

    # ------------------------------------------------------------ manual kerning (per-glyph x offsets)

    def fit_offsets(self, style, p, offs=None, rng=1.6, step=0.1, passes=2, lam=0.002):
        """Coordinate descent on per-glyph x offsets (px), each glyph scored by soft IoU in its own window."""
        lay = layout(self.string, style)
        n = len(lay)
        offs = np.zeros(n) if offs is None else np.array(offs, float)
        gl = run_glyphs(self.string, style, p[0], p[1], p[2], p[3], offs)
        covs = [coverage([gl[i]], self.box) for i in range(n)]
        total = np.sum(covs, 0)
        bx0 = self.box[0]
        W = self.alpha.shape[1]
        for _ in range(passes):
            for i in range(n):
                cons = gl[i][2]
                xs = np.concatenate([c[:, 0] for c in cons])
                w0 = max(0, int(np.floor(xs.min() - bx0 - rng - 2)))
                w1 = min(W, int(np.ceil(xs.max() - bx0 + rng + 2)))
                others = (total - covs[i])[:, w0:w1]
                al = self.alpha[:, w0:w1]
                best = None
                for d in np.arange(-rng, rng + 1e-9, step):
                    g1 = (gl[i][0], gl[i][1], [c + [d, 0] for c in cons])
                    ci = coverage([g1], self.box)
                    sc = soft_iou(al, np.clip(others + ci[:, w0:w1], 0, 1)) - lam * abs(offs[i] + d)
                    if best is None or sc > best[0]:
                        best = (sc, d, ci)
                _, d, ci = best
                if d != 0:
                    offs[i] += d
                    gl[i] = (gl[i][0], gl[i][1], [c + [d, 0] for c in cons])
                    total = total - covs[i] + ci
                    covs[i] = ci
        return offs

    def fit_kerned(self, style, p0, verbose=True, fix_size=None):
        """Global fit -> per-glyph offsets -> global refit with offsets -> offsets again."""
        p = np.array([p0["size"], p0["tracking"], p0["x"], p0["baseline"]])
        offs = self.fit_offsets(style, p)
        r = self.fit_style(style, offs=offs, fix_size=fix_size)
        p = np.array([r["size"], r["tracking"], r["x"], r["baseline"]])
        offs = self.fit_offsets(style, p, offs, rng=0.8, step=0.05, passes=1)
        cov = self.render(style, p, offs=offs)
        lay = layout(self.string, style)
        # Illustrator manual kerning (1/1000 em) at each glyph's character index; the first offset folds into x
        kern = {str(lay[i][1]): round(float((offs[i] - offs[i - 1]) * 1000.0 / p[0]), 1) for i in range(1, len(lay))}
        out = {"style": style, "size": float(p[0]), "tracking": float(p[1]), "x": float(p[2]), "baseline": float(p[3]),
               "offsets_px": [round(float(o), 3) for o in offs], "kerning": kern,
               "iou_soft": soft_iou(self.alpha, cov), "iou": bin_iou(self.alpha, cov)}
        if verbose:
            print('   kerned %-9s size=%6.2f track=%7.1f soft=%.4f bin=%.4f  max|off|=%.2f' % (
                style, out["size"], out["tracking"], out["iou_soft"], out["iou"], np.abs(offs).max()))
        return out
