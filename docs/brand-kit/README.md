# Alliance AI Partners: Brand & Design Kit (Adobe Illustrator masters)

The finalized logos in `docs/logos` rebuilt as native Illustrator vector artwork: every colour is a global brand
swatch, all type is Montserrat converted to outlines, and the logo suite, badges and sticker have print masters.

**Hand-off:** give clients and vendors `01_Master-Logo-Suite/`, `02_Original-Recreations/`, `03_Brand-Graphics/`,
`Print-Masters/` and this README. `_build/` is the internal build system (scripts, vector components, measurements
and intermediates) and is not part of the kit; the verification records cited below live there.

## What is here

| Folder | Master file | Contents |
|---|---|---|
| `01_Master-Logo-Suite/` | `AAP_Master-Logo-Suite.ai` | 56 artboards: 10 lockups in 6 colour states (favicons in 4). `AI_per-artboard/` (each artboard, lockup x state, as its own .ai), `PNG/` (2x, transparent), `PNG-Favicon/` (exact 16 and 32 px), `SVG/` (web-safe: unique ids per file) |
| `02_Original-Recreations/` | `AAP_Original-Recreations.ai` | 17 artboards, one per original image at its own pixel size, in the measured colours. `AI_per-artboard/`, `PNG/` (1x, with background), `SVG/` |
| `03_Brand-Graphics/` | `AAP_Brand-Graphics.ai` | Icon set (overview + 12 icons in duotone, mono and dark), 5 seamless pattern swatches (tile + preview each), ribbon wave and data mesh, badges (shield, seal with ring text set on a path and outlined, starburst), die-cut sticker (CutContour on its own layer), swallow mascot. `PNG/` (2x), `PNG-Icons/` (4x), `SVG/` |
| `Print-Masters/` | CMYK and Pantone (coated) `.ai` | PDF/X-4 and a viewing proof, one EPS per artboard for each master, `Badges-Sticker/` (CMYK print files for the badges and the sticker), `Print-Specs.md` for vendors |

## The originals

The recreations are numbered as below. `docs/logos` also holds `1f3b28e6-ad6c-4e5d-80d8-e2f2e1e38954 (1).jpeg`, a
byte-identical copy of 03, which was not recreated twice.

| # | File in docs/logos | Content |
|---|---|---|
| 01 | `0bba6030-3597-4e47-831a-3da1f20439a7.jpeg` | Horizontal: gradient AP + 'ALLIANCE AI PARTNERS' + tagline, light |
| 02 | `11d44af0-e70b-4d0f-ba3e-1fc0d871167b.jpeg` | Brand guidelines & style board |
| 03 | `1f3b28e6-ad6c-4e5d-80d8-e2f2e1e38954.jpeg` | App icon: flat cyan AP in rounded-square outline, navy |
| 04 | `29138393-2121-469f-8575-a5dbb045ed7b.jpeg` | Horizontal dark: gradient AP + 'ALLIANCE / AI PARTNERS' white |
| 05 | `449dea5f-2cbe-468a-a59e-a382b46ec7ba.jpeg` | Stacked: faceted bird above 'ALLIANCE / AI PARTNERS', light |
| 06 | `4bdc99a9-5ffc-431f-a439-5a456f59c07e.jpeg` | Hero gradient AP mark only, light (MASTER GEOMETRY) |
| 07 | `697cd1fe-d189-4888-a600-180e6e979700.jpeg` | Horizontal dark: flat cyan AP + 'ALLIANCE AI / PARTNERS' white |
| 08 | `7580025b-e049-4a17-b0ab-97d45dcb6acc.jpeg` | Horizontal: bird + 'ALLIANCE / AI PARTNERS' (AI cyan), off-white |
| 09 | `7f533882-f9ad-48ce-9044-9b179b26109d.jpeg` | Stacked dark: flat cyan AP above 'ALLIANCE AI / PARTNERS' white |
| 10 | `8a267aa5-f173-4f96-a624-04d36e242078.jpeg` | Horizontal dark: flat cyan AP + 'ALLIANCE' bold / 'AI PARTNERS' light |
| 11 | `8e16c218-08cf-46d6-bd9e-8d7ae6ad929b.jpeg` | Two-tone mark: white A + cyan ribbon/P, navy |
| 12 | `90cf7a67-67f3-4bfe-8aea-0e10c2dab1a2.jpeg` | Flat cyan AP mark, navy |
| 13 | `a9ff3937-6b76-4717-b0fd-356a7cf4de8c.jpeg` | Horizontal: gradient AP + name + cyan rule + 'ENTERPRISE AI CONSULTING' |
| 14 | `b161ddd4-d580-4aa3-b20f-8a20e2ed1fa2.jpeg` | Stacked: gradient AP above 'ALLIANCE AI PARTNERS', light |
| 15 | `c516876b-0a00-4b22-9252-6f521ca520a6.jpeg` | Faceted bird mark only, light (MASTER BIRD) |
| 16 | `da60ac39-875a-4f6e-805f-a710b7e2ae17.jpeg` | Stacked dark: flat cyan AP above 'ALLIANCE AI / PARTNERS' white |
| 17 | `e7dbe480-3073-48eb-9568-d84c3239a496.jpeg` | Shield badge: gradient AP in beveled shield + banner |

## Logo suite

Each lockup comes in the four essential colour states plus two flat brand-ink states. Artboards are named
`NN-Lockup_State`; exported files carry the prefix `AAP_`. Each lockup artboard is the lockup plus its clear space on
every side (a favicon artboard is the icon itself), and each lockup is grouped so it moves as a unit.

| # | Lockup | From original | Construction |
|---|---|---|---|
| 01 | **Primary-Horizontal** | 02, 04 | Mark beside ALLIANCE / AI PARTNERS, both lines Bold and justified to one width (line 2 = 0.7446 x line 1), block centred on the mark, gap 0.51 cap |
| 02 | **Secondary-Stacked** | 14 | Mark centred above the one-line wordmark (0.2136 x mark height), gap 1.07 cap |
| 03 | **Logomark** | 06 | The 3D gradient AP alone |
| 04 | **Wordmark** | 01, 13, 14, 17 | ALLIANCE AI PARTNERS, Montserrat Bold, tracking -11, metric kerning, AI accented |
| 05 | **Favicon-32** | 12, 03 | Micro-mark: the AP silhouette without the interlace cuts, 17 px tall, apex, baseline and P stem on whole pixels |
| 06 | **Favicon-16** | 12, 03 | Micro-mark drawn on the pixel grid: condensed to 14 x 10 px with 1 px margins, both counters open, crisp edges |
| 07 | **Horizontal-Tagline** | 01 | Mark + wordmark + tagline (Regular, +24, 0.607 x wordmark size), shared left edge |
| 08 | **Horizontal-Descriptor** | 13 | Mark + wordmark + Ribbon Cyan rule + ENTERPRISE AI CONSULTING (Medium, justified to the wordmark) |
| 09 | **Stacked-Tagline** | 02 | The brand board's hero lockup: mark, wordmark and tagline (0.587 x wordmark size) centred |
| 10 | **Stacked-TwoLine** | 09, 16 | Mark above ALLIANCE AI / PARTNERS, both lines Bold at one size and tracking, centred |

| State | Treatment |
|---|---|
| **FullColor-Light** | 3D gradient mark; Partner Navy type, AI in Alliance Blue; transparent. Favicons: the micro-mark in Alliance Blue |
| **FullColor-Dark** | dark-colourway mark (original 04's colours with the darkest shading lifted so it separates from dark and slate grounds); white type, AI in Ribbon Cyan; shown on Partner Navy. Favicons: Ribbon Cyan |
| **Mono-Black** | one ink, AAP Black #000000 (K100, overprinting in the CMYK master); the one-colour mark with its two interlace cuts |
| **Mono-White** | one ink, Pure White #FFFFFF knockout; shown on Alliance Blue |
| **Flat-Light** | solid brand inks: the one-colour mark in Alliance Blue, Partner Navy type, AI in Alliance Blue, cyan rule; pure spot in the Pantone master |
| **Flat-Dark** | solid brand inks for dark grounds: mark and AI in Ribbon Cyan, white type; shown on Partner Navy |

FullColor-Dark is drawn for Partner Navy, near-black and dark slate grounds. On mid-tone slate (about L* 30-45, for
example `#475569`) use Mono-White or Flat-Dark instead.

**Clear space.** x = 0.287 x mark height, the margin drawn on the brand board's clear-space panel; no other artwork
inside it. The wordmark on its own keeps the same x expressed in its type: 1.45 x cap height. The favicons are drawn
to their pixel grid instead.

**Minimum sizes.**

| Artwork | Print | Screen | Note |
|---|---|---|---|
| 3D gradient mark (FullColor states) | 15 mm high | 48 px high | below this use the Flat or Mono mark |
| One-colour mark with interlace cuts (Mono, Flat) | 20 mm high (cuts stay 0.3 mm wide) | 32 px high | foil, embossing, engraving: 25 mm; below 20 mm use the micro-mark |
| Micro-mark (favicon silhouette) | 5 mm high | 16 px | screen printing and embroidery below about 50 mm |
| Horizontal lockups 01, 07, 08 | 40 mm wide | 200 px wide | tagline / descriptor lockups 60 mm wide, else drop the line |
| Stacked lockups 02, 09, 10 | 25 mm wide | 140 px wide |  |

## Colour

One unified palette, "A, P and the Ribbon" (`_build/palette.json`; the Brand Colors variables in the Figma file
[Alliance AI Partners — Logo Suite](https://www.figma.com/design/rXNPaaMds46oWgM64QPRI6/Alliance-AI-Partners-%E2%80%94-Logo-Suite)
hold the same 14 colours, and their code syntax uses the CSS names in `design-system/tokens/tokens.css`). The six
core colours keep the brand board's exact values, so every CMYK build and PANTONE reference is unchanged; only their
names changed, to tell one story: A for Alliance, P for Partner, and the ribbon between them.

| Colour | Formerly | Hex | RGB | CMYK (Coated GRACoL 2006) | PANTONE coated | PANTONE uncoated |
|---|---|---|---|---|---|---|
| Alliance Blue | Vibrant Blue | `#1B56FF` | 27/86/255 | C84 M64 Y0 K0 | PANTONE 2726 C | PANTONE 2387 U |
| Ribbon Cyan | Bright Cyan | `#00D5FF` | 0/213/255 | C62 M0 Y3 K0 | PANTONE 305 C | PANTONE 305 U |
| Partner Navy | Deep Navy | `#121B2A` | 18/27/42 | C56 M28 Y0 K93 | PANTONE 7547 C | PANTONE 5395 U |
| Pure White | - | `#FFFFFF` | 255/255/255 | C0 M0 Y0 K0 | - | - |
| Daylight | Off-White | `#F4F7FB` | 244/247/251 | C4 M2 Y0 K0 | PANTONE 656 C (panel tint reference; not a logo ink) | PANTONE 656 U |
| Black | - | `#000000` | 0/0/0 | C0 M0 Y0 K100 | - | - |

The 3D mark is drawn from the core blue, cyan and navy plus eight shading tokens on two lightness ramps, in both
colourways (swatch group `AAP Mark Shading`). They replace the 32 tones measured from the AI-generated originals, so
the mark's lit faces are the same blue as the "AI" and its ribbon the same cyan, and the dark colourway climbs the same
ramps instead of inventing lifted tones. The Brand Graphics use the same colours: each of the 72 tones measured in the
swallow, shield, wave, data mesh and pattern tiles takes its nearest palette colour (CIEDE2000, palette.json
`stopMap.graphics`), so their facets and gradients climb the same ramps and `AAP_Brand-Graphics.ai` holds no swatch
outside the palette.

| Shading token | Hex | Ramp | Where in the mark | CMYK (Coated GRACoL 2006) |
|---|---|---|---|---|
| Partner 30 | `#1A2D4E` | Partner | the P's underside and the shadow band of the A's left bevel (light mark) | C100 M87 Y40 K37 |
| Partner 38 | `#2E4265` | Partner | slate shadow faces of the A's right leg; deepest faces of the dark mark | C89 M74 Y35 K22 |
| Partner 46 | `#42587C` | Partner | slate mid faces (P bowl, A's right leg); also secondary text on white | C80 M63 Y29 K13 |
| Partner 50 | `#4D6388` | Partner | lifted slate highlights of the dark mark on navy | C76 M58 Y25 K9 |
| Alliance 38 | `#243F7B` | Alliance | deep-blue shadow bands on the A under the ribbon (light mark) | C96 M83 Y19 K6 |
| Alliance 46 | `#244EB6` | Alliance | blue faces turning into shadow, the ribbon's shaded end; hover/pressed Alliance Blue | C88 M71 Y0 K0 |
| Alliance 50 | `#2153D8` | Alliance | the top of the A's left bevel in both colourways | C85 M67 Y0 K0 |
| Ribbon 57 | `#006DF5` | Alliance | the ribbon's turn from blue into cyan, in both colourways; lies on Daybreak | C82 M57 Y0 K0 |

Signature gradient **Daybreak**: Partner Navy (0%) to Alliance Blue (54%) to Ribbon Cyan (100%),
for hero bands and brand graphics, not behind small text.

Contrast (WCAG 2.x): Partner Navy on Pure White 17.27:1; Partner Navy on Daylight 16.07:1; Alliance Blue on Pure White 5.49:1; Pure White on Alliance Blue 5.49:1; Ribbon Cyan on Partner Navy 9.84:1; Ribbon Cyan on Pure White 1.76:1. Body text needs 4.5:1, so Ribbon Cyan is never text on white or Daylight.

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

| Original | Content | Foreground IoU | Mean dE, whole image | Mean dE, artwork | Background |
|---|---|---|---|---|---|
| 01 | Horizontal: gradient AP + 'ALLIANCE AI PARTNERS' + tagline, light | 0.9715 | 0.3 | 3.67 | `#FFFFFF` |
| 02 | Brand guidelines & style board | 0.9578 | 1.92 | 4.49 | `#F4F7FB` |
| 03 | App icon: flat cyan AP in rounded-square outline, navy | 0.9796 | 0.77 | 0.89 | `#132237` |
| 04 | Horizontal dark: gradient AP + 'ALLIANCE / AI PARTNERS' white | 0.9184 | 1.05 | 2.95 | `#132032` |
| 05 | Stacked: faceted bird above 'ALLIANCE / AI PARTNERS', light | 0.9671 | 0.41 | 3.55 | `#FFFFFF` |
| 06 | Hero gradient AP mark only, light (MASTER GEOMETRY) | 0.9961 | 0.33 | 1.93 | `#FFFFFF` |
| 07 | Horizontal dark: flat cyan AP + 'ALLIANCE AI / PARTNERS' white | 0.9698 | 0.54 | 2.52 | `#142336` |
| 08 | Horizontal: bird + 'ALLIANCE / AI PARTNERS' (AI cyan), off-white | 0.9613 | 1.02 | 3.94 | `#F4F7FB` |
| 09 | Stacked dark: flat cyan AP above 'ALLIANCE AI / PARTNERS' white | 0.9722 | 0.99 | 2.16 | `#112034` |
| 10 | Horizontal dark: flat cyan AP + 'ALLIANCE' bold / 'AI PARTNERS' light | 0.9345 | 1.96 | 4.73 | `#121B2A` |
| 11 | Two-tone mark: white A + cyan ribbon/P, navy | 0.9941 | 0.52 | 0.63 | `#112131` |
| 12 | Flat cyan AP mark, navy | 0.9952 | 0.6 | 0.75 | `#121F32` |
| 13 | Horizontal: gradient AP + name + cyan rule + 'ENTERPRISE AI CONSULTING' | 0.9577 | 0.4 | 4.39 | `#FFFFFF` |
| 14 | Stacked: gradient AP above 'ALLIANCE AI PARTNERS', light | 0.9863 | 0.34 | 2.54 | `#FFFFFF` |
| 15 | Faceted bird mark only, light (MASTER BIRD) | 0.9948 | 0.18 | 2.39 | `#FFFFFF` |
| 16 | Stacked dark: flat cyan AP above 'ALLIANCE AI / PARTNERS' white | 0.9695 | 2.02 | 2.42 | `#121B2A` |
| 17 | Shield badge: gradient AP in beveled shield + banner | 0.9869 | 0.78 | 2.95 | `#FFFFFF` |

The lowest scores are 04 (0.9184), 10 (0.9345), 13 (0.9577). What limits them: the originals are AI-generated
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
