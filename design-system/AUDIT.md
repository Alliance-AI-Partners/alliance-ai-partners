# Alliance AI Partners design system audit

The quality record for the design system and brand kit built on 2026-11-02. The reference repository's audit examines an existing website before a redesign. Alliance has no website yet, so this file records instead how the new system was checked, what the checks found, and what is still open.

- **Evidence base.** The impeccable finish review: one review and three scoring rounds, judged on the captures in `.impeccable/review/`. Also the impeccable detector (`.impeccable/review/detect.json`), the contrast ratios recorded in [tokens/tokens.json](tokens/tokens.json), and the checks the email and template builds ran ([../brand-kit/emails/README.md](../brand-kit/emails/README.md), [../brand-kit/templates/README.md](../brand-kit/templates/README.md)).
- **Status.** The reviewer's disposition is **fix**. Every craft finding is resolved. The one open item is the comp round, which is Alliance's decision (see [Open decisions](#open-decisions)).

## Finish review

| # | Finding | Result |
|---|---|---|
| 1 | Persistence. The build path chosen was comp-first, but no comp round ran: when the direction round ran, the image key had not been found. | **Open.** Alliance decides (see below). |
| 2 | The ribbon did not thread the page. It ran only in the hero. | Resolved. One continuous ribbon runs from the P of the hero mark to the mark of the footer lockup, down the side gutters and across the open middle of each gap. |
| 3 | The ribbon was a flat stroke with a soft halo. | Resolved. It is now a satin band lit from the top left. It twists to show its Partner 38 back and pinches to a Partner 30 edge. There is no glow. |
| 4 | Alliance Blue appeared beyond the one action. | Resolved. Links are underlined Partner Navy. Tabs, the slider, the current-city clock, form states and accent words no longer use blue. |
| 5 | Small uppercase labels sat above the email headings. | Resolved. They are removed from all six emails; dates and issue numbers moved to a meta line below the heading. |
| 6 | A third ground (`#ECEFF4` bands) appeared between sections. | Resolved. The page is Daylight with Partner Navy chapters only. |
| 7 | The brand board carried sequence numbers that said nothing. | Resolved on the page and in `brand-board.png`. |
| | Regressions raised while fixing: the ribbon struck through the hero title, ribbon ends crowded section intros, and the ribbon crowded the content on phones. | Resolved. The ribbon passes above the title and has no loose ends. On phones it clears the content by 11 to 12 px, because the showcase keeps its side gutters at least 32 px. The third scoring round found no new regressions. |

## Detector

`impeccable detect` runs on the showcase, the specimen, the component CSS, the emails and the templates. With DESIGN.md in place it also checks every page against the documented type ramp, radii and fonts. It now reports **0 findings**.

Fixed:

- A 4.4:1 title in the brand board's mock browser, now secondary text.
- Two board panels whose light text sat on images over a white fallback. The mock site's hero and the river panel now have a Partner Navy ground under their images, and the river panel's headline moved onto the dark hills in Daylight.
- Board radii set in panel units, now the `md` and `sm` radius tokens.
- 12 px text on the digital business card and in the email footers, now 13 px (the caption size).
- A skipped heading level in the newsletter: h3 is now h2.

Exceptions, each scoped to the files named and recorded with its reason in `.impeccable/config.json`:

| Rule | Where | Why |
|---|---|---|
| `overused-font` "mona sans" | Everywhere | The user asked us to choose the fonts and approved Mona Sans; its width axis echoes the wordmark. |
| `overused-font`, `design-system-font` | Email signature, emails | Email clients don't load web fonts reliably, so they use the email-safe Helvetica and Arial stack. |
| `design-system-font-size` | The five social and cover artboards, emails | Fixed-size canvases set type at their own scale; emails need fixed pixel sizes. |
| `design-system-radius` | Social story | A 1080 x 1920 artboard drawn at 2.2x; its 22 px is the `md` radius at that scale. |
| `cramped-padding` | Showcase, specimen, the five artboards | Content is inset by the container (32 px minimum) or by the artboards' 56 px margins. |
| `marketing-buzzword` | Showcase | The voice section quotes banned words on purpose. |
| `oversized-h1` | Presentation cover | A slide title, meant to be read across a room. |

## Accessibility

- Every text colour pairing passes WCAG 2.x AA, and each token records its ratio:
  - Partner Navy on Daylight: 16.07:1.
  - Secondary text: 6.7:1.
  - White on the primary button: 5.49:1.
  - Ribbon Cyan on navy: 9.84:1.
- Ribbon Cyan is never used as text on light grounds (1.63:1).
- Colour never marks a link on its own: links are always underlined.
- Focus is always visible: a 2 px ring with a 2 px offset.
- Controls are 44 px tall by default.
- Reduced motion, reduced transparency and increased contrast preferences are honoured.
- The ribbon is decorative and hidden from assistive technology. It is drawn by script, so without script the page reads the same without it.
- Emails pass AA in light and dark mode; the lowest ratio is 5.14:1. Templates pass AA.

## Rendering

- There is no horizontal overflow at 390, 768, 1024 or 1440 px. There are no console errors and no broken images.
- The ribbon clears the content column by about 22 px at 1440, 11 px at 1024 and 12 px on phones.
- Emails were checked at 680, 390 and 375 px, in light and dark mode, in Chromium only (see the email README's checklist for real-client testing).

## Provenance

There are 17 generated images: 8 nature backgrounds and 9 merchandise mockups, made with Gemini `gemini-3-pro-image-preview` and reviewed by eye. Each ships as JPEG and WebP with the exact prompt embedded in the file (`impeccable embed-prompt --scan` finds 0 missing) and a JSON sidecar holding the prompt, model, aspect ratio and reference images. The mockups were conditioned on the real logo files; they show how goods could look, while the artwork files in `brand-kit/merch/artwork/` are what gets made.

## Open decisions

These are Alliance's to make; nothing in the kit decides them silently.

1. **The comp round.** The build path chosen was comp-first, but the build ran code-led. Either run a comp round for the showcase now that the image key works, or record in your own words that code-led stands.
2. **The starburst badge** reads "Certified AI Partner", and nothing backs a certification. Its manifest entry says to use it only once one exists.
3. **The descriptor lockups** read "ENTERPRISE AI CONSULTING", which doesn't match the founder and CEO positioning. Their manifest entries say to check the descriptor before use.
4. **The domain.** The digital card's QR code, email links and the hosted email images and fonts all wait on it.
5. **Email clients.** Test the templates in Gmail, Outlook and Apple Mail (Litmus or Email on Acid) before sending.
6. **Prices and results.** `[PRICE]` and the bracketed figures stay until real numbers exist; no figure was invented.
