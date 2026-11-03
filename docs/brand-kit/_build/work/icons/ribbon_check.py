"""Brand-fidelity check for the icon ribbon: measure the monogram swoosh centreline on original 11
(the only cyan left of the P stem), fit the icon construction (two tangent-continuous cubics with a level
middle) to it, and save verify/icon-ribbon-check.png. Prints the fitted angles and the residual."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import build_icons as B  # noqa: E402
kit = B.kit

rgb = kit.load("11")
cy = kit.de2000(kit.srgb_to_lab(rgb), kit.srgb_to_lab(rgb[600, 300].astype(float))) < 12
STEM_L, STEM_R, STEM_TOP_Y = 546, 634, 480          # P stem edges, measured on the mask (rows 300-480)

pts = []
for x in range(165, 470, 3):                         # level part: per-column midpoint of the ribbon run
    ys = np.where(cy[480:, x])[0] + 480
    if len(ys):
        pts.append((x + 0.5, (ys.min() + ys.max() + 1) / 2))
for y in range(486, 556, 3):                         # rising part: per-row midpoint, ribbon into the stem
    xs = np.where(cy[y, 380:STEM_R + 1])[0] + 380
    if len(xs):
        pts.append(((xs.min() + xs.max() + 1) / 2, y + 0.5))
for y in range(300, 480, 6):                         # the stem it becomes
    pts.append(((STEM_L + STEM_R + 1) / 2, y + 0.5))
pts = np.array(pts)
START, END = pts[pts[:, 0].argmin()], pts[pts[:, 1].argmin()]  # ribbon tip (bottom-left) and top of the stem


def curve(p0, pm, p1, a0, a1, n=500):
    pen = B.swoosh(B.Pen(), p0, pm, p1, a0, a1)
    poly = kit.flatten(kit.parse_d(pen.d()), tol=0.2)[0]
    return np.array(poly)


def resid(params):
    p0, pm, p1 = params[0:2], params[2:4], params[4:6]
    c = curve(tuple(p0), tuple(pm), tuple(p1), params[6], params[7])
    d = np.sqrt(((pts[:, None, :] - c[None, :, :]) ** 2).sum(-1)).min(1)
    return float(d.mean())


best = np.array([*START, 330.0, 590.0, *END, 45.0, 85.0])
step = np.array([10, 10, 30, 20, 4, 10, 8, 6.0])
rng = np.random.default_rng(7)
err = resid(best)
for it in range(3000):  # ponytail: plain random-walk search, fine for 8 params and ~180 points
    cand = best + rng.normal(0, 1, 8) * step * (0.25 if it > 1500 else 1.0)
    cand[7] = min(cand[7], 90.0)
    e = resid(cand)
    if e < err:
        best, err = cand, e
chord = float(np.hypot(*(END - START)))
print("logo ribbon fit: entry %.1f deg, exit %.1f deg, level point (%.0f, %.0f); mean centreline error %.2f px = %.2f%% of chord %.0f px"
      % (best[6], best[7], best[2], best[3], err, 100 * err / chord, chord))

# overlay: original crop, measured centreline (white dots), fitted icon construction (red)
x0, y0, x1, y1 = 120, 260, 900, 760
im = Image.fromarray(rgb).crop((x0, y0, x1, y1)).convert("RGB")
d = ImageDraw.Draw(im)
fit = curve(tuple(best[0:2]), tuple(best[2:4]), tuple(best[4:6]), best[6], best[7])
d.line([(x - x0, y - y0) for x, y in fit], fill=(255, 40, 60), width=5)
for x, y in pts:
    d.ellipse([x - x0 - 3, y - y0 - 3, x - x0 + 3, y - y0 + 3], fill=(255, 255, 255))
d.text((10, 8), "original 11: white = measured ribbon centreline, red = icon ribbon construction fitted to it "
       "(entry %.0f deg, exit %.0f deg, mean error %.1f px = %.1f%% of chord)" % (best[6], best[7], err, 100 * err / chord),
       fill=(255, 255, 255))

# the three icon ribbons, drawn large at the same scale, for a side-by-side read of the motif
panel = Image.new("RGB", (im.width, 260), "#FFFFFF")
pd = ImageDraw.Draw(panel)
icons = {"growth": B.growth, "research-insights": B.research_insights, "launch": B.launch}
for k, (slug, fn) in enumerate(icons.items()):
    svg = B.svg_text(slug, fn(), B.BLUE, B.CYAN, "duotone")
    tile = Image.fromarray(kit.over(B.render(svg, 220), "#FFFFFF").round().astype(np.uint8))
    panel.paste(tile, (20 + k * 250, 30))
    pd.text((20 + k * 250, 10), slug, fill=(18, 27, 42))
sheet = Image.new("RGB", (im.width, im.height + panel.height), "white")
sheet.paste(im, (0, 0))
sheet.paste(panel, (0, im.height))
out = kit.VERIFY / "icon-ribbon-check.png"
sheet.save(out)
print(out)
