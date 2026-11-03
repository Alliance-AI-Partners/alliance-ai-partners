"""Verify components/graphic-wave.svg against original 02: render with VectorCraft, composite on the
board background, metrics (silhouette IoU, dE in ribbon / glow / whole crop), diff sheet."""
import json
import numpy as np
from PIL import Image
import kit
import wavegeom as g

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
X0, X1, Y0, Y1 = 1015, 1340, 482, 612
BG = "#F5F9FC"  # measured board background around panel 05


def original_mask(im):
    lab = kit.srgb_to_lab(im.astype(float))
    L, C = lab[..., 0], np.hypot(lab[..., 1], lab[..., 2])
    h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
    m = (L < 72) | ((C > 38) & (h < 225))
    out = np.zeros(m.shape, bool)
    out[495:600, 1030:1325] = m[495:600, 1030:1325]
    # fill pin holes (bright cyan pixels that fell outside the classifier)
    out |= kit.erode(kit.dilate(out, 1), 1)
    return out


def main(svg=B + r'\components\graphic-wave.svg', tag='graphic-wave'):
    im = kit.load('02')
    rgba = kit.render_svg(svg)
    ren = kit.over(rgba, BG)
    M = g.load()
    F = g.faces(M)
    rib = kit.raster(g.path_d(g.face_segments(F["ribbon"])), 1376, 768) > 0.5
    om = original_mask(im)
    sl = (slice(Y0, Y1), slice(X0, X1))
    iou = kit.iou(om[sl], rib[sl])
    full = kit.compare(im[sl].astype(float), ren[sl])
    de = full["de_map"]
    core = rib[sl]
    near = kit.dilate(rib, 16)[sl] & ~core
    m = {"iou_silhouette": round(iou, 4),
         "de_mean_crop": full["de_mean"], "de_p95_crop": full["de_p95"],
         "de_mean_ribbon": round(float(de[core].mean()), 2), "de_p95_ribbon": round(float(np.percentile(de[core], 95)), 2),
         "de_mean_glow": round(float(de[near].mean()), 2), "de_p95_glow": round(float(np.percentile(de[near], 95)), 2)}
    for f in "ABCD":
        fm = (kit.raster(g.path_d(g.face_segments(F[f])), 1376, 768) > 0.999)
        fm = kit.erode(fm, 1)[sl]
        m["de_mean_face_" + f] = round(float(de[fm].mean()), 2)
    s = 3
    o = Image.fromarray(im[sl]).resize(((X1 - X0) * s, (Y1 - Y0) * s), Image.NEAREST)
    r = Image.fromarray(np.clip(ren[sl], 0, 255).astype(np.uint8)).resize(o.size, Image.NEAREST)
    dm = np.kron(de, np.ones((s, s)))
    kit.diff_sheet(np.asarray(o), np.asarray(r), B + rf'\verify\{tag}_diff.png', dm,
                   label=f"{tag}: IoU {iou:.4f}  dE mean {full['de_mean']} p95 {full['de_p95']} (crop x{X0}-{X1} y{Y0}-{Y1}, x3)")
    print(json.dumps(m, indent=1))
    return m, ren


if __name__ == '__main__':
    main()
