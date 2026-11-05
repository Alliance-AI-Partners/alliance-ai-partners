# 003 — Animate the accordion's answer and icon

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: MEDIUM
- **Category**: Missed opportunities (state indication)
- **Estimated scope**: 3 files, about 45 lines

## Problem

`.aap-accordion` is a native `<details>`. Its answer snaps open and shut, pushing everything below it by up to 100px in one frame. The plus and close icons swap with `display: none`:

```css
/* app/globals.css:111 — current */
.aap-accordion[open] > summary > .site-icon-closed,
.aap-accordion:not([open]) > summary > .site-icon-open {
  display: none;
}
```

```tsx
// components/home/questions.tsx:50 — current
<summary>
  <h3>{item.question}</h3>
  <Icon name="plus" className="site-icon-closed" />
  <Icon name="close" className="site-icon-open" />
</summary>
```

## Target

- **Answer (design system, every accordion)**: height and opacity over 240ms. Height uses `--aap-easing-out`, opacity `--aap-easing-standard`. This runs where the browser can animate `<details>` (`::details-content`, plus `interpolate-size` for the height); elsewhere the answer opens at once. Reduced motion keeps the fade and drops the height animation.

```css
@supports selector(::details-content) {
  .aap-accordion { interpolate-size: allow-keywords; }
  .aap-accordion::details-content {
    block-size: 0;
    overflow-y: clip;
    opacity: 0;
    transition:
      block-size var(--aap-duration-base) var(--aap-easing-out),
      opacity var(--aap-duration-base) var(--aap-easing-standard),
      content-visibility var(--aap-duration-base) allow-discrete;
  }
  .aap-accordion[open]::details-content { block-size: auto; opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .aap-accordion::details-content { transition-property: opacity, content-visibility; }
}
```

- **Icons (site)**: the two icons stack in one 20px cell and cross-fade while turning. Closed shows the plus upright; open turns the plus 90° away and the close icon in from -90°. Rotation takes 240ms on the spring, opacity 150ms on the standard curve. Reduced motion keeps the cross-fade and drops the turn.

```css
.site-accordion-icon { display: grid; flex: none; width: 20px; height: 20px; }
.site-accordion-icon > svg {
  grid-area: 1 / 1; width: 20px; height: 20px;
  transition: opacity var(--aap-duration-fast) var(--aap-easing-standard), rotate var(--aap-duration-base) var(--aap-easing-spring);
}
.aap-accordion:not([open]) .site-icon-open { opacity: 0; rotate: -90deg; }
.aap-accordion[open] .site-icon-closed { opacity: 0; rotate: 90deg; }
@media (prefers-reduced-motion: reduce) {
  .site-accordion-icon > svg { rotate: none; transition-property: opacity; }
}
```

## Repo conventions to follow

- The answer animation belongs to the component, so it goes in `design-system/css/components.css`, after `.aap-accordion__body`. Document it in `design-system/COMPONENTS.md`.
- The icon pair is a site-level substitution for the component's drawn plus (Figma uses the sprite icons), so its CSS stays in `app/globals.css`.
- Tokens: `--aap-duration-fast: 150ms`, `--aap-duration-base: 240ms`, `--aap-easing-spring` (critically damped `linear()`), `--aap-easing-out`, `--aap-easing-standard`.

## Steps

1. `design-system/css/components.css`: add the answer CSS above after the `.aap-accordion__body` rule. Add the reduced-motion line to the block at the end of the file.
2. `components/home/questions.tsx:50`: wrap the two `<Icon>`s in `<span className="site-accordion-icon">…</span>`.
3. `app/globals.css`: replace the `.aap-accordion > summary > svg` sizing and the `display: none` swap (lines 105–114) with the icon CSS above.

## Boundaries

- Keep `<details>`/`<summary>`: the questions must still work without JavaScript. Do NOT convert to React state or Motion `AnimatePresence`.
- Do NOT animate `padding` or `margin`: the answer's spacing stays on `.aap-accordion__body`.

## Verification

- **Mechanical**: `npm run lint`, `npm run typecheck`, `npm run build`.
- **Feel check**: open and close "Where is your team?". The answer grows and fades in, the rows below glide down, and the plus turns into the close icon. Click quickly twice: it reverses from where it is, with no restart. Keyboard Enter and Space still toggle it. With reduced motion, the answer fades with no height animation and the icons cross-fade without turning.
- **Done when**: the computed `block-size` of `::details-content` goes from 0 to the content height over about 240ms in Chromium.
