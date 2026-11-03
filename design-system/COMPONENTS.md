# Components

Every class in [css/components.css](css/components.css), with its markup, states and the tokens behind it. The live page is [specimen.html](specimen.html); renders are in [screenshots/pages/](screenshots/pages/). Load [tokens/tokens.css](tokens/tokens.css) before `components.css`.

Two rules run through all of them:

- **One committing action per view.** Only `.aap-button--primary` is Alliance Blue. Everything else is navy outline, quiet text or a link.
- **Markup never changes for dark chapters.** Wrap a section in `.aap-surface-inverse` and the semantic tokens flip (text, borders, links, focus ring, status colours), so every component below works on Partner Navy as written.

## Base

The base layer themes what the browser would otherwise draw itself: `border-box` sizing, Daylight page ground, Partner Navy text, Mona Sans with optical sizing, the selection colour (Ribbon Cyan at 38 %), caret and form accent colour (Partner Navy; Alliance Blue is kept for the one action), scrollbar colours, link underline offset, a 2 px Alliance Blue focus ring with a 2 px offset (Ribbon Cyan on navy), tabular numerals in tables, and balanced headings. All base rules use `:where()` so they have zero specificity and never fight your classes.

`.aap-skip-link` is the first focusable element on every page: hidden until focused, then an Alliance Blue chip at the top left.

## Surfaces and layout

| Class | What it does |
|---|---|
| `.aap-surface-inverse` | A Partner Navy chapter. Re-points `--aap-color-text-*`, `--aap-color-border-*`, `--aap-color-surface-raised`, the link and focus colours and the status colours to their navy-ground values (secondary text `#BFCBE0`, 10.55:1). |
| `.aap-surface-sunken` | A Neutral 50 well for code, tables or quiet panels. |
| `.aap-container` | Centred content, `min(100% - 2 x gutter, 1320px)`. The gutter is fluid (16 to 32 px). |
| `.aap-section` | Vertical section padding, fluid 72 to 128 px. |
| `.aap-measure` | Caps a text column at 68ch. |

## Type

`.aap-display-xl`, `.aap-display-lg`, `.aap-h1` to `.aap-h4`, `.aap-lead`, `.aap-body`, `.aap-small`, `.aap-label`, `.aap-caption`, `.aap-numeral`, `.aap-mono`. Each applies a full role from the tokens (size, weight, line height, tracking and width). Roles and their reasoning are in [fonts/FONTS.md](fonts/FONTS.md).

`.aap-accent` marks one word or phrase in a headline: a regular weight inside the semibold headline on light grounds, Ribbon Cyan on navy. Never Alliance Blue, which is kept for the one action, never a gradient fill, and never more than one accent per heading.

```html
<h1 class="aap-display-xl">Put AI to <span class="aap-accent">work.</span></h1>
<p class="aap-lead">We build the AI tools and software your business needs, then help you use them to grow.</p>
```

There is deliberately no eyebrow or kicker style: a heading carries its own weight.

## The ribbon

The system's one signature. A Daybreak stroke (Partner Navy to Alliance Blue to Ribbon Cyan) that draws itself as it scrolls into view, using CSS scroll-driven animation. Where that is unsupported, or the visitor prefers reduced motion, it is simply drawn.

```html
<svg class="aap-ribbon" viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true" style="height: 120px">
  <defs>
    <linearGradient id="daybreak" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#121B2A"/><stop offset=".54" stop-color="#1B56FF"/><stop offset="1" stop-color="#00D5FF"/>
    </linearGradient>
  </defs>
  <path d="M0 96 C 220 96, 300 20, 520 24 S 860 104, 1200 18" pathLength="1" stroke="url(#daybreak)"/>
</svg>
```

- Keep `pathLength="1"`; the draw animation depends on it.
- Put the gradient inside the same SVG. Chrome does not paint gradients referenced from an SVG with `display: none`.
- `--aap-ribbon-width` (default 3) sets the stroke.
- `.aap-ribbon-rule` is the straight version: a 3 px ribbon-gradient rule that grows from the left as it enters.

Use the ribbon once or twice per page, to tie sections together. It is not a divider for every block.

## Buttons and links

```html
<a class="aap-button aap-button--primary aap-button--lg" href="/check-up">
  See where AI can help
  <svg data-direction="forward" aria-hidden="true"><use href="/icons/sprite.svg#icon-arrow-right"/></svg>
</a>
<a class="aap-button" href="/brand/logo-kit.zip">Download the logo kit</a>
<button class="aap-button aap-button--quiet" type="button">Read the price list</button>
```

| Modifier or state | Effect |
|---|---|
| (none) | Secondary: navy text and a 3:1 outline, Neutral 100 fill on hover. |
| `--primary` | Alliance Blue, white text (5.49:1), hover Alliance 50, pressed Alliance 46. |
| `--quiet` | No border, tight padding. |
| `--sm`, `--lg` | 36 px and 52 px heights (default 44 px, the touch target). |
| `:active` | Moves down 1 px and scales to 0.985 on press, at once. |
| `[aria-busy="true"]` | Loading: the ribbon runs along the button's foot; clicks are ignored. |
| `:disabled`, `[aria-disabled="true"]` | 45 % opacity, no pointer events. |

An icon with `data-direction="forward"` slides 3 px on hover with the spring easing. `.aap-link` is an inline text link (Partner Navy and always underlined, so colour alone never marks a link; Ribbon Cyan inside a navy chapter) with an optional trailing arrow that does the same. Add `.aap-link--standalone` to a link on its own line, such as "Read the price list" under a button: it gets a 44 px touch target without moving the layout, so keep 8 px or more between it and the next control.

## Forms

```html
<div class="aap-field">
  <label class="aap-field__label" for="email">Work email</label>
  <input class="aap-input" id="email" type="email" aria-invalid="true" aria-describedby="email-error">
  <p class="aap-field__error" id="email-error">Add the domain, for example ops@company.com, so we can reply.</p>
</div>
```

- Labels always sit above the control. Help text (`.aap-field__help`) and errors (`.aap-field__error`) sit below it.
- `.aap-input`, `.aap-select` and `.aap-textarea` are 44 px tall with a 3:1 border (`--aap-color-border-strong`). Hover darkens the border; focus shows a 3 px Alliance Blue halo; `aria-invalid="true"` turns the border to the error colour.
- Errors name the problem and the fix, and are wired to the control with `aria-describedby`.
- `.aap-check` wraps a checkbox or radio with its label; checked controls fill Partner Navy (Ribbon Cyan with a navy tick inside a navy chapter).

## Tags and chips

- `.aap-tag`: a quiet label for services or topics.
- `.aap-chip`: a pill with a status dot. Use `--live` (green, for example "Team online") or `--away`.

## Cards and media

`.aap-card` is a raised white plane with a lit top edge, as on the mark's bevels. Use a card only when the thing is one object (an offer, a download, a person). A row of same-size icon cards as page structure is off-system. An `a.aap-card` lifts 2 px on hover with the spring easing.

`.aap-media` frames an image or video: 18 px radius, `object-fit: cover`.

## Sourced claims

Every number on the site carries its source and date. Key the claim, then list the sources at the end of the section:

```html
<p>A full-time developer in the United States costs the employer about
  <span class="aap-claim">US$196,500 a year<a class="aap-claim__key" href="#src-1">1</a></span>.</p>
<ol class="aap-sources">
  <li id="src-1">U.S. Bureau of Labor Statistics, software developers, median pay May 2025. Retrieved 2026-11-02.</li>
</ol>
```

The key is a small boxed numeral in Mona Sans Mono; the targeted source highlights when the key is followed.

## Time zones

`.aap-timezones` is a row of identical cells, one per city, each with a name, the local time in Mona Sans Mono and a short note. Mark the team's own cell with `aria-current="true"` (its time turns semibold and its name gains the live dot). Keep the times live with a few lines of JavaScript (`Intl.DateTimeFormat` with each city's IANA time zone); never hard-code them on the live site.

## The four steps

`.aap-steps` is an ordered list of the four ways Alliance works: Understand, Plan, Build, Run and grow. The ribbon (Ribbon 57 into Ribbon Cyan, the ribbon's light) threads the steps, and each step is numbered because the order is the point. On phones the ribbon turns vertical. Use `.aap-steps__title` and `.aap-steps__text` inside each `li`.

## Tabs, accordion, table

- `.aap-tabs__list` with `.aap-tabs__tab[aria-selected]`: the selected tab is marked by a Partner Navy underline that grows in with the spring easing. Wire the roles and arrow-key behaviour with the WAI-ARIA tabs pattern.
- `details.aap-accordion` with a `summary` and `.aap-accordion__body`: native disclosure, a plus that turns to a cross when open. Use it for the questions buyers ask.
- `.aap-table`: hairline rows, tabular figures, `.is-num` for right-aligned Mona Sans Mono figures, and `tr.is-ours` to tint Alliance's own row in a comparison.

## Feedback

- `.aap-alert` with `--success`, `--warning`, `--error` (info is the default): a tinted surface with a tinted border on all sides and an icon. There is no coloured left stripe. Use `role="status"` for confirmations and `role="alert"` for errors.
- `.aap-skeleton`: a shimmering placeholder sized like the content it replaces. Use it instead of spinners; it stops shimmering under reduced motion.
- `.aap-empty`: an empty state that says what will appear and when.

## Header and footer

- `.aap-header` is sticky and translucent (86 % Daylight with a blur), fading into the page instead of drawing a hard line. It turns solid under `prefers-reduced-transparency`. Inside it: `.aap-header__bar`, `.aap-header__logo` (36 px tall) and `.aap-nav` with `.aap-nav__link`. The current page (`aria-current="page"`) carries a ribbon underline.
- `.aap-footer` sits in a navy chapter (`.aap-surface-inverse`): `.aap-footer__grid` (2:1:1:1, two columns on tablets, one on phones), `.aap-footer__heading`, `.aap-footer__list`, `.aap-footer__base`.

## Motion

| Token | Value | Use |
|---|---|---|
| `--aap-duration-instant` | 80 ms | Press feedback |
| `--aap-duration-fast` | 150 ms | Hover and colour |
| `--aap-duration-base` | 240 ms | Most transitions |
| `--aap-duration-slow` | 400 ms | Panels and reveals |
| `--aap-duration-ribbon` | 1400 ms | The ribbon drawing itself |
| `--aap-easing-spring` | `linear()` approximation of a critically damped spring | Anything that moves in space |
| `--aap-easing-standard` | `cubic-bezier(0.2, 0, 0, 1)` | Colour and opacity |

Feedback starts on press, not on release. Movement uses the spring with no overshoot. In React, use Motion with `{ type: "spring", bounce: 0, duration: 0.35 }`; add bounce only after a flick or drag. Under `prefers-reduced-motion` the slow and ribbon durations drop to 1 ms, the shimmer and busy animations stop, and hover lifts are removed.

## Accessibility checklist

- All text pairs pass WCAG AA; the ratios are recorded in each token's description in [tokens/tokens.json](tokens/tokens.json).
- Ribbon Cyan is never text on light grounds (1.63:1 on Daylight).
- Focus is always visible: 2 px ring, 2 px offset, Alliance Blue on light and Ribbon Cyan on navy.
- Controls are at least 44 px tall by default.
- `prefers-reduced-motion`, `prefers-reduced-transparency` and `prefers-contrast: more` are all handled.
