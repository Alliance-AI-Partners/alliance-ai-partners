"""Zoomed original | render | dE heat strips for regions of 01 (inspection only).  python work/ap-01/zoom.py svg out.png"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import kit

REG = {"left-foot": (112, 380, 232, 495), "crossing": (250, 330, 380, 450), "p-top": (300, 262, 420, 340),
       "p-bowl": (380, 262, 492, 420), "apex": (190, 262, 300, 340), "p-stem": (300, 400, 400, 495)}
svg, out = sys.argv[1], sys.argv[2]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 4
rgb = kit.load("01").astype(float)
ren = kit.over(kit.render_svg(svg), "#FFFFFF")
de = kit.de2000(kit.srgb_to_lab(rgb), kit.srgb_to_lab(ren))
rows = []
for name, (x0, y0, x1, y1) in REG.items():
    o, r, d = rgb[y0:y1, x0:x1], ren[y0:y1, x0:x1], de[y0:y1, x0:x1]
    t = np.clip(d / 10, 0, 1)[..., None]
    h = np.array([255, 255, 255]) * (1 - t) + np.array([220, 30, 30]) * t
    strip = np.concatenate([o, np.full((y1 - y0, 4, 3), 128), r, np.full((y1 - y0, 4, 3), 128), h], 1)
    im = Image.fromarray(np.clip(strip, 0, 255).astype(np.uint8)).resize((strip.shape[1] * k, strip.shape[0] * k), Image.NEAREST)
    ImageDraw.Draw(im).text((4, 4), f"{name} {x0},{y0}  mean dE {d.mean():.2f}", fill=(255, 0, 0))
    rows.append(im)
for i in range(0, len(rows), 2):
    pair = rows[i:i + 2]
    W = max(p.width for p in pair); H = sum(p.height for p in pair) + 8
    sheet = Image.new("RGB", (W, H), "white"); y = 0
    for p in pair:
        sheet.paste(p, (0, y)); y += p.height + 8
    sheet.save(out.replace(".png", f"_{i // 2}.png"))
