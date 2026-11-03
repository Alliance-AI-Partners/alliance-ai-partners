"""Colour bookkeeping for my components: snap to the core palette (dE2000 <= 4) and merge supporting
tones closer than dE2000 3 (agglomerative, weighted means)."""
import numpy as np
import kit

PAL = kit.PALETTE


def snap(hexc, limit=4.0):
    name, h, de = kit.nearest_palette(hexc)
    return (h, name) if de <= limit else (hexc, None)


def merge_tones(hexes, weights=None, limit=3.0):
    """Greedy agglomerative merge of colours (hex list) closer than `limit` dE2000.
    Returns mapping original hex -> merged hex (weighted Lab mean of its cluster, rounded)."""
    hexes = list(hexes)
    w = list(weights) if weights is not None else [1.0] * len(hexes)
    clusters = [{"members": [h], "w": wi, "rgb": kit.hexrgb(h)} for h, wi in zip(hexes, w)]
    while True:
        best = None
        labs = [kit.srgb_to_lab(c["rgb"]) for c in clusters]
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = float(kit.de2000(labs[i], labs[j]))
                if d < limit and (best is None or d < best[0]):
                    best = (d, i, j)
        if best is None:
            break
        _, i, j = best
        a, b = clusters[i], clusters[j]
        wt = a["w"] + b["w"]
        a["rgb"] = (a["rgb"] * a["w"] + b["rgb"] * b["w"]) / wt
        a["w"] = wt
        a["members"] += b["members"]
        del clusters[j]
    out = {}
    for c in clusters:
        h = kit.rgbhex(c["rgb"])
        for m in c["members"]:
            out[m] = h
    return out
