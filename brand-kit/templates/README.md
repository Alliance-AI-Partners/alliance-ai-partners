# Brand application templates

Nine standalone HTML templates that apply the Alliance AI Partners design system (`../../design-system/`) to real artefacts: a link-share card, two social posts, a LinkedIn banner, a printed and a digital business card, an email signature, a letterhead and a proposal cover.

Each page links `../../design-system/tokens/tokens.css` for Mona Sans and the `--aap-*` tokens, and keeps its own styles inline. The digital business card also links `../../design-system/css/components.css` for `aap-surface-inverse` and `aap-button--primary`. The artefact root always has `id="artefact"` and is sized exactly to the output, so any page can be screenshotted or printed on its own. Built and checked on 2026-11-02.

## Templates

| Template | Size | Use | Print and safe-area specs | Assets used | Notes |
|---|---|---|---|---|---|
| [og-image.html](og-image.html) | 1200 x 630 px | Open Graph / link-share card for the homepage and pages without their own image | Screen only. Text and logo sit at least 56 px inside the edges, because some platforms crop toward the centre. | Primary horizontal lockup, full-colour light (SVG). Logomark, full-colour dark (SVG). | "Put AI to work." with "work." as the one Alliance Blue accent, and "The AI team you don't have to hire." |
| [social-square.html](social-square.html) | 1080 x 1080 px | Feed post for one point of the honest pricing promise | Screen only. 80 px side margins. Instagram's profile grid shows posts as 3:4 thumbnails and trims the sides of a square post; the post itself shows in full. | Primary horizontal lockup, full-colour dark | Shows the fixed-quote point. The file's comment lists other promise points that fit the same layout. Brand DNA asks that each promise is confirmed true before it is published. |
| [social-story.html](social-story.html) | 1080 x 1920 px | Story with the brand line and the AI check-up call to action | Screen only. Platform UI covers about the top 250 px and the bottom 340 px, so the lockup, headline, call to action and URL sit between y 280 and y 1580. Only the ribbon, the swallow's wingtip and the navy ground run outside that zone. | Primary horizontal lockup, full-colour light. Swallow mascot, full colour. | The button is part of the picture and can't be tapped. Add the platform's link sticker over it when posting. |
| [linkedin-banner.html](linkedin-banner.html) | 1584 x 396 px | LinkedIn company page cover | Screen only. The page logo covers about the left 400 px on mobile and overlaps the bottom-left on desktop, so that strip carries only the ribbon. The copy starts at x 480 and stays vertically centred, because small screens crop the cover. | None. The page's own logo sits beside the cover. | Partner Navy ground, with "work." in Ribbon Cyan. |
| [business-card.html](business-card.html) | 3.5 x 2 in (88.9 x 50.8 mm), front and back | Staff business card | Bleed: 0.125 in (3.2 mm) on each side. Supply 3.75 x 2.25 in artwork by extending the navy front; the ribbon already runs past the trim. Safe area: text and logo sit 0.25 in inside the trim (the usual printer minimum is 0.125 in). Smallest text is 7 pt. The back's Daylight stands for the paper: print it on bright white stock and leave it unprinted, or print C4 M2 Y0 K0 as a flood. Print colours are listed below. | Primary horizontal lockup, full-colour dark. The art is 47 mm wide; the print minimum is 40 mm. | Prints as 2 pages at 3.5 x 2 in. On screen the sheet is zoomed 1.5625x, so a capture at device scale 2 gives 1050 x 600 px per side (300 ppi). |
| [digital-business-card.html](digital-business-card.html) | 390 x 780 px | Phone e-card behind a contact link or a QR code | Screen only. At 236 px wide the lockup keeps the 3D mark 49.7 px tall; the screen minimum is 48 px. | Primary horizontal lockup, full-colour dark. The phone, mail, globe and download UI icons, inlined from `icons/ui/`. | **The QR code is a labelled placeholder and is not scannable** (see "QR code" below). "Save contact" is the one Alliance Blue action, and links to a sample vCard URL. |
| [email-signature.html](email-signature.html) | 600 px maximum, table-based | Staff email signature | Email only. Inline styles, presentation tables, and Helvetica then Arial, because email clients ignore web fonts. Before use, host the logo PNG on https and replace the relative `src`. | `assets/email-signature-logo-tile.png` (derived, see below), shown at 256 x 88 px | Carries the tagline "Partners in AI. Partners in growth." and one Alliance Blue link, "See where AI can help". See "Dark mode" below. |
| [letterhead.html](letterhead.html) | 210 x 297 mm (A4) | Letters and formal notices | Office printing with no bleed (`@page` A4, margin 0). Margins are 22 mm left and right, with the body from 62 mm. The body must end by 247 mm to clear the ribbon. The footer sits 11 mm above the bottom edge, clear of the printer's unprintable strip. The ribbon runs off both side edges; on printers that can't reach the edge, its last few millimetres show white. The page holds one page of letter; for longer letters, add a continuation page without the header. | Primary horizontal lockup, full-colour light. The art is 48 mm wide; the print minimum is 40 mm. | Placeholders in square brackets stay until real details exist. |
| [presentation-cover.html](presentation-cover.html) | 1920 x 1080 px (16:9) | Title slide for proposals | Screen and PDF export. 112 px margins. | Primary horizontal lockup, full-colour dark | The title states the reader's gain and the subtitle names the fixed quote, because proposals open with what changes for the reader (PRODUCT.md). Edit the title for each proposal. "[Partner name]" and "[Proposal number]" are placeholders. |

Previews are in `previews/<name>.png`. The OG, social, banner, cover and letterhead previews use device scale 1 (the letterhead at 96 px per inch, 794 x 1123 px). The business card, digital card and signature previews use device scale 2. The business card preview shows the front and back side by side, 1050 x 600 px each. `previews/email-signature-dark-mode.png` shows the signature under Chromium's forced dark mode.

To re-render a preview (the tool captures `#artefact`):

```
export PLAYWRIGHT_PATH=C:/Users/dalig/Desktop/MaintainTech/MaintainOrg/suretraq-rpm/node_modules/playwright
node brand-kit/tools/capture.cjs brand-kit/templates/<name>.html brand-kit/templates/previews/<name>.png --width 1600 --height 1000 --scale 1
```

Use `--scale 2` for `business-card`, `digital-business-card` and `email-signature`.

## How the direction is applied

These rules come from "The Ribbon" contract (`.impeccable/surfaces/brand-kit-index-html.md`), PRODUCT.md and the tokens.

- **Grounds.** Every piece is built from whole Daylight (#F4F7FB) and Partner Navy (#121B2A) regions, never a tint or a gradient field. The signature and letterhead sit on white paper.
- **The ribbon.** One path is drawn twice with `<use>`. The first stroke is the Daybreak band: Partner Navy, then Alliance Blue at 54 %, then Ribbon Cyan. The second is its lit top edge, a stroke about 0.3 times as wide that runs from Ribbon 57 (#006DF5) to Ribbon Cyan and is shifted up so its top meets the band's, the way the mark's ribbon carries its cyan face. The navy end always lies on Daylight and the cyan end on Partner Navy, so the ribbon reads on both grounds and seems to rise out of the navy. To reshape it, edit the path's `d` and keep it clear of text. There is no glow, glass, gradient text or sparkle. The brand-kit wave graphic isn't used, because its glow is baked in.
- **Colour roles.** Type is Partner Navy on Daylight and Daylight on navy. Alliance Blue appears only on the one action (story, digital card, signature). Accent words are marked by weight on light grounds (OG, square) and set in Ribbon Cyan on navy (LinkedIn, cover). The banner, cover, business card and letterhead use no Alliance Blue at all.
- **Type.** Display type is Mona Sans Expanded (125 %) at weight 620 to 640, with -0.035em to -0.025em tracking. The letter's subject line is Semi-expanded (112.5 %). Text is normal width. Mona Sans Mono carries URLs, phone numbers, dates, the time zone and placeholders. Headlines use `text-wrap: balance`, and accent phrases never break across lines.
- **Logos.** Full-colour light sits on Daylight and white; full-colour dark sits on Partner Navy. Mono-white isn't needed, because no template uses photography. Each lockup is placed by its artwork edge: the SVG artboards carry 69 of 1139 units of clear space, and each file's CSS comment states the offset. Every lockup meets the minimum sizes in `docs/brand-kit/README.md`. The horizontal-descriptor lockup ("ENTERPRISE AI CONSULTING") isn't used.
- **Imagery.** Only the logo kit: the ribbon, the 3D mark and the swallow. There are no regional or cultural motifs; "Philippines · UTC+8" on the e-card states the team's base as a fact.
- **Craft.** There is no eyebrow or kicker label above any heading, no emoji, and no grid of same-size icon cards. Every text element passes WCAG AA (see Verification).

## Print colours

From `docs/brand-kit/README.md` (Coated GRACoL 2006). The HTML prints RGB, so for litho, rebuild the card from `docs/brand-kit/Print-Masters/` or convert with these values, and ask for a hard proof: the Daybreak band runs from a rich navy into cyan and can band or shift on press.

| Colour | Hex | CMYK | PANTONE coated | Used in |
|---|---|---|---|---|
| Partner Navy | `#121B2A` | C56 M28 Y0 K93 | 7547 C | Card front ground, type, ribbon start |
| Alliance Blue | `#1B56FF` | C84 M64 Y0 K0 | 2726 C | Ribbon middle, lockup "AI" (light lockup) |
| Ribbon Cyan | `#00D5FF` | C62 M0 Y3 K0 | 305 C | Ribbon end and lit edge |
| Ribbon 57 | `#006DF5` | C82 M57 Y0 K0 | - | Ribbon lit edge |
| Alliance 38 | `#243F7B` | C96 M83 Y19 K6 | - | Start of the lit edge on the card front |
| Daylight | `#F4F7FB` | C4 M2 Y0 K0 | 656 C (tint reference only) | Card back, if printed as a flood |

## Dark mode (email signature)

- **The logo is a self-contained tile.** Email clients never recolour images, so the Partner Navy tile with the full-colour dark lockup looks the same in every mode. A transparent PNG with navy type would vanish on a dark background.
- **The text has an explicit white background.** Clients that invert colours (Gmail apps, Outlook) flip the white background and the navy text together. Clients that keep authored colours keep a readable white block.
- **Checked under forced dark mode.** Chromium's forced dark mode (`--blink-settings=forceDarkModeEnabled=true`) inverts like those clients. In `previews/email-signature-dark-mode.png`, the text turns light, the tile stays intact, and the Daybreak rule and link stay legible.
- **Not tested in real clients.** Send a test to Gmail (web and iOS), Outlook (Windows and web) and Apple Mail before rolling the signature out.

## QR code

No QR library was available: on 2026-11-02, `python -c "import segno"` and `python -c "import qrcode"` both failed, and nothing was installed. The digital card shows a dashed placeholder with three finder squares and the words "QR sample", next to the label "Placeholder, not scannable" and the target URL.

The real code can only be made once the domain is chosen, because it encodes the vCard URL. With segno available, run `segno.make('<vCard URL>', error='m').save('qr.svg', border=4, dark='#121B2A')`, then replace the placeholder `<svg>` in `digital-business-card.html` with the output, keeping the white ground and the 4-module quiet zone.

## Derived asset

`assets/email-signature-logo-tile.png` is 512 x 176 px (2x of 256 x 88) and 29 KB. It is the primary horizontal lockup, full-colour dark (`../../design-system/logos/lockups/alliance-ai-partners-primary-horizontal-full-color-dark.png`), resized to 480 px wide (Lanczos) and centred on a Partner Navy tile with 20 px corners (10 px at 1x, `radius-md`). It is transparent outside the corners. It was made with Pillow on 2026-11-02. Remake it if the lockup changes.

## Copy and sample data

- **Taglines** come from Brand DNA section 7:
  - "Put AI to work." (OG, LinkedIn)
  - "The AI team you don't have to hire." (OG, story)
  - "We build it, run it, and help you grow." (story, LinkedIn)
  - "Partners in AI. Partners in growth." (signature, letterhead footer)
- **Call to action.** "See where AI can help" is the site's primary call to action (PRODUCT.md).
- **Square.** It shows the fixed-quote point of the honest pricing promise (Brand DNA section 6).
- **Fictional people.** Isabel Navarro (partner success lead) appears on the card, e-card, signature, letter and cover. Hannah Whitfield is the letter's recipient and the cover's "prepared for".
- **Contact details are samples.** `+1 202 555 0147` is in the North American 555-0100 to 555-0199 range, which is reserved for fictional use. `allianceaipartners.example` is a placeholder until the domain is chosen; the `.example` domain is reserved and never resolves. The vCard URL is a sample too.
- **The letter is sample content.** The three slow spots and the Friday 20 November date are invented.
- **Placeholders.** These stay as they are until real details exist: `[two weeks]`, `[PRICE]`, `[Registered address]`, `[Company number]`, `[Recipient organisation]`, `[Recipient address]`, `[Partner name]` and `[Proposal number]`. Never fill them with invented values.
- **Nothing is invented.** No price, result, partner name or testimonial appears in any template, and the copy avoids every banned word in PRODUCT.md.

## Design-system issues found while building these

Found while building the templates (2026-11-02) and since resolved or recorded in the design system:

1. **Tailwind width utilities did nothing.** `@utility font-display` and `font-heading` resolved to a unitless `font-stretch`, which browsers reject. Fixed at the source: `build-tokens.py` now emits the `--aap-font-stretch-*` tokens as percentages (`125%`, `112.5%`, `100%`), so the utilities and any direct use of the tokens work.
2. **A stray tool folder sat in the app icons.** Removed. It held a tool's state files, never brand assets, and the logo-kit zip only packs SVG, PNG, ICO and webmanifest files.
3. **The wave graphic has a glow in the logo-kit artwork.** Kept as the logo kit drew it; `imagery.json` and `IMAGERY.md` now limit it to hero and print use, never behind UI text or controls. The templates draw the ribbon in code.
4. **The starburst badge reads "Certified AI Partner".** Nothing in PRODUCT.md backs a certification, so its manifest entry now says to use it only once one exists. The templates don't use it. This needs a decision from Alliance.
5. **The descriptor lockups read "ENTERPRISE AI CONSULTING".** This doesn't match the founder and CEO positioning; their manifest entries now say to check the descriptor before use. The templates don't use them. This needs a decision from Alliance.

## Verification (2026-11-02)

These checks ran with headless Chromium (Playwright 1.63) over `file://`:

- **Requests and errors.** All nine pages load with no failed requests, HTTP errors, console errors or broken images.
- **Fonts.** Mona Sans and Mona Sans Mono load on the eight pages that use them. The signature uses system fonts on purpose.
- **Size.** Each `#artefact` measures its stated size.
- **Clipping.** No text is clipped, and no text sits outside its artefact.
- **Contrast.** Each text element was measured against the ground under it, and every one passes WCAG AA. The lowest was 5.11:1, Alliance Blue accent words on Daylight; since the finish review those words are Partner Navy marked by weight (16.07:1).
- **Print output.** Printing to PDF with the CSS page size gives the business card 2 pages at 252 x 144 pt (3.5 x 2 in) and the letterhead 1 page of A4.
- **Dark mode.** The signature stays readable under forced dark mode (see "Dark mode").
- **Visual review.** Two review rounds by eye fixed these problems:
  - the story's call to action overlapped its URL
  - the square's accent phrase broke across lines
  - the signature's contact values didn't align
  - the e-card URL broke mid-word
  - the cover's ribbon read as a straight slash
  - the swallow crowded the story's headline
  - the letter body could run into the ribbon
