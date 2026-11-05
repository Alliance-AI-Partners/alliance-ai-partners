# Animation plans

Plans written with the `improve-animations` skill after a `find-animation-opportunities` audit of the site (commit `7c89681`). Each plan is self-contained: the problem with the current code, the exact target values from the design system's motion tokens (`design-system/tokens/tokens.css`: `--aap-duration-*`, `--aap-easing-*`), steps, boundaries and a feel check.

| # | Plan | Severity | Status |
|---|---|---|---|
| 001 | [Gate the arrow nudges to real hover and ease link colour changes](001-gate-hover-nudges-and-ease-link-colour.md) | MEDIUM | DONE |
| 002 | [Animate the mobile menu sheet in and out](002-animate-the-mobile-menu-sheet.md) | MEDIUM | DONE |
| 003 | [Animate the accordion's answer and icon](003-animate-the-questions-accordion.md) | MEDIUM | DONE |
| 004 | [Reveal card groups as they scroll into view, and grow the steps ribbon](004-reveal-groups-on-scroll-and-grow-the-steps-ribbon.md) | LOW | DONE |
| 005 | [Ease the hero's supporting lines in on first load](005-ease-the-hero-in-on-first-load.md) | LOW | DONE |
| 006 | [Add a gentle parallax to the two image bands](006-add-parallax-to-the-image-bands.md) | LOW | DONE |
| 007 | [Show a ribbon bar while a page loads](007-show-a-ribbon-bar-while-a-page-loads.md) | LOW | DONE |

## Order and dependencies

All seven are done (see each plan's "As built" note where the build differs from the plan). They were run in number order. 001 to 003 are independent fixes to existing UI. 006 was planned to extend the client component that 004 creates (`components/scroll-effects.tsx`); as built it is pure CSS. 005 and 007 are independent.

## Rejected in the audit

- A full-screen splash on first load: the page is static HTML that paints at once, so a splash could only add delay (plan 007 is the honest loading state).
- A route-level `app/loading.tsx` (tried for plan 007): with Cache Components it put a loading state into the static HTML, and pages without JavaScript showed only "Loading".
- Counting up the cost figures: they are sourced numbers people check, and counting makes them look like they are changing.
- Flipping the live clock digits each minute: information people read, so the motion pulls the eye.
- Lifting the goal cards on hover: only their "Explore" link is clickable, so a lift would advertise a target that isn't there.
- A header shadow on scroll: DESIGN.md has the header fade into the page on purpose.
