---
name: Alliance AI Partners
description: The Ribbon. A Daylight system drawn only from the A+P logo kit, tied together by one lit ribbon.
colors:
  alliance-blue: "#1B56FF"
  ribbon-cyan: "#00D5FF"
  partner-navy: "#121B2A"
  daylight: "#F4F7FB"
  pure-white: "#FFFFFF"
  shading-partner-30: "#1A2D4E"
  shading-partner-38: "#2E4265"
  shading-partner-46: "#42587C"
  shading-partner-50: "#4D6388"
  shading-alliance-38: "#243F7B"
  shading-alliance-46: "#244EB6"
  shading-alliance-50: "#2153D8"
  shading-ribbon-57: "#006DF5"
  neutral-50: "#ECEFF4"
  neutral-100: "#E3E6EC"
  neutral-150: "#D8DDE4"
  neutral-200: "#CCD1D9"
  neutral-400: "#979FAB"
  neutral-500: "#78818F"
  neutral-600: "#60697A"
  neutral-800: "#323E50"
  neutral-900: "#202C3E"
  text-inverse-secondary: "#BFCBE0"
  text-inverse-tertiary: "#95A6C1"
  status-error: "#C42B42"
  status-error-surface: "#FCEBEE"
  status-error-inverse: "#FF8B9A"
  status-success: "#0B7A55"
  status-success-surface: "#E5F5EE"
  status-success-inverse: "#5FD8A8"
  status-warning: "#8A5800"
  status-warning-surface: "#FFF4DD"
  status-warning-inverse: "#FFC46B"
  status-info-surface: "#E8EEFF"
  print-black: "#000000"
typography:
  display-xl:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(3rem, 1.979rem + 4.19vw, 5.75rem)"
    fontWeight: 640
    lineHeight: 0.98
    letterSpacing: "-0.035em"
    fontVariation: "'wdth' 125"
  display-lg:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 1.85rem + 2.667vw, 4.25rem)"
    fontWeight: 620
    lineHeight: 1.02
    letterSpacing: "-0.03em"
    fontVariation: "'wdth' 125"
  heading-1:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.125rem, 1.707rem + 1.714vw, 3.25rem)"
    fontWeight: 600
    lineHeight: 1.06
    letterSpacing: "-0.025em"
    fontVariation: "'wdth' 112.5"
  heading-2:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 1.471rem + 1.143vw, 2.5rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
    fontVariation: "'wdth' 112.5"
  heading-3:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.375rem, 1.236rem + 0.5714vw, 1.75rem)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.012em"
  heading-4:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.125rem, 1.079rem + 0.1905vw, 1.25rem)"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.006em"
  body-lg:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.125rem, 1.055rem + 0.2857vw, 1.3125rem)"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.004em"
  body:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1rem, 0.9768rem + 0.09524vw, 1.0625rem)"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  body-sm:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(0.875rem, 0.8518rem + 0.09524vw, 0.9375rem)"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0.003em"
  label:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 540
    lineHeight: 1.3
    letterSpacing: "0.01em"
  caption:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 450
    lineHeight: 1.4
    letterSpacing: "0.012em"
  numeral:
    fontFamily: "Mona Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 1.943rem + 2.286vw, 4rem)"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "'tnum' 1, 'lnum' 1"
    fontVariation: "'wdth' 125"
  mono:
    fontFamily: "Mona Sans Mono, ui-monospace, SF Mono, Cascadia Code, Menlo, Consolas, monospace"
    fontSize: "clamp(0.8125rem, 0.7893rem + 0.09524vw, 0.875rem)"
    fontWeight: 420
    lineHeight: 1.5
    letterSpacing: "0em"
    fontFeature: "'tnum' 1"
rounded:
  none: "0px"
  sm: "4px"
  md: "10px"
  lg: "18px"
  xl: "28px"
  pill: "999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "20px"
  "6": "24px"
  "8": "32px"
  "10": "40px"
  "12": "48px"
  "16": "64px"
  "20": "80px"
  "24": "96px"
  "32": "128px"
  section: "clamp(4.5rem, 3rem + 5vw, 8rem)"
  gutter: "clamp(1rem, 0.6rem + 1.6vw, 2rem)"
components:
  button-primary:
    backgroundColor: "{colors.alliance-blue}"
    textColor: "{colors.pure-white}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.shading-alliance-50}"
  button-primary-pressed:
    backgroundColor: "{colors.shading-alliance-46}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.partner-navy}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 20px"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.neutral-100}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.partner-navy}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "44px"
  link:
    textColor: "{colors.partner-navy}"
  link-inverse:
    textColor: "{colors.ribbon-cyan}"
  input:
    backgroundColor: "{colors.pure-white}"
    textColor: "{colors.partner-navy}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "44px"
  card:
    backgroundColor: "{colors.pure-white}"
    textColor: "{colors.partner-navy}"
    rounded: "{rounded.lg}"
    padding: "32px"
  tag:
    backgroundColor: "{colors.neutral-50}"
    textColor: "{colors.shading-partner-46}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "0 12px"
    height: "26px"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.shading-partner-46}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: "0 12px"
    height: "28px"
  nav-link:
    textColor: "{colors.shading-partner-46}"
    typography: "{typography.label}"
  nav-link-current:
    textColor: "{colors.partner-navy}"
  tab:
    textColor: "{colors.shading-partner-46}"
    typography: "{typography.label}"
    padding: "12px 0"
  tab-selected:
    textColor: "{colors.partner-navy}"
  chapter-inverse:
    backgroundColor: "{colors.partner-navy}"
    textColor: "{colors.daylight}"
  panel-inverse:
    backgroundColor: "{colors.shading-partner-30}"
    textColor: "{colors.daylight}"
---

# Design System: Alliance AI Partners

## Overview

**Creative North Star: "The Ribbon"**

One continuous ribbon, the one that binds the A and the P in the mark, leaves the logo and ties the whole surface together. Everything else is taken from the same logo kit and nothing else: its palette, its eight shading tones, its top-left light, its wide wordmark, its facets and its swallow. The world is user-pinned and international by design; the Philippines base is a fact stated in copy, never a visual theme.

The ground is Daylight, calm and open, broken by whole Partner Navy chapters (the voice section, the footer). Type is Partner Navy and does the work; colour is rationed. Alliance Blue is reserved for the single action that commits, so it reads as a decision rather than decoration. Ribbon Cyan is light: the ribbon's lit end, accents on navy, focus on navy. Depth is lit the way the 3D mark is lit, from the top left, with soft directional shadows and a lit top edge, never glow, with blur only where it does a job.

The system refuses the AI-agency default of a dark grid, glowing gradients and three identical feature cards, and the usual AI imagery (sparkles, glowing brains, circuit boards, robot faces, purple-and-pink gradients).

**Key Characteristics:**
- Daylight ground with whole Partner Navy chapters; no other section grounds.
- One Alliance Blue committing action per view; everything else interactive is navy.
- The ribbon as the single signature: a satin band, lit from the top left, that twists to show its Partner 38 back.
- Mona Sans Expanded display over normal-width text, Mona Sans Mono for sources, times and codes.
- Depth lit from the top left: soft navy-tinted shadows and a lit top edge, never glow.

## Colors

A cool, near-monochrome navy-and-daylight palette with one electric blue kept for decisions and one cyan kept for light, every value taken from the logo kit's "A, P and the Ribbon" palette.

### Primary
- **Alliance Blue** (`alliance-blue`): the fill of the one committing action in a view (the primary button) and the focus ring on light grounds. Also the lit faces of the 3D A in the artwork. Hover steps down to Alliance 50, pressed to Alliance 46.

### Secondary
- **Ribbon Cyan** (`ribbon-cyan`): the ribbon's light. On Partner Navy it is the link colour, the accent word, the focus ring, checked controls and step markers. On light grounds it appears only inside the ribbon artwork and as a faint tint (text selection at 38%, the highlighted table row at 10%).

### Tertiary
- **The Alliance and Ribbon shading tones** (`shading-alliance-38`, `shading-alliance-46`, `shading-alliance-50`, `shading-ribbon-57`): the mark's own shadow bands. They build the ribbon face, the hover and pressed states of the primary button, and chart series 4.
- **The Partner shading tones** (`shading-partner-30` to `shading-partner-50`): the slate faces of the P. Partner 30 is the ribbon's edge where it turns edge-on and the raised panel inside a navy chapter; Partner 38 is the ribbon's back; Partner 46 is secondary text on light grounds (6.7:1 on Daylight).

### Neutral
- **Partner Navy** (`partner-navy`): all type on light grounds (16.07:1 on Daylight), the navy chapter ground, links, checked controls, selected tabs, step markers.
- **Daylight** (`daylight`): the page ground and print paper; also primary text on navy.
- **Pure White** (`pure-white`): raised surfaces (cards, inputs, menus), one step lighter than the page; text on Alliance Blue (5.49:1).
- **Cool neutrals** (`neutral-50` to `neutral-900`, derived from Partner Navy toward Daylight): Neutral 50 is the sunken well for code, tables and quiet panels; 150 and 200 are hairlines and card edges; 500 is the 3:1 control border; 600 is tertiary text (5.14:1); 800 and 900 are dividers and wells inside navy chapters.
- **Navy-tinted inverse text** (`text-inverse-secondary`, `text-inverse-tertiary`): supporting copy and captions on navy, tinted from the navy hue rather than grey.
- **Status** (error, success, warning, each with a light surface and a navy-ground variant; info uses Alliance Blue and Ribbon Cyan): alerts, field errors and live states only.
- **Print Black** (`print-black`): one-ink print work only. Never a screen colour.

### Named Rules
**The One Commitment Rule.** Alliance Blue fills exactly one committing action per view, the primary button. Links, accent words, form accents, checked controls, tabs, and the current-city clock are never Alliance Blue. The focus ring stays blue as an accessibility affordance; the info alert's icon and edge and the first chart series are the only other blue, and they are status and data, not actions.

**The Navy Link Rule.** Links are Partner Navy and always underlined (a 1px underline at 45% that goes solid on hover); inside a navy chapter they turn Ribbon Cyan. Colour alone never marks a link.

**The Light Not Text Rule.** Ribbon Cyan is never text on a light ground. It is the ribbon's light, and on navy it is the accent.

**The Two Grounds Rule.** A section's ground is Daylight or a whole Partner Navy chapter. The sunken Neutral 50 is a well for code, tables and quiet panels, never a section ground.

## Typography

**Display Font:** Mona Sans at Expanded width (125%), with ui-sans-serif and system-ui fallbacks
**Body Font:** Mona Sans at normal width (100%)
**Label/Mono Font:** Mona Sans Mono, with ui-monospace fallbacks

**Character:** One variable family carries the whole voice. Its width axis lets display type run as wide as the Montserrat wordmark, with tight negative tracking, while text stays at normal width and reads calmly; the mono cut marks anything sourced, timed or coded.

### Hierarchy
- **Display XL** (640, 48px to 92px fluid, 0.98, Expanded): the one statement per page, such as the hero title.
- **Display LG** (620, 40px to 68px fluid, 1.02, Expanded): chapter openers; every showcase section title.
- **Heading 1 / Heading 2** (600, 34px to 52px and 28px to 40px fluid, Semi-expanded 112.5%): page and section titles in documents and templates.
- **Heading 3 / Heading 4** (600, 22px to 28px and 18px to 20px, normal width): sub-sections, card and step titles, accordion summaries.
- **Body LG** (400, 18px to 21px, 1.55, max 60ch, Partner 46): lead paragraphs.
- **Body** (400, 16px to 17px, 1.6, max 68ch): running text.
- **Body SM / Caption** (400 at 14px to 15px; 450 at 13px): secondary text, meta, help text.
- **Label** (540, 14px, 0.01em, sentence case): buttons, form labels, nav, tabs.
- **Numeral** (600, 40px to 64px, Expanded, tabular lining figures): prices and figures.
- **Mono** (420, 13px to 14px, tabular): sources, times, hex values, codes.

### Named Rules
**The Wide Voice Rule.** Width carries rank: Expanded for display, Semi-expanded for section headings, normal width for everything a reader reads at length.

**The Light Accent Rule.** The one marked word in a headline drops to regular weight (400) on light grounds and turns Ribbon Cyan on navy. Never Alliance Blue, never a gradient fill.

**The No Label Above Rule.** Nothing sits above a heading. There is no eyebrow role; dates and issue numbers go in a meta line below.

## Layout

Content sits in a 1320px container with a fluid side gutter (16px to 32px). Sections breathe with fluid vertical padding (72px to 128px); reading text stops at 68ch, leads at 60ch. The spacing scale is a 4px base (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128), with 32px card padding, 48px between a section head and its content, and 80px to 128px between chapters.

Section heads are asymmetric two-column grids (title 0.9fr, lead 1.1fr, aligned to the baseline); the hero splits text and mark 1.08fr to 1fr. Below 1024px every two-column grid collapses to one column and multi-column galleries drop to two. Breakpoints are 640, 768, 1024, 1280 and 1536px, min-width.

## Elevation & Depth

Depth is lit like the 3D mark: light from the top left, so every shadow falls down and to the right, tinted with Partner Navy, soft and low-contrast. Raised planes add a lit top edge (a white inset highlight) in place of a border-light trick. Flat tonal steps do the rest: Daylight page, white raised surface, Neutral 50 well; Partner Navy chapter, Partner 30 panel. There is no glow and no glass anywhere a reader reads or acts.

### Shadow Vocabulary
- **Resting** (`0 1px 2px rgba(18, 27, 42, 0.06)`): buttons and inputs at rest.
- **Card** (`1px 2px 6px -1px rgba(18, 27, 42, 0.10), 0 1px 2px rgba(18, 27, 42, 0.05)`): cards at rest, always paired with the lit edge.
- **Raised** (`2px 10px 24px -8px rgba(18, 27, 42, 0.18)`): hovered cards, menus, the swatch strip.
- **Lifted** (`4px 24px 48px -16px rgba(18, 27, 42, 0.24)`): dialogs and the hero object.
- **Lit edge** (`inset 0 1px 0 rgba(255, 255, 255, 0.65)`): the top edge of a raised plane, as on the mark's bevels. The primary button carries a softer one at 20%.

### Named Rules
**The Top-Left Light Rule.** Every shadow and every gradient obeys one light source at the top left. A shadow that falls up or left, or a light that comes from below, is wrong.

**The No Glow Rule.** Depth never comes from glow, bloom or neon, and blur is never decoration. The one material is the sticky header: translucent Daylight with a backdrop blur, a specific effect that keeps the bar legible over content scrolling beneath it and turns solid under reduced transparency. The ribbon is lit artwork, not a light source.

## Shapes

Corners are gently rounded and scale with the size of the plane: 4px for tags, checkboxes and focus rings; 10px for buttons, inputs and alerts; 18px for cards and media; 28px for feature panels such as the palette strip; full pills only for status chips, the sticker and ribbon rules. Lines that belong to the ribbon (rules, ribbon strokes, full-bleed media) keep square or round caps, never a radius. Borders are 1px hairlines; 2px is reserved for focus and selection.

## Components

### Buttons
Confident and quiet: a label-weight word in a 44px control, never shouting.
- **Shape:** gently rounded (10px), 44px tall (36px small, 52px large), 20px side padding.
- **Primary:** Alliance Blue with white label, the resting shadow and a soft lit top edge. One per view.
- **Hover / Focus:** primary steps down to Alliance 50 and lifts to the card shadow; press feedback is immediate (80ms, a 1px drop and 98.5% scale) and goes to Alliance 46. A forward arrow slides 3px on hover with a no-overshoot spring. Focus is a 2px Alliance Blue outline at 2px offset (Ribbon Cyan on navy).
- **Secondary:** transparent with a Partner Navy label and a Neutral 500 border; hover fills Neutral 100. On navy the label turns Daylight and the hover fill is 8% Daylight.
- **Quiet:** borderless secondary with 12px padding, for the second action beside a primary.
- **Busy:** a cyan light sweeps along the bottom edge while `aria-busy` is set.

### Chips and Tags
- **Tag:** Neutral 50 fill, Partner 46 text at caption size, 4px corners, 26px tall.
- **Chip:** pill outline in the default border with a status dot (success green for live, Neutral 400 for away).

### Cards / Containers
- **Corner Style:** 18px.
- **Background:** white on Daylight; Partner 30 inside a navy chapter.
- **Shadow Strategy:** card shadow with the lit edge at rest, raised shadow on hover (see Elevation & Depth).
- **Border:** 1px subtle hairline (Neutral 150).
- **Internal Padding:** 32px.

### Inputs / Fields
- **Style:** white field, 1px Neutral 500 border (3:1 against the ground), 10px corners, 44px tall, 16px side padding, resting shadow. Labels sit above in Label type; help text below in Caption.
- **Focus:** the border turns Alliance Blue with a 3px ring at 28%; hover darkens the border to Partner 46.
- **Checked controls:** checkboxes and radios fill Partner Navy with a white mark (Ribbon Cyan with a navy mark on navy), never Alliance Blue.
- **Error / Disabled:** error border and message in the error red (the lighter error variant on navy); disabled at 45% opacity.

### Navigation
- **Header:** sticky, 72px tall, translucent Daylight at 86% with a 16px backdrop blur, fading into the page with a short gradient instead of a hard divider; solid under reduced transparency. Logo 36px tall.
- **Links:** Label type in Partner 46; hover and current page turn Partner Navy. The current page carries a short ribbon-gradient underline, the only place a nav state uses the ribbon.
- **Tabs:** same type and colours; the selected tab carries a Partner Navy underline bar. Never Alliance Blue.
- **Footer:** a Partner Navy chapter with a 2:1:1:1 grid (two columns on tablets, one on phones).

### Sourced Claims and Time Zones
- **Claims:** a figure carries a small mono key in a hairline box that links to its source in a mono source list below a hairline; the targeted source turns primary.
- **Time zones:** cities in a hairline-ruled row, the time in 28px Mono. The current city is marked by semibold weight and a green live dot, in navy, never blue.

### The Ribbon (signature)
The one signature, used once or twice per surface to tie sections together, never as a divider for every block.
- **Full form (the thread):** one continuous band from the hero mark's P to the mark of the footer lockup, never hidden behind content. It runs down the side gutters, beside the content, and crosses between sections through the open middle of each gap, clear of the caps of any headline (in the hero it arcs over the mark and above the title). It is a satin band sampled every 5px and lit from the top left: the face runs Alliance 46 through Ribbon 57 to Ribbon Cyan, brightening toward Daylight where it catches the light; the back is Partner 38; seen edge-on it pinches to a Partner 30 edge. It makes one full twist as it arcs over the mark, one in each crossing, and about one every 1100px along a long run. About 15px wide at 1440 and about 8px on phones: its width scales with the gutter, and the showcase keeps its side gutters at least 32px (`--aap-space-gutter: 2rem`) so the ribbon always has clear space beside the content. No offset underside, no glow. It is drawn by `drawThread` in `brand-kit/index.html` and redrawn whenever the page reflows.
- **Line form:** a 3px Daybreak stroke that draws itself as it enters view; the ribbon rule is its straight version, a 3px Ribbon 57 to Ribbon Cyan rule that grows from the left.
- **Steps:** the four-step sequence hangs from a ribbon-gradient rule with navy numbered markers (cyan on navy).

## Do's and Don'ts

### Do:
- **Do** draw every visual from the logo kit: the A+P ribbon mark, its palette and shading, the wave, facets, patterns and swallow. Nature is built from ribbon and facets.
- **Do** keep Alliance Blue to the one committing action in view; make every other interactive accent Partner Navy (Ribbon Cyan inside a navy chapter).
- **Do** underline every inline link.
- **Do** light depth from the top left: navy-tinted shadows falling down and right, plus a lit top edge on raised planes.
- **Do** set display type at Expanded width with negative tracking, and running text at normal width within 68ch.
- **Do** put sources, times, codes and hex values in Mona Sans Mono with tabular figures.
- **Do** keep all text at WCAG AA or better on its ground.
- **Do** keep the glow of the graphic-wave artwork to hero and print use, never behind UI text or controls.

### Don't:
- **Don't** use Alliance Blue for links, accent words, checked controls, tabs or form accents.
- **Don't** set Ribbon Cyan as text on Daylight or white.
- **Don't** use the sunken Neutral 50 well, or any third tone, as a section ground.
- **Don't** create depth with glow, neon or bloom, don't use blur as decoration (the sticky header's material is the one functional use), and don't draw the ribbon as a glowing line or as an offset copy of itself.
- **Don't** put the Daybreak gradient behind small text, or fill text with a gradient.
- **Don't** put a small label above a heading.
- **Don't** use Philippine or other regional cultural motifs; the base is stated in copy, never shown as a theme.
- **Don't** use sparkles, glowing brains, circuit boards, robot faces, or purple-and-pink gradients.
- **Don't** use Print Black on screen.
