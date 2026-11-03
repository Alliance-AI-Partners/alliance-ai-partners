"""Type fitting for the Alliance AI Partners originals (agent prefix text-).

Re-sets every text run of the originals in Illustrator's own Montserrat outlines (kit.text_paths) and fits
style / size / tracking / x / baseline to the original's anti-aliased text coverage.
Run:  python work/type/run_fit.py [ids...]   -> fit/text-<id>.json, verify/text-<id>_overlay.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BUILD = Path(r"C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build")
sys.path.insert(0, str(BUILD))
import kit  # noqa: E402

WORK = BUILD / "work" / "type"
STYLES = ["Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"]
P = kit.PALETTE
NAVY, BLUE, CYAN, WHITE = P["Deep Navy"], P["Vibrant Blue"], P["Bright Cyan"], P["Pure White"]

# Each run: string, search box (x0, y0, x1, y1) in source px that holds only this run's ink (from row/column
# ink profiles, ~6 px margin), the foreground color guesses used to un-mix anti-aliasing, the semantic
# alignment of the lockup, and the char ranges that carry an accent color.
RUNS = {
    "01": [dict(s="ALLIANCE AI PARTNERS", box=(510, 330, 1278, 391), fg=[NAVY, BLUE], align="left"),
           dict(s="Partners in AI. Partners in growth.", box=(512, 396, 1170, 446), fg=[NAVY], align="left")],
    "04": [dict(s="ALLIANCE", box=(612, 286, 1203, 381), fg=[WHITE], align="left"),
           dict(s="AI PARTNERS", box=(612, 393, 1203, 467), fg=[WHITE], align="left")],
    "05": [dict(s="ALLIANCE", box=(400, 466, 976, 570), fg=[NAVY], align="center"),
           dict(s="AI PARTNERS", box=(400, 573, 976, 645), fg=[NAVY], align="center")],
    "07": [dict(s="ALLIANCE AI", box=(564, 287, 1246, 378), fg=[WHITE], align="left"),
           dict(s="PARTNERS", box=(564, 388, 1160, 481), fg=[WHITE], align="left")],
    "08": [dict(s="ALLIANCE", box=(576, 233, 1288, 350), fg=[NAVY], align="left"),
           dict(s="AI PARTNERS", box=(577, 362, 1287, 455), fg=[NAVY, CYAN], align="left")],
    "09": [dict(s="ALLIANCE AI", box=(112, 558, 910, 664), fg=[WHITE], align="center"),
           dict(s="PARTNERS", box=(176, 672, 850, 777), fg=[WHITE], align="center")],
    "10": [dict(s="ALLIANCE", box=(522, 278, 1272, 391), fg=[WHITE], align="left"),
           dict(s="AI PARTNERS", box=(523, 396, 1272, 489), fg=[WHITE], align="left")],
    "13": [dict(s="ALLIANCE AI PARTNERS", box=(485, 317, 1297, 390), fg=[NAVY, BLUE], align="left"),
           dict(s="ENTERPRISE AI CONSULTING", box=(485, 412, 1295, 475), fg=[NAVY], align="left")],
    "14": [dict(s="ALLIANCE AI PARTNERS", box=(97, 650, 926, 718), fg=[NAVY, BLUE], align="center")],
    "16": [dict(s="ALLIANCE AI", box=(126, 590, 896, 691), fg=[WHITE], align="center"),
           dict(s="PARTNERS", box=(195, 706, 831, 806), fg=[WHITE], align="center")],
    "17": [dict(s="ALLIANCE AI PARTNERS", box=(293, 500, 1082, 562), fg=[NAVY, BLUE], align="center")],
}
RULES = {"13": dict(box=(485, 393, 1297, 410), fg=CYAN)}


# ------------------------------------------------------------------ coverage extraction

def bg_field(crop):
    """Smooth background estimate: plane fit (per channel) to the pixels close to the border median."""
    lab = kit.srgb_to_lab(crop)
    h, w = crop.shape[:2]
    border = np.concatenate([crop[:2].reshape(-1, 3), crop[-2:].reshape(-1, 3), crop[:, :2].reshape(-1, 3), crop[:, -2:].reshape(-1, 3)])
    b0 = np.median(border, 0)
    sel = kit.de2000(lab, kit.srgb_to_lab(b0)) < 8
    yy, xx = np.mgrid[0:h, 0:w]
    A = np.stack([np.ones(sel.sum()), xx[sel] / w, yy[sel] / h], 1)
    coef = np.linalg.lstsq(A, crop[sel], rcond=None)[0]
    return coef[0] + (xx / w)[..., None] * coef[1] + (yy / h)[..., None] * coef[2], b0


def coverage(crop, bg, fgs):
    """Per-pixel ink coverage alpha in 0..1 and the index of the foreground color that explains it:
    pixel = alpha * fg_k + (1 - alpha) * bg, with k picked by the smallest residual."""
    best_a = np.zeros(crop.shape[:2])
    best_r = np.full(crop.shape[:2], np.inf)
    best_k = np.zeros(crop.shape[:2], int)
    for k, f in enumerate(fgs):
        v = np.asarray(f, float) - bg
        a = np.clip(((crop - bg) * v).sum(-1) / np.maximum((v * v).sum(-1), 1e-6), 0, 1)
        r = np.linalg.norm(crop - bg - a[..., None] * v, axis=-1)
        better = r < best_r
        best_a[better], best_r[better], best_k[better] = a[better], r[better], k
    return best_a, best_k


def measure_fg(crop, bg, guesses, iters=4):
    """Refine foreground colors from the strongly-inked pixels (k-means seeded by the palette guesses)."""
    fgs = [kit.hexrgb(g) for g in guesses]
    for _ in range(iters):
        a, k = coverage(crop, bg, fgs)
        for j in range(len(fgs)):
            sel = (a > 0.9) & (k == j)
            if sel.sum() > 30:
                fgs[j] = np.median(crop[sel], 0)
    return fgs


# ------------------------------------------------------------------ geometry

def string_bbox(s, style):
    """Ink bbox (x0, y0, x1, y1) of the string at 100 pt, tracking 0, origin (0, 0)."""
    pts = np.concatenate([np.array(p) for d in kit.text_paths(s, style) for p in kit.flatten(kit.parse_d(d), 0.05)])
    return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()


_POLY = {}


def glyph_polys(style, ch):
    """Flattened contours of one glyph at 100 pt (cached); flattening commutes with scale + shift."""
    key = (style, ch)
    if key not in _POLY:
        d = kit.glyphs()["weights"][style]["chars"][ch]["d"]
        _POLY[key] = [np.array(p, float) for p in kit.flatten(kit.parse_d(d), 0.02) if len(p) >= 3]
    return _POLY[key]


def layout(s, style, size, tracking, x, base):
    """[(ch, char index, x origin)] exactly as kit.text_paths places them."""
    k = size / 100.0
    return [(ch, idx, x + dx * k + idx * tracking / 1000.0 * size)
            for ch, idx, dx in kit.glyphs()["weights"][style]["strings"][s]]


def fast_raster(s, style, size, tracking, x, base, w, h, ss=4, only=None, shifts=None):
    """Same fill rule and supersampling as kit.raster (even-odd per glyph, union across glyphs), but each
    glyph is filled in its own small window from cached flattened contours (~5x faster, for the search;
    every reported number uses kit.raster). only: optional set of char indices to draw;
    shifts: optional {char index: dx px} for the per-glyph spacing diagnostic."""
    acc = np.zeros((h * ss, w * ss), bool)
    k = size / 100.0
    for ch, idx, ox in layout(s, style, size, tracking, x, base):
        if only is not None and idx not in only:
            continue
        ox += (shifts or {}).get(idx, 0.0)
        polys = [(p * k + (ox, base)) * ss for p in glyph_polys(style, ch)]
        allp = np.concatenate(polys)
        gx0, gy0 = int(np.floor(allp[:, 0].min())) - 1, int(np.floor(allp[:, 1].min())) - 1
        gx1, gy1 = int(np.ceil(allp[:, 0].max())) + 2, int(np.ceil(allp[:, 1].max())) + 2
        cx0, cy0, cx1, cy1 = max(gx0, 0), max(gy0, 0), min(gx1, w * ss), min(gy1, h * ss)
        if cx1 <= cx0 or cy1 <= cy0:
            continue
        m = np.zeros((gy1 - gy0, gx1 - gx0), bool)
        for p in polys:
            img = Image.new("1", (gx1 - gx0, gy1 - gy0), 0)
            ImageDraw.Draw(img).polygon([tuple(v) for v in (p - (gx0, gy0))], fill=1)
            m ^= np.asarray(img, bool)
        acc[cy0:cy1, cx0:cx1] |= m[cy0 - gy0:cy1 - gy0, cx0 - gx0:cx1 - gx0]
    return acc.reshape(h, ss, w, ss).mean((1, 3))


def render(s, style, size, tracking, x, base, box, ss=4, **kw):
    x0, y0, x1, y1 = box
    return fast_raster(s, style, size, tracking, x - x0, base - y0, x1 - x0, y1 - y0, ss=ss, **kw)


def kit_render(s, style, p, box):
    """The reported coverage: kit.raster of kit.text_paths, in the box."""
    x0, y0, x1, y1 = box
    return kit.raster(kit.text_paths(s, style, p[0], p[1], p[2] - x0, p[3] - y0), x1 - x0, y1 - y0)


def soft_iou(r, a):
    return float(np.minimum(r, a).sum() / max(np.maximum(r, a).sum(), 1e-9))


def ink_bbox(a, thr=0.5):
    ys, xs = np.nonzero(a > thr)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def initial(s, style, a, box):
    """Size from ink height, x/baseline from the ink edges, tracking from the ink width."""
    bx0, by0, bx1, by1 = string_bbox(s, style)
    mx0, my0, mx1, my1 = ink_bbox(a)
    size = 100 * (my1 - my0) / (by1 - by0)
    k = size / 100
    base = box[1] + my1 - by1 * k
    x = box[0] + mx0 - bx0 * k
    n = len(s) - 1
    tracking = ((mx1 - mx0) - (bx1 - bx0) * k) / (n * size / 1000) if n else 0.0
    return [size, tracking, x, base]


def to_q(s, style, p):
    """(size, tracking, x, base) -> (size, x of the last glyph origin, x, base): decorrelated search space."""
    size, tr, x, base = p
    ch, idx, dx = kit.glyphs()["weights"][style]["strings"][s][-1]
    return [size, x + dx * size / 100 + idx * tr / 1000 * size, x, base]


def from_q(s, style, q):
    size, xl, x, base = q
    ch, idx, dx = kit.glyphs()["weights"][style]["strings"][s][-1]
    tr = (xl - x - dx * size / 100) * 1000 / (idx * size) if idx else 0.0
    return [size, tr, x, base]


def fit(s, style, a, box, p0=None, steps=(1.0, 0.5, 0.25, 0.1, 0.05, 0.02), ss=4):
    """Pattern search maximizing soft IoU against the coverage map, over (size, last-glyph x, x, baseline)."""
    q = to_q(s, style, p0 or initial(s, style, a, box))
    cache = {}

    def f(qq):
        key = tuple(round(v, 4) for v in qq)
        if key not in cache:
            cache[key] = soft_iou(render(s, style, *from_q(s, style, qq), box, ss=ss), a)
        return cache[key]

    best = f(q)
    for st in steps:
        improved = True
        while improved:
            improved = False
            for i in range(4):
                for sgn in (1, -1):
                    qq = list(q)
                    qq[i] += sgn * st
                    v = f(qq)
                    if v > best + 1e-6:
                        q, best, improved = qq, v, True
    return from_q(s, style, q), best, len(cache)


def glyph_offsets(s, style, p, a, box, win=4.0, step=0.25):
    """Diagnostic: per glyph, the horizontal shift (px) that best matches the original in that glyph's own
    neighborhood, i.e. how far the original's letter spacing departs from uniform Montserrat tracking."""
    x0, y0, x1, y1 = box
    out = []
    for ch, idx, ox in layout(s, style, *p):
        g = render(s, style, *p, box, only={idx})
        xs = np.nonzero(g.max(0) > 0)[0]
        gx0, gx1 = max(int(xs.min() - win - 1), 0), min(int(xs.max() + win + 2), x1 - x0)
        sub = (x0 + gx0, y0, x0 + gx1, y1)  # render only this glyph's window
        best = (-1.0, 0.0)
        for d in np.arange(-win, win + 1e-9, step):
            v = soft_iou(render(s, style, *p, sub, shifts={idx: d}), a[:, gx0:gx1])
            if v > best[0] + 1e-9:
                best = (v, float(d))
        out.append({"ch": ch, "i": idx, "dx": round(best[1], 2)})
    return out


def stems(cov, s, style, p, box):
    """Mean integrated coverage (px) across the vertical stems of I, L, T, i in the middle third of the
    stem: a blur-independent stroke-weight measure, taken the same way on the original and on renders."""
    x0, y0, x1, y1 = box
    size, tr, x, base = p
    out = []
    for ch, idx, ox in layout(s, style, *p):
        if ch not in "ILTi":
            continue
        g = render(s, style, *p, box, only={idx})
        xs = np.nonzero(g.max(0) > 0.5)[0]
        gx0, gx1 = xs.min(), xs.max() + 1
        if ch == "L":
            gx1 = gx0 + (gx1 - gx0) // 2
        if ch == "T":
            c, hw = (gx0 + gx1) / 2, (gx1 - gx0) * 0.3
            gx0, gx1 = int(c - hw), int(c + hw) + 1
        top = 0.70 * size if ch != "i" else 0.52 * size  # cap height / x-height
        yb = base - y0
        rows = np.arange(int(yb - 0.62 * top), int(yb - 0.38 * top) + 1)
        out.append(float(np.mean([cov[r, max(gx0 - 2, 0):gx1 + 2].sum() for r in rows])))
    return float(np.mean(out)) if out else None


# ------------------------------------------------------------------ driver

def prep(oid, run):
    """Crop, background field, measured foreground colors, soft coverage a, and the fitting target: the
    binary 0.5-isoline mask of a (the quantity IoU measures; insensitive to the JPEG/sharpening halos
    and core clipping that bias the integrated coverage)."""
    rgb = kit.load(oid).astype(float)
    x0, y0, x1, y1 = run["box"]
    crop = rgb[y0:y1, x0:x1]
    bg, b0 = bg_field(crop)
    fgs = measure_fg(crop, bg, run["fg"])
    a, k = coverage(crop, bg, fgs)
    return crop, bg, fgs, a, (a > 0.5).astype(float)


def edge_err(r, m):
    """Mean edge offset in px between two binary masks: |r xor m| / mean perimeter."""
    def perim(b):
        return float((b ^ np.roll(b, 1, 0)).sum() + (b ^ np.roll(b, 1, 1)).sum())
    return float((r ^ m).sum() / max(0.5 * (perim(r) + perim(m)), 1))


def fine_fit(s, st, M, box, p0, spread=0.04, n=9):
    """The soft objective is flat along the size/tracking ridge of long, irregularly spaced AI-made strings, so
    scan the size over +-4 % with both string ends held (q space), polish each start, and keep the start with the
    best binary IoU (fast raster to rank, kit.raster to confirm the top three)."""
    q0 = to_q(s, st, p0)
    cands = []
    for f in np.linspace(1 - spread, 1 + spread, n):
        q = list(q0)
        q[0] *= f
        p, v, k = fit(s, st, M, box, p0=from_q(s, st, q), steps=(0.25, 0.1, 0.05, 0.02))
        cands.append((kit.iou(render(s, st, *p, box) > 0.5, M > 0.5), v, p))
    cands.sort(key=lambda c: -c[0])
    top = [(kit.iou(kit_render(s, st, p, box) > 0.5, M > 0.5), v, p) for i, v, p in cands[:3]]
    return max(top, key=lambda c: c[0])


def fit_run(oid, run, styles=STYLES, log=print, top=3):
    """Every style: coarse pattern search; the best `top`: fine search with size restarts (both string ends
    held). Style = best IoU (kit.raster vs the 0.5 mask); when the two best are within 0.01 IoU the stem-weight
    measurement decides between them."""
    crop, bg, fgs, a, M = prep(oid, run)
    s, box = run["s"], run["box"]
    coarse = []
    for st in styles:
        p, v, n = fit(s, st, M, box, steps=(1.0, 0.5, 0.25))
        coarse.append((v, st, p))
        log(f"  {oid} {s[:24]:24s} {st:9s} coarse {v:.4f}")
    coarse.sort(reverse=True)
    fine = []
    for v0, st, p0 in coarse[:top]:
        iou_, v, p = fine_fit(s, st, M, box, p0)
        r = kit_render(s, st, p, box)
        so, sr = stems(a, s, st, p, box), stems(r, s, st, p, box)
        fine.append({"iou": iou_, "soft": v, "style": st, "p": p, "stem_orig": so, "stem_render": sr})
        log(f"  {oid} {s[:24]:24s} {st:9s} fine {v:.4f} IoU {fine[-1]['iou']:.4f} stems {so} / {sr}  p {[round(t, 3) for t in p]}")
    fine.sort(key=lambda d: -d["iou"])
    best = fine[0]
    if len(fine) > 1 and best["stem_orig"] and fine[1]["iou"] > best["iou"] - 0.01:
        lr = lambda d: abs(np.log(d["stem_orig"] / d["stem_render"]))
        if lr(fine[1]) < lr(best):
            best, fine[0], fine[1] = fine[1], fine[1], fine[0]
            best["chosen_by"] = "stem weight (IoU within 0.01)"
    best.setdefault("chosen_by", "IoU")
    return {"coarse": [(round(v, 4), st) for v, st, p in coarse], "fine": fine, "a": a, "M": M, "fgs": fgs, "bg": bg}
