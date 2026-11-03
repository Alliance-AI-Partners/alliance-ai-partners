"""Verify components/graphic-datamesh.svg against original 02: render, dE inside the panel, bar
statistics re-detected on the render with the same detector, diff sheet."""
import json
import numpy as np
from PIL import Image
import kit
import meshlib as ml

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
X0, X1, Y0, Y1 = 1030, 1326, 606, 718
BG = "#F5F9FC"


def main():
    im = kit.load('02')
    ren = kit.over(kit.render_svg(B + r'\components\graphic-datamesh.svg'), BG)
    sl = (slice(Y0, Y1), slice(X0, X1))
    full = kit.compare(im[sl].astype(float), ren[sl])
    x0, y0, x1, y1 = ml.PANEL
    inner = np.zeros(im.shape[:2], bool)
    inner[int(np.ceil(y0)) + 1:int(y1) - 1, int(np.ceil(x0)) + 1:int(x1) - 1] = True
    de = kit.de2000(kit.srgb_to_lab(im.astype(float)), kit.srgb_to_lab(ren))
    # panel IoU (dark field) original vs render
    om = kit.srgb_to_lab(im.astype(float))[..., 0] < 75
    rm = kit.srgb_to_lab(ren)[..., 0] < 75
    reg = np.zeros(om.shape, bool); reg[Y0:Y1, X0:X1] = True
    so = ml.stats(ml.detect(im))
    sr = ml.stats(ml.detect(np.clip(ren, 0, 255)))
    m = {"de_mean_crop": full["de_mean"], "de_p95_crop": full["de_p95"],
         "de_mean_panel_inside": round(float(de[inner].mean()), 2), "de_p95_panel_inside": round(float(np.percentile(de[inner], 95)), 2),
         "iou_panel": round(kit.iou(om & reg, rm & reg), 4), "stats_original": so, "stats_render": sr}
    s = 3
    o = Image.fromarray(im[sl]).resize(((X1 - X0) * s, (Y1 - Y0) * s), Image.NEAREST)
    r = Image.fromarray(np.clip(ren[sl], 0, 255).astype(np.uint8)).resize(o.size, Image.NEAREST)
    kit.diff_sheet(np.asarray(o), np.asarray(r), B + r'\verify\graphic-datamesh_diff.png', np.kron(full["de_map"], np.ones((s, s))),
                   label=f"graphic-datamesh: dE mean {full['de_mean']} p95 {full['de_p95']} (crop x{X0}-{X1} y{Y0}-{Y1}, x3)")
    print(json.dumps(m, indent=1))
    return m


if __name__ == '__main__':
    main()
