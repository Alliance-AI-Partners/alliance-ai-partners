Alliance AI Partners · Decision log · Started November 2026

This note records the big brand decisions: what we chose, when, and which older notes it replaced. When a decision changes what another note says, add a dated row here and update that note.

## Where the current answers live

| Question | Look here |
|---|---|
| What we do, who we serve, how we sound, how we price | [Brand DNA & Foundation](Brand%20DNA%20%26%20Foundation.md) and `PRODUCT.md` |
| How the brand looks, and how the website should be built | `DESIGN.md` and the `design-system/` folder |
| Logo, Illustrator and print files | `docs/brand-kit/` |
| The logo suite, palette and brand graphics in Figma | [Alliance AI Partners — Logo Suite](https://www.figma.com/design/rXNPaaMds46oWgM64QPRI6/Alliance-AI-Partners-%E2%80%94-Logo-Suite) |
| How every website page looks, on desktop and mobile | [Alliance AI Partners — Website](https://www.figma.com/design/1VGkymJ9AH6vGYgFDAU68A/Alliance-AI-Partners-%E2%80%94-Website) in Figma, with page records in `docs/website/` |
| Exact color values | `docs/brand-kit/_build/palette.json`, compiled into `design-system/tokens/` |

Files outside this vault are named by their path in the repository, because Obsidian can't open them.

## Decisions

| Date (2026) | What we decided | Where it shows |
|---|---|---|
| 18 Oct | Added the Brand DNA (version 2.0) to the repository. Its big idea was a wolf pack and a constellation. | Brand DNA, in git history |
| 22 Oct | Put the big idea on hold and researched 15 options. The research recommended Joinery. | [Big Idea Options](Big%20Idea%20Options.md), Brand DNA 2.1 |
| 23 Oct | Added the price pitch, the Philippines pitch and the rules for price claims. | Brand DNA section 6 |
| 25 Oct | Scored 20 design directions (Draft 3). | Design System Directions, in git history (commit `252bfc1`) |
| 28 Oct | Dropped all 20 directions as not strong enough. Drew the top 8 as logos with four AI tools. None was used. | [Design System Directions](Design%20System%20Directions.md) (Draft 4), `Logos/` |
| Not recorded | Wrote 15 more logo concepts and drew Concept 1 with two Gemini image models. None was used. | `logo-concepts/`, `Logos/concept-01-the-structural-keystone/` |
| Late Oct | Chose the 3D A+P ribbon logo. It started as 17 AI-generated images, which were rebuilt as exact vector and print files. Which tool and prompt made the images was not recorded. | `docs/logos/`, `docs/brand-kit/` |
| 1 Nov | Chose one palette, "A, P and the Ribbon": six core colors and eight shading tones for the 3D mark. | `docs/brand-kit/_build/palette.json`, the Figma Palette page |
| 2 Nov | Chose "The Ribbon" as the big idea behind the design, over the Banig Weave look a design tool suggested. Ruled out Philippine and other regional motifs, because we work internationally. Chose Mona Sans for all live text and Next.js on Vercel for the website. Built the design system and the brand kit. | `PRODUCT.md`, `DESIGN.md`, `design-system/`, `brand-kit/` |
| 3 Nov | Matched the Figma file to the website code: its color variables now carry the CSS names, and its usage notes follow `DESIGN.md`. Updated the Brand DNA to version 2.2. | The Figma file, this note |
| 3 Nov | Designed the website in Figma: 39 pages, each at desktop (1,440 pixels) and mobile (390 pixels) widths, built from the design system's variables and components. The copy comes from the Brand DNA, with placeholders where facts are still missing. Images are marked slots with written prompts, to be generated with Gemini in a later session. | The Figma Website file, `docs/website/`, `design-system/imagery/website/` |
| 3 Nov | Shortened the reading measure to 52ch for running text and 44ch for leads (it was 68ch and 60ch). Measured in Mona Sans, 68ch held about 97 characters a line, well past the 45 to 75 that read comfortably; the new values hold about 74 and 63. | `DESIGN.md`, `design-system/tokens/` |
| 4 Nov | Generated the 52 new website images with Gemini and placed all 76 images in the Figma Website file, filling its 157 slots. Each image was reviewed by eye. One with a visible seam (IMG-05-1) was regenerated. 19 that drifted off the palette, with a cream ground or a warm cast, were corrected in post, and each image's record says what changed. | `design-system/imagery/website/`, `design-system/imagery/IMAGERY.md`, the Figma Website file |
| 5 Nov | Started building the website in code: a Next.js 16 app with TypeScript and Tailwind CSS 4 at the root of the repository. It takes the tokens, components, fonts, icons, logos and images straight from `design-system/` and `brand-kit/`. Built the header, the mobile menu, the footer and Home, and checked them against the Figma frames at 1,440 and 390 pixels. Corrected the section padding token to 128 pixels at 1,440 wide, as in the Figma file (it gave 120). Moved the header's switch to the menu button from 640 to 1,024 pixels, so the bar never overflows on tablets. The time-zone clocks are live, so their caption now reads "Live times in each city." | `app/`, `components/`, `design-system/tokens/`, `DESIGN.md`, `docs/website/README.md` |

## Older rules that no longer apply

| Older note | What it said | What applies now |
|---|---|---|
| Big Idea Options | Joinery should be the big idea. | The Ribbon is the big idea. The research behind both still holds: "alliance" means "to bind," and binding ideas stand apart from the usual AI look. |
| Big Idea Options | A daylight base, dark ink lines and one warm accent. | A cool palette: Daylight and Partner Navy, with Alliance Blue and Ribbon Cyan. There is no warm accent. |
| Design System Directions | Avoid overused display fonts, including Montserrat. | Montserrat appears only inside the logo files, as outlined shapes. All live text is Mona Sans. |
| Design System Directions | No mascots. | The faceted swallow is part of the finished kit. Use it as `design-system/imagery/IMAGERY.md` describes. |
| Design System Directions | Shared foundations: a 1,200-pixel grid, a type scale, status colors and motion timings. | `DESIGN.md` and `design-system/tokens/` replace them, for example with a 1,320-pixel container. |
| Design System Directions | Logo clear space of one cap height, a symbol of at least 16 pixels and a wordmark of at least 96 pixels. | `docs/brand-kit/README.md` replaces these with exact values: clear space is 0.287 times the mark's height, and each version has its own minimum size (for example, 48 pixels high for the 3D mark). |
| Brand DNA 2.1 | The visual identity is on hold until the big idea is chosen. | Done. See section 8 of the Brand DNA. |
| `logo-concepts/`, `Logos/` | 15 logo concepts and 8 logo directions, each with its own palette and fonts. | Archived explorations. Don't take colors, fonts or marks from them. |

The research in the older notes is still useful. The findings about AI clichés and name clashes, and the accessibility rules, all still apply.

## Still open

- Trademark and domain checks (Brand DNA, Note 5). The logo is now final, so these are due. Include other "AP" monograms and ribbon-style marks in the search; the earlier research didn't cover them.
- Real starting prices to replace every `[PRICE]` (Brand DNA, section 6).
- A short, published data policy (Brand DNA, Note 6).
- A first target market (Brand DNA, Note 4).
- The content system and analytics (`PRODUCT.md`). The site map is drafted in the Figma Website file.
- The facts the website still needs from us before launch, listed in `docs/website/README.md`. Two examples: how hiring an embedded developer works, and how long the AI check-up call takes.
- Regenerating IMG-07-1 once the Gemini account has credits again. Its cream ground was corrected in post instead (`design-system/imagery/website/IMG-07-1.json`).
- Whether to keep the "Certified AI Partner" badge and the "ENTERPRISE AI CONSULTING" descriptor (`design-system/AUDIT.md`).
- Testing the emails in Gmail, Outlook and Apple Mail (`design-system/AUDIT.md`).
- Whether to run a mock-up round for the brand-kit page, or confirm that building it straight in code stands (`design-system/AUDIT.md`).
- Which Figma account should own the Logo Suite and Website files in the long term.
- Which tool and prompt made the original logo images, if anyone still has them.
- Approving the caption under the live time-zone clocks on Home ("Live times in each city.").
- Updating the Figma Website file where the coded Home page settled a difference: the two band images (IMG-01-4 and IMG-01-5 are placed as WebP, which Figma does not draw, so the bands show plain navy) and the desktop hero mark's shadow (still the 8x-scaled Lifted shadow; the code uses the brand kit's hero shadow, as the Home record's review asks).
