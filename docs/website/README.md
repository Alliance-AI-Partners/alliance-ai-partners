# Website page designs

The Alliance AI Partners website is designed in Figma, page by page, at desktop (1,440 px) and mobile (390 px) widths: [Alliance AI Partners — Website](https://www.figma.com/design/1VGkymJ9AH6vGYgFDAU68A/Alliance-AI-Partners-%E2%80%94-Website). This folder keeps the records that go with that file, so the site can be built in code (Next.js on Vercel, see `PRODUCT.md`) and the Figma file can be extended in the same way.

| Path | What |
|---|---|
| [pages/](pages/) | One record per page: its route, purpose, single primary action, SEO title and description, each section's job, layout, draft copy and images, and the IDs of its Figma frames |
| [toolkit/](toolkit/) | The code that built the pages (`pagekit.js`) and checks them (`lint.js`), a file of patterns (`example.js`), and the briefs the build and review agents followed |
| `design-system/imagery/website/manifest.json` | Every image slot: its prompt or repository file, sizes, alt text and Figma node IDs (see `design-system/imagery/IMAGERY.md`) |

Figma holds the final copy. Where a page record's draft copy differs from Figma, Figma wins.

## Pages

39 pages, in build order. Phase: Launch pages are needed for the first release, Next pages follow, and Later pages wait for real material (for example, case studies wait for real partner results).

| No. | Page | Route | Phase | What the page does | Record |
|---|---|---|---|---|---|
| 01 | Home | `/` | Launch | Show a founder in seconds what changes for them, why Alliance AI Partners costs less, and get them to start an AI check-up. | [home.json](pages/home.json) |
| 02 | AI check-up | `/ai-check-up` | Launch | Get a founder to book the AI check-up: our usual first project, short and low-risk, where we find where AI could save their team time or money. | [ai-check-up.json](pages/ai-check-up.json) |
| 03 | Services | `/services` | Launch | The hub. Let a founder pick one of three goals in seconds, see published starting prices, then browse every service and the industry packages. | [services.json](pages/services.json) |
| 04 | Scale AI | `/services/scale-ai` | Launch | Show a founder everything it takes to use AI across the company (strategy, training, software, operations, robotics, people) and that one team does all of it, starting small. | [scale-ai.json](pages/scale-ai.json) |
| 05 | Solve problems with AI | `/services/solve-problems-with-ai` | Launch | Show a founder which slow jobs AI can take off the team, what changes in one real-looking process, and that a person still checks the work. | [solve-problems-with-ai.json](pages/solve-problems-with-ai.json) |
| 06 | Grow | `/services/grow` | Launch | Show a founder how AI takes the repetitive part of marketing and sales so the team spends its time on customers, list every Grow service, and make retainers checkable. | [grow.json](pages/grow.json) |
| 07 | Embedded developers | `/services/embedded-developers` | Launch | Show a founder that a developer from our team can work inside theirs full time, what that costs next to hiring locally (sourced, like for like), what the monthly price covers, how a week runs and how the hours line up, then get them to describe the role. | [embedded-developers.json](pages/embedded-developers.json) |
| 08 | AI automation | `/services/ai-automation` | Launch | Show a founder that we take one slow process at a time and hand its repetitive steps to AI with a person checking the work, show a sample before and after, explain how a project runs and is priced (fixed quote, AI usage at cost), and get them to start an AI check-up. | [ai-automation.json](pages/ai-automation.json) |
| 09 | Websites and web apps | `/services/websites` | Launch | Show a founder that we build fast, accessible websites and web apps and keep them running, how AI and people share the work, how agency hourly rates compare (Clutch, sourced) against our fixed quote from [PRICE], and get them to ask for a fixed quote. | [websites.json](pages/websites.json) |
| 10 | Pricing | `/pricing` | Launch | Show a founder every starting price and the honest pricing promise in checkable form, explain fairly how other AI firms charge and why we cost less, then move them to an AI check-up. | [pricing.json](pages/pricing.json) |
| 11 | How we work | `/how-we-work` | Launch | Show a founder exactly what working with Alliance AI Partners is like, step by step, so the process feels safe and they start an AI check-up. | [how-we-work.json](pages/how-we-work.json) |
| 12 | About | `/about` | Launch | Tell a founder who Alliance AI Partners is, why it exists, what it holds to and where it is based, so they trust the team enough to start an AI check-up. | [about.json](pages/about.json) |
| 13 | Data and security | `/trust` | Launch | Show a founder or CTO, before they share anything, how Alliance AI Partners handles partner data: it stays in their systems wherever possible, we take only the access a job needs, a person reviews every piece of work, and a national privacy law stands behind it. | [data-and-security.json](pages/data-and-security.json) |
| 14 | Questions buyers ask | `/faq` | Launch | Answer, in plain words and before any sales call, the questions founders ask about quality, price, time zones, data and working together, so they can decide to start an AI check-up or ask us directly. | [questions-buyers-ask.json](pages/questions-buyers-ask.json) |
| 15 | Contact | `/contact` | Launch | Let a founder reach a person at Alliance AI Partners in the way that suits them (form, email or phone), show when our team is working in their time zone, give the company details, and nudge anyone unsure where to start toward the AI check-up. | [contact.json](pages/contact.json) |
| 16 | Privacy (legal template) | `/privacy` | Launch | A long-form legal page template: plain title, last updated line, contents that stay in view, numbered sections and a contact block. Privacy is the first use; Terms, Cookies and Accessibility reuse the same design. | [privacy.json](pages/privacy.json) |
| 17 | System pages | `404: any unknown path (app/not-found.tsx) · Error: any route that fails (app/error.tsx) · Newsletter confirmed: /insights/subscribed (the link in the double opt-in email)` | Launch | Three short pages that catch a visitor when something is missing, broken or just finished, say plainly what happened, and give a kind way back to the home page or the AI check-up. | [system-pages.json](pages/system-pages.json) |
| 18 | Insights | | Next | Being built | |
| 19 | Article | | Next | Being built | |
| 20 | Industries | | Next | Being built | |
| 21 | Finance and accounting | | Next | Being built | |
| 22 | Healthcare and clinics | | Next | Being built | |
| 23 | Online stores and retail | | Next | Being built | |
| 24 | Home services and local businesses | | Next | Being built | |
| 25 | Why the Philippines | `/why-the-philippines` | Next | Answer the question every buyer asks, why the Philippines, with sourced facts in the right order: skill first, then hours, the privacy law and price, and move the reader to an AI check-up. | [why-the-philippines.json](pages/why-the-philippines.json) |
| 26 | Australia | `/au` | Next | Give a founder in Australia the local case: how our hours line up, what a developer costs them locally, what agencies charge, our starting prices in their currency, and the AI check-up. | [australia.json](pages/australia.json) |
| 27 | United States | `/us` | Next | Give a founder in the United States the local case: how our hours line up, what a developer costs them locally, what agencies charge, our starting prices in their currency, and the AI check-up. | [united-states.json](pages/united-states.json) |
| 28 | United Kingdom | `/uk` | Next | Give a founder in the United Kingdom the local case: how our hours line up, what a developer costs them locally, what agencies charge, our starting prices in their currency, and the AI check-up. | [united-kingdom.json](pages/united-kingdom.json) |
| 29 | For agencies | `/for-agencies` | Next | Show agencies how white-label work with Alliance AI Partners runs: we build under the agency’s brand, the client relationship stays theirs, embedded developers when they need more hands, a fixed quote first and published starting prices, the four steps, and confidentiality terms to confirm. Move the reader to ask for a fixed quote. | [for-agencies.json](pages/for-agencies.json) |
| 30 | Careers | | Next | Being built | |
| 31 | Job post | | Next | Being built | |
| 32 | Brand and press | | Next | Being built | |
| 33 | Digital business card | | Next | Being built | |
| 34 | AI check-up sample report | `/ai-check-up/sample` | Next | Show, with a clearly labelled SAMPLE, what the AI check-up delivers, so a founder knows exactly what they get before they book a real one. | [ai-check-up-sample-report.json](pages/ai-check-up-sample-report.json) |
| 35 | Case studies | | Later | Being built | |
| 36 | Case study template | | Later | Being built | |
| 37 | Compare | `/compare` | Later | Let a founder weigh Alliance AI Partners fairly against hiring locally, US and Australian agencies and per-seat AI tools, with a source and a date for every number, say honestly when each option is the right choice, and move them to an AI check-up. | [compare.json](pages/compare.json) |
| 38 | Subprocessors | `/trust/subprocessors` | Later | List every AI provider and software tool that may touch partner data, with what it does, which data it may see and where it runs, and say how partners hear about changes. Until the list exists, every row is a marked placeholder. | [subprocessors.json](pages/subprocessors.json) |
| 39 | Security disclosure | `/security` | Later | Tell a security researcher, in one screen, where to send a vulnerability, what to include and what Alliance AI Partners promises in return, with the legal safe harbour held as a placeholder for review. | [security-disclosure.json](pages/security-disclosure.json) |

## How the Figma file is organised

- **Pages.** Cover, Foundations (colour and type), Components and Image slots come first, then one Figma page per site page, numbered as above.
- **Frames.** Each page has `<Page> — Desktop` (1,440 wide, at x 0) and `<Page> — Mobile` (390 wide, at x 1,600). Extra states sit to their right, for example `Contact — Desktop · Sent` or `Home — Mobile · Menu open`.
- **Variables.** Two collections drive everything: Theme (modes Daylight and Navy) and Viewport (modes Desktop and Mobile). Their names match the CSS tokens in `design-system/tokens/`. A Partner Navy chapter is a section frame set to the Navy mode; a mobile frame is set to the Mobile mode, which switches type sizes, the gutter and section padding.
- **Type.** The text styles follow `DESIGN.md`. In Figma, mono text uses Cascadia Mono as a stand-in, because Figma's font library has no Mona Sans Mono. The website uses Mona Sans Mono from `design-system/fonts/`.
- **Images.** Every raster image is an Image slot, labelled `New:` (to be generated) or `Existing:` (a file in this repository). See `design-system/imagery/IMAGERY.md`.

## Changing or adding a page

The toolkit and the lint are stored inside the Figma file, as text nodes `24:3` and `37:851` on the Image slots page, so any `use_figma` script can load them:

```js
const K = (new Function('figma', (await figma.getNodeByIdAsync('24:3')).characters + '\nreturn K;'))(figma);
await K.init('Desktop');                      // or 'Mobile'
await K.page('07 · Embedded developers');     // the Figma page name
// ... build or change sections with K.section, K.head, K.t, K.btn, K.img and the rest (see toolkit/pagekit.js)

const L = (new Function('figma', (await figma.getNodeByIdAsync('37:851')).characters + '\nreturn L;'))(figma);
return await L.run('<frame id>');             // banned words, unsourced figures, contrast and layout checks
```

Follow [toolkit/build-brief.md](toolkit/build-brief.md) for the rules and [toolkit/review-brief.md](toolkit/review-brief.md) for the checks. To change the toolkit itself, edit `toolkit/pagekit.js`, strip its comments, and write the result into text node `24:3`.

## Before launch: facts to confirm

The pages use only facts from the Brand DNA. Where a fact is missing, they show a placeholder in square brackets, such as `[PRICE]`. These need an answer from Alliance AI Partners before the site goes live:

1. Every `[PRICE]`, in each currency, and the notice period for monthly plans (`[30]` days). Brand DNA section 6 holds the price rules.
2. How hiring an embedded developer works. The Embedded developers page says we recruit and test candidates, the partner interviews the ones we put forward and chooses, and gets "a shortlist to interview". The Brand DNA doesn't describe this process yet.
3. How long the AI check-up takes (`[two weeks]`), and that its call lasts one hour. The hour comes from the brand-kit booking email.
4. How soon an embedded developer can start (`[two weeks]` after the partner says yes).
5. How fast we reply to messages (`[one working day]`, Contact page).
6. The published data policy behind the Data and security page (Brand DNA, Note 6).
7. The subprocessor list: each provider, what it does, the data it may see, where it runs, and how much notice partners get before a change.
8. The security contact, the PGP key fingerprint and the response times on the Security disclosure page.
9. The legal text of the Privacy page, and of the Terms, Cookies and Accessibility pages that share its template. A lawyer should write or review it.
10. The registered address and company number (`[Registered address]`, `[Company number]`), in the footer and on the legal pages.
11. The date of the Clutch SEO retainer figure (an average of US$3,199 a month), used on the Grow and Pricing pages. The Brand DNA gives it without a date, so Grow shows `[date to confirm]`.

Every figure on the site carries a source key and a dated source line, from the sources the Brand DNA lists. Recheck them before launch, because prices and statistics change.
