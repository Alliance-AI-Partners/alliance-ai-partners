"""Data-mesh measurement shared by the build and the verification: bar detection on a regular column
grid (vertical runs per column, split at strong brightness steps) and summary statistics."""
import numpy as np
import kit

PANEL = (1037.54, 613.14, 1318.19, 711.32)  # x0, y0, x1, y1 in 02 pixels (sub-pixel, measured)
PITCH, C0 = 6.118, 1041.95                   # column pitch and first column centre (fitted)
BAR_W = 4.5                                  # bar width (isolated-bar half-max width 4.2 blue .. 4.6 cyan)


def centers():
    x0, _, x1, _ = PANEL
    return [C0 + k * PITCH for k in range(-1, 50) if C0 + k * PITCH - BAR_W / 2 < x1 - 0.5 and C0 + k * PITCH + BAR_W / 2 > x0 + 0.5]


def detect(rgb, thresh=5.0, split=12.0, min_len=1.2):
    """Bars in an RGB image (02 pixel space). Returns list of dicts: col, x, y0, y1, rgb, L."""
    rgb = np.asarray(rgb, float)
    L = kit.srgb_to_lab(rgb)[..., 0]
    x0p, y0p, x1p, y1p = PANEL
    ylo, yhi = int(np.ceil(y0p)) + 1, int(np.floor(y1p)) - 1  # skip the 1-px border rows
    bars = []
    for k, c in enumerate(centers()):
        cols = [x for x in (int(np.floor(c)) - 1, int(np.floor(c)), int(np.floor(c)) + 1) if x0p + 0.5 < x < x1p - 1.2]
        if not cols:
            continue
        s = L[ylo:yhi, cols].mean(1)
        rc = rgb[ylo:yhi, cols].mean(1)
        n = len(s)
        base = np.array([np.percentile(s[max(0, i - 25):i + 26], 15) for i in range(n)])
        on = s - base > thresh
        i = 0
        while i < n:
            if not on[i]:
                i += 1
                continue
            j = i
            while j < n and on[j]:
                j += 1
            # split the run where the level steps by more than `split` (sustained for 2 px)
            cuts = [i]
            for t in range(i + 2, j - 1):
                if abs(s[t:t + 2].mean() - s[t - 2:t].mean()) > split and t - cuts[-1] >= 2:
                    cuts.append(t)
            cuts.append(j)
            for a, b in zip(cuts[:-1], cuts[1:]):
                lvl = float(np.median(s[a:b]))
                ya, yb = ylo + a, ylo + b
                # sub-pixel ends only where the run meets background (not at an internal split)
                if a == i and i > 0:
                    half = base[i] + 0.5 * (lvl - base[i])
                    if s[i] != s[i - 1]:
                        ya = ylo + i + 0.5 - np.clip((s[i] - half) / (s[i] - s[i - 1]), 0, 1)
                if b == j and j < n:
                    half = base[j - 1] + 0.5 * (lvl - base[j - 1])
                    if s[j - 1] != s[j]:
                        yb = ylo + j - 0.5 + np.clip((s[j - 1] - half) / (s[j - 1] - s[j]), 0, 1)
                if a == 0:
                    ya = y0p
                if b == n:
                    yb = y1p
                if yb - ya >= min_len:
                    bars.append({"col": k, "x": c, "y0": float(ya), "y1": float(yb),
                                 "rgb": rc[a:b].mean(0).tolist(), "L": lvl})
            i = j
    return bars


def stats(bars):
    """Summary statistics of a bar set (02 pixel space)."""
    x0p, y0p, x1p, y1p = PANEL
    lens = np.array([b["y1"] - b["y0"] for b in bars])
    lab = kit.srgb_to_lab(np.array([b["rgb"] for b in bars]))
    xs = np.array([b["x"] for b in bars])
    h = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360
    cov = lens.sum() * BAR_W / ((x1p - x0p) * (y1p - y0p))
    halves = {}
    for name, m in (("left", xs < 1178), ("right", xs >= 1178)):
        halves[name] = {"bars": int(m.sum()), "coverage": round(float(lens[m].sum() * BAR_W / ((1178 - x0p if name == "left" else x1p - 1178) * (y1p - y0p))), 3),
                        "L_mean": round(float(lab[m, 0].mean()), 1), "hue_mean": round(float(h[m].mean()), 1)}
    return {"bars": len(bars), "coverage": round(float(cov), 3), "len_mean": round(float(lens.mean()), 2),
            "len_median": round(float(np.median(lens)), 2), "len_p90": round(float(np.percentile(lens, 90)), 2),
            "L_mean": round(float(lab[:, 0].mean()), 1), "halves": halves}
