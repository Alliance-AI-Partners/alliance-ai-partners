"""Scratch: original vs render close-ups (stacked) for regions of an SVG in 02's pixel space."""
import sys
import numpy as np
from PIL import Image, ImageDraw
import kit

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'


def closeups(svg, regions, out, s=6, bg="#F5F9FC"):
    im = kit.load('02')
    ren = np.clip(kit.over(kit.render_svg(svg), bg), 0, 255).astype(np.uint8)
    tiles = []
    for (x0, x1, y0, y1) in regions:
        a = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * s, (y1 - y0) * s), Image.NEAREST)
        b = Image.fromarray(ren[y0:y1, x0:x1]).resize(a.size, Image.NEAREST)
        t = Image.new("RGB", (a.width, a.height * 2 + 4), "white")
        t.paste(a, (0, 0)); t.paste(b, (0, a.height + 4))
        ImageDraw.Draw(t).text((4, 4), f"{x0}-{x1},{y0}-{y1}", fill=(255, 0, 0))
        tiles.append(t)
    W = sum(t.width for t in tiles) + 6 * (len(tiles) - 1)
    H = max(t.height for t in tiles)
    sheet = Image.new("RGB", (W, H), (128, 128, 128))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0)); x += t.width + 6
    sheet.save(out)


if __name__ == '__main__':
    closeups(B + r'\components\graphic-wave.svg',
             [(1030, 1080, 550, 595), (1095, 1175, 498, 545), (1200, 1270, 553, 596), (1270, 1330, 497, 548)],
             B + r'\work\graphics\closeup_wave.png')
