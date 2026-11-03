# Page build brief: Alliance AI Partners website mock in Figma

You are building real, finished-looking website pages in Figma for Alliance AI Partners, a desktop frame (1440 wide) and a mobile-first frame (390 wide) for each page. The Home page is done and is the quality bar: look at it before you start (Figma page `01 · Home`, frames `Home — Desktop` 26:186 and `Home — Mobile` 30:420).

Paths below are relative to the repository root.

## 1. Setup (do this first)

1. Load the Figma skills with the Skill tool: `figma:figma-use` (mandatory before any use_figma call) and `figma:figma-generate-design`. Pass `skillNames: "figma-use,figma-generate-design"` on every use_figma call.
2. Load the Figma tools: `ToolSearch` with `select:mcp__Figma__use_figma,mcp__Figma__get_screenshot,mcp__Figma__get_metadata`.
3. Every Figma call uses fileKey `1VGkymJ9AH6vGYgFDAU68A` and the sessionId your own `create_session` call returns.
4. Read: `docs/website/toolkit/pagekit.js` (the toolkit, fully commented), `docs/website/toolkit/example.js` (patterns), `docs/website/pages/home.json` (spec format and image prompt style), `docs/website/README.md` (the page list), and the repo's `DESIGN.md` (sections "Typography" to "Do's and Don'ts") and `AllianceAIPartners/Brand DNA & Foundation.md` (copy source: who we are, mission and the four steps, values, voice, elevator pitch, price rules, cost comparison with sources, buyer questions, taglines, full services list with the three goals and industry packages). Skim `PRODUCT.md`.
5. Do not load the frontend design skills; the brand docs and this brief already apply them.

## 2. How to build

Every use_figma script starts with the toolkit loader (it is stored inside the Figma file):

```js
const K = (new Function('figma', (await figma.getNodeByIdAsync('24:3')).characters + '\nreturn K;'))(figma);
await K.init('Desktop');            // or 'Mobile'
await K.page('07 · Embedded developers');   // the exact Figma page name you were given; switches page once
const R = K.root('Embedded developers — Desktop', 0);   // desktop at x 0; mobile at x 1600
K.header(R, 'Services');            // the nav item to mark current: Services | Pricing | How we work | About | none
// ... sections ...
K.footer(R);
return K.report();
```

- Desktop frame `<Page> — Desktop` at x 0. Mobile frame `<Page> — Mobile` at x 1600. Extra states go to the right: desktop state at x 2150 (`<Page> — Desktop · <State>`), mobile state at x 3750. Keep y 0.
- A long page can be built in two calls: build the first half, then in the next call get the root by the ID the first call returned (`K.R = await figma.getNodeByIdAsync('<id>')`) and append the rest. Never guess node IDs; use IDs returned by your own calls.
- One use_figma call at a time. Scripts are safe to retry only if they check for existing frames by name first (as in EXAMPLE.js). On error, read the message, fix the cause, retry. If a script half-ran, remove only the frame you created (by its returned ID) and rebuild.
- Only touch your own pages. Never edit the Cover, Foundations, Components or Image slots pages, the toolkit node, the components, or other agents' pages. Never create new components.

## 3. Check your work (required)

Several builders share one per-minute Figma limit (the account is on the Figma Education plan), so use few, rich calls:

- Screenshots come back from inside use_figma: in ONE call, run `await node.screenshot({ scale: 0.5 })` on several section nodes in a row (at most 5: a call returns no more than five images, later ones are dropped silently); each comes back as an image in that one response. Use `{ scale: 1 }` only for a section you need to read closely. Do not use `mcp__Figma__get_screenshot` section by section. Do not re-screenshot the Home page more than once; its patterns are in EXAMPLE.js.
- Build a whole frame, or half of a long page, per use_figma call, and screenshot its sections at the end of the same call.
- Run the lint once per finished frame: `const L = (new Function('figma', (await figma.getNodeByIdAsync('37:851')).characters + '\nreturn L;'))(figma); return await L.run('<frameId>');` Fix every high and medium finding.
- If a call returns "reached the Figma MCP tool call limit", it is a short rolling limit, not a quota: do non-Figma work (write the spec) for about 60 seconds, then retry. Never call whoami or fetch Figma docs about it.
- Before you build a page, list the frames already on its Figma page. If a frame with your frame's name exists, it was left by an earlier builder that has stopped: check it (lint plus screenshots), then either complete it or remove it by its ID and rebuild. Never leave two frames with the same name.

Look for: clipped or overflowing text, collapsed frames (a frame given a fixed width must still hug its height; K.add handles it), text touching edges, overlapping layers, a label above a heading, more than one accent word, a second Primary button in one screenful, Ribbon Cyan text on a light ground, broken mobile layout (horizontal overflow beyond 390). Fix with targeted scripts, then re-check only what changed.

## 4. Design rules (never broken)

- One Primary (Alliance Blue) button per screenful: usually in the hero; a closing Navy CTA band may also use Primary. The header CTA is always the Secondary outline (already in the Header component). Elsewhere use Secondary buttons or Links.
- Links are underlined (Link component, or `links: [...]` in K.t for inline links). Partner Navy on Daylight, Ribbon Cyan inside a Navy chapter (automatic).
- Tints (for example a 10% Ribbon Cyan row): use `K.tint(node, 'cyan', 0.1)` or `K.f(..., { fill, fillOpacity })`. A bound paint assigned once in one step loses its opacity and comes back solid.
- Section grounds are Daylight or a whole Partner Navy chapter only (`K.section(R, name, {ground: 'navy'})`). Never Neutral 50 or any third tone as a ground. Cards are white on Daylight and Partner 30 on navy (automatic).
- No label or kicker above any heading. Meta (dates, read time) goes below.
- At most one accent word per headline, a single word (`accent: 'word.'`): regular weight on light, Ribbon Cyan on navy (automatic). Many headlines need none.
- Type: Display/XL only for the one hero statement per page. Display/LG for chapter openers and big bands. Heading/1 for navy chapter titles or page titles on simple pages, Heading/2 for section titles, Heading/3 and Heading/4 for cards, steps, rows. Body/LG for leads (keep leads to about 60ch: 560 to 700 px wide), Body/Default for running text, Body/SM and UI/Caption for secondary text. Data/Mono for prices in rows, sources, times and codes. Data/Numeral for big figures.
- Layout: 1320 container, section heads are asymmetric (`K.head`: title 0.9fr, lead 1.1fr), 48 px between a head and its content, hero splits 1.08fr to 1fr. Never centre a hero. Never put three identical cards in a row: use a bento (one large, two stacked), a 2-column zig-zag, list rows with hairlines, or a table. Vary layouts: no two adjacent sections with the same layout.
- Vary image presentation across a page and across pages: split image left or right, full-bleed band with a navy scrim and text over it, inset framed media, mosaic of 2 to 3 images of different sizes, image inside a large bento card, product visuals (framed email or template previews). Not every section needs an image; a rich page has 2 to 4 image slots, a simple page 0 to 1.
- Light from the top left; no glow; no gradient text; no sparkles, brains, circuits, robots, purple or pink; no Philippine or other regional motifs (the Philippines base is said in copy only).
- The ribbon signature at most once or twice per page: the Ribbon rule (`K.rule(w)`) or the Steps component.
- WCAG AA: never put Text/Tertiary on navy for important text; never put text on an image without a navy scrim, and keep that scrim at 82% navy or more under every line of text (fade it only beyond the text). The lint flags a weaker scrim as weak-scrim.

## 5. Mobile-first (design it, don't just stack)

- Use `K.init('Mobile')`: type sizes, gutter (16), container (358) and section padding (72) switch automatically. Components with a Viewport variant (Header, Footer, Steps, Time zones, Service row) pick the Mobile variant automatically.
- Re-order for content priority: headline and the action first, proof next, detail last. Primary buttons go full width (`K.add(parent, K.btn(...), {w: 'fill'})`, size LG).
- Re-crop images: 16:9 bands become 4:5 or 3:4; split images move under the lead; mosaics drop to one large plus one small; full-bleed bands keep text at the top with a scrim from the top.
- Collapse long lists into accordions, tables into stacked rows (one row per item with label and value), multi-column grids into one column or a horizontal row of 2. No horizontal overflow beyond 390.

## 6. Copy rules

- Write as Alliance AI Partners: result first, plain words, short sentences, "we will" not "we can", "partners" for client companies and "customers" for their customers. Reuse Brand DNA wording where it fits. Always the full name "Alliance AI Partners".
- Banned words: leverage, seamless, cutting-edge, revolutionary, game-changing, disrupt, supercharge, unleash, unlock, 10x, synergy, magic, ninja, guru, rockstar, hustle, alpha. Also never "cheapest", "best rate", "a fraction of the cost", "Top 1%".
- Never invent facts: no prices, partner names or logos, testimonials, case studies, results, metrics, team names or photos, certifications, years in business or headcounts. Keep placeholders exactly: `[PRICE]`, `[30]` days, `[Name]`, `[Role]`, `[Registered address]`, `[Company number]`, `[Partner name]`, `[two weeks]`. Mark samples as samples ("Sample role", "Sample article", "Sample report").
- Any number needs a Source key and a dated source line in the same section (`K.sources`), using only the Brand DNA sources (IBPAP 2025, EF EPI 2025, Clutch September 2026, BLS May 2025 and June 2026, ONS 2026, Jobs and Skills Australia May 2025, NSW Government, NIST, Republic Act 10173, Microsoft, Intercom, Smith.ai). Write "Retrieved 2026-11-02."
- Contact samples only: `hello@allianceaipartners.example`, `+1 202 555 0147`. The sample person Isabel Navarro (partner success lead) appears only on the Digital business card.
- Sample clock moment (November): Manila 9:41 am · Sydney 12:41 pm · New York 8:41 pm the day before · London 1:41 am.

## 7. Image slots

- Place every raster as an Image slot: `K.img(id, short, label, w, h, {tone: 'Navy' for navy sections, radius: 0 for full-bleed})`. IDs are per page: `IMG-<page number>-<n>`, e.g. page `07 · Embedded developers` uses `IMG-07-1`, `IMG-07-2`. The same image on desktop and mobile keeps the same ID.
- Label is `Existing: <repo path>` for repo rasters, or `New: <one-line subject>` for images the next session will generate. Existing rasters you may use: the 8 backgrounds in `design-system/imagery/backgrounds/` (`design-system/imagery/IMAGERY.md` says where text can sit; use any one at most twice across the whole site), `brand-kit/emails/previews/*` and `brand-kit/templates/previews/*` (framed product visuals), `brand-kit/brand-board.png`, `brand-kit/merch/mockups/*` (Brand page only).
- For every new image write a full Gemini prompt in your spec: what it depicts (it must clearly show the section's idea), composition, where the calm text area is, aspect ratio, then the fixed rules: "Palette only: Partner Navy #121B2A, Alliance Blue #1B56FF, Ribbon Cyan #00D5FF, Daylight #F4F7FB and the shades between them. Nature built from satin ribbon and flat paper facets. Light from the upper left, soft navy-tinted shadows falling down and to the right. No text or letters, no people, no hands, no robots, no brains, no circuit boards, no sparkles, no glow, no purple or pink, no regional or cultural motifs, no real places or landmarks." See `docs/website/pages/home.json`.

## 8. Deliverables per page

1. `docs/website/pages/<slug>.json` in the format of `docs/website/pages/home.json` (sections with id, layout, ground, job, images with imageId, slotName, kind, source or prompt, aspects, placement, textArea, alt; plus frames with the Figma IDs you built). Validate with `python3 -I -c "import json,sys; json.load(open(sys.argv[1]))" <file>`.
2. The Figma frames: Desktop and Mobile, plus the listed states.
3. Return the structured result your task asks for.
