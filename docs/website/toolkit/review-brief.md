# Page review brief: Alliance AI Partners website mock in Figma

You are an independent design reviewer. Other agents built these pages; assume they made mistakes and find them. Then fix what you find, directly in Figma, and report.

Paths below are relative to the repository root.

## Setup

1. Load the skills `figma:figma-use` and `figma:figma-generate-design` with the Skill tool (pass `skillNames: "figma-use,figma-generate-design"` on use_figma calls). Load the tools with `ToolSearch` `select:mcp__Figma__use_figma,mcp__Figma__get_screenshot`.
2. fileKey `1VGkymJ9AH6vGYgFDAU68A`; call `create_session` once and pass its sessionId on every call.
3. Read `docs/website/toolkit/build-brief.md` (the rules the builders followed: they are your rubric, with the design-review checklist below), `docs/website/toolkit/pagekit.js` (the toolkit for fixes), the repo `DESIGN.md`, and the Brand DNA sections you need to check copy (`AllianceAIPartners/Brand DNA & Foundation.md`). Each page's spec is in `docs/website/pages/<slug>.json`.

## Rate limit (important)

Several agents share one per-minute Figma limit. Use few, rich calls: one call per frame for the lint, one call per frame for screenshots (return up to 5 section screenshots from one use_figma call; more are dropped silently with `await node.screenshot({ scale: 0.5 })`; use scale 1 for a section you need to read closely). Batch fixes for a frame into one call. If you see "reached the Figma MCP tool call limit", wait about 60 seconds doing non-Figma work, then retry. Never call whoami or fetch docs about it.

## For every frame you review (Desktop, Mobile and each state)

1. Find the frames: one read-only call on the Figma page returning `figma.currentPage.children.map(n => ({id: n.id, name: n.name, w: n.width, h: n.height}))`, then the section list of each frame.
2. Lint (one call): `const L = (new Function('figma', (await figma.getNodeByIdAsync('37:851')).characters + '\nreturn L;'))(figma); return await L.run('<frameId>');` It reports banned words, unsourced figures, multi-word or repeated accents, cyan text on light grounds, straight quotes, tiny text, text outside the frame, collapsed frames, two Primary buttons within one screenful, labels above headings, image-slot naming, and the placeholders used. Fix every high and medium finding.
3. Read the copy (one call): return every text node in order (`R.findAll(n => n.type === 'TEXT').map(t => t.characters)`). Check the voice (result first, plain words, short sentences, "we will"), the full name "Alliance AI Partners", no invented facts (prices, partners, logos, testimonials, results, people, certifications, years, headcounts), placeholders intact, every number sourced and dated with the Brand DNA sources, samples marked as samples, curly quotes and apostrophes, no "Get started" or "Learn more" buttons.
4. Look (one or two calls of section screenshots) and judge with the rubric:
   - Trunk test: site, page name, main sections, options, where am I, all clear?
   - Landing-page rules: the first viewport reads as one composition; brand, headline, body, CTA in that order; one job per section; hero budget (one headline, one supporting sentence, one action group, one visual); no cards in the hero.
   - DESIGN.md: one Primary per screenful (header CTA is the Secondary outline); Daylight or whole Navy chapters only; no label above a heading; at most one single-word accent; Display XL only once; asymmetric section heads; 1320 container aligned; card radius 18 and 32 px padding; light from the top left; no glow, no gradient text; ribbon at most once or twice per page.
   - Checklist: hierarchy (clear focal point, squint test), typography (sizes from the styles, measure 45 to 75 characters for body, leads about 60ch), spacing (4 px scale, 48 px head to content, more space above a heading than below), colour and contrast (WCAG AA; tertiary text never carries important copy on navy), responsive (mobile is designed, not stacked; no overflow beyond 390; full-width primary on mobile; 44 px touch targets), content (no happy talk, no instructions paragraphs, specific button labels).
   - Hard rejections: generic SaaS card grid as the first impression; strong headline with no clear action; busy imagery behind text (every text-over-image needs a navy scrim); sections repeating the same mood statement; three identical cards in a row; app UI made of stacked cards.
   - AI-slop tells: icon-in-circle feature rows, centred everything, uniform bubbly radius, decorative blobs, generic hero copy, cookie-cutter section rhythm (same layout in adjacent sections), template counters, card grids of equal boxes for unequal content.
   - Tints: Ribbon Cyan on Daylight is only ever a 10% tint (for example the own-row tint in tables). Check every cyan fill on a light ground.
   - Scrims: every scrim over an image holds at least 82% Partner Navy under every line of text (the lint flags a weaker one as weak-scrim). The lead set this across the site; never weaken a scrim.
   - Standalone links on mobile are 26 px tall in Figma. The code gives them a 44 px touch target (`.aap-link--standalone` in `design-system/css/components.css`), so don't count them as a finding.
   - Layout bugs: clipped or overlapping text, text touching edges, collapsed or zero-height frames, misaligned columns, an image slot label overflowing, sections that end abruptly, inconsistent section padding.
   - Image variety: the page mixes presentations (split, full-bleed band with scrim, inset media, mosaic, card image, product visual), each image slot is named `IMG-<page>-<n> · <short>` with a clear `Existing:` or `New:` label, and the spec's prompt for every new image depicts the section's idea and carries the fixed palette and exclusion rules.
5. Fix: targeted scripts that change only the broken parts (load the toolkit for new nodes: `const K = (new Function('figma', (await figma.getNodeByIdAsync('24:3')).characters + '\nreturn K;'))(figma); await K.init('Desktop'|'Mobile');`). Load fonts before editing text (`await figma.loadFontAsync({ family: 'Mona Sans' })` loads every style). If a section is weak (generic layout, missing image variety, a mood section with no job), rebuild that section properly rather than nudging it. Keep frame names, IDs and positions. Update the spec JSON if you change images or sections.
6. Re-lint and re-screenshot only what changed. Stop when the frame passes.

## Never

Touch the Cover, Foundations, Components or Image slots pages, the toolkit or lint nodes, components, or pages outside your list. Create components. Invent facts. Guess node IDs.

## Report

Return the structured result: for each page, the frames reviewed, a Design score and an AI-slop score (A to F, each category starts at A; a high finding drops a letter, a medium half a letter), the fixes you made, and anything left unresolved with the reason.
