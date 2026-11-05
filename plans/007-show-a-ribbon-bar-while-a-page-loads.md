# 007 — Show a ribbon bar while a page loads

- **Status**: DONE
- **Commit**: 7c89681
- **Severity**: LOW
- **Category**: Missed opportunities (feedback)
- **Estimated scope**: 1 new file, 1 edited, about 35 lines

## As built

`app/loading.tsx` was built as planned, then removed. With Cache Components on, a route-level loading file wraps the page in a Suspense boundary, so even the fully static Home HTML started with the loading state and swapped the content in with a script. With JavaScript off, the page showed only "Loading" (checked in a browser).

As built, it follows the Next.js 16 guidance for this case (`useLinkStatus`, `node_modules/next/dist/docs/01-app/03-api-reference/04-functions/use-link-status.md`):

- `components/site-link.tsx` wraps `next/link` and adds an invisible `LinkPendingSignal`. Every internal link uses it.
- `components/navigation-progress.tsx` counts pending links and renders the bar (`aria-hidden`) at the top of the window, mounted once in `app/layout.tsx`.
- `.site-loading-bar` in `app/globals.css`: hidden at rest; with `data-active="true"` it fades in after 150ms and the `aap-busy` sweep runs. Reduced motion keeps the bar without the sweep.

Checked on a throttled network: following a footer link, the bar is still invisible at 60ms, fully shown with the sweep at 560ms, and gone once the page arrives.

## Problem

When a link leads to a page whose content is not ready yet, the old page stays put with no sign that anything is happening. Next.js shows `app/loading.tsx` during that wait, and the site has none.

A full-screen splash on first load was rejected in the audit. The page is static HTML that paints at once, so a splash could only add delay.

## Target

- `app/loading.tsx`: a 3px Ribbon 57 to Ribbon Cyan bar across the top of the viewport, above the header. It has `role="status"` and visually hidden "Loading" text, and keeps the content area at least 60vh tall so the footer doesn't jump up.
- **Motion**: the design system's busy language. A cyan light sweeps along the bar using the existing `aap-busy` keyframes, 1.1s on `--aap-easing-in-out`, repeating. The bar fades in only after 150ms (`--aap-duration-fast`), so fast navigations never flash it.
- **Reduced motion**: the bar shows without the sweep.

```css
.site-loading-bar {
  position: fixed; inset: 0 0 auto; z-index: var(--aap-zIndex-overlay);
  height: var(--aap-border-ribbon);
  background:
    linear-gradient(90deg, transparent, var(--aap-color-brand-ribbon-cyan), transparent) 0 0 / 40% 100% no-repeat,
    var(--aap-gradient-ribbon);
  opacity: 0;
  animation:
    site-appear var(--aap-duration-fast) var(--aap-easing-standard) var(--aap-duration-fast) forwards,
    aap-busy 1.1s var(--aap-easing-in-out) infinite;
}
@keyframes site-appear { to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) {
  .site-loading-bar { animation: site-appear var(--aap-duration-fast) var(--aap-easing-standard) var(--aap-duration-fast) forwards; }
}
```

## Repo conventions to follow

- The `aap-busy` keyframes are defined in `design-system/css/components.css` (they move `background-position` from -40% to 140%); reuse them rather than defining new ones.
- Tokens: `--aap-gradient-ribbon`, `--aap-border-ribbon` (3px), `--aap-zIndex-overlay` (300, above the header's 200).

## Steps

1. Create `app/loading.tsx` exporting a default `Loading` component that returns `<div className="min-h-[60vh]"><div role="status" className="site-loading-bar"><span className="sr-only">Loading</span></div></div>`.
2. `app/globals.css`: add the CSS above in a "site chrome" `@layer components` block.

## Boundaries

- Do NOT add a full-screen overlay or delay the first paint of any page.
- Do NOT read data or time in `loading.tsx`.

## Verification

- **Mechanical**: `npm run build`. Home is still prerendered as static, and the built `index.html` still contains the Home content, not the loading bar.
- **Feel check**: with DevTools throttling ("Slow 4G"), follow a footer link. After about 150ms a thin ribbon bar with a sweeping light appears at the very top until the new page shows. On a fast connection nothing flashes. With reduced motion, the bar shows without the sweep.
- **Done when**: the bar never shows on navigations shorter than 150ms and screen readers announce "Loading" when it does.
