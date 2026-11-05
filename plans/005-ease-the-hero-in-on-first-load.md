# 005 — Ease the hero's supporting lines in on first load

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: LOW
- **Category**: Missed opportunities (rare delight: the first impression)
- **Estimated scope**: 2 files, about 20 lines

## Problem

On first load only the ribbon moves (it draws itself over 1.4s, `app/globals.css`, `.home-hero-ribbon`). The lead, the two actions and the base line are simply there. The hero is the first thing a visitor sees, once per visit, which is where the delight budget belongs.

```tsx
// components/home/hero.tsx:19, 22, 35, 41 — current
<p className="max-w-[560px] text-body-lg text-ink-secondary">…</p>
<div className="flex flex-col items-center gap-4 lg:flex-row lg:gap-6">…</div>
<p className="hidden max-w-[480px] text-caption text-ink-tertiary lg:block">{baseLine}</p>
<p className="text-caption text-ink-tertiary lg:hidden">{baseLine}</p>
```

## Target

- The lead, the actions and the base line rise 8px and fade in, one after another. Each takes 400ms (`--aap-duration-slow`), `translate` on `--aap-easing-out` and `opacity` on `--aap-easing-standard`, starting 80ms in and 60ms apart (`--rise-index` 0, 1, 2).
- The headline and the 3D mark stay still. They are the largest things the page paints first, and fading them would delay that paint and the moment the page looks ready. The ribbon already brings motion to the mark.
- Pure CSS keyframes, so they run before hydration and without JavaScript. Reduced motion shows everything at once.

```css
@keyframes home-rise {
  from { opacity: 0; translate: 0 8px; }
}
@media (prefers-reduced-motion: no-preference) {
  .home-hero-rise {
    animation: home-rise var(--aap-duration-slow) var(--aap-easing-out) both;
    animation-delay: calc(80ms + var(--rise-index, 0) * 60ms);
  }
}
```

(A keyframe animation is right here: it plays once on load and is never interrupted. Use one curve per keyframe: `--aap-easing-out` for both properties.)

## Repo conventions to follow

- Home-only CSS lives in the "home page" `@layer components` block of `app/globals.css`, next to `.home-hero-ribbon`.
- Set the index with `style={{ "--rise-index": 1 } as CSSProperties}`. Exemplar of a CSS variable in a style prop: `components/ribbon.tsx` (`--aap-ribbon-width`).

## Steps

1. `app/globals.css`: add the keyframes and the rule above.
2. `components/home/hero.tsx`: add `home-hero-rise` to the lead (`--rise-index: 0`), the actions `<div>` (`1`), the desktop base line (`2`) and the mobile base line (`2`). Import `type CSSProperties` from `react`.

## Boundaries

- Do NOT animate the `<h1>`, the mark `<Image>` or the ribbon.
- Do NOT add JavaScript.

## Verification

- **Mechanical**: `npm run lint`, `npm run typecheck`, `npm run build`.
- **Feel check**: reload at 1440 and 390. The headline is there at once, the lead, actions and base line follow within half a second, and the ribbon draws over the mark. At 10% speed the three lines start 60ms apart. The buttons can be clicked during the animation. With reduced motion, everything is there at once.
- **Done when**: the hero's lines finish within 600ms of first paint.
