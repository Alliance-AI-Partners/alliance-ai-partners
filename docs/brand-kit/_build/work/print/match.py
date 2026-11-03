"""Nearest PANTONE Solid Coated / Uncoated match and ICC CMYK builds for any sRGB hex.

    python -I match.py "#2A6FFF" "#0B1220"        # report for extra hexes (e.g. 3D shading tones)
    python -I match.py --json "#2A6FFF"           # the full match() dicts as JSON
    python -I match.py --selftest

    import match; match.match("#2A6FFF")         # dict: lab_d50, pantone_c, pantone_u, cmyk, recommended

Pantone data: pantone_ref.json (built by make_ref.py; sources listed in its "meta").
Ranking: CIEDE2000 (kit.de2000) between the hex (sRGB -> CIELAB D50 via Bradford, the ICC convention)
and each Pantone colour, taken as the MEDIAN over the published value sets available for that colour:
  pcm  = Pantone Color Manager V4 Lab, plus = PANTONE+ Lab (or ok2pan Lab where PANTONE+ lacks it),
  web  = Pantone's published sRGB (Solid Coated only, and only where the ink lies inside sRGB).
CMYK: Pillow ImageCms (littleCMS), sRGB -> profile, relative colorimetric + black point compensation.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # _build, for kit
import kit  # noqa: E402

PROFILE_DIR = Path(r"C:\Program Files (x86)\Common Files\Adobe\Color\Profiles\Recommended")
PROFILES = {"swop": ("U.S. Web Coated (SWOP) v2", "USWebCoatedSWOP.icc"),
            "gracol": ("Coated GRACoL 2006 (ISO 12647-2:2004)", "CoatedGRACoL2006.icc"),
            "fogra39": ("Coated FOGRA39 (ISO 12647-2:2004)", "CoatedFOGRA39.icc")}
MASTER = "gracol"  # recommended CMYK master profile (argued in print-colors.md)

# ---------------------------------------------------------------- sRGB <-> CIELAB D50

_M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
_BR = np.array([[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]])
_W50 = np.array([0.96422, 1.0, 0.82521])
_A = np.linalg.inv(_BR) @ np.diag((_BR @ _W50) / (_BR @ _M.sum(1))) @ _BR  # Bradford D65 -> D50
_RGB2XYZ50 = _A @ _M


def lab50(c):
    """sRGB hex or 0-255 triple(s) -> CIELAB D50 (..., 3)."""
    c = (kit.hexrgb(c) if isinstance(c, str) else np.asarray(c, float)) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = c @ _RGB2XYZ50.T / _W50
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def hex_from_lab50(lab):
    """CIELAB D50 -> (sRGB hex, in_gamut). Out-of-gamut values are clipped per channel."""
    L, a, b = np.asarray(lab, float)
    fy = (L + 16) / 116
    f = np.array([fy + a / 500, fy, fy - b / 200])
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * _W50
    lin = np.linalg.solve(_RGB2XYZ50, xyz)
    ok = bool(np.all(lin >= -0.002) and np.all(lin <= 1.002))
    lin = np.clip(lin, 0, 1)
    srgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return kit.rgbhex(srgb * 255), ok


def de(lab1, lab2):
    return float(kit.de2000(np.asarray(lab1, float), np.asarray(lab2, float)))


# ---------------------------------------------------------------- Pantone

_REF, _ARR = None, {}


def ref():
    global _REF
    if _REF is None:
        _REF = json.loads((HERE / "pantone_ref.json").read_text(encoding="utf-8"))
    return _REF


def _arrays(side):
    """Per side: names, guides, and one Lab array per value set (NaN where a colour lacks it)."""
    if side not in _ARR:
        recs = ref()[side]
        names = list(recs)
        nan = [np.nan] * 3
        # Pantone's sRGB is clipped for inks outside sRGB, so it only counts where the ink's Lab is inside sRGB
        web_ok = lambda r: "web" in r and hex_from_lab50(r.get("pcm") or r.get("plus") or r.get("ok2pan"))[1]
        sets = {"pcm": [recs[n].get("pcm", nan) for n in names],
                "plus": [recs[n].get("plus", recs[n].get("ok2pan", nan)) for n in names],
                "web": [lab50(recs[n]["web"]) if web_ok(recs[n]) else nan for n in names]}
        _ARR[side] = (names, [recs[n]["guide"] for n in names], {k: np.array(v, float) for k, v in sets.items()})
    return _ARR[side]


def pantone(hex_, side="C", n=3, guides=("Formula Guide",)):
    """Top-n Pantone colours for an sRGB hex, ranked by the median CIEDE2000 over the available value sets."""
    names, gd, sets = _arrays(side)
    L = lab50(hex_)
    with np.errstate(invalid="ignore"):
        des = {k: kit.de2000(L, v) for k, v in sets.items()}  # NaN where a set lacks the colour
    med = np.nanmedian(np.vstack(list(des.values())), 0)
    keep = np.array([g in guides for g in gd])
    order = [i for i in np.argsort(np.where(keep, med, np.inf)) if keep[i]][:n]
    out = []
    for i in order:
        r = ref()[side][names[i]]
        lab = r.get("pcm") or r.get("plus") or r.get("ok2pan")
        hx = r.get("web") or r.get("slab")
        calc, in_gamut = hex_from_lab50(lab)
        out.append({"name": "PANTONE " + names[i], "de2000": round(float(med[i]), 2),
                    "de2000_by_set": {k: round(float(v[i]), 2) for k, v in des.items() if not np.isnan(v[i])},
                    "lab_d50": lab, "lab_source": "pcm" if "pcm" in r else ("plus" if "plus" in r else "ok2pan"),
                    "hex": hx or calc,
                    "hex_source": "web" if "web" in r else ("slab" if "slab" in r else "computed from Lab"),
                    **({"hex_pantone_com_slab": r["slab"]} if "slab" in r else {}),
                    "hex_from_lab": calc, "lab_in_srgb": in_gamut,
                    "guide": r["guide"], **({"note": r["note"]} if "note" in r else {})})
    return out


# ---------------------------------------------------------------- CMYK (littleCMS via Pillow)

_SRGB, _LAB = ImageCms.createProfile("sRGB"), ImageCms.createProfile("LAB")  # LAB defaults to D50
_REL, _BPC = ImageCms.Intent.RELATIVE_COLORIMETRIC, ImageCms.Flags.BLACKPOINTCOMPENSATION
_XF = {}


def _xf(key):
    if key not in _XF:
        kind, prof, bpc = key
        p = ImageCms.getOpenProfile(str(PROFILE_DIR / PROFILES[prof][1]))
        flags = _BPC if bpc else ImageCms.Flags.NONE
        _XF[key] = (ImageCms.buildTransform(_SRGB, p, "RGB", "CMYK", _REL, flags) if kind == "fwd"
                    else ImageCms.buildTransform(p, _LAB, "CMYK", "LAB", _REL, flags))
    return _XF[key]


def to_cmyk(hex_, prof):
    """sRGB hex -> raw CMYK percentages (8-bit precision, 0.39 % steps)."""
    im = Image.new("RGB", (1, 1), tuple(int(v) for v in kit.hexrgb(hex_)))
    return np.array(ImageCms.applyTransform(im, _xf(("fwd", prof, True))).getpixel((0, 0))) / 2.55


_NEIGH = np.array(np.meshgrid(*[np.arange(-2, 3)] * 4, indexing="ij")).reshape(4, -1).T.astype(float)  # 625 offsets


def cmyk_lab(cmyk, prof, bpc=True):
    """CMYK percentages -> CIELAB D50 through the profile (bpc=True undoes the forward BPC: soft-proof round trip;
    bpc=False is the print's colorimetry relative to paper white).
    Pillow reads Lab back at 8 bits (L 0.39, a/b 1.0 steps), so the value is the intercept of a least-squares
    plane through the neighbouring 8-bit CMYK inputs (+-2 levels; channels at 0 or 100 % are held, since the
    tone curve bends hardest there): that averages the rounding out to a few hundredths."""
    c0 = np.asarray(cmyk, float) * 2.55
    free = (c0 > 0.5) & (c0 < 254.5)
    pts = np.unique(np.clip(np.round(c0) + _NEIGH * free, 0, 255), axis=0)
    im = Image.frombytes("CMYK", (len(pts), 1), pts.astype(np.uint8).tobytes())
    o = np.frombuffer(ImageCms.applyTransform(im, _xf(("inv", prof, bpc))).tobytes(), np.uint8).reshape(-1, 3)
    lab = np.c_[o[:, 0].astype(float) * 100 / 255, o.view(np.int8)[:, 1:].astype(float)]  # Pillow LAB: a, b signed
    return np.linalg.lstsq(np.c_[np.ones(len(pts)), (pts - c0)[:, free]], lab, rcond=None)[0][0]


def tidy(raw, prof, lab):
    """Whole percent; then drop 1-2 % traces (they do not hold on press) and make 98-99 % screens solid,
    each change kept only if it costs no more than 0.5 dE2000 on the round trip."""
    c = np.round(np.asarray(raw, float))
    for i in np.argsort(c):
        if 0 < c[i] <= 2 or 98 <= c[i] < 100:
            t = c.copy()
            t[i] = 0 if c[i] <= 2 else 100
            if de(lab, cmyk_lab(t, prof)) <= de(lab, cmyk_lab(c, prof)) + 0.5:
                c = t
    return c


def cmyk(hex_, prof):
    lab = lab50(hex_)
    raw = to_cmyk(hex_, prof)
    cl = tidy(raw, prof, lab)
    return {"profile": PROFILES[prof][0], "raw": [round(float(v), 1) for v in raw], "clean": [int(v) for v in cl],
            "tac_clean": int(cl.sum()), "tac_profile_max": round(float(to_cmyk("#000000", prof).sum()), 1),
            "rt_de2000_raw": round(de(lab, cmyk_lab(raw, prof)), 2),
            "rt_de2000_clean": round(de(lab, cmyk_lab(cl, prof)), 2),
            "paper_relative_de2000_clean": round(de(lab, cmyk_lab(cl, prof, bpc=False)), 2),
            "lab_d50_clean_rt": [round(float(v), 1) for v in cmyk_lab(cl, prof)]}


def match(hex_, n=3):
    """Everything the print spec needs for one sRGB colour."""
    hex_ = kit.rgbhex(kit.hexrgb(hex_))
    builds = {p: cmyk(hex_, p) for p in PROFILES}
    pc, pu = pantone(hex_, "C", n), pantone(hex_, "U", n)
    return {"hex": hex_, "lab_d50": [round(float(v), 2) for v in lab50(hex_)],
            "pantone_c": pc, "pantone_u": pu,
            "pastels_neons": {"C": pantone(hex_, "C", 1, ("Pastels & Neons",)), "U": pantone(hex_, "U", 1, ("Pastels & Neons",))},
            "cmyk": builds,
            "recommended": {"pantone_c": pc[0]["name"], "pantone_u": pu[0]["name"],
                            "cmyk_profile": PROFILES[MASTER][0], "cmyk": builds[MASTER]["clean"]}}


def _fmt(m):
    out = [f"{m['hex']}  Lab D50 {m['lab_d50']}"]
    for side in ("pantone_c", "pantone_u"):
        out.append("  " + side + ": " + "; ".join(f"{p['name']} dE {p['de2000']} ({p['hex']})" for p in m[side]))
    for p, b in m["cmyk"].items():
        out.append(f"  {p:8s} raw {b['raw']}  clean {b['clean']}  TAC {b['tac_clean']}  round-trip dE {b['rt_de2000_clean']}")
    return "\n".join(out)


def _selftest():
    assert np.allclose(lab50("#FFFFFF"), [100, 0, 0], atol=1e-3)
    assert hex_from_lab50(lab50("#1B56FF"))[0] == "#1B56FF"
    assert de([50, 0, 0], [50, 0, 0]) == 0
    top = pantone("#485CC7", "C", 1)[0]  # Pantone's own sRGB for 2726 C
    assert top["name"] == "PANTONE 2726 C" and top["de2000"] < 1.5, top
    w = cmyk("#FFFFFF", "swop")
    assert w["clean"] == [0, 0, 0, 0] and w["rt_de2000_clean"] < 0.5, w
    k = to_cmyk("#000000", "swop")
    assert 280 < k.sum() <= 301, k  # SWOP v2 separates black to its 300 % TAC
    print("selftest ok")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv:
        _selftest()
    elif "--json" in sys.argv:
        print(json.dumps([match(h) for h in args], indent=1))
    else:
        for h in args or ["#1B56FF"]:
            print(_fmt(match(h)))
