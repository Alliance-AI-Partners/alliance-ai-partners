# Alliance AI Partners design system

The design system for the new Alliance AI Partners website: tokens, components, fonts, icons, imagery and logos in one place, built from the finalized logo kit so the site, the emails, the stationery and the merchandise all look like one company. The brand kit that shows these assets lives at [../brand-kit/index.html](../brand-kit/index.html).

| | |
|---|---|
| Built | 2026-11-02 |
| Source | The finalized logo kit (`docs/brand-kit/` and the Figma file [Alliance AI Partners — Logo Suite](https://www.figma.com/design/rXNPaaMds46oWgM64QPRI6/Alliance-AI-Partners-%E2%80%94-Logo-Suite)) and its palette, "A, P and the Ribbon" (`docs/brand-kit/_build/palette.json`) |
| Product truth | [../PRODUCT.md](../PRODUCT.md) and the Brand DNA guide (`AllianceAIPartners/Brand DNA & Foundation.md`) |
| Stack | Next.js on Vercel; plain CSS custom properties plus a Tailwind CSS v4 theme |
| Type | Mona Sans and Mona Sans Mono (SIL Open Font License) |
| Direction | "The Ribbon": one Daybreak ribbon (Partner Navy to Alliance Blue to Ribbon Cyan) ties the page together, the way it binds the A and the P |

## Documents in this folder

| File | What it answers |
|---|---|
| [README.md](README.md) | This map: what is where, how to start, naming and rights |
| [DESIGN.md](../DESIGN.md) | The design language as rules: atmosphere, colour roles, type, components, layout, motion and what is banned |
| [AUDIT.md](AUDIT.md) | The quality record: the finish review, detector triage, accessibility, provenance and the decisions still open |
| [COMPONENTS.md](COMPONENTS.md) | Every `aap-*` class with markup, states and accessibility notes |
| [fonts/FONTS.md](fonts/FONTS.md) | Why Mona Sans, the type roles, `@font-face`, Next.js loading, fallbacks and licence |
| [imagery/IMAGERY.md](imagery/IMAGERY.md) | Art direction, the brand graphics, the generated backgrounds and text over images |
| [specimen.html](specimen.html) | Every component live, on Daylight and on a Partner Navy chapter |

## Quick start

1. **Static pages.** Link the tokens, then the components. Keep the folder structure intact: `tokens.css` loads the fonts through relative `../fonts/` URLs.

   ```html
   <link rel="stylesheet" href="design-system/tokens/tokens.css">
   <link rel="stylesheet" href="design-system/css/components.css">
   <link rel="stylesheet" href="design-system/imagery/image-overlays.css"> <!-- only for text over imagery -->
   ```

   `tokens.css` defines `@font-face` rules and every `--aap-*` custom property on `:root`; it has no classes. [css/components.css](css/components.css) holds the `aap-*` component classes built on those tokens.

2. **The Next.js site with Tailwind CSS v4.** Import the tokens and the generated theme into the global stylesheet, and load the fonts with `next/font` (recipe in [fonts/FONTS.md](fonts/FONTS.md)):

   ```css
   /* app/globals.css */
   @import "tailwindcss";
   @import "../design-system/tokens/tokens.css";
   @import "../design-system/tokens/tailwind-theme.css";
   @import "../design-system/css/components.css"; /* optional: the aap-* classes */
   ```

   The theme clears Tailwind's default palette, so only brand colours exist as utilities: `bg-page`, `bg-raised`, `bg-inverse`, `text-ink`, `text-ink-secondary`, `border-line`, `bg-action hover:bg-action-hover`, `text-link`, plus the type roles (`text-display-xl`, `text-heading-2`, `text-body`...), radii (`rounded-md`...), shadows and easings. `font-display` and `font-heading` set the two type widths.

3. **Icons.** Inline the SVGs from [icons/ui/](icons/ui/) and [icons/social/](icons/social/) or use the sprite. Every icon inherits `currentColor`.

   ```html
   <button type="button" aria-label="Search">
     <svg width="24" height="24" aria-hidden="true"><use href="/icons/sprite.svg#icon-search"/></svg>
   </button>
   ```

   Chrome blocks `<use href="sprite.svg#...">` on `file://` pages, so pages opened from disk inline the SVG instead. In React, the design-taste guidance recommends `@phosphor-icons/react` for icons beyond this set; keep its stroke at the same weight.

4. **The logo for the surface.**

   | Surface | File |
   |---|---|
   | Daylight or white | [logos/lockups/alliance-ai-partners-primary-horizontal-full-color-light.svg](logos/lockups/alliance-ai-partners-primary-horizontal-full-color-light.svg) |
   | Partner Navy | [logos/lockups/alliance-ai-partners-primary-horizontal-full-color-dark.svg](logos/lockups/alliance-ai-partners-primary-horizontal-full-color-dark.svg) |
   | Photographs under a scrim | [logos/lockups/alliance-ai-partners-primary-horizontal-mono-white.svg](logos/lockups/alliance-ai-partners-primary-horizontal-mono-white.svg) |
   | Embroidery, screen print | `*-flat-light.svg` or `*-flat-dark.svg` (one brand ink) |
   | One-ink print, stamps | `*-mono-black.svg` |
   | Small spaces (avatars, favicons) | [logos/marks/](logos/marks/) and [logos/favicons/](logos/favicons/) |

   Clear space is 0.287 x the mark's height on every side. Minimum sizes are on the brand-kit page and in `docs/brand-kit/README.md`.

5. **App icons.** [logos/app-icons/](logos/app-icons/) holds the favicons, the touch icon, the PWA icons (including a maskable one) and `site.webmanifest`:

   ```html
   <link rel="icon" href="/favicon.ico" sizes="32x32">
   <link rel="icon" href="/favicon.svg" type="image/svg+xml">
   <link rel="apple-touch-icon" href="/apple-touch-icon.png">
   <link rel="manifest" href="/site.webmanifest">
   <meta name="theme-color" content="#121B2A">
   ```

## What is where

```
design-system/
  README.md  AUDIT.md  COMPONENTS.md  specimen.html   (DESIGN.md lives at the project root)
  tokens/        tokens.json (source), tokens.css, tailwind-theme.css, tokens-manifest.json, build-tokens.py
  css/           components.css
  fonts/         FONTS.md, mona-sans/ (variable TTF masters + OFL.txt)
  icons/         icons.json, sprite.svg, build-icons.py, ui/ (28), social/ (5), brand/ (12 service icons x 3 styles, SVG + PNG)
  imagery/       IMAGERY.md, imagery.json, image-overlays.css, graphics/ (logo-kit brand graphics), backgrounds/ (generated)
  logos/         logos.json, lockups/, marks/, favicons/, app-icons/
  screenshots/   pages/ (specimen, desktop and mobile), components/ (one capture per specimen section)
```

Every asset folder has a JSON manifest (`{area, retrieved, files[]}`) with each file's path, description and source. Files we made ourselves, rather than took from the logo kit, are marked `"derived": true`.

## Naming

- Files are lowercase kebab-case: `alliance-ai-partners-<lockup>-<state>.svg`, `<icon-name>.svg`, `<service>-<style>.png`.
- Custom properties are `--aap-<group>-<name>`; classes are `aap-<component>` with `--modifier` and `__part`. The Figma Logo Suite's Brand Colors variables use these names as their code syntax (for example `var(--aap-color-brand-partner-navy)`), so rename a colour token in both places.
- Colour names are the palette's: Alliance Blue, Ribbon Cyan, Partner Navy, Daylight, Pure White, and the shading tokens (Partner 30 to 50, Alliance 38 to 50, Ribbon 57). Their numbers are OKLCH lightness x 100.

## Rebuilding

| Change | Run |
|---|---|
| A token value | edit `tokens/tokens.json`, then `python design-system/tokens/build-tokens.py` |
| An icon | edit `icons/build-icons.py`, then run it |
| Backgrounds or merch mockups | `brand-kit/tools/generate-imagery.py` (needs `GEMINI_API_KEY`) |
| The brand-kit page data | `python brand-kit/tools/build-assets-data.py` |
| Screenshots | `node brand-kit/tools/capture.cjs <page.html> <out.png> --width 1440 --full` (needs Playwright) |

## Accessibility

Every text colour pairing passes WCAG 2.x AA, and the ratio is recorded in the token's description. Focus is always visible, controls are 44 px tall by default, and reduced motion, reduced transparency and increased contrast preferences are honoured. Ribbon Cyan is never used as text on light grounds (1.63:1).

## Rights

The logo, palette, graphics and mascot belong to Alliance AI Partners. Mona Sans and Mona Sans Mono are licensed under the SIL Open Font License 1.1 (see [fonts/mona-sans/OFL.txt](fonts/mona-sans/OFL.txt)). The UI and social icons were drawn for this system; the social glyphs are simplified versions of third-party marks for footers, so use each platform's official asset where an exact mark is required. Generated images carry their prompt and model in a sidecar JSON.
