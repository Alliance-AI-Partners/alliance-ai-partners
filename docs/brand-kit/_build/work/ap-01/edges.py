"""Sub-pixel edge offsets, hero-01 render vs original 01, on probe scanlines across the main silhouette edges.
Edge = where dE2000 from the background crosses 18 (kit.bg_mask's threshold), linearly interpolated.
python work/ap-01/edges.py [svg]   (also used by hero01.py for the JSON)"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import kit

# name: (axis, fixed range, scan from, scan to); scans run from the background into the mark;
# axis 'y' = scan down/up a column, 'x' = scan along a row
PROBES = {"A apex top": ("y", range(222, 258), 262, 280), "A apex left": ("x", range(271, 276), 205, 230),
          "A left leg outer": ("x", range(378, 383), 160, 190), "left foot baseline": ("y", range(125, 165), 498, 480),
          "right leg outer foot": ("x", range(470, 486), 390, 360), "A counter bottom": ("y", range(222, 258), 392, 410),
          "P top": ("y", range(330, 420), 262, 280), "P stem left": ("x", range(274, 300), 300, 326),
          "P bowl outer right": ("x", range(330, 352), 496, 474), "P bowl outer top-right": ("y", range(440, 460), 262, 290),
          "P counter top": ("y", range(372, 418), 324, 304), "P counter bottom": ("y", range(372, 418), 362, 382),
          "P counter left": ("x", range(320, 366), 372, 350), "P counter right": ("x", range(330, 356), 420, 452)}


def crossing(de, thr=18.0):
    i = np.nonzero(de > thr)[0]
    if len(i) == 0 or i[0] == 0:
        return None
    k = i[0]
    return k - 1 + (thr - de[k - 1]) / (de[k] - de[k - 1])


def offsets(rgb, ren, bg="#FFFFFF"):
    """{probe: {'mean', 'min', 'max', 'n'}} of (01 edge - render edge) in px along the scan; + = 01's mark is smaller."""
    ref = kit.srgb_to_lab(kit.hexrgb(bg))
    d0, d1 = kit.de2000(kit.srgb_to_lab(rgb), ref), kit.de2000(kit.srgb_to_lab(ren), ref)
    out = {}
    for name, (ax, fixed, a, b) in PROBES.items():
        idx = np.arange(a, b, 1 if b > a else -1)
        off = []
        for f in fixed:
            c0 = crossing(d0[idx, f] if ax == "y" else d0[f, idx])
            c1 = crossing(d1[idx, f] if ax == "y" else d1[f, idx])
            if c0 is not None and c1 is not None:
                off.append(c0 - c1)
        off = np.array(off)
        out[name] = {"mean": round(float(off.mean()), 2), "min": round(float(off.min()), 2),
                     "max": round(float(off.max()), 2), "n": len(off)}
    return out


if __name__ == "__main__":
    svg = sys.argv[1] if len(sys.argv) > 1 else str(kit.COMP / "rec" / "hero-01.svg")
    for k, v in offsets(kit.load("01").astype(float), kit.over(kit.render_svg(svg), "#FFFFFF")).items():
        print(f"{k:24s} {v}")
