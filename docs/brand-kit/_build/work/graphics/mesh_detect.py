"""Scratch: detect the data-mesh bars in original 02 (regular column grid, vertical runs per column),
measure each run's colour, save mesh_bars.json and an overlay."""
import json
import numpy as np
from PIL import Image, ImageDraw
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
PX0, PY0, PX1, PY1 = 1037.54, 613.14, 1318.19, 711.32  # panel rect (sub-pixel, measured)

im = kit.load('02').astype(float)
lab = kit.srgb_to_lab(im)
L = lab[..., 0]

# --- column grid: centroid of each bright column band in the column-mean profile
ys0, ys1 = int(np.ceil(PY0 + 1)), int(PY1 - 1)
cm = L[ys0:ys1, 1038:1318].mean(0)
xs = np.arange(1038, 1318) + 0.5
best = None
for p in np.arange(5.95, 6.30, 0.002):
    for ph in np.arange(0, p, 0.05):
        ang = 2 * np.pi * (xs - 1038 - ph) / p
        sc = float((cm * np.cos(ang)).sum())
        if best is None or sc > best[0]:
            best = (sc, p, ph)
_, P, PH = best
c0 = 1038 + PH
centers = [c0 + k * P for k in range(-2, 60) if PX0 + 1 < c0 + k * P < PX1 - 1]
print('pitch %.4f first center %.3f n %d' % (P, centers[0], len(centers)))

# per-column measured centroid (for jitter stats)
jit = []
for c in centers:
    lo, hi = int(np.floor(c - 3)), int(np.ceil(c + 3))
    w = np.clip(cm[lo - 1038:hi - 1038] - np.percentile(cm, 10), 0, None)
    xx = np.arange(lo, hi) + 0.5
    if w.sum() > 0:
        jit.append(float((w * xx).sum() / w.sum() - c))
print('column centroid offset from regular grid: mean %.3f sd %.3f max %.3f' % (np.mean(jit), np.std(jit), np.max(np.abs(jit))))

# --- runs per column
bars = []
for k, c in enumerate(centers):
    cols = [int(np.floor(c)) - 1, int(np.floor(c)), int(np.floor(c)) + 1]
    s = L[:, cols].mean(1)
    rgbcol = im[:, cols].mean(1)
    y_lo, y_hi = int(np.ceil(PY0)), int(np.floor(PY1))
    seg = s[y_lo:y_hi]
    # local background along the column: robust low envelope
    base = np.array([np.percentile(seg[max(0, i - 25):i + 25], 15) for i in range(len(seg))])
    on = seg - base > 6.0
    i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            top_lvl = seg[i:j].max()
            # sub-pixel edges at half level between base and run level
            lvl = np.median(seg[i:j])
            half_t = base[i] + 0.5 * (lvl - base[i])
            half_b = base[j - 1] + 0.5 * (lvl - base[j - 1])
            yt = y_lo + i
            if i > 0 and seg[i] != seg[i - 1]:
                yt = y_lo + i - (seg[i] - half_t) / (seg[i] - seg[i - 1]) + 0.5
            yb = y_lo + j
            if j < len(seg) and seg[j - 1] != seg[j]:
                yb = y_lo + j - 1 + (seg[j - 1] - half_b) / (seg[j - 1] - seg[j]) + 0.5
            rgb = rgbcol[y_lo + i:y_lo + j].mean(0)
            bars.append({"col": k, "x": round(c, 3), "y0": round(float(max(yt, PY0)), 2), "y1": round(float(min(yb, PY1)), 2),
                         "rgb": [round(float(v), 1) for v in rgb], "L": round(float(lvl), 1), "peak": round(float(top_lvl), 1)})
            i = j
        else:
            i += 1
json.dump({"panel": [PX0, PY0, PX1, PY1], "pitch": P, "centers": centers, "bars": bars}, open(W + r'\mesh_bars.json', 'w'), indent=0)
lens = np.array([b["y1"] - b["y0"] for b in bars])
print('bars', len(bars), 'length mean %.1f median %.1f min %.1f max %.1f' % (lens.mean(), np.median(lens), lens.min(), lens.max()))
print('length histogram', np.histogram(lens, bins=[0, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50, 100]))

s = 6
X0, X1, Y0, Y1 = 1030, 1326, 606, 718
ov = Image.fromarray(im[Y0:Y1, X0:X1].astype(np.uint8)).resize(((X1 - X0) * s, (Y1 - Y0) * s), Image.NEAREST)
d = ImageDraw.Draw(ov)
for b in bars:
    d.rectangle([((b["x"] - 2.25) - X0) * s, (b["y0"] - Y0) * s, ((b["x"] + 2.25) - X0) * s, (b["y1"] - Y0) * s], outline=(255, 0, 0))
ov.save(W + r'\mesh_detect_x6.png')
