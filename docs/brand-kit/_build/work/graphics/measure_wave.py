"""Scratch: per-column sub-pixel measurement of the wave in original 02: outer top/bottom edges and
internal face boundaries (Lab gradient peaks). Writes wave_edges.json and an overlay png."""
import json
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
from PIL import Image, ImageDraw
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
im = kit.load('02').astype(float)
lab = kit.srgb_to_lab(im)
L, C = lab[..., 0], np.hypot(lab[..., 1], lab[..., 2])
h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
core = (L < 72) | ((C > 38) & (h < 225))
core[:480] = False; core[605:] = False; core[:, :1030] = False; core[:, 1325:] = False


def cross(col, y_out, y_in):
    """Sub-pixel crossing of the half-way colour between pixel rows y_out (outside) and y_in (inside)."""
    c_out, c_in = col[y_out], col[y_in]
    d = c_in - c_out
    step = 1 if y_in > y_out else -1
    ys = list(range(y_out, y_in + step, step))
    f = [float(np.dot(col[y] - c_out, d) / np.dot(d, d)) for y in ys]
    for k in range(len(ys) - 1):
        if f[k] < 0.5 <= f[k + 1]:
            return ys[k] + 0.5 + step * (0.5 - f[k]) / (f[k + 1] - f[k])
    return None


out = {}
for x in range(1032, 1324):
    ys = np.nonzero(core[:, x])[0]
    if len(ys) < 6:
        continue
    col = lab[:, x]
    top = cross(col, ys[0] - 3, ys[0] + 2)
    bot = cross(col, ys[-1] + 3, ys[-1] - 2)
    # internal: gradient magnitude along y, peaks inside the band
    g = np.sqrt(((col[2:] - col[:-2]) ** 2).sum(-1)) / 2  # at y = 1..n-2
    peaks = []
    for y in range(ys[0] + 2, ys[-1] - 1):
        gy = g[y - 1]
        if gy > 4.0 and gy >= g[y - 2] and gy > g[y]:
            a, b, c = g[y - 2], gy, g[y]
            off = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
            peaks.append([round(y + 0.5 + off, 2), round(float(gy), 1),
                          kit.rgbhex(im[y - 2, x]), kit.rgbhex(im[y + 2, x])])
    out[x] = {"top": top and round(top, 2), "bot": bot and round(bot, 2), "peaks": peaks}

json.dump(out, open(W + r'\wave_edges.json', 'w'), indent=0)

# overlay
X0, X1, Y0, Y1, s = 1025, 1330, 495, 600, 6
base = Image.fromarray(im[Y0:Y1, X0:X1].astype(np.uint8)).resize(((X1 - X0) * s, (Y1 - Y0) * s), Image.BICUBIC)
d = ImageDraw.Draw(base)
for x, v in out.items():
    px = (x + 0.5 - X0) * s
    for key, colr in (("top", (255, 0, 0)), ("bot", (255, 0, 0))):
        if v[key] is not None:
            py = (v[key] - Y0) * s
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=colr)
    for p in v["peaks"]:
        py = (p[0] - Y0) * s
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 255, 0) if p[1] > 8 else (255, 140, 0))
base.save(W + r'\edges_overlay_x6.png')
for x in range(1035, 1324, 8):
    if x in out:
        print(x, out[x]["top"], out[x]["bot"], [(p[0], p[1]) for p in out[x]["peaks"]])
