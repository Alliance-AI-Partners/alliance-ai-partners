# 006 — Add a gentle parallax to the two image bands

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: LOW
- **Category**: Missed opportunities (marketing chapter openers)
- **Estimated scope**: 3 files, about 40 lines

## As built

Built with the browser's own scroll timeline in CSS instead of Motion's `scroll()`. Measured in the production build, Motion's `animate` and `scroll` added 25 KB (gzipped) of JavaScript to every page (207.0 KB against 181.9 KB), for an effect the browser runs natively, off the main thread, in Chrome, Edge and Safari 26+. Firefox shows the photograph still. Motion stays for the reveals (`inView`, plan 004).

The rule (`app/globals.css`): `:has(> [data-parallax]) { view-timeline: --home-band block; }` and `[data-parallax] { animation: home-parallax linear both; animation-timeline: --home-band; }`, inside `@supports (animation-timeline: view())` and `prefers-reduced-motion: no-preference`. The keyframes run from `translateY(-24px)` to `translateY(24px)`. The timeline is named on the band because the band's `overflow: hidden` makes it a scroll container, so a plain `view()` on the layer never advanced (caught in testing: the transform stayed at 0).

Checked: the layer drifts from -24px to 24px across each band and covers the band at every scroll position (1440 px, both bands, five positions each).

## Problem

The overnight band and the closing band are the page's two full-bleed photographs, and they scroll like flat paper. A slight lag between the photograph and the text gives these two chapter openers depth. This is the one scroll-linked effect on the page.

```tsx
// components/home/overnight-band.tsx:15 — current
<Image src={daybreakSwallows} alt="" fill sizes="100vw" className="-z-20 object-cover object-[20%_50%] lg:object-center" />

// components/home/closing-cta.tsx:14 — current
<Image src={dawnWave} alt="" fill sizes="100vw" className="-z-20 object-cover" />
```

## Target

- Each image sits in a wrapper 24px taller than the band at the top and bottom (`absolute inset-x-0 -top-6 -bottom-6 -z-20`). As the band crosses the viewport, the wrapper moves from `translateY(-24px)` to `translateY(24px)`, so the photograph scrolls slightly slower than the text without ever showing an edge.
- Driven by Motion: `scroll(animate(wrapper, { transform: ["translateY(-24px)", "translateY(24px)"] }, { ease: "linear" }), { target: band, offset: ["start end", "end start"] })`. Motion uses the browser's native scroll timeline where it exists, off the main thread, and falls back to JavaScript elsewhere. Linear is the right curve for motion tied to scroll.
- Only `transform` changes, never layout.
- Reduced motion: no parallax.

## Repo conventions to follow

- The scroll wiring joins the reveal controller from plan 004 (`components/scroll-effects.tsx`) and runs in the same `useEffect`, keyed on the pathname.
- Elements opt in with an attribute: `data-parallax` on the wrapper. The band `<section>` is its `parentElement`.

## Steps

1. `components/home/overnight-band.tsx` and `components/home/closing-cta.tsx`: move the `<Image>` into `<div data-parallax aria-hidden="true" className="absolute inset-x-0 -top-6 -bottom-6 -z-20">`, and drop `-z-20` from the `<Image>`.
2. `components/scroll-effects.tsx`: for each `[data-parallax]`, add the `scroll(animate(…), { target: el.parentElement, offset: [...] })` call above, unless reduced motion is on. Keep each stop function for cleanup.

## Boundaries

- Do NOT move the scrim or the text: only the image wrapper moves.
- Do NOT exceed ±24px: the wrapper only extends 24px beyond the band.

## Verification

- **Mechanical**: `npm run lint`, `npm run typecheck`, `npm run build`.
- **Feel check**: scroll through each band at 1440 and 390. The photograph drifts slower than the headline, and no gap appears at the band's top or bottom edge at any scroll position. Scroll fast: no stutter (Performance panel: no long tasks from scrolling). With reduced motion, the photograph is fixed to the band.
- **Done when**: at the band's entry and exit the wrapper's transform is ±24px, and the band's edges never show the navy ground behind the image.
