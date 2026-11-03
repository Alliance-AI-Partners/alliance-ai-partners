"""Write print-colors.json and print-colors.md (docs/brand-kit/_build) from match.py + pantone_ref.json.

    python -I build.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import PIL

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import match  # noqa: E402

kit = match.kit
OUT = HERE.parents[1]
P = match.PROFILES
M = match.MASTER


def by_name(hex_, name):
    """match.pantone() entry for one named colour (side taken from the name)."""
    return next(p for p in match.pantone(hex_, name[-1], 10 ** 6, ("Formula Guide", "Pastels & Neons")) if p["name"] == name)


def low_tac_navy(hex_, prof):
    """K-heavy, yellow-free build for the navy: minimum round-trip dE2000 over C, M, K (coarse grid, then +-3)."""
    L = match.lab50(hex_)
    f = lambda c, m, k: match.de(L, match.cmyk_lab([c, m, 0, k], prof))
    _, c0, m0, k0 = min((f(c, m, k), c, m, k) for c in range(30, 101, 4) for m in range(0, 61, 4) for k in range(80, 101, 2))
    d, c, m, k = min((f(c, m, k), c, m, k) for c in range(c0 - 3, min(100, c0 + 3) + 1)
                     for m in range(max(0, m0 - 3), m0 + 4) for k in range(k0 - 3, min(100, k0 + 3) + 1))
    return {"cmyk": [c, m, 0, k], "tac": c + m + k, "rt_de2000": round(d, 2),
            "paper_relative_de2000": round(match.de(L, match.cmyk_lab([c, m, 0, k], prof, False)), 2),
            "lab_d50_paper_relative": [round(float(v), 1) for v in match.cmyk_lab([c, m, 0, k], prof, False)]}


def tint_estimate(target_hex, ink_lab):
    """Screen % of a spot ink on white stock that reaches the target lightness (Murray-Davies in XYZ, no dot gain)."""
    def xyz(lab):
        L, a, b = lab
        fy = (L + 16) / 116
        f = np.array([fy + a / 500, fy, fy - b / 200])
        return np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27))

    def lab(x):
        f = np.where(x > 216 / 24389, np.cbrt(x), (24389 / 27 * x + 16) / 116)
        return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])
    tgt, ink = match.lab50(target_hex), xyz(ink_lab)
    t = (1 - xyz(tgt)[1]) / (1 - ink[1])
    lt = lab((1 - t) + t * ink)
    return {"screen_pct": round(float(t * 100)), "lab_d50": [round(float(v), 1) for v in lt], "de2000": round(match.de(tgt, lt), 2)}


def chroma(lab):
    return float(np.hypot(lab[1], lab[2]))


def decision(cname, e):
    c, u, su = e["pantone_c"], e["pantone_u"], e["same_ink_uncoated"]
    b = e["cmyk"]
    if cname == "Alliance Blue":
        return ("%s is the closest coated ink on all three value sets. %s is far outside both the Pantone and the CMYK "
                "gamut (chroma %.0f against %.0f for %s and %.0f for the best CMYK build), so every print version is visibly "
                "less electric than the screen; the spot ink still gets much closer than process (dE %.1f against %.1f). "
                "On uncoated stock the same ink (%s) is dE %.1f away, so the uncoated spec is %s (dE %.1f)." % (
                    c["name"], e["hex"], chroma(e["lab_d50"]), chroma(c["lab_d50"]), c["name"].replace("PANTONE ", ""),
                    chroma(b[M]["lab_d50_clean_rt"]), c["de2000"], b[M]["rt_de2000_clean"], su["name"], su["de2000"],
                    u["name"], u["de2000"]))
    if cname == "Ribbon Cyan":
        return ("%s / %s: the same ink is the closest on both stocks. %s is partly outside CMYK (round trip dE %.1f on SWOP v2, "
                "%.1f on GRACoL 2006, %.1f on FOGRA39): process cyan cannot reach its lightness and chroma together." % (
                    c["name"], u["name"], e["hex"], b["swop"]["rt_de2000_clean"], b["gracol"]["rt_de2000_clean"],
                    b["fogra39"]["rt_de2000_clean"]))
    if cname == "Partner Navy":
        cand = e["pantone_c_candidates"]
        alt = cand[1]
        firsts = sum(1 for k in c["de2000_by_set"] if c["de2000_by_set"][k] < alt["de2000_by_set"].get(k, 99))
        alt_u = e["alt_same_ink_uncoated"]
        return ("%s (dE %.2f) and %s (dE %.2f) tie within the data's precision; %s is taken because %d of the 3 value sets rank "
                "it first, its published sRGB (%s) is the nearest to %s, and its uncoated version is darker (%s dE %.1f "
                "against %s dE %.1f). No uncoated ink gets within dE 15 (best %s, dE %.1f): uncoated stock cannot print this "
                "dark, so the navy reads as a dark slate there." % (
                    c["name"], c["de2000"], alt["name"], alt["de2000"], c["name"].replace("PANTONE ", ""), firsts, c["hex"],
                    e["hex"], su["name"], su["de2000"], alt_u["name"], alt_u["de2000"], u["name"], u["de2000"]))
    if cname == "Pure White":
        return ("No Pantone ink: white is the unprinted substrate. On dark, clear or metallic substrates it becomes an opaque "
                "white ink spot (see the notes). The nearest Pantone inks (dE %.1f and up) are listed for completeness only." %
                e["pantone_c_candidates"][0]["de2000"])
    return ("%s / %s are the nearest inks (dE %.1f / %.1f), but a full-strength flood is too dark (L* %.0f against %.0f). In "
            "print, Daylight is the paper itself (coated stock measures about L* 95). Where a visible panel is needed on "
            "white stock, use the CMYK tint or a light screen of %s, confirmed by a drawdown." % (
                c["name"], u["name"], c["de2000"], u["de2000"], c["lab_d50"][0], e["lab_d50"][0], c["name"]))


def main():
    colors = {}
    for cname, hx in kit.PALETTE.items():
        m = match.match(hx, n=3)
        pc, pu = m["pantone_c"], m["pantone_u"]
        su = by_name(hx, pc[0]["name"][:-1] + "U")
        white = cname == "Pure White"
        e = {"hex": hx, "lab_d50": m["lab_d50"],
             "pantone_c": None if white else pc[0], "pantone_u": None if white else pu[0],
             "pantone_c_candidates": pc, "pantone_u_candidates": pu,
             "same_ink_uncoated": None if white else {k: su[k] for k in ("name", "de2000", "hex", "lab_d50")},
             "pastels_neons_nearest": {s: m["pastels_neons"][s][0] for s in "CU"},
             "cmyk": m["cmyk"]}
        rec = {"pantone_c": None if white else pc[0]["name"], "pantone_u": None if white else pu[0]["name"],
               "cmyk_profile": P[M][0], "cmyk": m["cmyk"][M]["clean"], "cmyk_swop": m["cmyk"]["swop"]["clean"]}
        if cname == "Partner Navy":
            alt = by_name(hx, pc[1]["name"][:-1] + "U")
            e["alt_same_ink_uncoated"] = {k: alt[k] for k in ("name", "de2000", "hex")}
            e["cmyk_low_tac"] = {p: low_tac_navy(hx, p) for p in P}
            rec["cmyk"], rec["cmyk_swop"] = e["cmyk_low_tac"][M]["cmyk"], e["cmyk_low_tac"]["swop"]["cmyk"]
            rec["cmyk_note"] = "K-heavy build (cmyk_low_tac): matches as well as the ICC build with far less ink; the ICC build stays valid."
        if white:
            rec["note"] = "No ink (substrate white); opaque white ink spot on dark, clear or metallic substrates."
        if cname == "Daylight":
            e["tint_of_pantone_c"] = tint_estimate(hx, pc[0]["lab_d50"])
            rec["note"] = "Unprinted paper in print; for a visible panel the CMYK tint or a ~%d %% screen of %s." % (
                e["tint_of_pantone_c"]["screen_pct"], pc[0]["name"])
        e["decision"] = decision(cname, e)
        e["recommended"] = rec
        colors[cname] = e

    meta = json.loads((HERE / "pantone_ref.json").read_text(encoding="utf-8"))["meta"]
    ref = match.ref()["C"]
    inside = [match.de(r["pcm"], match.lab50(r["web"])) for r in ref.values()
              if "pcm" in r and "web" in r and match.hex_from_lab50(r["pcm"])[1]]
    meta["agreement_de2000"]["C: pcm vs web, inks inside sRGB"] = {"n": len(inside), "mean": round(float(np.mean(inside)), 2),
                                                                  "p95": round(float(np.percentile(inside, 95)), 2)}
    navy = colors["Partner Navy"]
    swatches = []
    for cname, e in colors.items():
        if e["pantone_c"]:
            for side in ("pantone_c", "pantone_u"):
                swatches.append({"name": e[side]["name"], "type": "spot", "mode": "Lab", "lab_d50": e[side]["lab_d50"],
                                 "hex_preview": e[side]["hex"], "brand_color": cname})
        swatches.append({"name": "AAP %s" % cname, "type": "global process", "mode": "CMYK", "profile": P[M][0],
                         "cmyk": e["recommended"]["cmyk"], "cmyk_swop": e["recommended"]["cmyk_swop"], "brand_color": cname})
    swatches.append({"name": "AAP Mono Black", "type": "global process", "mode": "CMYK", "cmyk": [0, 0, 0, 100],
                     "note": "Monochrome Black artboards: single K plate, overprint"})
    doc = {
        "generated_by": "work/print/build.py (match.py + pantone_ref.json); Pillow %s / littleCMS %s" % (
            PIL.__version__, match.ImageCms.core.littlecms_version),
        "method": {
            "lab": "Brand sRGB -> CIELAB D50 (Bradford), the ICC convention Pantone's D50 Lab uses.",
            "pantone_ranking": "CIEDE2000 (kit.de2000), median over the value sets available for each colour: pcm = Pantone "
                               "Color Manager V4 Lab, plus = PANTONE+ Lab (or ok2pan Lab where PANTONE+ lacks the colour), "
                               "web = Pantone's published sRGB (Solid Coated, only where the ink is inside sRGB).",
            "cmyk": "Pillow ImageCms (littleCMS), sRGB -> profile, relative colorimetric + black point compensation. "
                    "raw = 8-bit result in %, clean = whole %, 1-2 % traces dropped and 98-99 % made solid when that "
                    "costs <= 0.5 dE. rt_de2000 = back to Lab with the same intent + BPC (gamut loss); "
                    "paper_relative_de2000 = back to Lab without BPC (what the sheet measures against its white).",
        },
        "document_profile": {
            "recommended": P[M][0], "file": P[M][1],
            "why": ("Darker black point and higher ink limit (TAC %d against %d on SWOP v2): the navy prints at paper-relative "
                    "dE %.1f on GRACoL 2006 against %.1f on SWOP v2, the blue matches as well, and GRACoL 2006 / FOGRA39 are "
                    "the ISO 12647-2 coated-sheetfed conditions most brand collateral is printed to, while SWOP v2 is a web-offset "
                    "publication condition. SWOP v2 is better only for Ribbon Cyan (dE %.1f against %.1f). Coated FOGRA39 is the "
                    "equivalent choice for vendors who print to ISO 12647-2 / FOGRA39 (common outside North America); "
                    "builds for all three are given. Ask each vendor for its printing condition first.") % (
                round(navy["cmyk"]["gracol"]["tac_profile_max"]), round(navy["cmyk"]["swop"]["tac_profile_max"]),
                navy["cmyk"]["gracol"]["paper_relative_de2000_clean"], navy["cmyk"]["swop"]["paper_relative_de2000_clean"],
                colors["Ribbon Cyan"]["cmyk"]["swop"]["rt_de2000_clean"], colors["Ribbon Cyan"]["cmyk"]["gracol"]["rt_de2000_clean"]),
        },
        "colors": colors,
        "illustrator_swatches": swatches,
        "sources": meta,
    }
    (OUT / "print-colors.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "print-colors.md").write_text(md(doc), encoding="utf-8")
    sheet(doc, OUT / "verify" / "print-swatches.png")
    print("wrote", OUT / "print-colors.json", OUT / "print-colors.md", OUT / "verify" / "print-swatches.png")


def sheet(doc, out):
    """Visual check: brand colour | Pantone C | Pantone U | recommended CMYK per profile, soft-proofed to sRGB
    (top half: round trip with BPC; bottom half: paper-relative, i.e. the press black point)."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.load_default(14)
    cw, ch, lw, top = 190, 120, 120, 34
    cols = ["brand sRGB", "PANTONE C", "PANTONE U"] + ["CMYK " + P[p][0].split(" (")[0].replace("Coated ", "") for p in P]
    im = Image.new("RGB", (lw + cw * len(cols), top + (ch + 30) * len(doc["colors"])), "#808080")
    d = ImageDraw.Draw(im)
    for j, c in enumerate(cols):
        d.text((lw + j * cw + 6, 8), c, fill="white", font=font)
    for i, (n, e) in enumerate(doc["colors"].items()):
        y = top + i * (ch + 30)
        d.text((6, y + ch // 2 - 8), n, fill="white", font=font)
        cells = [(e["hex"], None, e["hex"])]
        for side in ("pantone_c", "pantone_u"):
            p = e[side]
            cells.append((p["hex"], None, "%s  dE %.1f" % (p["name"].replace("PANTONE ", ""), p["de2000"])) if p else (None, None, "no ink"))
        for p in P:
            b = e["cmyk_low_tac"][p] if "cmyk_low_tac" in e else None
            v = b["cmyk"] if b else e["cmyk"][p]["clean"]
            top_hex = match.hex_from_lab50(match.cmyk_lab(v, p))[0]
            bot_hex = match.hex_from_lab50(match.cmyk_lab(v, p, bpc=False))[0]
            rt = b["rt_de2000"] if b else e["cmyk"][p]["rt_de2000_clean"]
            pa = b["paper_relative_de2000"] if b else e["cmyk"][p]["paper_relative_de2000_clean"]
            cells.append((top_hex, bot_hex, "%d/%d/%d/%d  rt %.1f  paper %.1f" % (*v, rt, pa)))
        for j, (h1, h2, lab) in enumerate(cells):
            x = lw + j * cw
            if h1:
                d.rectangle([x + 4, y, x + cw - 4, y + ch], fill=h1)
                if h2:
                    d.rectangle([x + 4, y + ch // 2, x + cw - 4, y + ch], fill=h2)
            d.text((x + 6, y + ch + 6), lab, fill="white", font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


def fmt_c(v):
    return "C%d M%d Y%d K%d" % tuple(v)


def lab_s(v):
    return " / ".join("%g" % round(x, 2) for x in v)


def md(doc):
    C, pr, s = doc["colors"], doc["document_profile"], doc["sources"]
    nv = C["Partner Navy"]["cmyk_low_tac"]
    L = []
    w = L.append
    w("# Alliance AI Partners: print colour specification\n")
    w("Spot (PANTONE) and process (CMYK) values behind the CMYK and Pantone master files. Generated by "
      "`work/print/build.py`; the machine-readable twin is `print-colors.json`. For any extra colour (for example the 3D "
      "shading tones) run `python -I work/print/match.py \"#HEX\"`.\n")
    w("## Summary\n")
    w("| Colour | sRGB | Lab D50 | PANTONE C (dE2000) | PANTONE U (dE2000) | CMYK master, %s | CMYK on SWOP v2 |" % pr["recommended"].split(" (")[0])
    w("|---|---|---|---|---|---|---|")
    for n, e in C.items():
        r = e["recommended"]
        sp = lambda k: "none: paper or white ink" if e[k] is None else "%s (%.1f)" % (e[k]["name"], e[k]["de2000"])
        w("| %s | `%s` | %s | %s | %s | %s | %s |" % (n, e["hex"], lab_s(e["lab_d50"]), sp("pantone_c"), sp("pantone_u"),
                                                   fmt_c(r["cmyk"]), fmt_c(r["cmyk_swop"])))
    vb, bc = C["Alliance Blue"], C["Ribbon Cyan"]
    w("\nPlainly: **Alliance Blue %s is outside the CMYK gamut and outside every Pantone ink** (nearest ink dE %.1f, CMYK "
      "dE %.1f to %.1f). **Ribbon Cyan %s is partly outside CMYK** (dE %.1f to %.1f) and its nearest ink is dE %.1f away. "
      "Both print less vivid than on screen, so use the spot inks wherever the job allows. Partner Navy comes close on coated "
      "stock with a spot ink (dE %.1f), but process CMYK cannot print it as dark as the screen (see the notes), and no "
      "uncoated ink comes within dE 15.\n" % (
          vb["hex"], vb["pantone_c"]["de2000"], min(b["rt_de2000_clean"] for b in vb["cmyk"].values()),
          max(b["rt_de2000_clean"] for b in vb["cmyk"].values()), bc["hex"],
          min(b["rt_de2000_clean"] for b in bc["cmyk"].values()), max(b["rt_de2000_clean"] for b in bc["cmyk"].values()),
          bc["pantone_c"]["de2000"], C["Partner Navy"]["pantone_c"]["de2000"]))
    w("dE2000 reading guide: under 1 is invisible side by side, 1 to 2 is a close match, 2 to 4 is noticeable side by side, "
      "above 5 looks like a different colour.\n")

    w("## Pantone matches\n")
    w("dE2000 per value set: **pcm** = Pantone Color Manager V4 Lab, **plus** = PANTONE+ (2010) Lab or, where PANTONE+ "
      "lacks the colour, the ok2pan Lab, **web** = Pantone's published sRGB (coated only, counted only where the ink lies "
      "inside sRGB). The rank is the median. Lab values are CIELAB D50 / 2 deg as Pantone publishes them in its colour "
      "books (8-bit: L* in 0.39 steps, a* and b* in whole units).\n")
    for n, e in C.items():
        w("### %s `%s`\n" % (n, e["hex"]))
        w(e["decision"] + "\n")
        w("| Side | Rank | Candidate | dE2000 (median) | pcm | plus | web | Lab D50 | sRGB (published) |")
        w("|---|---|---|---|---|---|---|---|---|")
        for side, key in (("C", "pantone_c_candidates"), ("U", "pantone_u_candidates")):
            for i, p in enumerate(e[key], 1):
                g = lambda k: "%.2f" % p["de2000_by_set"][k] if k in p["de2000_by_set"] else "-"
                hx = "`%s`" % p["hex"] + (" (slab `%s`)" % p["hex_pantone_com_slab"]
                                          if p["hex_source"] == "web" and "hex_pantone_com_slab" in p else "")
                hx += "" if p["hex_source"] != "slab" else " (slab)"
                w("| %s | %d | %s | **%.2f** | %s | %s | %s | %s | %s |" % (side, i, p["name"], p["de2000"], g("pcm"), g("plus"),
                                                                            g("web"), lab_s(p["lab_d50"]), hx))
        if e["pantone_c"]:
            c, u = e["pantone_c"], e["pantone_u"]
            w("\n**Chosen:** %s, Lab D50 %s, sRGB `%s` (Pantone's published value%s); %s, Lab D50 %s, sRGB `%s` "
              "(pantone.com slab; `%s` computed from its Lab)." % (
                  c["name"], lab_s(c["lab_d50"]), c["hex"],
                  ", pantone.com slab `%s`" % c["hex_pantone_com_slab"] if "hex_pantone_com_slab" in c else "",
                  u["name"], lab_s(u["lab_d50"]), u["hex"], u["hex_from_lab"]))
        if n in ("Pure White", "Daylight"):
            pn = e["pastels_neons_nearest"]
            w("\nPastels & Neons guide (a separate Pantone guide, not ranked above): nearest %s dE %.2f, %s dE %.2f." % (
                pn["C"]["name"], pn["C"]["de2000"], pn["U"]["name"], pn["U"]["de2000"]))
        if "tint_of_pantone_c" in e:
            t = e["tint_of_pantone_c"]
            w("\nA %d %% screen of %s on white stock estimates to Lab %s, dE %.2f (Murray-Davies, before dot gain: proof it)." % (
                t["screen_pct"], e["pantone_c"]["name"], lab_s(t["lab_d50"]), t["de2000"]))
        w("")

    w("## CMYK builds\n")
    w("ICC conversions with Pillow ImageCms (littleCMS %s): sRGB to each profile, relative colorimetric with black point "
      "compensation. **raw** is the 8-bit result, **clean** is whole percent with 1-2 %% traces dropped and 98-99 %% made "
      "solid, each only when it costs at most 0.5 dE2000. **rt dE** is the round trip back to Lab with the same intent and "
      "BPC, which isolates gamut loss. **paper dE** reads the build back without BPC, which is what the printed sheet "
      "measures against its own white: dark colours lose depth there because a press black is lighter than screen black. "
      "The Lab readback is averaged over neighbouring 8-bit inputs (precision about 0.05 dE).\n" % doc["generated_by"].split("littleCMS ")[1])
    w("| Colour | Profile | raw | clean | TAC (profile max) | rt dE raw | rt dE clean | paper dE clean |")
    w("|---|---|---|---|---|---|---|---|")
    for n, e in C.items():
        for p, b in e["cmyk"].items():
            w("| %s | %s | %s | %s | %d (%d) | %.2f | %.2f | %.2f |" % (
                n, b["profile"], " / ".join("%g" % v for v in b["raw"]), fmt_c(b["clean"]), b["tac_clean"],
                round(b["tac_profile_max"]), b["rt_de2000_raw"], b["rt_de2000_clean"], b["paper_relative_de2000_clean"]))
    w("\n**Partner Navy, low-TAC build (recommended).** The profiles separate the navy almost as a four-colour rich black "
      "(TAC %s). A K-heavy, yellow-free build found by minimising the same round-trip dE2000 matches as well with far less "
      "ink, dries faster and tolerates misregistration better because the black plate carries the shape:\n" %
      " / ".join(str(C["Partner Navy"]["cmyk"][p]["tac_clean"]) for p in P))
    w("| Profile | Low-TAC build | TAC | rt dE | paper dE |")
    w("|---|---|---|---|---|")
    for p, b in nv.items():
        w("| %s | %s | %d | %.2f | %.2f |" % (P[p][0], fmt_c(b["cmyk"]), b["tac"], b["rt_de2000"], b["paper_relative_de2000"]))
    w("\n### Document profile\n")
    w("**Recommended: %s** (`%s`). %s\n" % (pr["recommended"], pr["file"], pr["why"]))
    w("The default build per colour for the CMYK master is the **clean** build on that profile (navy: the low-TAC build). "
      "The SWOP v2 column of the summary is the drop-in set if the master stays on SWOP.\n")

    w("## Practical notes\n")
    pl = nv["gracol"]["lab_d50_paper_relative"][0], nv["swop"]["lab_d50_paper_relative"][0]
    w("**K100 versus rich navy.** The Monochrome Black (1-colour) artboards are `C0 M0 Y0 K100` and nothing else: stamps, "
      "embossing and foil dies, laser engraving and 1-colour jobs need a single plate, and a four-colour black would "
      "misregister on fine detail. Set K100 type to overprint. Navy is different: large dark-mode backgrounds and "
      "big shapes take the multi-ink navy (`%s` on GRACoL 2006, `%s` on SWOP v2) because K100 alone prints a flat charcoal "
      "(dE about 10 from the navy). Even so, process navy measures about L* %.0f on GRACoL and L* %.0f on SWOP against L* %.1f "
      "on screen, while the spot ink %s sits at L* %.1f, so stationery and anything with fine navy type is best printed "
      "with the spot. Keep reversed (white) type out of rich navy at 8 pt bold or larger, and avoid hairlines.\n" % (
          fmt_c(nv["gracol"]["cmyk"]), fmt_c(nv["swop"]["cmyk"]), pl[0], pl[1], C["Partner Navy"]["lab_d50"][0],
          C["Partner Navy"]["pantone_c"]["name"], C["Partner Navy"]["pantone_c"]["lab_d50"][0]))
    w("**White ink on dark substrates.** On paper, white is unprinted stock and the Monochrome White artboards are "
      "knockouts. On dark, clear or metallic media (vehicle-wrap film, clear decals, dark garments, kraft, dark plastic) "
      "white has to be printed: add a spot swatch for the white ink, named exactly as the vendor's RIP expects (Roland "
      "VersaWorks, for example, looks for `RDG_WHITE`), give it a visible proxy colour, put it on its own layer set to "
      "overprint, and add a white underbase beneath the blue and cyan so they stay bright (choke the underbase slightly so "
      "no white halo shows). Wrap printers usually print CMYK on white cast film and convert spots in their RIP: send the "
      "Pantone references and ask for a printed swatch. For cut-vinyl signage, pick the nearest stock film colour from the "
      "film maker's swatch book using the Pantone references.\n")
    w("**Embroidery.** Thread is matched to colour references, not mixed: give the digitiser the PANTONE C references "
      "(%s) and the hex values, let them map to their thread line (the major thread makers publish Pantone cross-reference "
      "charts) and approve a physical sew-out, since glossy rayon or polyester reads brighter than ink. Stitch only the flat "
      "lockups (two-colour or 1-colour marks); the 3D gradient cannot be stitched. Keep lettering at least about 6 mm "
      "(1/4 in) tall and drop the tagline on small placements. On navy garments use the Monochrome White or the white and "
      "cyan mark.\n" % ", ".join(C[k]["pantone_c"]["name"].replace("PANTONE ", "") for k in ("Alliance Blue", "Ribbon Cyan", "Partner Navy")))
    w("**3D gradient logo with spot inks.** The full-colour gradient master is a process (CMYK) file. If a spot version is "
      "needed (for example 2-colour offset, flexo or screen with %s and %s), rebuild the gradient with the spot swatches as "
      "stops: Illustrator outputs a DeviceN blend in which each plate carries its own tint ramp. Do not mix process and spot "
      "stops in one gradient unless the printer agrees. A tint ramp of one ink only gets lighter, so shading darker than the "
      "full-strength ink needs a third, darker ink (a low tint of %s overprinting) or the shading flattens. Keep the lightest "
      "tint at 3 to 5 %% or more (smaller dots drop out and leave a hard edge) and check long gradients for banding. Where "
      "two transparent spot inks overlap they print darker than the on-screen blend: check Overprint Preview and "
      "Separations Preview and ask for a press proof or drawdown. Screen-printed apparel and embroidery use the flat "
      "versions.\n" % tuple(C[k]["pantone_c"]["name"] for k in ("Alliance Blue", "Ribbon Cyan", "Partner Navy")))
    w("**Defining the spot swatches in Illustrator.** Pantone libraries are no longer bundled with Illustrator (Pantone "
      "Connect is required), so create each spot by hand: Swatch Options, Color Type = Spot Color, Color Mode = Lab, the Lab "
      "D50 values above and the exact name (`%s`, `%s`, `%s`; the U names for uncoated jobs). Printers match by the name; "
      "the Lab values drive the on-screen preview and any conversion. `illustrator_swatches` in the JSON lists them with "
      "the process swatches.\n" % tuple(C[k]["pantone_c"]["name"] for k in ("Alliance Blue", "Ribbon Cyan", "Partner Navy")))

    a = s["agreement_de2000"]
    w("## Method and caveats\n")
    w("- Pantone Lab values are absolute measurements of the guide swatches (D50, 2 deg, white = perfect diffuser) while "
      "the brand colours are screen colours (white = paper). Pantone's own conversions compare them the same way; it "
      "matters most for the whites, where the coated paper itself (about L* 95) is the closest match.")
    w("- The newest Pantone data (Solid Coated V5 in Pantone Connect, with decimals) needs a paid account and was not "
      "used. The PCM V4 export equals the V3 export (Aug 2019) for all 1,846 shared colours. PCM V4 and PANTONE+ (2010) "
      "differ by mean dE %.2f (p95 %.2f) on the %d coated colours they share, and PCM V4 and Pantone's published sRGB by "
      "mean dE %.2f (p95 %.2f) for the %d inks inside sRGB. Where the value sets disagree on the order (Partner Navy) the "
      "difference is inside that spread." % (a["C: pcm vs plus"]["mean"], a["C: pcm vs plus"]["p95"], a["C: pcm vs plus"]["n"],
                                              a["C: pcm vs web, inks inside sRGB"]["mean"], a["C: pcm vs web, inks inside sRGB"]["p95"],
                                              a["C: pcm vs web, inks inside sRGB"]["n"]))
    w("- The measurement condition (M0, M1, M2) shifts Pantone Lab values on paper with optical brighteners, and the colour "
      "books used here do not state theirs. Treat dE differences under about 1 as ties.")
    w("- pantone.com slab images are lossy WebP, within 1-2 levels of Pantone's sRGB: the pantonecolors.net hex values "
      "match them that closely, and PCM V4 Lab sits at mean dE %.2f (coated) and %.2f (uncoated) from them. Uncoated sRGB "
      "values come only from those slabs." % (a["C: pcm vs slab"]["mean"], a["U: pcm vs slab"]["mean"]))
    w("- littleCMS and Adobe's ACE engine implement black point compensation slightly differently, so Illustrator's own "
      "conversion can differ from these builds by 1-2 points per channel. Confirm critical colours with a contract proof.")
    w("- The Pastels & Neons guide and 13 colours found only in PANTONE+ 2010 (metallics 871-877 and a few base inks) are "
      "kept in `work/print/pantone_ref.json` but excluded from the main ranking.")
    w("- `pantone_ref.json` is Pantone colour data taken from third-party mirrors of Pantone's colour books: use it "
      "internally for matching and do not publish or ship it with the brand kit.\n")

    w("## Using match.py for other colours\n")
    w("```\npython -I docs/brand-kit/_build/work/print/match.py \"#2A6FFF\" \"#0B1220\"\n```\n")
    w("or `import match; match.match(\"#2A6FFF\")`: top-3 Pantone C and U with dE per value set, CMYK builds on the three "
      "profiles and the recommended set. `pantone_ref.json` holds %d Solid Coated and %d Solid Uncoated entries; "
      "`make_ref.py` rebuilds it from the sources below.\n" % (sum(s["counts"]["C"].values()), sum(s["counts"]["U"].values())))

    w("## Sources\n")
    for k, v in s["sets"].items():
        w("- **%s**: %s. %s" % (k, v["desc"], v["url"]))
    w("- **pcm V3 check**: Pantone Color Manager export, Aug 2019 (PANTONE+ Solid Coated / Uncoated V3). "
      "https://github.com/adai-me/Pantone-color-libraries")
    w("- **web**: %s. %s" % (s["web"]["desc"], s["web"]["url"]))
    w("- **slab**: pantone.com colour finder pages (values on the page sit behind Pantone Connect; the slab images are "
      "public), e.g. " + ", ".join("https://www.pantone.com/color-finder/" + c for c in
                                    ("2726-c", "305-c", "7547-c", "656-c", "2387-u", "305-u", "5395-u", "656-u")))
    w("- 7547 C hex cross-check (#131E29): https://www.colorxs.com/color/pantone-7547-c")
    w("- White-ink spot naming (Roland VersaWorks `RDG_WHITE`): "
      "https://downloadcenter.rolanddg.com/contents/manuals/UV-Guide_USE_EN/sjr1605050982690.html")
    w("- V4 measurement-condition context (Pantone moved its targets to M1 with V4): "
      "https://printplanet.com/threads/pantone-or-not.291618/")
    w("- Why libraries rebuilt from website sRGB are not Pantone Lab (screened, not used): "
      "https://community.adobe.com/t5/illustrator-discussions/for-the-community-unofficial-2024-pantone-solid-coated-acb-file-quot-v5-quot/m-p/14782030")
    w("- ICC profiles: Adobe's `USWebCoatedSWOP.icc`, `CoatedGRACoL2006.icc`, `CoatedFOGRA39.icc` in "
      "`C:\\Program Files (x86)\\Common Files\\Adobe\\Color\\Profiles\\Recommended`.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
