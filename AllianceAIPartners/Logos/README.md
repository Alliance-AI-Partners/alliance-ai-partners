# Logo explorations

Logos for the top directions in [Design System Directions](../Design%20System%20Directions.md), made with four different tools. Each tool has its own folder, each direction has a numbered folder inside it, and every file name starts with the direction and the tool, so a file stays labeled even if it's moved.

## Where each tool's logos are

| Folder | Tool | Model | Directions | What's there |
|---|---|---|---|---|
| `1-muapi-logo-creator/` | muapi-logo-creator skill (`create-logo.sh`), then a Gemini touch-up | Ideogram v3 (Imagen 4 for 04); touch-ups with Gemini 3.1 Flash Image | Top 8 | 8 of 8. Ideogram's input filter rejected 04 On the Level three times, so 04 was made with Imagen 4 through the same skill. Every image has a Gemini touch-up, and the board uses the touch-ups. |
| `2-logo-creator/` | logo-creator skill (Nano Banana batch) | Gemini 3.1 Flash Image (Nano Banana 2) | Top 8 | 3 variations per direction, each folder with the skill's `preview.html` gallery. One pick per direction is traced and on the board. |
| `3-recraft/` | Recraft API | Recraft V4.1 vector (`recraftv4_1_vector`) | Top 5 | 5 of 5, native SVG. |
| `4-nanobanana/` | nanobanana skill (`generate.py`, 2K) | Gemini 3.1 Flash Image (Nano Banana 2) | Top 8 | 8 of 8 full lockups, symbol and wordmark together. |

## What the file names mean

| Ending | What it is |
|---|---|
| `__muapi-ideogram-v3.webp`, `__muapi-imagen4.webp` | Track 1's image as muapi returned it |
| `__gemini-refined.png` | Gemini's touch-up of the image named before it |
| `__logo-creator-01.png` to `-03.png` | Track 2's three variations |
| `__recraft-v4.1-vector.svg` | Recraft's own vector. The `.ai`, `.vectorcraft` and `.png` beside it are VectorCraft re-saves |
| `__nano-banana-2__lockup.png` | Track 4's full lockup. Its type is drawn by the model, not set in a font |
| `__vectorcraft-trace.svg` / `.ai` / `.vectorcraft` / `.png` | VectorCraft's logo-mode trace of the image named before it: background removed, colors snapped to the direction's palette |
| `__rejected-…` | Kept for the record, not used |

Each track folder also has:

- `prompts.md`: every prompt sent and the model it went to, failed ones marked.
- `<track>__illustrator-board.ai`: one artboard per direction with the vector and a caption naming the exact source file. Tracks 1 to 3 add the wordmark set in the direction's real font; track 4's lockups already include theirs. The `.png` beside it is an overview.

## Picks on the boards

- **Track 1:** the Gemini touch-up of each image.
- **Track 2:** Joinery 01, Counterpart 02, Interchange 03, On the Level 03, Backstage 02, Cantilever 03, Less, but Better 01, Relay 02. The other variations stay in each folder's gallery.
- **Tracks 3 and 4:** the one image per direction.

## First look

- **Nano Banana 2 lockups (track 4)** are the most complete: every one spells the name right and follows its direction's type brief.
- **logo-creator (track 2)** came closest to the mark briefs: Joinery's through tenon and peg, Interchange's A meeting at a ring, Cantilever's one-sided overhang and Relay's offset A.
- **muapi (track 1):** Counterpart, Less, but Better and Relay matched closely. Gemini's touch-ups fixed Joinery's dark background, Cantilever's broken leg and On the Level's stray glyphs, and turned Interchange's X into an A inside a ring.
- **Recraft (track 3):** Backstage and Joinery are the strongest. Recraft treats the palette as a hint (Counterpart came out pure red, not seal red), and its SVGs are kept exactly as made.
- **Wordmarks on the boards:** Joinery's ALLIANCE is Archivo Bold widened to 120%, standing in for the extra-wide cut.

## Rebuilding

From `_source/`, with a Python that has `google-genai` and `Pillow`. Keys come from the repo's `.env`.

```
python generate_logos.py logocreator           # or muapi, recraft, nanobanana; add ranks to redo some, e.g. muapi 4
python generate_logos.py refine <image> <rank>
python generate_logos.py trace <image> <rank>
python generate_logos.py board <track>         # muapi, logocreator, recraft or nanobanana
```

`_source/directions.json` holds the one brief per direction that every tool received, and `_source/build_board.jsx` lays out the Illustrator boards. The script never stores the keys.
