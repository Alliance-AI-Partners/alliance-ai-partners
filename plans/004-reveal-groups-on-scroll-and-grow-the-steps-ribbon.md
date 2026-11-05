# 004 — Reveal card groups as they scroll into view, and grow the steps ribbon

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: LOW
- **Category**: Missed opportunities (group entrances; explanation)
- **Estimated scope**: 1 new file, 8 edited, about 120 lines

## Problem

The Home page is a marketing page people see occasionally. Its card grids and lists are simply there when they scroll to them. The four steps are a sequence ("each step is numbered because the order is the point", `design-system/COMPONENTS.md`), yet they appear all at once, and their ribbon never draws, although DESIGN.md says the ribbon rule "grows from the left".

## Target

- **Trigger**: Motion's `inView` (from `motion/react`). Once per group, when its top passes 10% above the viewport's bottom edge (`margin: "0px 0px -10% 0px"`).
- **Motion**: CSS transitions on the tokens, not JavaScript tweens. Each item rises 12px and fades in over `--aap-duration-slow` (400ms): `translate` on `--aap-easing-out`, `opacity` on `--aap-easing-standard`. Items are 60ms apart by default (`--reveal-stagger`).
- **Steps**: the ribbon rule grows from the left over `--aap-duration-ribbon` (1400ms) on `--aap-easing-out`. It grows from the top on phones, where it runs down the side. The steps follow 80ms apart, starting 120ms in.
- **Progressive**: the server HTML is fully visible. Only groups that are below the fold when the page starts get hidden, so there is no flash, no hidden content without JavaScript, and no effect on what the browser first paints. Print always shows everything.
- **Reduced motion**: nothing is hidden and nothing moves.

```css
[data-reveal-group][data-revealed="false"] [data-reveal-item],
[data-reveal-group][data-revealed="false"][data-reveal-item] { opacity: 0; translate: 0 12px; }
[data-reveal-group][data-revealed="true"] [data-reveal-item],
[data-reveal-group][data-revealed="true"][data-reveal-item] {
  transition: opacity var(--aap-duration-slow) var(--aap-easing-standard), translate var(--aap-duration-slow) var(--aap-easing-out);
  transition-delay: calc(var(--reveal-delay, 0ms) + var(--reveal-index, 0) * var(--reveal-stagger, 60ms));
}
.aap-steps { --reveal-stagger: 80ms; --reveal-delay: 120ms; }
.aap-steps[data-revealed="false"]::before { scale: 0 1; }
.aap-steps[data-revealed="true"]::before { transition: scale var(--aap-duration-ribbon) var(--aap-easing-out); }
.aap-steps::before { transform-origin: left center; }
@media (max-width: 767px) {
  .aap-steps::before { transform-origin: center top; }
  .aap-steps[data-revealed="false"]::before { scale: 1 0; }
}
@media print { [data-reveal-item] { opacity: 1 !important; translate: none !important; } }
```

## Repo conventions to follow

- Client components are small and sit in `components/`. Exemplar: `components/home/live-time-zones.tsx`: it reads the browser only inside `useEffect`, never during prerender (Cache Components is on).
- Motion imports: `motion/react` in client components (never `framer-motion`).
- Mount once in `app/layout.tsx` after `<SiteFooter />`; re-run on route change with `usePathname()`, because the layout survives client navigation.

## Steps

1. Create `components/scroll-effects.tsx` (`"use client"`), exporting `ScrollEffects`, which renders `null`. In a `useEffect` keyed on `usePathname()`:
   - Return early if `matchMedia("(prefers-reduced-motion: reduce)")` matches.
   - For each `[data-reveal-group]`: skip it if its `getBoundingClientRect()` overlaps the viewport. Otherwise set `--reveal-index` on each `[data-reveal-item]` inside it (or on the group itself if it carries `data-reveal-item`) and set `data-revealed="false"` on the group. Then call `inView(group, () => { group.dataset.revealed = "true"; }, { margin: "0px 0px -10% 0px" })`. Collect the stop functions and call them in the cleanup.
2. `app/layout.tsx`: render `<ScrollEffects />` after `<SiteFooter />`.
3. `app/globals.css`: add the CSS above, with a comment, in the home `@layer components` block.
4. Mark the groups (attributes only, no structural change):
   - `components/home/pitch.tsx`: `data-reveal-group data-reveal-item` on the image's `.aap-media`. On the outcomes `<ul>` `data-reveal-group`, and on each `<li>` `data-reveal-item`.
   - `components/home/goals.tsx`: `data-reveal-group` on the bento grid `<div>`, `data-reveal-item` on each `<article>`.
   - `components/home/how-we-work.tsx`: `data-reveal-group` on `<ol className="aap-steps">`, `data-reveal-item` on each `<li>`.
   - `components/home/honest-pricing.tsx`: groups on the promise `<ul>` (stagger 40ms: `style={{ "--reveal-stagger": "40ms" }}`) and the price-row `<ul>`, items on their `<li>`s. On the `<figure>`, `data-reveal-group data-reveal-item`.
   - `components/home/cost-of-hiring.tsx`: group on the stats `<ul>`, items on its `<li>`s. On the price card, `data-reveal-group data-reveal-item`.
   - `components/home/live-time-zones.tsx`: group on `<ul className="aap-timezones">`, items on its `<li>`s.
   - `components/home/questions.tsx`: group on the accordion wrapper `<div className="border-t border-line">` (stagger 40ms), items on each `<details>`.

## Boundaries

- Do NOT hide anything in the server HTML (no `opacity-0` classes in JSX).
- Do NOT reveal headings, leads, the hero or the footer: groups only.
- Do NOT animate layout properties: `opacity` and `translate`/`scale` only.

## Verification

- **Mechanical**: `npm run lint`, `npm run typecheck`, `npm run build`. The built `index.html` contains no `data-revealed` attribute (JavaScript adds it).
- **Feel check** (1440 and 390): scroll down slowly. Each group rises and fades in once, items in reading order, and the steps ribbon draws left to right (top to bottom on phones) before the steps settle. Scrolling back up does not replay anything. Reload halfway down the page: the groups already in view are visible at once, not faded. With JavaScript disabled, everything is visible. With reduced motion, nothing moves.
- **Done when**: no group ever stays hidden after it has been in view, and print preview shows every item.
