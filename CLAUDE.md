# Alliance AI Partners

Brand foundation for Alliance AI Partners, a Philippines-based AI company that works as an embedded team for companies in the US, Australia and the UK. This repo holds the strategy, the finished logo kit, the design system, the brand kit, the records of the website design and the website itself. The website is designed in Figma, desktop and mobile, and is being built at the root of this repo with Next.js 16, TypeScript and Tailwind CSS v4, for Vercel. Built so far: the header, the mobile menu, the footer and Home.

## Sources of truth

Read these before changing anything. Where older notes disagree, these win.

| Topic | File |
|---|---|
| Product, audience, positioning, brand commitments | `PRODUCT.md` |
| Voice, values, services, pricing pitch and price-claim rules | `AllianceAIPartners/Brand DNA & Foundation.md` |
| Design language "The Ribbon": colour roles, type, components, banned looks | `DESIGN.md` |
| Tokens, components, fonts, icons, imagery, web logos | `design-system/` (start with its README) |
| Logo masters and print files | `docs/brand-kit/` (start with its README) |
| Palette values | `docs/brand-kit/_build/palette.json`, compiled into `design-system/tokens/` |
| Figma: logo suite | [Alliance AI Partners — Logo Suite](https://www.figma.com/design/rXNPaaMds46oWgM64QPRI6/Alliance-AI-Partners-%E2%80%94-Logo-Suite) |
| Figma: every website page, desktop and mobile | [Alliance AI Partners — Website](https://www.figma.com/design/1VGkymJ9AH6vGYgFDAU68A/Alliance-AI-Partners-%E2%80%94-Website) (start with its Cover page); page records, routes and copy in `docs/website/` (start with its README) |
| Website images: prompts, repo sources, alt text and slot locations | `design-system/imagery/website/manifest.json` |
| Website code: pages, components, global styles | `app/`, `components/`, `lib/` (see "Working with the website code") |
| What was decided, when, and what it replaced | `AllianceAIPartners/Decision Log.md` |

Historical, kept for the record, not guidance: `AllianceAIPartners/Big Idea Options.md`, `AllianceAIPartners/Design System Directions.md`, `AllianceAIPartners/logo-concepts/`, `AllianceAIPartners/Logos/`, `docs/logos/` (the AI-generated source images), `.impeccable/` (design-tool review records) and `.claude-flow/` (a tool ledger).

## Rules that are never broken

- Always write the full name "Alliance AI Partners".
- Never invent prices, partner names or logos, testimonials, case studies, results or team details. Keep placeholders such as `[PRICE]` until real figures exist, and give every published number a source and a date.
- Follow the voice in Brand DNA section 5: the result first, plain words, short sentences. Never use leverage, seamless, cutting-edge, revolutionary, game-changing, disrupt, supercharge, unleash, unlock, 10x, synergy, magic, ninja, guru, rockstar, hustle or alpha.
- Alliance Blue fills one committing action per view: the primary button. Links are Partner Navy and always underlined; inside Partner Navy sections they turn Ribbon Cyan.
- Ribbon Cyan is never text on a light ground. A section's ground is Daylight or Partner Navy, nothing else.
- Light comes from the top left. No glow, no decorative blur, no gradient-filled text.
- No AI clichés (sparkles, glowing brains, circuit boards, robot faces, purple-and-pink gradients) and no Philippine or other regional motifs.
- All text passes WCAG 2.x AA.
- Live text is Mona Sans, with Mona Sans Mono for prices, sources, times and codes. Montserrat exists only as outlined type inside the logo files; never type the company name as a stand-in for the logo.

## Working with the design system

- Tokens: edit `design-system/tokens/tokens.json`, then run `python design-system/tokens/build-tokens.py` to regenerate `tokens.css` and `tailwind-theme.css`. Don't hand-edit the generated files.
- Names: custom properties are `--aap-<group>-<name>` (for example `--aap-color-brand-partner-navy`); classes are `aap-<component>` with `--modifier` and `__part`. The Figma file's Brand Colors variables use these exact names as their WEB code syntax, so rename a colour token in both places.
- File names are lowercase kebab-case.

## Working with the Figma website file

- Each page has `<Page> — Desktop` (1,440 wide, at x 0) and `<Page> — Mobile` (390 wide, at x 1,600); extra states sit to their right. Everything is built from the file's variables, which carry the CSS token names, and its components. Never detach them or type raw colours.
- Images are Image slot instances named `IMG-<page>-<n> · <short>`. The manifest above gives each slot's prompt or repo source and its node IDs; `brand-kit/tools/generate-website-images.py` generates the new ones.
- The page toolkit and the lint live in the file as text nodes `24:3` and `37:851` on the Image slots page, with their source in `docs/website/toolkit/`. Load them as `docs/website/README.md` shows, and don't delete them.
- The Figma account is on the Education plan, which limits MCP calls per minute: build a whole frame per call, and take screenshots inside `use_figma` (at most five come back from one call).

## Working with the website code

- Run `npm install`, then `npm run dev` and open http://localhost:3000. Before pushing, run `npm run lint`, `npm run typecheck` and `npm run build`.
- Next.js 16 differs from older versions. Read the guide in `node_modules/next/dist/docs/` before writing Next.js code (`AGENTS.md`, which `next dev` keeps current, says the same). Cache Components is on: a page must not read the time, `Math.random()` or request data while it prerenders; read the time in the browser, as `components/home/live-time-zones.tsx` does.
- `app/globals.css` loads Tailwind, the tokens, the generated Tailwind theme and `design-system/css/components.css` (in Tailwind's components layer, so a utility can override one property). Style with the `aap-*` classes and the theme utilities (`text-body-lg`, `text-ink-secondary`, `border-line`); never type raw colours or sizes a token covers. Where Figma differs from a component, add a commented rule to `globals.css`.
- Images, logos, icons and fonts are imported straight from `design-system/` and `brand-kit/` (images and SVG logos through `next/image`, icons through `components/icon.tsx`). Don't copy them into `public/`.
- Motion follows the design system's tokens (`--aap-duration-*`, `--aap-easing-*`) and `plans/README.md`: CSS does the moving; Motion (`motion/react`) only triggers scroll reveals (`data-reveal-group` and `data-reveal-item`, `components/scroll-effects.tsx`). Never hide content in the server HTML, keep motion to `opacity` and transforms, and give every effect a `prefers-reduced-motion` path. Internal links use `components/site-link.tsx`, which drives the page-loading bar.
- Layouts switch from the Figma mobile frame to the desktop frame at 1,024 px (`lg`). Copy that Figma words differently in the two frames is rendered twice, with `lg:hidden` and `hidden lg:inline`.
- Check each page against its Figma frames at 1,440 and 390 wide: section tops and heights, text positions, and image and card boxes. Figma rounds every line height to a whole pixel and draws small Mona Sans about 2% wider than browsers do, so expect a few pixels of drift and the odd different line break; spacing itself should match.

## Build caveats

- The Illustrator build in `docs/brand-kit/_build/` runs only on Windows, with Adobe Illustrator (driven over COM), Montserrat, Python 3.11 and the VectorCraft CLI. It cannot run in a Linux or cloud session.
- `docs/brand-kit/README.md` and `docs/brand-kit/Print-Masters/Print-Specs.md` are generated by `_build/docs.py` (`python build.py docs`). Change the generator as well as the output.
- Image generation (`brand-kit/tools/generate-imagery.py` and `brand-kit/tools/generate-website-images.py`) needs `GEMINI_API_KEY`, read from the environment or the git-ignored `.env`. Never commit keys. A cloud session also needs `generativelanguage.googleapis.com` in its environment's allowed domains.
- The repo is about 255 MB, mostly print and logo binaries. Don't add large binaries unless they belong to the kit.

## Conventions

- Commit messages: a short imperative sentence in sentence case, for example "Add the price pitch to the brand guide".
- The Obsidian vault is the `AllianceAIPartners/` folder. Notes link to each other with Markdown links (spaces written as `%20`) and refer to files outside the vault by their path in backticks, because Obsidian can't open them. Vault notes use American spelling; `DESIGN.md` and `design-system/` use British spelling.
- When a decision changes what another note says, add a dated row to the Decision Log and update that note.
