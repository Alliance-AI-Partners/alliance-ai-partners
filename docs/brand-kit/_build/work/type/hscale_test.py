import sys, json
sys.path.insert(0, r"C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\type")
import textfit as T
import numpy as np
from PIL import Image, ImageDraw
kit = T.kit

def hs_raster(s, style, size, tr, x, base, w, h, hs, ss=4):
    acc = np.zeros((h * ss, w * ss), bool)
    k = size / 100.0
    for ch, idx, dx in kit.glyphs()["weights"][style]["strings"][s]:
        ox = x + dx * k * hs + idx * tr / 1000.0 * size
        polys = [(p * (k * hs, k) + (ox, base)) * ss for p in T.glyph_polys(style, ch)]
        allp = np.concatenate(polys)
        gx0, gy0 = int(np.floor(allp[:, 0].min())) - 1, int(np.floor(allp[:, 1].min())) - 1
        gx1, gy1 = int(np.ceil(allp[:, 0].max())) + 2, int(np.ceil(allp[:, 1].max())) + 2
        cx0, cy0, cx1, cy1 = max(gx0, 0), max(gy0, 0), min(gx1, w * ss), min(gy1, h * ss)
        if cx1 <= cx0 or cy1 <= cy0:
            continue
        m = np.zeros((gy1 - gy0, gx1 - gx0), bool)
        for p in polys:
            img = Image.new("1", (gx1 - gx0, gy1 - gy0), 0)
            ImageDraw.Draw(img).polygon([tuple(v) for v in (p - (gx0, gy0))], fill=1)
            m ^= np.asarray(img, bool)
        acc[cy0:cy1, cx0:cx1] |= m[cy0 - gy0:cy1 - gy0, cx0 - gx0:cx1 - gx0]
    return acc.reshape(h, ss, w, ss).mean((1, 3))

def fit_hs(s, st, M, box, p0, hs, steps=(0.5, 0.25, 0.1, 0.05)):
    x0, y0, x1, y1 = box
    q = list(p0)
    def f(q):
        return T.soft_iou(hs_raster(s, st, q[0], q[1], q[2] - x0, q[3] - y0, x1 - x0, y1 - y0, hs), M)
    best = f(q)
    sc = [1, 4, 1, 1]
    for stp in steps:
        imp = True
        while imp:
            imp = False
            for i in range(4):
                for sg in (1, -1):
                    qq = list(q); qq[i] += sg * stp * sc[i]
                    v = f(qq)
                    if v > best + 1e-6:
                        q, best, imp = qq, v, True
    r = hs_raster(s, st, q[0], q[1], q[2] - x0, q[3] - y0, x1 - x0, y1 - y0, hs)
    return q, best, kit.iou(r > 0.5, M > 0.5)

for oid, j in [("13", 1), ("16", 1), ("10", 1), ("01", 1), ("10", 0)]:
    R = json.load(open(T.WORK / f"res_{oid}.json"))["runs"][j]
    run = T.RUNS[oid][j]
    crop, bg, fgs, a, M = T.prep(oid, run)
    p0 = [R["size"], R["tracking"], R["x"], R["baseline"]]
    out = []
    for hs in (0.96, 0.98, 1.0, 1.02, 1.04):
        q, v, i = fit_hs(R["s"], R["style"], M, tuple(run["box"]), p0, hs)
        out.append((hs, round(v, 4), round(i, 4), round(q[1], 1)))
    print(oid, R["s"], R["style"], out, flush=True)
