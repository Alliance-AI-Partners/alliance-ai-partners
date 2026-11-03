# Print specifications: Alliance AI Partners logo masters

For printers, sign makers, embroiderers and other vendors. All type is converted to outlines; the files contain no
fonts and no raster artwork (each EPS carries only the usual low-resolution screen preview). CMYK values are Coated
GRACoL 2006 (ISO 12647-2:2004) builds.

## Files

| File | Use |
|---|---|
| `AAP_Master-Logo-Suite_CMYK.ai` | Process master: every colour a global CMYK swatch; Mono-Black art is K100 set to overprint |
| `AAP_Master-Logo-Suite_PMS-Coated.ai` | Spot master, coated stock: Alliance Blue, Ribbon Cyan and Partner Navy are PANTONE 2726 C, 305 C, 7547 C |
| `AAP_Master-Logo-Suite_CMYK_PDF-X4.pdf` | All 56 artboards, PDF/X-4, output intent Coated GRACoL 2006 (ISO 12647-2:2004) (CGATS TR 006) with the profile embedded |
| `AAP_Master-Logo-Suite_Proof.pdf` | Viewing proof: the dark and knockout artboards shown on their background panels |
| `EPS_CMYK/`, `EPS_PMS-Coated/` | One EPS per artboard (`AAP_CMYK_01-Primary-Horizontal_FullColor-Light.eps`, ...), Illustrator CS6 EPS |
| `Badges-Sticker/` | CMYK master of the Brand Graphics with PDF/X-4 and EPS of the shield, seal, starburst and die-cut sticker |

For uncoated stock, ask the printer to swap the three spots for PANTONE 2387 U, 305 U and 5395 U (listed below).
The `.ai` masters are saved in the current Illustrator format. Background panels sit on a non-printing layer and are
not in the EPS files or the PDF/X-4: the FullColor-Dark, Mono-White and Flat-Dark artboards are white artwork meant
for dark stock or a printed ground (see the proof PDF).

## Which artboards for which job

| State | Inks in the CMYK master | Inks in the Pantone master |
|---|---|---|
| FullColor-Light / -Dark | CMYK (the 3D mark is a process gradient) | CMYK + the brand spots: like the AI, the 3D mark's lit faces print in 2726 C and its ribbon in 305 C; light adds 7547 C (type and the mark's deepest shadow). 7 plates light, 6 dark, the logomark alone too; the wordmark alone is pure spot (2726 C + 7547 C light, 305 C dark) |
| Flat-Light | CMYK | pure spot: 2726 C (mark, AI) + 7547 C (type) + 305 C (rule in 08), 1-3 plates |
| Flat-Dark | CMYK | pure spot: 305 C (mark, AI); type is a white knockout |
| Mono-Black | K only, overprinting | K only |
| Mono-White | no ink (knockout; white ink on dark media) | no ink |
| Favicons 05, 06 | CMYK | pure spot: 2726 C (light) or 305 C (dark) |

## Artboard sizes

Every lockup artboard includes its clear space on all sides (x = 0.287 x mark height; for the wordmark alone, 1.45 x
cap height); a favicon artboard is the icon itself, with no margin. The artwork is the size in the last column: scale
the files to the artwork size you need, not the box.

| Lockup | Artboard | Artboard (mm) | Artwork inside |
|---|---|---|---|
| 01-Primary-Horizontal | 1139 x 378 pt | 402 x 133 mm | 1001 x 240 pt |
| 02-Secondary-Stacked | 771 x 453 pt | 272 x 160 mm | 633 x 315 pt |
| 03-Logomark | 550 x 378 pt | 194 x 133 mm | 412 x 240 pt |
| 04-Wordmark | 1438 x 276 pt | 507 x 97 mm | 1235 x 73 pt |
| 05-Favicon-32 | 32 x 32 pt | 11 x 11 mm | whole artboard |
| 06-Favicon-16 | 16 x 16 pt | 6 x 6 mm | whole artboard |
| 07-Horizontal-Tagline | 1425 x 378 pt | 503 x 133 mm | 1287 x 240 pt |
| 08-Horizontal-Descriptor | 1425 x 378 pt | 503 x 133 mm | 1287 x 240 pt |
| 09-Stacked-Tagline | 771 x 498 pt | 272 x 176 mm | 633 x 360 pt |
| 10-Stacked-TwoLine | 795 x 595 pt | 280 x 210 mm | 657 x 457 pt |

## Minimum reproduction sizes

| Artwork | Print | Screen | Note |
|---|---|---|---|
| 3D gradient mark (FullColor states) | 15 mm high | 48 px high | below this use the Flat or Mono mark |
| One-colour mark with interlace cuts (Mono, Flat) | 20 mm high (cuts stay 0.3 mm wide) | 32 px high | foil, embossing, engraving: 25 mm; below 20 mm use the micro-mark |
| Micro-mark (favicon silhouette) | 5 mm high | 16 px | screen printing and embroidery below about 50 mm |
| Horizontal lockups 01, 07, 08 | 40 mm wide | 200 px wide | tagline / descriptor lockups 60 mm wide, else drop the line |
| Stacked lockups 02, 09, 10 | 25 mm wide | 140 px wide |  |

## Brand colours

| Colour | Screen hex | RGB | CMYK (Coated GRACoL 2006) | PANTONE coated | PANTONE uncoated |
|---|---|---|---|---|---|
| Alliance Blue | Vibrant Blue | `#1B56FF` | 27/86/255 | C84 M64 Y0 K0 | PANTONE 2726 C | PANTONE 2387 U |
| Ribbon Cyan | Bright Cyan | `#00D5FF` | 0/213/255 | C62 M0 Y3 K0 | PANTONE 305 C | PANTONE 305 U |
| Partner Navy | Deep Navy | `#121B2A` | 18/27/42 | C56 M28 Y0 K93 | PANTONE 7547 C | PANTONE 5395 U |
| Pure White | - | `#FFFFFF` | 255/255/255 | C0 M0 Y0 K0 | - | - |
| Daylight | Off-White | `#F4F7FB` | 244/247/251 | C4 M2 Y0 K0 | PANTONE 656 C (panel tint reference; not a logo ink) | PANTONE 656 U |
| Black | - | `#000000` | 0/0/0 | C0 M0 Y0 K100 | - | - |

Builds for other printing conditions (for vendors who print to SWOP v2 or FOGRA39):

| Swatch | Screen hex | Coated GRACoL 2006 | U.S. Web Coated (SWOP) v2 | Coated FOGRA39 |
|---|---|---|---|---|
| AAP Alliance Blue | `#1B56FF` | C84 M64 Y0 K0 | C81 M67 Y0 K0 | C86 M66 Y0 K0 |
| AAP Ribbon Cyan | `#00D5FF` | C62 M0 Y3 K0 | C60 M0 Y0 K0 | C62 M0 Y4 K0 |
| AAP Partner Navy | `#121B2A` | C56 M28 Y0 K93 | C85 M76 Y55 K69 | C95 M82 Y52 K71 |
| AAP Pure White | `#FFFFFF` | C0 M0 Y0 K0 | C0 M0 Y0 K0 | C0 M0 Y0 K0 |
| AAP Daylight | `#F4F7FB` | C4 M2 Y0 K0 | C3 M1 Y0 K0 | C5 M2 Y0 K0 |
| AAP Black | `#000000` | C0 M0 Y0 K100 | C0 M0 Y0 K100 | C0 M0 Y0 K100 |

- Alliance Blue `#1B56FF` is outside both the CMYK gamut and every Pantone ink (nearest ink dE2000 5.5, CMYK about 8):
  print it as the spot ink wherever the job allows.
- Ribbon Cyan is partly outside CMYK (dE 4 to 5.5); PANTONE 305 C/U is the nearest ink.
- Partner Navy: the CMYK build is a low-ink, K-heavy navy (TAC 177). Process navy prints lighter than the screen;
  PANTONE 7547 C is the dark match on coated stock. No uncoated ink reaches it (5395 U is the nearest).
- For small navy type (under about 9 pt) use PANTONE 7547 C or a K-only build so the three-plate navy cannot misregister.
- Pure White is the paper (or an opaque white ink on dark substrates). Daylight is a light panel tint only.

## Shading tones

The full-colour mark is a process gradient built from these global swatches; the badges in `Badges-Sticker/`, the
shield's bevel included, use the same builds. The 0 tones marked (perceptual)
would print as one colour with the standard separation, so they use a perceptual separation that keeps the facets
distinct. Highest total ink in any build: 264 %.

| Swatch | Screen hex | Coated GRACoL 2006 | U.S. Web Coated (SWOP) v2 | Coated FOGRA39 |
|---|---|---|---|---|
| AAP Partner 30 | `#1A2D4E` | C100 M87 Y40 K37 | C95 M84 Y42 K40 | C100 M83 Y40 K40 |
| AAP Partner 38 | `#2E4265` | C89 M74 Y35 K22 | C89 M76 Y37 K24 | C89 M72 Y35 K25 |
| AAP Partner 46 | `#42587C` | C80 M63 Y29 K13 | C81 M65 Y31 K13 | C80 M62 Y30 K15 |
| AAP Partner 50 | `#4D6388` | C76 M58 Y25 K9 | C76 M61 Y28 K7 | C75 M57 Y27 K11 |
| AAP Alliance 38 | `#243F7B` | C96 M83 Y19 K6 | C98 M86 Y23 K9 | C97 M81 Y21 K7 |
| AAP Alliance 46 | `#244EB6` | C88 M71 Y0 K0 | C89 M77 Y0 K0 | C90 M71 Y0 K0 |
| AAP Alliance 50 | `#2153D8` | C85 M67 Y0 K0 | C84 M71 Y0 K0 | C87 M68 Y0 K0 |
| AAP Ribbon 57 | `#006DF5` | C82 M57 Y0 K0 | C80 M59 Y0 K0 | C84 M59 Y0 K0 |

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
