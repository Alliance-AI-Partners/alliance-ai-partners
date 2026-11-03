# Merch

Placement artwork for Alliance AI Partners merchandise: caps, tumblers, t-shirts, hoodies, tote bags, notebooks, mugs, stickers, lanyards and ID badges. Each file is drawn at its real size in millimetres with the finalized logo files inlined as vectors, so a vendor can place it directly. [merch.json](merch.json) is the machine-readable version of the table below.

## Which logo goes where

The process decides the artwork, not taste:

| Process | Artwork | Why |
|---|---|---|
| Embroidery, screen print, deboss | **Flat** marks (one brand ink: Ribbon Cyan on dark goods, Alliance Blue on light) or **Mono** | Thread, ink and dies cannot hold a gradient. The flat states are the kit's own one-ink versions. |
| UV print, sublimation, digital print | **Full colour** marks | These processes print the 3D mark's gradients faithfully. |
| Laser engraving | **Mono-white** mark | The laser shows the metal; it has no colour. |

Dark goods are Partner Navy (PMS 7547 C), never black.

## Specs

| Item | Placement | Size (mm) | Method | Inks or threads | On | Artwork |
|---|---|---|---|---|---|---|
| Cap | Front panel, centred, 6 mm above the seam line | 57 x 39.2 | Flat embroidery in one thread, about 9,000 stitches | Ribbon Cyan thread (PMS 305 C match) | Partner Navy structured cap | [cap-front-embroidery.svg](artwork/cap-front-embroidery.svg) |
| Cap | Back, above the strap | 60 x 11.5 | Flat embroidery | Daylight white thread; Ribbon Cyan thread | Partner Navy structured cap | [cap-back-embroidery.svg](artwork/cap-back-embroidery.svg) |
| Tumbler | Full wrap: the mark on the front (handle at the seam), the line on the back | 235 x 102 | UV-LED full-colour print on Partner Navy powder coat | CMYK + white underbase; Partner Navy ground (PMS 7547 C) | Partner Navy 20 oz tumbler | [tumbler-wrap-20oz.svg](artwork/tumbler-wrap-20oz.svg) |
| T-shirt | Left chest, 90 mm wide, 80 mm below the collar | 90 x 61.9 | Screen print, 1 spot colour | PMS 305 C (Ribbon Cyan) | Partner Navy cotton tee | [tee-front-chest.svg](artwork/tee-front-chest.svg) |
| T-shirt | Back, 280 mm wide, 60 mm below the collar | 280 x 70 | Screen print, 3 spot colours (the ribbon as a 4-step halftone blend) | White; PMS 305 C; PMS 2726 C | Partner Navy cotton tee | [tee-back-tagline.svg](artwork/tee-back-tagline.svg) |
| Hoodie | Centre chest, 100 mm wide, 110 mm below the hood seam | 100 x 68.7 | Flat embroidery in one thread | Ribbon Cyan thread (PMS 305 C match) | Partner Navy heavyweight hoodie | [hoodie-chest-embroidery.svg](artwork/hoodie-chest-embroidery.svg) |
| Tote bag | Front panel, lockup centred, ribbon across the foot | 300 x 300 | Screen print, 2 spot colours (the ribbon as a navy-to-blue halftone blend) | PMS 7547 C (Partner Navy); PMS 2726 C (Alliance Blue) | Natural or Daylight-white canvas tote | [tote-front.svg](artwork/tote-front.svg) |
| Notebook | Front cover, centred, 40 mm wide | 40 x 27.5 | Blind deboss (black = die area) | Blind (no ink) on Partner Navy linen; ribbon marker in Ribbon Cyan satin | A5 hardcover, Partner Navy linen | [notebook-cover-deboss.svg](artwork/notebook-cover-deboss.svg) |
| Mug | Wrap: mark on the drinking side, line on the other | 210 x 85 | Sublimation, full colour | CMYK | White 11 oz ceramic mug | [mug-wrap-11oz.svg](artwork/mug-wrap-11oz.svg) |
| Stickers | A5 kiss-cut sheet: pill lockup, round mark, "Put AI to work.", ribbon | 148 x 210 | Digital print on white vinyl, kiss-cut with 2 mm bleed | CMYK | White gloss vinyl | [sticker-sheet-a5.svg](artwork/sticker-sheet-a5.svg) |
| Lanyard | Full length, wordmark every 150 mm | 900 x 20 | Dye-sublimation on polyester | CMYK (the Daybreak gradient); White | 20 mm flat polyester lanyard | [lanyard-20mm.svg](artwork/lanyard-20mm.svg) |
| ID badge | CR80 card, portrait | 54 x 86 | Dye-sublimation or direct-to-card print | CMYK | White PVC card, 0.76 mm | [id-badge-cr80.svg](artwork/id-badge-cr80.svg) |

## Notes for vendors

- **Cap:** the flat-dark mark is the kit's one-ink state, made for thread. Keep 3 mm clear of the panel seams and approve a sew-out before the run. The back wordmark is at its smallest legible size in thread.
- **Tumbler:** the ribbon crosses the seam, so align it within 1 mm. For a single-colour job, laser-engrave the mono-white mark instead.
- **T-shirt back:** convert the type to outlines before sending.
- **Tote bag:** print area 300 x 300 mm; keep 25 mm from the handles.
- **Notebook:** the cyan ribbon marker is the brand's ribbon made literal; specify PMS 305 C for the satin.
- **Mug:** keep 15 mm clear on either side of the handle.
- **Stickers:** the die-cut sticker master with its CutContour line is in `docs/brand-kit/Print-Masters/Badges-Sticker/`.
- **Lanyard:** the lanyard is the ribbon worn: the gradient runs end to end, navy at the clip.
- **ID badge:** name and role are placeholders; print one per person.
- **Proofs:** ask for a physical proof or sew-out on every first order. Brand blue is outside the CMYK gamut on screen; match PMS 2726 C where a spot ink is available.

## Files

| Folder | What |
|---|---|
| [artwork/](artwork/) | The placement SVGs. Text is live Mona Sans (in `design-system/fonts/`); convert it to outlines before release. |
| [previews/](previews/) | Flat renders of each artwork on its ground (`<name>-artwork.png`). |
| [mockups/](mockups/) | Photographic mockups generated with Gemini from the real logo files, one per item, each with a `.json` record of its prompt and references. Mockups show how the goods could look; the artwork files are what gets made. |

## Rebuilding

```bash
python brand-kit/merch/build-merch.py                       # artwork, merch.json and the preview pages
node brand-kit/tools/capture.cjs brand-kit/merch/previews/_artwork/<name>.html brand-kit/merch/previews/<name>-artwork.png
<gemini skill venv python> brand-kit/tools/generate-imagery.py   # mockups; the key comes from the environment or the gitignored .env
python brand-kit/tools/build-assets-data.py                 # refresh the brand-kit page
```

`capture.cjs` needs Playwright (`PLAYWRIGHT_PATH` can point at an existing install).
