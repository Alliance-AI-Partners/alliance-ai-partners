# Imagery

Every image comes from the logo kit's own language: **the ribbon** that binds the A and the P, **the facets** of the 3D mark, and **the swallow**. Nature is the subject (birds, flowers, leaves, water, daybreak) because Alliance is about growth, but it is drawn in that language and in the palette, so a background and the logo always look like one company.

## The rules

- **Palette only.** Partner Navy, Alliance Blue, Ribbon Cyan and Daylight, with their in-between shades. The Daybreak gradient (navy to blue to cyan) is the light of every scene.
- **Ribbon and facets, not stock nature.** Petals folded from satin ribbon, leaves and birds built from flat planes, rivers and waves that move like the ribbon.
- **Light from the upper left**, as on the mark's bevels, with shadows falling to the lower right.
- **Room for words.** Every background leaves a calm area for a headline; the description of each image says where.
- **Nothing regional.** Alliance works internationally, so no national flowers, landmarks or cultural patterns (user decision, 2026-11-02).
- **Never:** robots, glowing brains, circuit boards, sparkles, purple or pink gradients, people as stock models, or any text inside an image. No photographs or names of real partners.

## Folders

| Folder | What | Manifest |
|---|---|---|
| [graphics/](graphics/) | The logo kit's brand graphics: ribbon wave, data mesh, five patterns (tile and swatch each), badges, sticker artwork and the swallow mascot. PNG at 2x plus SVG. | [imagery.json](imagery.json) |
| [backgrounds/](backgrounds/) | Generated nature backgrounds. Each has a web `.webp` (1920 px wide), a `.jpg` master and a `.json` record of its exact prompt, model, aspect ratio and date. | [imagery.json](imagery.json), `category: "background"` |

## Backgrounds

Generated with Google Gemini (`gemini-3-pro-image-preview`, through the gemini-image-generator skill) by [../../brand-kit/tools/generate-imagery.py](../../brand-kit/tools/generate-imagery.py). The script holds the full prompt of every image, so the set can be regenerated or extended in the same style: add an entry, run it, and only the new image is made.

| Name | Ratio | Ground | Text goes |
|---|---|---|---|
| daybreak-swallows | 16:9 | Daybreak sky | Left two thirds (open sky) |
| ribbon-blossoms | 16:9 | Daylight | Left half |
| faceted-leaves | 16:9 | Deep navy | Right side, white text |
| faceted-swallow | 1:1 | Daylight | Around the bird (cards, social) |
| ribbon-river | 16:9 | Dawn landscape | Top third |
| paper-garden | 16:9 | Light | Anywhere, dark text |
| dawn-wave | 16:9 | Dark navy sky | Upper half, white text |
| meadow-first-light | 9:16 | Pale sky | Upper half (stories) |

These are generated illustrations, not photographs, and they show no real places, people or partners. They are marked `"derived": true` in the manifest.

**Run it.** The script reads `GEMINI_API_KEY` from the environment, or from the repository's `.env`, which git ignores. Never commit the key or paste it into a file that is tracked:

```bash
~/.claude/skills/gemini-image-generator/scripts/venv/Scripts/python.exe brand-kit/tools/generate-imagery.py            # fills gaps only
~/.claude/skills/gemini-image-generator/scripts/venv/Scripts/python.exe brand-kit/tools/generate-imagery.py dawn-wave  # regenerates one
python brand-kit/tools/build-assets-data.py   # refreshes the brand-kit page
```

All eight were reviewed by eye on 2026-11-02: palette only, no text, the calm area where the table says. Generated images vary from run to run, so review any regenerated image the same way before it ships.

## Brand graphics with conditions

- **graphic-wave** carries a soft glow in the logo-kit artwork. Use it as a hero or print graphic, never behind UI text or controls, where the system has no glows.
- **badge-starburst** reads "Certified AI Partner". Use it only once Alliance holds the certification it names; nothing in PRODUCT.md backs one yet.

## Text over imagery

Use [image-overlays.css](image-overlays.css) when copy has to sit on a busy part of an image. The scrims are Partner Navy gradients, so text on them is checked against navy (16:1 for Daylight text), never against the image.

```html
<div class="aap-media aap-scrim-start" style="aspect-ratio: 16 / 9">
  <img src="imagery/backgrounds/dawn-wave.webp" alt="">
  <div class="aap-surface-inverse" style="background: none">...</div>
</div>
```

- `.aap-scrim-start`: navy from the reading-start edge, fading out by 60 %.
- `.aap-scrim-bottom`: navy from the bottom, for captions and stories.
- Decorative backgrounds get `alt=""`; an image that carries meaning gets a description of what it shows.

## Formats

| Use | Size | Format |
|---|---|---|
| Hero and section backgrounds | 1920 px wide | WebP (from the JPEG master) |
| Social and cards | 1080 px | WebP or JPEG |
| Graphics and logos | vector | SVG first, PNG at 2x |

In Next.js, serve images through `next/image` with explicit `sizes` so phones receive smaller files.
