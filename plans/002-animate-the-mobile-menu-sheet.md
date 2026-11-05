# 002 — Animate the mobile menu sheet in and out

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: MEDIUM
- **Category**: Missed opportunities (preventing a jarring change)
- **Estimated scope**: 2 files, about 40 lines

## Problem

The full-screen menu (a native modal `<dialog>`) appears and disappears in one frame, so the whole page is swapped for the menu with nothing to connect the two:

```tsx
// components/mobile-menu.tsx:55 — current
<dialog
  ref={dialogRef}
  aria-label="Menu"
  className="m-0 h-dvh max-h-none w-full max-w-none overflow-y-auto overscroll-contain border-0 bg-page p-0 text-ink backdrop:bg-transparent"
>
```

It is opened from the menu button a few times per visit on phones and tablets: occasional, so a standard drawer-sized animation is right.

## Target

- **Open (240ms)**: the sheet fades in and settles 8px down into place; the five links follow, each fading and settling 8px up, 30ms apart, starting 60ms in.
- **Close (150ms)**: the sheet fades out and lifts 8px. The system's response is faster than the entrance.
- **Reduced motion**: fade only, no movement and no stagger.
- CSS only, with `@starting-style` and `transition-behavior: allow-discrete` on `display` and `overlay`, so the dialog stays in the top layer while it fades out. Browsers without them open and close at once, as today.

```css
.site-menu {
  transition:
    opacity var(--aap-duration-fast) var(--aap-easing-standard),
    translate var(--aap-duration-fast) var(--aap-easing-out),
    overlay var(--aap-duration-fast) allow-discrete,
    display var(--aap-duration-fast) allow-discrete;
}
.site-menu:not([open]) { opacity: 0; translate: 0 -8px; }
.site-menu[open] { transition-duration: var(--aap-duration-base); }
@starting-style { .site-menu[open] { opacity: 0; translate: 0 -8px; } }

.site-menu__item {
  transition: opacity var(--aap-duration-base) var(--aap-easing-standard), translate var(--aap-duration-base) var(--aap-easing-out);
  transition-delay: calc(60ms + var(--item-index, 0) * 30ms);
}
@starting-style { .site-menu[open] .site-menu__item { opacity: 0; translate: 0 8px; } }

@media (prefers-reduced-motion: reduce) {
  .site-menu:not([open]) { translate: none; }
  @starting-style { .site-menu[open] { translate: none; } }
  .site-menu__item { transition: none; }
}
```

## Repo conventions to follow

- Tokens: `--aap-duration-fast: 150ms`, `--aap-duration-base: 240ms`, `--aap-easing-standard: cubic-bezier(0.2, 0, 0, 1)` (colour and opacity), `--aap-easing-out: cubic-bezier(0.16, 1, 0.3, 1)` (entrances).
- Site rules go in `app/globals.css` inside `@layer components`, each with a comment. Exemplar: the `.home-scrim-overnight` block.
- Use the individual `translate` property (compositor-only), not `transform`, so it never fights the design system's transforms.

## Steps

1. `components/mobile-menu.tsx:55`: add `site-menu` to the dialog's `className`.
2. `components/mobile-menu.tsx:78`: give each `<li>` `className="site-menu__item"` and `style={{ "--item-index": index } as CSSProperties}` (add `index` to the `map` callback and import `type CSSProperties` from `react`).
3. `app/globals.css`: add the CSS above, with a comment, in a "site chrome" `@layer components` block.

## Boundaries

- Do NOT change the dialog's focus handling, Escape behaviour or the `close` listener in the effect.
- Do NOT add Motion here: the dialog never leaves the DOM, so CSS covers both directions.

## Verification

- **Mechanical**: `npm run lint`, `npm run typecheck`, `npm run build`.
- **Feel check** (390 x 844): tap the menu button. The sheet settles 8px down as it fades in, then the links follow in order. Tap close: it lifts and fades faster than it came in. Open and close quickly: nothing jumps or restarts from zero. At 10% speed in the Animations panel, the links start after the sheet. With reduced motion, the sheet only fades.
- **Done when**: opening and closing both animate in Chromium, focus still returns to the menu button on close, and Escape still closes.
