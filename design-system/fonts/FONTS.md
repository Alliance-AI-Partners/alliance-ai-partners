# Fonts

One superfamily carries the whole website: **Mona Sans** for every heading, body line and control, and its companion **Mona Sans Mono** for numbers that need to line up. Both are open source (SIL Open Font License 1.1), so they can ship on the site, in print and on merchandise with no per-seat or per-view fee.

## Why Mona Sans

- **It rhymes with the wordmark.** The logo's wordmark is Montserrat Bold, a wide geometric sans. Mona Sans has a width axis from 75 to 125, and its Expanded end gives headlines the same wide, steady stance without repeating Montserrat, which is common enough on the web to look like a template.
- **One family does every job.** Width, weight (200 to 900) and optical size live in one variable file: Expanded semibold for display, Semi-expanded for section headings, normal width for reading, all from the same file.
- **It reads as built, not bought.** It is precise and calm, has true tabular figures for prices and tables, and it is not one of the faces every AI-built site defaults to (Inter, DM Sans, Plus Jakarta Sans, Space Grotesk and the like).
- **The mono belongs to the same family.** Sources, times and invoice figures use Mona Sans Mono, so data never looks pasted in from another product.

## Roles

| Role | Family | Width | Weight | Size (390 px to 1440 px) | Tracking | Use |
|---|---|---|---|---|---|---|
| display-xl | Mona Sans | 125 % | 640 | 48 to 92 px | -0.035em | The one statement on a page |
| display-lg | Mona Sans | 125 % | 620 | 40 to 68 px | -0.03em | Chapter openers |
| heading-1 | Mona Sans | 112.5 % | 600 | 34 to 52 px | -0.025em | Page titles |
| heading-2 | Mona Sans | 112.5 % | 600 | 28 to 40 px | -0.02em | Section titles |
| heading-3 | Mona Sans | 100 % | 600 | 22 to 28 px | -0.012em | Sub-sections, card titles |
| heading-4 | Mona Sans | 100 % | 600 | 18 to 20 px | -0.006em | Small headings |
| body-lg | Mona Sans | 100 % | 400 | 18 to 21 px | -0.004em | Lead paragraphs |
| body | Mona Sans | 100 % | 400 | 16 to 17 px | 0 | Running text |
| body-sm | Mona Sans | 100 % | 400 | 14 to 15 px | 0.003em | Secondary text |
| label | Mona Sans | 100 % | 540 | 14 px | 0.01em | Buttons, form labels, navigation |
| caption | Mona Sans | 100 % | 450 | 13 px | 0.012em | Captions, meta |
| numeral | Mona Sans | 125 % | 600 | 40 to 64 px | -0.03em | Prices and figures (tabular lining numerals) |
| mono | Mona Sans Mono | n/a | 420 | 13 to 14 px | 0 | Sources, times, codes, invoice lines |

Tracking tightens as size grows and opens slightly as it shrinks; never use one letter-spacing for every size. Every value above is a token in [../tokens/tokens.json](../tokens/tokens.json) (`typography.*`) and a custom property in [../tokens/tokens.css](../tokens/tokens.css) (`--aap-typography-<role>-size`, `-weight`, `-line-height`, `-tracking`, `-stretch`).

## Files

| File | Axes | Size |
|---|---|---|
| [mona-sans/MonaSansVF-wdth-opsz-wght.ttf](mona-sans/MonaSansVF-wdth-opsz-wght.ttf) | width 75-125, weight 200-900, optical size | 774 KB |
| [mona-sans/MonaSansVF-Italic-wdth-opsz-wght.ttf](mona-sans/MonaSansVF-Italic-wdth-opsz-wght.ttf) | the same, italic | 749 KB |
| [mona-sans/MonaSansMonoVF-wght.ttf](mona-sans/MonaSansMonoVF-wght.ttf) | weight 200-900 | 96 KB |
| [mona-sans/OFL.txt](mona-sans/OFL.txt) | licence | |

Source: [github.com/github/mona-sans](https://github.com/github/mona-sans), release v2.0.27 (2026-05-19), file `mona-sans-variable-v2.0.27.zip`, downloaded 2026-11-02 with the user's approval. The files are the official variable fonts, unmodified.

## Using them

**Static pages, emails previews and print.** [../tokens/tokens.css](../tokens/tokens.css) declares the `@font-face` rules with relative URLs, so keep this folder next to `tokens/`.

**The Next.js site.** These masters are large because they carry every width. The website loads them with `next/font/local`, which serves them from the site, preloads them and adds a size-matched fallback, so text does not jump when the font arrives. It does not subset local files (only `next/font/google` does), so the site loads just two: the upright Mona Sans and Mona Sans Mono. The italic master stays out until a page sets type in italics. The site's `app/fonts.ts`:

```tsx
// app/fonts.ts
import localFont from "next/font/local";

export const monaSans = localFont({
  src: "../design-system/fonts/mona-sans/MonaSansVF-wdth-opsz-wght.ttf",
  style: "normal",
  weight: "200 900",
  variable: "--font-mona-sans",
  display: "swap",
  // Declare the width axis, or the browser clamps font-stretch to 100% and Expanded display type falls back to normal width.
  declarations: [{ prop: "font-stretch", value: "75% 125%" }],
});

export const monaSansMono = localFont({
  src: "../design-system/fonts/mona-sans/MonaSansMonoVF-wght.ttf",
  style: "normal",
  weight: "200 900",
  variable: "--font-mona-sans-mono",
  display: "swap",
});
```

Then put both classes on `<html>` and point the tokens at the variables (`--aap-font-family-sans: var(--font-mona-sans), ...`), as `app/layout.tsx` and `app/globals.css` do. If you load Mona Sans from Google Fonts through `next/font/google` instead, confirm first that the width axis is offered and requested (`axes: ["wdth"]`); without it the Expanded display widths fall back to normal width.

## Fallbacks

`ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` for Mona Sans; `ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace` for the mono. Email clients mostly ignore web fonts, so the email templates are designed to hold up in Helvetica and Arial.

## Licence

SIL Open Font License 1.1, with the Reserved Font Name "Mona". Using, embedding, printing and redistributing the unmodified files are all allowed, including commercially. A modified version (for example a subset you make yourself and redistribute) may not use the name "Mona"; serving the files through `next/font` on your own site, as the website does, is the normal web-font use. The licence text is in [mona-sans/OFL.txt](mona-sans/OFL.txt).

## Logo type

The logo's wordmark is Montserrat Bold converted to outlines in the logo files. Do not set the company name in live Montserrat or in Mona Sans as a stand-in for the logo; use the files in [../logos/](../logos/).
