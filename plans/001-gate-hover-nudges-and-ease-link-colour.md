# 001 — Gate the arrow nudges to real hover and ease link colour changes

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: MEDIUM
- **Category**: Accessibility, Cohesion & tokens
- **Estimated scope**: 2 files, about 25 lines

## Problem

The forward-arrow nudge on buttons and links is a bare `:hover` rule. Touch screens fire `:hover` on tap, so the arrow stays shifted 3px after a tap, and the nudge still moves under `prefers-reduced-motion: reduce`:

```css
/* design-system/css/components.css:266 — current */
.aap-button:hover svg[data-direction="forward"] {
  transform: translateX(3px);
}

/* design-system/css/components.css:334 — current */
.aap-link:hover svg {
  transform: translateX(3px);
}
```

Navigation and footer links change colour instantly, while buttons and inline links fade their colour over 150ms:

```css
/* design-system/css/components.css:962 — current (no transition) */
.aap-nav__link { position: relative; padding-block: var(--aap-space-2); color: var(--aap-color-text-secondary); … }

/* design-system/css/components.css:1010 — current (no transition) */
.aap-footer__list a { color: var(--aap-color-text-secondary); text-decoration: none; }
```

The site's own price-row arrow (`components/home/honest-pricing.tsx`, `group-hover:translate-x-[3px]`) is already hover-gated by Tailwind 4, but keeps moving under reduced motion.

## Target

```css
/* the nudges, only where a fine pointer can really hover */
@media (hover: hover) and (pointer: fine) {
  .aap-button:hover svg[data-direction="forward"] { transform: translateX(3px); }
}
@media (hover: hover) and (pointer: fine) {
  .aap-link:hover svg { transform: translateX(3px); }
}

/* colour, like the other links: 150ms, standard easing */
.aap-nav__link { transition: color var(--aap-duration-fast) var(--aap-easing-standard); }
.aap-footer__list a { transition: color var(--aap-duration-fast) var(--aap-easing-standard); }

/* reduced motion keeps colour feedback and drops the movement */
@media (prefers-reduced-motion: reduce) {
  .aap-button:hover svg[data-direction="forward"],
  .aap-link:hover svg { transform: none; }
}
```

Price-row arrow: add `motion-reduce:group-hover:translate-x-0` to its class list.

## Repo conventions to follow

- Motion tokens: `--aap-duration-fast: 150ms`, `--aap-easing-standard: cubic-bezier(0.2, 0, 0, 1)` in `design-system/tokens/tokens.css`. Never type raw values.
- Exemplar: `:where(a)` at `design-system/css/components.css:46` already transitions `text-decoration-color var(--aap-duration-fast) var(--aap-easing-standard)`.
- The reduced-motion block lives at the end of `components.css` (line 1060); add to it rather than creating a second one.

## Steps

1. `design-system/css/components.css:266`: wrap the `.aap-button:hover svg[data-direction="forward"]` rule in `@media (hover: hover) and (pointer: fine) { … }`.
2. `design-system/css/components.css:334`: wrap the `.aap-link:hover svg` rule the same way.
3. `.aap-nav__link` (line 962) and `.aap-footer__list a` (line 1010): add `transition: color var(--aap-duration-fast) var(--aap-easing-standard);`.
4. In the `@media (prefers-reduced-motion: reduce)` block at line 1060, add the `transform: none` rule above.
5. `components/home/honest-pricing.tsx`: add `motion-reduce:group-hover:translate-x-0` to the price-row arrow's classes.
6. `design-system/COMPONENTS.md`, "Motion": say that the arrow nudges need a hovering pointer and stop under reduced motion.

## Boundaries

- Do NOT change durations, easings or the press feedback (`.aap-button:active`, 80ms, `translateY(1px) scale(0.985)`): DESIGN.md documents it.
- Do NOT touch any other component.

## Verification

- **Mechanical**: `npm run lint`, `npm run typecheck`, `npm run build` all pass.
- **Feel check**: with a mouse, hovering "Read the price list" slides its arrow 3px on the spring and back. In DevTools device mode (touch), tapping does not leave the arrow shifted. Hovering a nav link fades its colour (slow the Animations panel to 10% to see it). With Rendering → `prefers-reduced-motion: reduce`, the arrows stay put and the colour still changes.
- **Done when**: no `transform` on `:hover` in `components.css` sits outside a `(hover: hover) and (pointer: fine)` query.
