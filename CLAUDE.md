# Alliance AI Partners

Brand foundation for Alliance AI Partners, a Philippines-based AI company that works as an embedded team for companies in the US, Australia and the UK. This repo holds the strategy, the finished logo kit, the design system, the brand kit and the records of the website design. The website is designed in Figma, desktop and mobile, but not yet built in code; the planned stack is Next.js on Vercel with Tailwind CSS v4.

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

## Build caveats

- The Illustrator build in `docs/brand-kit/_build/` runs only on Windows, with Adobe Illustrator (driven over COM), Montserrat, Python 3.11 and the VectorCraft CLI. It cannot run in a Linux or cloud session.
- `docs/brand-kit/README.md` and `docs/brand-kit/Print-Masters/Print-Specs.md` are generated by `_build/docs.py` (`python build.py docs`). Change the generator as well as the output.
- Image generation (`brand-kit/tools/generate-imagery.py` and `brand-kit/tools/generate-website-images.py`) needs `GEMINI_API_KEY`, read from the environment or the git-ignored `.env`. Never commit keys. A cloud session also needs `generativelanguage.googleapis.com` in its environment's allowed domains.
- The repo is about 255 MB, mostly print and logo binaries. Don't add large binaries unless they belong to the kit.

## Conventions

- Commit messages: a short imperative sentence in sentence case, for example "Add the price pitch to the brand guide".
- The Obsidian vault is the `AllianceAIPartners/` folder. Notes link to each other with Markdown links (spaces written as `%20`) and refer to files outside the vault by their path in backticks, because Obsidian can't open them. Vault notes use American spelling; `DESIGN.md` and `design-system/` use British spelling.
- When a decision changes what another note says, add a dated row to the Decision Log and update that note.
