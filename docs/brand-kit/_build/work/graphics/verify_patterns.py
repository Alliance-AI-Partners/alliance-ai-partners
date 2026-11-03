"""Verify the pattern tiles: render each tile alone and tiled 3x3 (nine translated copies of the tile
body), check that the centre copy equals the single tile, measure seam continuity, and write
verify/pattern_sheet.png."""
import json
import re
import numpy as np
from PIL import Image
import kit

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
T = 240


def tiled_svg(svg, n=3):
    defs = re.search(r"<defs>.*?</defs>", svg, re.S)
    body = re.sub(r"<defs>.*?</defs>", "", svg[svg.index(">", svg.index("<svg")) + 1:svg.rindex("</svg>")], flags=re.S)
    parts = [f'<g transform="translate({i * T} {j * T})">{body}</g>' for j in range(n) for i in range(n)]
    return kit.svg_doc(n * T, n * T, "\n".join(parts), defs.group(0)[6:-7] if defs else "")


def seam_ratio(img, axis):
    """Mean |difference| across the tile seams vs across all other neighbouring pixel lines."""
    a = img.astype(float)
    d = np.abs(np.diff(a, axis=axis)).mean(axis=(1 - axis, 2) if a.ndim == 3 else 1 - axis)
    seams = [T - 1, 2 * T - 1]
    other = np.delete(d, seams)
    return float(d[seams].mean() / max(other.mean(), 1e-9)), float(d[seams].max() / max(np.percentile(other, 99), 1e-9))


def main():
    info = json.load(open(B + r'\components\patterns.json'))
    imgs, labels, report = [], [], {}
    for t in info["tiles"]:
        svg = open(B + r'\components\\' + t["file"], encoding='utf-8').read()
        assert re.search(r'<g id="[^"]+">\s*$|<rect id="bg"', svg), t["file"]
        first = re.search(r"<(rect|path|circle|g)\b[^>]*>", svg[svg.index("</defs>") + 7 if "</defs>" in svg else svg.index(">", svg.index("<svg")):])
        assert first and 'id="bg"' in first.group(0), "bg rect must come first: " + t["file"]
        single = kit.over(kit.render_svg(svg), "#FFFFFF")
        big = kit.over(kit.render_svg(tiled_svg(svg)), "#FFFFFF")
        centre = big[T:2 * T, T:2 * T]
        diff = float(np.abs(centre - single).max())
        rx = seam_ratio(big, 1)
        ry = seam_ratio(big, 0)
        report[t["name"]] = {"centre_vs_single_max_abs": round(diff, 2),
                             "seam_x_mean_ratio": round(rx[0], 3), "seam_x_max_vs_p99": round(rx[1], 3),
                             "seam_y_mean_ratio": round(ry[0], 3), "seam_y_max_vs_p99": round(ry[1], 3)}
        imgs.append(Image.fromarray(np.clip(big, 0, 255).astype(np.uint8)))
        labels.append(f"{t['file']}  3x3  seam ratio x {rx[0]:.2f} y {ry[0]:.2f}")
    kit.contact(imgs, labels, B + r'\verify\pattern_sheet.png', cols=3, width=480)
    print(json.dumps(report, indent=1))
    return report


if __name__ == '__main__':
    main()
