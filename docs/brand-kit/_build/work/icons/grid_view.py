"""Scratch: render every icon at 4x over the 48 grid (1-unit grid, 4 px padding, circle/square keylines)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import build_icons as B  # noqa: E402

Z = 5
tag = sys.argv[1] if len(sys.argv) > 1 else "x"
only = sys.argv[2:] or [s for s, _, _ in B.ICONS]
cells = []
for slug, name, fn in B.ICONS:
    if slug not in only:
        continue
    els = fn()
    svg = B.svg_text(slug, els, B.BLUE, B.CYAN, "duotone")
    rgba = B.render(svg, 48 * Z)
    bg = Image.new("RGB", (48 * Z, 48 * Z), "white")
    d = ImageDraw.Draw(bg)
    for i in range(49):
        c = (236, 239, 244) if i % 4 else (214, 220, 230)
        d.line([(i * Z, 0), (i * Z, 48 * Z)], fill=c)
        d.line([(0, i * Z), (48 * Z, i * Z)], fill=c)
    d.rectangle([4 * Z, 4 * Z, 44 * Z, 44 * Z], outline=(255, 140, 140))
    d.ellipse([4 * Z, 4 * Z, 44 * Z, 44 * Z], outline=(255, 190, 120))
    d.rectangle([6 * Z, 6 * Z, 42 * Z, 42 * Z], outline=(150, 210, 150))
    a = rgba[..., 3:4]
    comp = rgba[..., :3] * 255 * a + np.asarray(bg, float) * (1 - a)
    im = Image.fromarray(comp.round().astype(np.uint8))
    ImageDraw.Draw(im).text((4, 2), slug, fill=(200, 0, 0))
    cells.append(im)
cols = 4
W, H = 48 * Z, 48 * Z
sheet = Image.new("RGB", (cols * (W + 6), ((len(cells) + cols - 1) // cols) * (H + 6)), "#888888")
for i, c in enumerate(cells):
    sheet.paste(c, ((i % cols) * (W + 6), (i // cols) * (H + 6)))
out = Path(__file__).parent / ("inspect-%s.png" % tag)
sheet.save(out)
print(out)
