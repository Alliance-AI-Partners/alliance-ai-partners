"""Build components/graphic-datamesh.svg: the "data mesh" panel of original 02 (panel 05, lower
element) in 02's pixel space. Bars sit on the measured regular column grid (pitch 6.118 px, bar width
4.5 px); their runs and brightness come from a per-column detection on the original, quantised to 8
tones (k-means in Lab). The navy field is a horizontal gradient fitted to the background pixels.
Also writes fit/graphic-datamesh_fit.json (grid, tones, bars, measured statistics)."""
import json
import numpy as np
import kit
import meshlib as ml
from gradfit import fit_gradient

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
K_TONES = 8


def kmeans_tones(bars, K=K_TONES, seed=0):
    rgb = np.array([b["rgb"] for b in bars])
    w = np.array([b["y1"] - b["y0"] for b in bars])
    lab = kit.srgb_to_lab(rgb)
    rng = np.random.default_rng(seed)
    best = None
    for rep in range(10):
        c = lab[rng.choice(len(lab), K, replace=False)]
        for _ in range(60):
            a = kit.de2000(lab[:, None, :], c[None]).argmin(1)
            c = np.array([np.average(lab[a == k], axis=0, weights=w[a == k]) if (a == k).any() else c[k] for k in range(K)])
        d = kit.de2000(lab[:, None, :], c[None])
        a = d.argmin(1)
        score = float(np.average(d[np.arange(len(lab)), a], weights=w))
        if best is None or score < best[0]:
            best = (score, a)
    a = best[1]
    tones = [kit.rgbhex(np.average(rgb[a == k], axis=0, weights=w[a == k])) for k in range(K)]
    order = np.argsort([kit.srgb_to_lab(kit.hexrgb(t))[0] for t in tones])
    remap = {int(o): i for i, o in enumerate(order)}
    tones = [tones[o] for o in order]
    return tones, [remap[int(x)] for x in a], best[0]


def background(im, bars):
    x0, y0, x1, y1 = ml.PANEL
    mask = np.zeros(im.shape[:2], bool)
    for b in bars:
        mask[int(np.floor(b["y0"])) - 1:int(np.ceil(b["y1"])) + 1, int(b["x"] - 3.6):int(b["x"] + 3.6) + 1] = True
    ys, xs = np.mgrid[int(y0) + 2:int(y1) - 1, int(x0) + 3:int(x1) - 2]
    sel = ~mask[ys, xs]
    xy = np.stack([xs[sel] + 0.5, ys[sel] + 0.5], -1)
    r = fit_gradient(xy, im[ys[sel], xs[sel]].astype(float), K=3, angles=np.radians(np.arange(-20, 21, 2)))
    return r


def build(fit):
    x0, y0, x1, y1 = fit["panel"]
    g = fit["bg"]
    defs = kit.lin_grad("mesh-grad-field", g["p0"][0], g["p0"][1], g["p1"][0], g["p1"][1],
                        [(k / (len(g["stops"]) - 1), s) for k, s in enumerate(g["stops"])])
    f = lambda v: ("%.2f" % v).rstrip("0").rstrip(".")
    body = ['<g id="graphic-datamesh">',
            f'<rect id="mesh-field" x="{f(x0)}" y="{f(y0)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}" fill="url(#mesh-grad-field)"/>',
            '<g id="mesh-bars">']
    bars = sorted(fit["bars"], key=lambda b: (b["col"], b["y0"]))
    count = {}
    for i, b in enumerate(bars):
        bx0 = max(b["x"] - ml.BAR_W / 2, x0)
        bx1 = min(b["x"] + ml.BAR_W / 2, x1)
        ya, yb = max(b["y0"], y0), min(b["y1"], y1)
        nxt = bars[i + 1] if i + 1 < len(bars) else None
        if nxt and nxt["col"] == b["col"] and abs(nxt["y0"] - b["y1"]) < 0.3:
            yb = min(yb + 0.4, y1)  # tuck under the next segment of the same bar: no hairline seam
        count[b["col"]] = count.get(b["col"], 0) + 1
        body.append(f'<rect id="mesh-bar-c{b["col"]:02d}-{count[b["col"]]:02d}" x="{f(bx0)}" y="{f(ya)}" '
                    f'width="{f(bx1 - bx0)}" height="{f(yb - ya)}" fill="{fit["tones"][b["tone"]]}"/>')
    body += ['</g>', '</g>']
    return kit.svg_doc(1376, 768, "\n".join(body), defs)


if __name__ == '__main__':
    im = kit.load('02')
    bars = ml.detect(im)
    tones, assign, err = kmeans_tones(bars)
    bg = background(im, bars)
    fit = {"panel": list(ml.PANEL), "pitch": ml.PITCH, "first_center": ml.C0, "bar_width": ml.BAR_W,
           "tones": tones, "tone_fit_de_weighted": round(err, 2),
           "bg": {"p0": bg["p0"].tolist(), "p1": bg["p1"].tolist(), "stops": [kit.rgbhex(s) for s in bg["stops"]],
                  "fit_de_mean": round(bg["de_mean"], 2)},
           "bars": [{"col": b["col"], "x": round(b["x"], 3), "y0": round(b["y0"], 2), "y1": round(b["y1"], 2), "tone": t}
                    for b, t in zip(bars, assign)],
           "stats_original": ml.stats(bars)}
    json.dump(fit, open(B + r'\fit\graphic-datamesh_fit.json', 'w'), indent=1)
    open(B + r'\components\graphic-datamesh.svg', 'w', encoding='utf-8').write(build(fit))
    print('tones', tones, 'tone dE %.2f' % err)
    print('bg', fit["bg"])
    print('bars', len(bars))
