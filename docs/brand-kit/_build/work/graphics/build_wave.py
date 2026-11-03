"""Build components/graphic-wave.svg (in original 02's pixel space) and graphic-wave-master.svg
(1600x400) from the parametric wave model in fit/graphic-wave_fit.json.

Model: a twisted 4-sided ribbon. The silhouette is bounded by two smooth edge curves (cubic splines
in x, fitted to sub-pixel edge measurements) and two vertical end cuts; three face boundaries B1..B3
sweep across the band (each leaves/joins an edge tangentially), so the faces A, B, C, D roll over
from the bottom edge to the top edge as the ribbon twists. Each face has a linear gradient fitted
to the original; the glow is a stack of offset copies of the silhouette at low fill-opacity (an
expanded blend) that samples a Gaussian edge falloff fitted to the original's halo.

usage: python build_wave.py [--refit-colors]
"""
import json
import sys
import numpy as np
import kit
import wavegeom as g
from gradfit import fit_gradient
from tones import snap, merge_tones

COMP = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\components'
FACES = ["A", "B", "C", "D"]
K_STOPS = {"A": 7, "B": 8, "C": 8, "D": 7}
# Glow: Gaussian edge falloff alpha(d) = A0/2 * erfc((d - mu) / (sigma sqrt2)), d = distance outside the
# silhouette in 02 pixels, fitted to the halo (glow_fit4.py). Sampled into N nested offset copies at
# equal alpha steps: 8 at 1:1 (steps ~1.5 px), 20 in the 3.3x master so no banding shows.
GLOW = {"color": "#17BEF2", "model": {"A0": 0.97, "mu": 3.0, "sigma": 7.4}}
BASE = "#121B2A"  # Deep Navy under-layer, inset 0.6 px: fills anti-aliasing seams between faces


def poly_d(q):
    return "M" + " L".join("%.3f %.3f" % (x, y) for x, y in q) + " Z"


def fit_colors(M):
    im = kit.load('02').astype(float)
    F = g.faces(M)
    grads, raw = {}, []
    for name in FACES:
        cov = kit.raster(poly_d(g.outline(F[name])), 1376, 768)
        inner = kit.erode(cov > 0.999, 1)
        ys, xs = np.nonzero(inner)
        xy = np.stack([xs + 0.5, ys + 0.5], -1)
        r = fit_gradient(xy, im[ys, xs], K_STOPS[name])
        stops = [kit.rgbhex(s) for s in r["stops"]]
        grads[name] = {"p0": r["p0"].tolist(), "p1": r["p1"].tolist(), "stops": stops,
                       "fit_de_mean": round(r["de_mean"], 2), "fit_de_p95": round(r["de_p95"], 2), "n_px": int(len(xy))}
        raw += [(s, len(xy) / len(stops)) for s in stops]
        print(name, 'angle %.1f' % r["angle_deg"], 'dE %.2f / p95 %.2f' % (r["de_mean"], r["de_p95"]), stops)
    # palette snap (<= 4) then merge supporting tones (< 3 apart)
    snapped = {}
    for s, _ in raw:
        snapped[s] = snap(s)[0]
    sup = [(snapped[s], w) for s, w in raw if snap(s)[1] is None]
    agg = {}
    for h, w in sup:
        agg[h] = agg.get(h, 0) + w
    merged = merge_tones(list(agg), list(agg.values()))
    for name in grads:
        grads[name]["stops"] = [snapped[s] if snap(s)[1] else merged[snapped[s]] for s in grads[name]["stops"]]
    M["colors"] = {"gradients": grads, "glow": GLOW, "base": BASE}
    return M


def glow_layers(N, A0=0.97, mu=3.0, sigma=7.4, d_in=0.5):
    """[(offset, fill-opacity)] outermost first; the composite alpha inside ring k equals the model at
    the ring's middle, so each copy adds the same alpha step."""
    from math import erfc, sqrt
    dd = np.linspace(-5, 40, 9001)
    Am = np.array([A0 * 0.5 * erfc((x - mu) / (sigma * sqrt(2))) for x in dd])
    a_in = float(np.interp(d_in, dd, Am))
    radii = sorted((float(np.interp(-a_in * (k + 0.5) / N, -Am, dd)) for k in range(N)), reverse=True)
    out, prev = [], 0.0
    for k, r in enumerate(radii):
        t = a_in * (k + 1) / N
        out.append((round(max(r, 0.4), 2), round(1 - (1 - t) / (1 - prev), 4)))
        prev = t
    return out


def gradient_xml(gid, p0, p1, stops, xform):
    a, b = xform(np.array(p0)), xform(np.array(p1))
    return kit.lin_grad(gid, a[0], a[1], b[0], b[1], [(k / (len(stops) - 1), s) for k, s in enumerate(stops)])


def build_svg(M, w, h, xform=lambda p: np.asarray(p, float), scale=1.0, label="graphic-wave", n_glow=8):
    F = g.faces(M)
    C = M["colors"]
    defs, body = [], [f'<g id="{label}">']
    gl = C["glow"]
    for k, (r, a) in enumerate(glow_layers(n_glow, **gl["model"])):
        d = g.path_d(g.glow_segments(M, r), xform)
        body.append(f'<path id="wave-glow-{k + 1}" d="{d}" fill="{gl["color"]}" fill-opacity="{a:.3f}"/>')
    d = g.path_d(g.inset_segments(M, 0.6), xform)
    body.append(f'<path id="wave-base" d="{d}" fill="{BASE}"/>')
    for name, gid, pid in [(f, f"wave-grad-face-{f.lower()}", f"wave-face-{f.lower()}") for f in FACES]:
        gr = C["gradients"][name]
        defs.append(gradient_xml(gid, gr["p0"], gr["p1"], gr["stops"], xform))
        d = g.path_d(g.face_segments(F[name]), xform)
        body.append(f'<path id="{pid}" d="{d}" fill="url(#{gid})"/>')
    body.append('</g>')
    return kit.svg_doc(w, h, "\n".join(body), "\n".join(defs))


def master_xform(M, W=1600, H=400, margin=8):
    top, bot, _ = g.curves(M)
    rmax = max(r for r, _ in glow_layers(20, **M["colors"]["glow"]["model"]))
    xs = np.linspace(M["XL"], M["XR"], 2000)
    x0, x1 = M["XL"] - rmax, M["XR"] + rmax
    y0, y1 = float(top(xs).min()) - rmax, float(bot(xs).max()) + rmax
    s = min((W - 2 * margin) / (x1 - x0), (H - 2 * margin) / (y1 - y0))
    dx = W / 2 - s * (x0 + x1) / 2
    dy = H / 2 - s * (y0 + y1) / 2
    return (lambda p: np.asarray(p, float) * s + np.array([dx, dy])), s


if __name__ == '__main__':
    M = g.load()
    if "--refit-colors" in sys.argv or "colors" not in M:
        M = fit_colors(M)
    M["colors"]["glow"], M["colors"]["base"] = dict(GLOW, layers_1to1=glow_layers(8, **GLOW["model"])), BASE
    json.dump(M, open(g.FIT, "w"), indent=1)
    svg = build_svg(M, 1376, 768)
    open(COMP + r'\graphic-wave.svg', 'w', encoding='utf-8').write(svg)
    xf, s = master_xform(M)
    svg = build_svg(M, 1600, 400, xf, s, label="graphic-wave-master", n_glow=20)
    open(COMP + r'\graphic-wave-master.svg', 'w', encoding='utf-8').write(svg)
    print('wrote graphic-wave.svg, graphic-wave-master.svg (master scale %.3f)' % s)
    import glow_smooth  # ponytail: the 8/20-copy glow above only frames the master; swap in the smooth blend
    glow_smooth.build()
