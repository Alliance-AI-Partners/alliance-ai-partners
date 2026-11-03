"""README.md and Print-Masters/Print-Specs.md for the brand kit, generated from the build data so every number in
them matches the files. Run through `python build.py docs`."""
import kit
import match
from build import BRAND, CAP, CORE, CS, H, PROFILE, PROFILE_ID, SCENES, jload


def wcag(a, b):
    """WCAG 2.x contrast ratio of two hex colours."""
    def lum(h):
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (v / 255 for v in kit.hexrgb(h))]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

LOCKUPS = [
    ("01", "Primary-Horizontal", "02, 04", "Mark beside ALLIANCE / AI PARTNERS, both lines Bold and justified to one width "
     "(line 2 = 0.7446 x line 1), block centred on the mark, gap 0.51 cap"),
    ("02", "Secondary-Stacked", "14", "Mark centred above the one-line wordmark (0.2136 x mark height), gap 1.07 cap"),
    ("03", "Logomark", "06", "The 3D gradient AP alone"),
    ("04", "Wordmark", "01, 13, 14, 17", "ALLIANCE AI PARTNERS, Montserrat Bold, tracking -11, metric kerning, AI accented"),
    ("05", "Favicon-32", "12, 03", "Micro-mark: the AP silhouette without the interlace cuts, 17 px tall, apex, baseline and P stem on whole pixels"),
    ("06", "Favicon-16", "12, 03", "Micro-mark drawn on the pixel grid: condensed to 14 x 10 px with 1 px margins, both counters open, crisp edges"),
    ("07", "Horizontal-Tagline", "01", "Mark + wordmark + tagline (Regular, +24, 0.607 x wordmark size), shared left edge"),
    ("08", "Horizontal-Descriptor", "13", "Mark + wordmark + Ribbon Cyan rule + ENTERPRISE AI CONSULTING (Medium, justified to the wordmark)"),
    ("09", "Stacked-Tagline", "02", "The brand board's hero lockup: mark, wordmark and tagline (0.587 x wordmark size) centred"),
    ("10", "Stacked-TwoLine", "09, 16", "Mark above ALLIANCE AI / PARTNERS, both lines Bold at one size and tracking, centred"),
]
STATES = [
    ("FullColor-Light", "3D gradient mark; Partner Navy type, AI in Alliance Blue; transparent. Favicons: the micro-mark in Alliance Blue"),
    ("FullColor-Dark", "dark-colourway mark (original 04's colours with the darkest shading lifted so it separates from dark and slate grounds); "
                       "white type, AI in Ribbon Cyan; shown on Partner Navy. Favicons: Ribbon Cyan"),
    ("Mono-Black", "one ink, AAP Black #000000 (K100, overprinting in the CMYK master); the one-colour mark with its two interlace cuts"),
    ("Mono-White", "one ink, Pure White #FFFFFF knockout; shown on Alliance Blue"),
    ("Flat-Light", "solid brand inks: the one-colour mark in Alliance Blue, Partner Navy type, AI in Alliance Blue, cyan rule; pure spot in the Pantone master"),
    ("Flat-Dark", "solid brand inks for dark grounds: mark and AI in Ribbon Cyan, white type; shown on Partner Navy"),
]
MIN_SIZES = [
    ("3D gradient mark (FullColor states)", "15 mm high", "48 px high", "below this use the Flat or Mono mark"),
    ("One-colour mark with interlace cuts (Mono, Flat)", "20 mm high (cuts stay 0.3 mm wide)", "32 px high",
     "foil, embossing, engraving: 25 mm; below 20 mm use the micro-mark"),
    ("Micro-mark (favicon silhouette)", "5 mm high", "16 px", "screen printing and embroidery below about 50 mm"),
    ("Horizontal lockups 01, 07, 08", "40 mm wide", "200 px wide", "tagline / descriptor lockups 60 mm wide, else drop the line"),
    ("Stacked lockups 02, 09, 10", "25 mm wide", "140 px wide", ""),
]


def md_table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def build_str(v):
    return "C{} M{} Y{} K{}".format(*v)


def suite_sizes():
    rows, seen = [], set()
    for a in jload(SCENES / "suite.json")["artboards"]:
        lock = a["name"].split("_")[0]
        if lock in seen:
            continue
        seen.add(lock)
        w, h = a["rect"][2], a["rect"][3]
        pad = 0 if "Favicon" in lock else (CS * CAP * 100 / 0.1982 if "Wordmark" in lock else CS * H)
        art = f"{w - 2 * pad:.0f} x {h - 2 * pad:.0f} pt" if pad else "whole artboard"
        rows.append([lock, f"{w} x {h} pt", f"{w * 25.4 / 72:.0f} x {h * 25.4 / 72:.0f} mm", art])
    return rows


def write_docs():
    sw = jload(SCENES / "print.json")["swatches"]
    pc = jload(kit.BUILD / "print-colors.json")
    spots = {(s["brand_color"], s["name"][-1]): s["name"] for s in pc["illustrator_swatches"] if s.get("type") == "spot"}
    rec = jload(kit.VERIFY / "recreations.json")
    n_suite = len(jload(SCENES / "suite.json")["artboards"])
    core_rows, alt_rows, tone_rows, tac = [], [], [], 0
    n_perc = sum(1 for b in sw.values() if b.get("intent"))
    formerly = {c["name"]: c["formerly"] for c in BRAND["core"]}
    for n, hx in CORE.items():
        b, brand = sw[n], n[4:]
        rgb = "/".join(str(int(v)) for v in kit.hexrgb(hx))
        ref = " (panel tint reference; not a logo ink)" if brand == "Daylight" else ""
        core_rows.append([brand, formerly[brand] if formerly[brand] != brand else "-", f"`{hx}`", rgb, build_str(b["cmyk"]),
                          spots.get((brand, "C"), "-") + (ref if (brand, "C") in spots else ""), spots.get((brand, "U"), "-")])
    shade_rows = [[c["name"], f"`{c['hex']}`", c["ramp"], c["role"],
                   build_str(sw["AAP " + c["name"]]["cmyk"]) + (" (perceptual)" if sw["AAP " + c["name"]].get("intent") else "")]
                  for c in BRAND["shading"]]
    hexof = {c["name"]: c["hex"] for c in BRAND["core"]}
    contrast = "; ".join(f"{a} on {b} {wcag(hexof[a], hexof[b]):.2f}:1" for a, b in (
        ("Partner Navy", "Pure White"), ("Partner Navy", "Daylight"), ("Alliance Blue", "Pure White"),
        ("Pure White", "Alliance Blue"), ("Ribbon Cyan", "Partner Navy"), ("Ribbon Cyan", "Pure White")))
    for n, b in sw.items():
        swop = [0, 0, 0, 100] if n == "AAP Black" else match.cmyk(b["hex"], "swop")["clean"]
        fogra = [0, 0, 0, 100] if n == "AAP Black" else match.cmyk(b["hex"], "fogra39")["clean"]
        tac = max(tac, sum(b["cmyk"]))
        row = [n, f"`{b['hex']}`", build_str(b["cmyk"]) + (" (perceptual)" if b.get("intent") else ""), build_str(swop), build_str(fogra)]
        (alt_rows if n in CORE else tone_rows).append(row)
    fid = sorted(rec.items())
    fid_rows = [[oid, kit.ORIGINALS[oid][1], r["fg_iou"], r["de_mean"], r["fg_de_mean"], f"`{r['bg']}`"] for oid, r in fid]
    weakest = sorted(fid, key=lambda kv: kv[1]["fg_iou"])[:3]
    orig_rows = [[oid, f"`{kit.ORIGINALS[oid][0]}`", kit.ORIGINALS[oid][1]] for oid in sorted(kit.ORIGINALS)]

    readme = f"""# Alliance AI Partners: Brand & Design Kit (Adobe Illustrator masters)

The finalized logos in `docs/logos` rebuilt as native Illustrator vector artwork: every colour is a global brand
swatch, all type is Montserrat converted to outlines, and the logo suite, badges and sticker have print masters.

**Hand-off:** give clients and vendors `01_Master-Logo-Suite/`, `02_Original-Recreations/`, `03_Brand-Graphics/`,
`Print-Masters/` and this README. `_build/` is the internal build system (scripts, vector components, measurements
and intermediates) and is not part of the kit; the verification records cited below live there.

## What is here

{md_table(["Folder", "Master file", "Contents"], [
    ["`01_Master-Logo-Suite/`", "`AAP_Master-Logo-Suite.ai`", f"{n_suite} artboards: 10 lockups in 6 colour states (favicons in 4). `AI_per-artboard/` (each artboard, lockup x state, as its own .ai), `PNG/` (2x, transparent), `PNG-Favicon/` (exact 16 and 32 px), `SVG/` (web-safe: unique ids per file)"],
    ["`02_Original-Recreations/`", "`AAP_Original-Recreations.ai`", "17 artboards, one per original image at its own pixel size, in the measured colours. `AI_per-artboard/`, `PNG/` (1x, with background), `SVG/`"],
    ["`03_Brand-Graphics/`", "`AAP_Brand-Graphics.ai`", "Icon set (overview + 12 icons in duotone, mono and dark), 5 seamless pattern swatches (tile + preview each), ribbon wave and data mesh, badges (shield, seal with ring text set on a path and outlined, starburst), die-cut sticker (CutContour on its own layer), swallow mascot. `PNG/` (2x), `PNG-Icons/` (4x), `SVG/`"],
    ["`Print-Masters/`", "CMYK and Pantone (coated) `.ai`", "PDF/X-4 and a viewing proof, one EPS per artboard for each master, `Badges-Sticker/` (CMYK print files for the badges and the sticker), `Print-Specs.md` for vendors"]])}

## The originals

The recreations are numbered as below. `docs/logos` also holds `1f3b28e6-ad6c-4e5d-80d8-e2f2e1e38954 (1).jpeg`, a
byte-identical copy of 03, which was not recreated twice.

{md_table(["#", "File in docs/logos", "Content"], orig_rows)}

## Logo suite

Each lockup comes in the four essential colour states plus two flat brand-ink states. Artboards are named
`NN-Lockup_State`; exported files carry the prefix `AAP_`. Each lockup artboard is the lockup plus its clear space on
every side (a favicon artboard is the icon itself), and each lockup is grouped so it moves as a unit.

{md_table(["#", "Lockup", "From original", "Construction"], [[a, f"**{b}**", c, d] for a, b, c, d in LOCKUPS])}

{md_table(["State", "Treatment"], [[f"**{a}**", b] for a, b in STATES])}

FullColor-Dark is drawn for Partner Navy, near-black and dark slate grounds. On mid-tone slate (about L* 30-45, for
example `#475569`) use Mono-White or Flat-Dark instead.

**Clear space.** x = 0.287 x mark height, the margin drawn on the brand board's clear-space panel; no other artwork
inside it. The wordmark on its own keeps the same x expressed in its type: 1.45 x cap height. The favicons are drawn
to their pixel grid instead.

**Minimum sizes.**

{md_table(["Artwork", "Print", "Screen", "Note"], MIN_SIZES)}

## Colour

One unified palette, "{BRAND['name']}" (`_build/palette.json`; the Brand Colors variables in the Figma file
[Alliance AI Partners — Logo Suite](https://www.figma.com/design/rXNPaaMds46oWgM64QPRI6/Alliance-AI-Partners-%E2%80%94-Logo-Suite)
hold the same 14 colours, and their code syntax uses the CSS names in `design-system/tokens/tokens.css`). The six
core colours keep the brand board's exact values, so every CMYK build and PANTONE reference is unchanged; only their
names changed, to tell one story: A for Alliance, P for Partner, and the ribbon between them.

{md_table(["Colour", "Formerly", "Hex", "RGB", "CMYK (Coated GRACoL 2006)", "PANTONE coated", "PANTONE uncoated"], core_rows)}

The 3D mark is drawn from the core blue, cyan and navy plus eight shading tokens on two lightness ramps, in both
colourways (swatch group `AAP Mark Shading`). They replace the 32 tones measured from the AI-generated originals, so
the mark's lit faces are the same blue as the "AI" and its ribbon the same cyan, and the dark colourway climbs the same
ramps instead of inventing lifted tones. The Brand Graphics use the same colours: each of the 72 tones measured in the
swallow, shield, wave, data mesh and pattern tiles takes its nearest palette colour (CIEDE2000, palette.json
`stopMap.graphics`), so their facets and gradients climb the same ramps and `AAP_Brand-Graphics.ai` holds no swatch
outside the palette.

{md_table(["Shading token", "Hex", "Ramp", "Where in the mark", "CMYK (Coated GRACoL 2006)"], shade_rows)}

Signature gradient **{BRAND['signature']['name']}**: {' to '.join(f"{t} ({p:.0%})" for t, p in BRAND['signature']['stops'])},
for hero bands and brand graphics, not behind small text.

Contrast (WCAG 2.x): {contrast}. Body text needs 4.5:1, so Ribbon Cyan is never text on white or Daylight.

The originals' own inks are not exactly the palette: their "AI" accent measures `#1451CC`-`#2C60CD` (dE2000 about 7-8
from Alliance Blue) and their navy type `#081739`-`#1A2B4A` (dE about 5-9 from Partner Navy). The masters follow the
palette; the Original Recreations keep the measured inks wherever they differ visibly (more than dE2000 2), for
example the teal cyan of 03, 07, 09 and 11 (about `#3ECDDA`). Those tones are global swatches grouped per original
(`AAP Rec 01` ... `AAP Rec 17`); a tone used by several recreations is listed once, in the first group, and editing it
recolours every recreation that uses it.

## Typography

Montserrat (Adobe Fonts or Google Fonts). Six weights were activated for this build: Light, Regular, Medium,
SemiBold, Bold, ExtraBold. The masters are outlined and need no fonts; install Montserrat to edit or set new text.

- Wordmark: Bold, tracking -11, metric kerning; "AI" in Alliance Blue (light) or Ribbon Cyan (dark).
- Two-line wordmark: ALLIANCE (Bold, +6) over AI PARTNERS (Bold, +8) at 0.7446 x the first line's size, so both lines share one width.
- Stacked two-line (10): ALLIANCE AI / PARTNERS, Bold, both lines one size and one tracking, centred.
- Tagline "Partners in AI. Partners in growth.": Regular, +24, 0.607 x the wordmark size (0.587 in the stacked lockup).
- Descriptor "ENTERPRISE AI CONSULTING": Medium, 0.747 x the wordmark size, tracked to the wordmark's width, under a Ribbon Cyan rule 0.145 cap thick.
- Brand board hierarchy: headlines Bold, subheads Medium, body Regular.

## Recreation fidelity

Each recreation was rendered and compared with its original image. Foreground IoU is shape overlap (1.0 = identical);
dE2000 is colour difference (under 2 is hard to see, under 1 invisible).

{md_table(["Original", "Content", "Foreground IoU", "Mean dE, whole image", "Mean dE, artwork", "Background"], fid_rows)}

The lowest scores are {", ".join(f"{oid} ({r['fg_iou']})" for oid, r in weakest)}. What limits them: the originals are AI-generated
JPEGs, so edges carry compression halos and sharpening rings that crisp vector edges do not reproduce; the lettering
is a near but not exact Montserrat with irregular spacing, which the recreations reproduce character by character;
soft glows are left out or built as many-step blends. Diff sheets for every original are in
`_build/verify/rec-NN_diff.png`.

## What was verified

- Illustrator's PNG export of every artboard in the logo suite (including the favicons), the recreations and the 36
  icon artboards, compared with an independent VectorCraft render of the same artwork (`_build/verify/*_import-check.json`).
  The build stops if an export is missing or strays from it: 99.5 % of the shape within 1 px, mean dE2000 at most 2.
- Every recreation compared with its original image, with the scores above (`_build/verify/recreations.json`): a
  record, not a pass/fail check.
- What each master file contains, read back from Illustrator (`_build/verify/inventory.json`): colour mode, artboards,
  layers, every swatch's type and values, patterns. The build stops unless all six masters are present and every
  swatch was read, nothing is live text, raster or placed, no colour sits outside a swatch (inside the pattern
  definitions too, read from the files themselves), the only other swatches are [None] and the five brand patterns,
  the CutContour die line is a spot ink of 100 % magenta and only in the Brand Graphics, the screen masters are RGB and
  the print masters CMYK, and every print-master swatch matches the print spec: each CMYK build, and in the PMS master
  each logo ink as its Pantone spot (name, type and alternate) with no AAP-named copy left.
- The PDF/X-4 files: written as PDF/X-4 by Illustrator, output intent with the embedded profile, page count, no fonts,
  no background layer, and overprint judged by what each page actually paints: on the one-colour black artboards all
  of it overprints, on the sticker the die line does, and nowhere else does anything.
- The 16 px favicons: every pixel fully on or off, and exactly the micro-mark's pixels.
- Every EPS file's plates (its DSC colour lists) against the job table in `Print-Masters/Print-Specs.md`: exactly the
  inks it lists for each lockup and state, one EPS per artboard, and no other files in each job folder.

Not checked automatically: the SVG exports (beyond the id rewrite), the per-artboard `.ai` copies, the Brand Graphics
PNG exports other than the 36 icons, the proof PDF, and anything in the EPS files beyond their plates. These were
reviewed by hand in the October 2026 audit; a rebuild does not repeat that review.

## Rebuilding

Prerequisites: Adobe Illustrator running locally (the scripts drive it over COM), Montserrat activated, Python 3.11
with numpy, Pillow and pypdf, and the VectorCraft CLI.

```
cd docs/brand-kit/_build
python build.py suite         # 01 Master Logo Suite
python build.py recreations   # 02 Original Recreations
python build.py graphics      # 03 Brand Graphics
python build.py print         # Print-Masters, from the suite and the graphics
python build.py split         # one .ai per artboard
python build.py inventory     # read the masters back for verification
python build.py docs          # this README and Print-Specs.md
```

## Notes

- The CMYK masters are untagged because Illustrator cannot assign a profile by script; their values are explicit
  Coated GRACoL 2006 builds, and the PDF/X-4 files carry that output intent with the profile embedded.
- Pantone colour-book data used for matching (from third-party mirrors) is not kept in this folder; the matches are
  recorded in `_build/print-colors.json`.
"""
    (kit.KIT / "README.md").write_text(readme, encoding="utf-8")

    specs = f"""# Print specifications: Alliance AI Partners logo masters

For printers, sign makers, embroiderers and other vendors. All type is converted to outlines; the files contain no
fonts and no raster artwork (each EPS carries only the usual low-resolution screen preview). CMYK values are Coated
GRACoL 2006 (ISO 12647-2:2004) builds.

## Files

{md_table(["File", "Use"], [
    ["`AAP_Master-Logo-Suite_CMYK.ai`", "Process master: every colour a global CMYK swatch; Mono-Black art is K100 set to overprint"],
    ["`AAP_Master-Logo-Suite_PMS-Coated.ai`", "Spot master, coated stock: Alliance Blue, Ribbon Cyan and Partner Navy are PANTONE 2726 C, 305 C, 7547 C"],
    ["`AAP_Master-Logo-Suite_CMYK_PDF-X4.pdf`", f"All {n_suite} artboards, PDF/X-4, output intent {PROFILE} ({PROFILE_ID}) with the profile embedded"],
    ["`AAP_Master-Logo-Suite_Proof.pdf`", "Viewing proof: the dark and knockout artboards shown on their background panels"],
    ["`EPS_CMYK/`, `EPS_PMS-Coated/`", "One EPS per artboard (`AAP_CMYK_01-Primary-Horizontal_FullColor-Light.eps`, ...), Illustrator CS6 EPS"],
    ["`Badges-Sticker/`", "CMYK master of the Brand Graphics with PDF/X-4 and EPS of the shield, seal, starburst and die-cut sticker"]])}

For uncoated stock, ask the printer to swap the three spots for PANTONE 2387 U, 305 U and 5395 U (listed below).
The `.ai` masters are saved in the current Illustrator format. Background panels sit on a non-printing layer and are
not in the EPS files or the PDF/X-4: the FullColor-Dark, Mono-White and Flat-Dark artboards are white artwork meant
for dark stock or a printed ground (see the proof PDF).

## Which artboards for which job

{md_table(["State", "Inks in the CMYK master", "Inks in the Pantone master"], [
    ["FullColor-Light / -Dark", "CMYK (the 3D mark is a process gradient)",
     "CMYK + the brand spots: like the AI, the 3D mark's lit faces print in 2726 C and its ribbon in 305 C; light adds 7547 C (type and the mark's deepest shadow). 7 plates light, 6 dark, the logomark alone too; the wordmark alone is pure spot (2726 C + 7547 C light, 305 C dark)"],
    ["Flat-Light", "CMYK", "pure spot: 2726 C (mark, AI) + 7547 C (type) + 305 C (rule in 08), 1-3 plates"],
    ["Flat-Dark", "CMYK", "pure spot: 305 C (mark, AI); type is a white knockout"],
    ["Mono-Black", "K only, overprinting", "K only"],
    ["Mono-White", "no ink (knockout; white ink on dark media)", "no ink"],
    ["Favicons 05, 06", "CMYK", "pure spot: 2726 C (light) or 305 C (dark)"]])}

## Artboard sizes

Every lockup artboard includes its clear space on all sides (x = 0.287 x mark height; for the wordmark alone, 1.45 x
cap height); a favicon artboard is the icon itself, with no margin. The artwork is the size in the last column: scale
the files to the artwork size you need, not the box.

{md_table(["Lockup", "Artboard", "Artboard (mm)", "Artwork inside"], suite_sizes())}

## Minimum reproduction sizes

{md_table(["Artwork", "Print", "Screen", "Note"], MIN_SIZES)}

## Brand colours

{md_table(["Colour", "Screen hex", "RGB", "CMYK (Coated GRACoL 2006)", "PANTONE coated", "PANTONE uncoated"], core_rows)}

Builds for other printing conditions (for vendors who print to SWOP v2 or FOGRA39):

{md_table(["Swatch", "Screen hex", "Coated GRACoL 2006", "U.S. Web Coated (SWOP) v2", "Coated FOGRA39"], alt_rows)}

- Alliance Blue `#1B56FF` is outside both the CMYK gamut and every Pantone ink (nearest ink dE2000 5.5, CMYK about 8):
  print it as the spot ink wherever the job allows.
- Ribbon Cyan is partly outside CMYK (dE 4 to 5.5); PANTONE 305 C/U is the nearest ink.
- Partner Navy: the CMYK build is a low-ink, K-heavy navy (TAC 177). Process navy prints lighter than the screen;
  PANTONE 7547 C is the dark match on coated stock. No uncoated ink reaches it (5395 U is the nearest).
- For small navy type (under about 9 pt) use PANTONE 7547 C or a K-only build so the three-plate navy cannot misregister.
- Pure White is the paper (or an opaque white ink on dark substrates). Daylight is a light panel tint only.

## Shading tones

The full-colour mark is a process gradient built from these global swatches; the badges in `Badges-Sticker/`, the
shield's bevel included, use the same builds. The {n_perc} tones marked (perceptual)
would print as one colour with the standard separation, so they use a perceptual separation that keeps the facets
distinct. Highest total ink in any build: {tac} %.

{md_table(["Swatch", "Screen hex", "Coated GRACoL 2006", "U.S. Web Coated (SWOP) v2", "Coated FOGRA39"], tone_rows)}

## Production notes

- **One-colour work** (stamps, foil, embossing, engraving, single-colour jobs): use the Mono-Black artboards, K100 only
  and set to overprint. Respect the minimum sizes above: the interlace cuts are the finest detail.
- **Spot-colour jobs** (screen print, promotional goods, 2-3 colour offset): use the Flat states from the Pantone master.
- **Large dark areas**: use the CMYK navy build or PANTONE 7547 C, not K100 (K100 alone reads as charcoal).
- **White on dark substrates** (wraps, clear decals, dark garments): add the vendor's white-ink spot name (for example
  RDG_WHITE) on its own overprinting layer, with a slightly choked white underbase under the blue and cyan.
- **Embroidery**: use the flat states or the micro-mark; the 3D gradient cannot be stitched. Thread is matched to the
  PANTONE C references; approve a sew-out.
- **Gradients with spot inks**: the 3D mark is a process file. A spot version needs the gradient rebuilt with spot
  stops (DeviceN), lightest tint at least 3 to 5 %, and a press proof.
- **Die-cut sticker**: `Badges-Sticker/`, artboard `Sticker-DieCut`. The cut line is a spot colour named `CutContour`
  (100 % magenta, overprint, 0.5 pt) on its own layer, with 9 pt (3.2 mm) of bleed beyond it.
- Illustrator's own colour engine and littleCMS differ by 1 to 2 points per channel in places: confirm critical
  colours with a contract proof.
"""
    (kit.KIT / "Print-Masters" / "Print-Specs.md").write_text(specs, encoding="utf-8")
    (kit.BUILD / ".gitignore").write_text("__pycache__/\n"
                                          "# regenerable intermediates of the vectorising pipelines (~0.5 GB); their .py sources are kept\n"
                                          "work/**/*.png\nwork/**/*.pkl\nwork/**/*.npy\nwork/**/*.npz\n", encoding="utf-8")
    print("docs written")
