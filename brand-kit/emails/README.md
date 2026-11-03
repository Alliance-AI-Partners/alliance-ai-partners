# Email templates

Six HTML email templates for Alliance AI Partners. They are built from `design-system/` (tokens, logos, icons, fonts) and follow the direction contract "The Ribbon" in `.impeccable/surfaces/brand-kit-index-html.md`. The copy follows `PRODUCT.md` and `AllianceAIPartners/Brand DNA & Foundation.md`.

Every template uses sample content. Each file opens with `<!-- Design template with sample content. Not an official Alliance AI Partners communication. -->`, and the same sentence appears in small type in every footer, so a screenshot can't be mistaken for a real send.

## Templates

| File | Type | Purpose | Subject line | Preheader |
|---|---|---|---|---|
| `welcome.html` | Service | New partner kickoff: the kickoff call, what happens each day of week one, who is on the team, how to reach us | Your first week with Alliance AI Partners | Kickoff is Monday, November 9. Meet your team, see the plan for each day, and learn how to reach us. |
| `check-up-booked.html` | Service | AI check-up confirmation: date and time in the partner's time zone with Manila time beside it, agenda, what to prepare, add to calendar, reschedule | Your AI check-up is booked for Tuesday, November 17 | 5:00 pm EST your time, 6:00 am Wednesday in Manila. Here is the agenda, what to prepare, and a calendar link. |
| `proposal-ready.html` | Service | Fixed quote ready: what the project changes, the total, what is included, what we never charge, AI usage at cost | Your fixed quote for order entry automation is ready | One fixed total, no per-seat fees, and AI usage at cost. Review the proposal and accept it online. |
| `monthly-report.html` | Service | Monthly "Run and grow" report: results with their source, work shipped, one issue and its fix, AI usage at cost, next month's plan | Your October report: what we shipped and what it changed | Results from your own systems, AI usage at cost, and the plan for November. |
| `newsletter.html` | Marketing | Insights newsletter: lead story, two short stories, one sourced figure with its source and date, AI check-up call to action | Insights: start with the work your team does twice | Where to start with AI, when AI is not the answer, and what a hire really costs. |
| `invoice-ready.html` | Service | Invoice: amount due, line items with AI usage on its own line, plan terms with [30] days' notice, pay link, PDF | Your October invoice is ready | [PRICE] due by December 1, 2026. AI usage is on its own line, passed on at cost. |

The subject line is set in your email platform. The `<title>` in each file matches it and names the browser tab when the email is opened with "View in browser".

Each email has exactly one Alliance Blue button, its single committing action: "Add the kickoff to your calendar", "Add to calendar", "Review and accept the quote", "Approve November's plan", "See where AI can help" (the site's primary call to action) and "Pay invoice". Everything else is a text link.

### Sample content

- Nothing here is a real price, result, partner, person or testimonial (PRODUCT.md, Evidence on Hand). Prices are `[PRICE]`. Results are bracketed sample numbers, such as `[12]` hours and Brand DNA's own `[1,400]` and `[90]`. People are `[Name]`, roles `[Role]`, partners `[Partner name]`.
- Booking values (dates, times, cities, invoice and proposal numbers) are realistic samples so the previews read naturally. The sample partner is in New York. The dates follow the 2026 calendar: New York is on EST after November 1, and Manila is UTC+8 all year, so 5:00 pm EST on Tuesday is 6:00 am PHT on Wednesday.
- The sample project, "order entry automation", and the proposal headline come from the before-and-after example in Brand DNA section 5 ("Your orders now go straight into your system. Nobody types them twice.").
- The newsletter's one sourced claim (benefits are 30.8 % of total compensation for US professional workers) is the figure Brand DNA section 6 cites from the US Bureau of Labor Statistics, June 2026. Its source line links to `https://www.bls.gov/news.release/ecec.t04.htm`, the link given in Brand DNA. Re-check the figure against the latest release before sending, and keep the source and date with it.
- `welcome.html` uses the US time-zone line ("Brief us before you log off, and you will see progress when you log on."). For Australian or UK partners, use the matching line from Brand DNA section 6.
- Article links in the newsletter are merge tags. The articles don't exist yet.

## Merge tags

Every action link is a merge tag. No URL, domain or email address is invented, because the domain is still open (PRODUCT.md). Rename the tags to match your email platform's syntax.

**Link merge tags (in `href`)**

| Tag | Used in |
|---|---|
| `{{view_in_browser_url}}`, `{{site_url}}` (logo), `{{privacy_url}}` | All |
| `{{social_linkedin_url}}`, `{{social_x_url}}`, `{{social_youtube_url}}`, `{{social_instagram_url}}`, `{{social_facebook_url}}` | All footers |
| `{{terms_url}}` | The five service emails |
| `{{preferences_url}}`, `{{unsubscribe_url}}` | Newsletter |
| `{{kickoff_calendar_url}}`, `{{project_lead_email}}` (mailto) | Welcome |
| `{{project_lead_phone}}` (tel) | Welcome, proposal |
| `{{calendar_ics_url}}`, `{{calendar_google_url}}`, `{{calendar_outlook_url}}`, `{{reschedule_url}}` | Check-up booked |
| `{{proposal_url}}` | Proposal |
| `{{plan_approval_url}}`, `{{report_url}}` | Monthly report |
| `{{article_1_url}}`, `{{article_2_url}}`, `{{article_3_url}}`, `{{ai_check_up_url}}` | Newsletter |
| `{{payment_url}}`, `{{invoice_pdf_url}}`, `{{billing_email}}` (mailto) | Invoice |

`{{company_address}}` is a text tag in every footer. No postal address is invented.

**Text merge fields.** Each value is wrapped in `<span data-merge="name">sample</span>`. Replace the span contents with your platform's tag:

- Welcome: `first_name`, `partner_name`, `project_name`, `kickoff_date`, `kickoff_time`, `project_lead_name`, `project_lead_email`, `project_lead_phone`, `engineer_name`, `engineer_role`, `designer_name`, `designer_role`, `shared_channel`
- Check-up booked: `partner_city`, `partner_date`, `partner_time`, `our_date`, `our_time`, `sender_name`, `sender_role`, `email`
- Proposal: `partner_name`, `total`, `project_name`, `timeline`, `proposal_number`, `valid_until`, `project_lead_name`, `project_lead_phone`, `ai_usage_estimate`, `off_the_shelf_note`
- Monthly report: `hours_saved`, `data_sources`, `questions_answered`, `questions_handed_over`, `source_note`, `assistant_topic`, `held_orders`, `held_hours`, `provider_1`, `provider_2`, `usage_1`, `usage_2`, `usage_total`, `review_date`, `project_lead_name`, `partner_name`
- Newsletter: `issue_number`, `check_up_price`, `email`
- Invoice: `amount_due`, `due_date`, `invoice_number`, `billing_period`, `partner_name`, `payment_methods`, `plan_name`, `milestone`, `proposal_number`, `provider`, `line_1`, `line_2`, `line_ai`, `subtotal`, `tax_label`, `tax`, `total_due`, `notice_days`, `billing_contact`, `billing_email`

**Repeating blocks** come from your data rather than a single tag: the week-one days, team rows, agenda, shipped-work rows, plan rows, results columns and invoice or usage line items. Each block repeats one table row (or one column) pattern.

## Files

```
brand-kit/emails/
  welcome.html  check-up-booked.html  proposal-ready.html
  monthly-report.html  newsletter.html  invoice-ready.html
  images/     email-safe PNGs (see Images)
  previews/   <name>-desktop.png (1200 px viewport) and <name>-mobile.png (390 px), full page
  README.md
```

## Structure

- **Order of rows.** A "View in browser" link on the page; the Partner Navy header band with the logo; the Daybreak ribbon rule; the white card, its sections split by 1 px #D8DDE4 hairlines; the Partner Navy footer. The footer holds the tagline "Partners in AI. Partners in growth." (Brand DNA section 7, for the lockup and email signature), the social icons, legal links, the reason the reader got the email, © 2026 Alliance AI Partners with `{{company_address}}`, and the sample-content notice.
- **Layout.** Tables with inline styles. Layout tables carry `role="presentation"`. The two money tables (AI usage in the monthly report, line items in the invoice) keep real table semantics with `<caption>` and `<th scope="col">`.
- **Width.** The container is fluid with `max-width:600px`, and an MSO ghost table fixes it at 600 px for Outlook on Windows.
- **Columns.** The check-up times, the report results and the newsletter's two stories are hybrid inline-block columns with ghost cells for Outlook. They sit side by side when there is room and stack when there isn't, even in clients that strip media queries.
- **Phones (below 620 px).** Side padding drops to 24 px, the card goes full bleed with square corners, the H1 goes to 26/32 and the button goes full width.
- **Three `<style>` blocks.** The first holds the media queries (phone layout and `prefers-color-scheme: dark`) and the Apple data-detector rule. The second holds the Outlook.com dark-mode selectors (`[data-ogsb]`, `[data-ogsc]`). The third holds `@font-face` and is hidden from Outlook on Windows. They are separate so a client that drops one block keeps the others. Everything else is inline.
- **Accessibility.** `lang="en"`, a `<title>`, a `role="article"` wrapper with an `aria-label`, a hidden preheader padded with `&#847;&zwnj;&nbsp;` so body text doesn't leak into the inbox preview, real headings (H1, H2, H3), descriptive link text, and no information carried by colour alone (links are underlined).
- **Images.** Every image has `width`, `height`, `alt` and `display:block`. Decorative images (the ribbon rule and the UI icons) have an empty `alt` so screen readers skip them; the logo and the social links have descriptive `alt`. No content depends on `background-image`, and no text sits in an image except the logo.
- **Size.** 20 to 30 KB per file, well under Gmail's 102 KB clipping limit.
- **Shared parts.** The six files share one header, footer, button, panel and type scale. When you change a shared part, change it in all six.

## Colour

Values are hex from `design-system/tokens/tokens.json`, inlined. Contrast is the WCAG 2.x ratio; every text pairing passes AA.

| Role | Colour | Contrast |
|---|---|---|
| Page | Daylight #F4F7FB | |
| Card | White #FFFFFF; panels inside it are Daylight with a 1 px #D8DDE4 edge and a 10 px radius (`radius.md`) | |
| Header and footer bands | Partner Navy #121B2A, 18 px corners on the container (`radius.lg`), square on phones and in Outlook | |
| Text on light | Primary #121B2A; secondary #42587C; tertiary #60697A, used only for small labels, table headers and source notes | 17.27, 7.2 and 5.53:1 on white; 16.07, 6.7 and 5.14:1 on Daylight |
| Text on Partner Navy | #F4F7FB, #BFCBE0, #95A6C1 | 16.07, 10.55 and 6.99:1 |
| Button | Alliance Blue #1B56FF, white 16 px semibold label, 52 px tall (`size.control-lg`), 10 px radius | 5.49:1 |
| Links | Partner Navy #121B2A, underlined | 17.27:1 on white |
| Ribbon Cyan #00D5FF | The Daybreak rule, and the 30.8 % figure on the Partner Navy panel in the newsletter. Never text on a light ground. | 9.84:1 on Partner Navy |

- Alliance Blue is kept for the one committing action, as the direction contract asks, so text links are Partner Navy and underlined, which is now also what the `text.link` token sets.
- The only gradient is the ribbon rule, an image with nothing on it. No gradient sits behind text.
- No emoji, sparkles, glow or AI imagery. The visual world is the logo, the ribbon and the navy bands.

## Type

- **Stack.** `'Mona Sans','Helvetica Neue',Helvetica,Arial,sans-serif` for all text. `'Mona Sans Mono',Menlo,Consolas,'Courier New',monospace` for times, codes, amounts and source notes, as `design-system/fonts/FONTS.md` assigns them.
- **Scale.** H1 30/36 (26/32 on phones), semibold, Semi-expanded (`font-stretch:112.5%`), -0.6 px tracking. H2 20/26 and H3 18/24, semibold. Lead 17/27; body 16/26; secondary 15/24 and 14/22; labels 13/18 semibold in sentence case, with no tracking and no capitals: the design system has no eyebrow role, so a heading is never topped by a small label (dates and issue numbers sit in a meta line below it). Money figures 40/44 at Expanded (`font-stretch:125%`), with only -0.4 px tracking so decimal points stay clear.
- **Web fonts.** The third style block declares `@font-face` for Mona Sans and Mona Sans Mono from `../../design-system/fonts/mona-sans/` (SIL OFL 1.1). Clients that load web fonts (Apple Mail, iOS Mail, Outlook for Mac, Samsung Email, Thunderbird) show Mona Sans once the files are hosted. Gmail, Outlook.com and Yahoo ignore it and show Helvetica or Arial. Outlook on Windows never sees the block, and an MSO-only rule sets Arial, which also stops its Times New Roman fallback.
- **Designed for the fallback.** Most readers will see Helvetica or Arial, so the widths and line lengths were checked with the web fonts blocked: the longest date ("Wednesday, November 18") stays on one line in its column, the results fit their columns, and nothing overflows at 390 px. Font stretch is ignored in Arial, which is fine. The mono fallback is Consolas on Windows and Menlo on Apple devices.
- **Previews** in `previews/` render with Mona Sans loaded from the design-system folder, so they show the intended type. Treat them as the Apple Mail view.

## Images

48 × 48 transparent PNGs shown at 24 × 24 for 2× screens, rendered on 2 November 2026 with Chromium (Playwright 1.63) at device scale 2 from the 24 px SVGs in `design-system/icons/`. Email clients handle SVG unreliably, so every image is PNG.

| PNG | Source | Notes |
|---|---|---|
| `alliance-ai-partners-primary-horizontal-full-color-dark.png` | `design-system/logos/lockups/`, exported at 440 × 146 for email (2× its display size, 22 KB; the 2278 px, 81 KB master stays in the logo kit) | Shown at 220 × 73 on the Partner Navy header. The PNG keeps the logo kit's clear space (6 % each side), so the header cell's left padding is 27 px, which puts the mark on the 40 px text edge (11 px on phones). The navy band stays dark in every mode, so the light wordmark is always on a dark ground. |
| `ribbon-rule.png` | The Daybreak stops from `gradient.daybreak`: #121B2A 0 %, #1B56FF 54 %, #00D5FF 100 %, drawn left to right | 1200 × 6, shown at 600 × 3 (`border.ribbon` is 3 px) directly under the header, so the ribbon leaves the navy band and brightens to cyan. Outlook ignores CSS gradients, so the rule is an image. |
| `social-{linkedin,x,youtube,instagram,facebook}-white-48.png` | `icons/social/*.svg`, #FFFFFF | Every footer. |
| `social-{linkedin,x,youtube,instagram,facebook}-grey-48.png` | `icons/social/*.svg`, #60697A | For light surfaces such as email signatures (5.53:1 on white). No template uses them yet. |
| `ui-{calendar,mail,phone,link,globe}-navy-48.png` | `icons/ui/*.svg`, Partner Navy | Welcome: kickoff panel and "How to reach us". |
| `ui-{link,check,lock}-navy-48.png` | same | Check-up booked: video call, what to prepare, the data note. |
| `ui-check-navy-48.png` | same | Proposal ("What is included") and invoice (plan terms). |
| `ui-alert-triangle-navy-48.png` | same | Monthly report: the issue panel. |
| `ui-download-navy-48.png` | same | Invoice: the PDF link. |

The UI icons are Partner Navy with a 1 px white keyline at 2× (four 0.5 px CSS drop shadows). On white and Daylight the keyline is invisible; when a client darkens the card on its own (Gmail apps, Outlook on Windows), it keeps the icon visible. The icons are decorative, and the text beside each one carries the meaning.

## Dark mode

- `<meta name="color-scheme" content="light dark">` and `<meta name="supported-color-schemes" content="light dark">`.
- Under `@media (prefers-color-scheme: dark)` (Apple Mail, iOS Mail, Outlook for Mac and some others): the page becomes Partner Navy #121B2A, the card Partner 30 #1A2D4E and panels #121B2A. Text becomes #F4F7FB, #BFCBE0 and #95A6C1 (12.78, 8.39 and 5.56:1 on #1A2D4E); links #F4F7FB underlined; hairlines #323E50. Class names use the `dm-` prefix.
- The header and footer bands, the logo, the ribbon rule and the Alliance Blue button look the same in both modes. The header and footer merge into the dark page, and the card floats between them.
- Outlook.com gets the same values through `[data-ogsb]` (backgrounds) and `[data-ogsc]` (text).
- Gmail apps and Outlook on Windows ignore these rules and invert colours themselves. Nothing depends on that going well: there is no dark text in any image, the logo only ever sits on the navy band, and the navy icons carry a white keyline.
- Dark renders were checked in Chromium with `prefers-color-scheme: dark`. They are working files and are not saved in `previews/`.

## Client notes

- **Outlook on Windows (Word engine).** The 600 px ghost table and the column ghost cells hold the layout. Buttons are VML `v:roundrect` (arcsize 19 %, about the 10 px radius) inside `<!--[if mso]>`, with the HTML link in `<!--[if !mso]><!-->`. Text is Arial. Rounded corners on the header, footer and panels render square. CSS dark mode is ignored.
- **Gmail (web and apps).** Uses the inline styles and the head media queries, and drops the web fonts, so text is Helvetica or Arial. Gmail clips messages over 102 KB; these are 20 to 30 KB. The apps may force their own dark mode (see Dark mode).
- **Apple Mail and iOS Mail.** Honour `prefers-color-scheme` and web fonts. `x-apple-disable-message-reformatting` stops automatic scaling. The `a[x-apple-data-detectors]` rule keeps auto-linked dates, times and phone numbers in the text colour, and `format-detection` turns most auto-linking off.
- **Clients that strip `<style>`.** The hybrid columns still stack on narrow screens, and every colour and size is inline, so the email stays readable in light mode.

## What was and was not tested

**Tested (Chromium only, headless, Playwright 1.63, 2 November 2026)**
- Each file over `file://` at 680, 390 and 375 px in light mode and at 680 and 390 px in dark mode: no console errors, no failed requests, no broken images, no horizontal overflow (`scrollWidth` no wider than the viewport), and Mona Sans and Mona Sans Mono loaded.
- Four files (check-up, monthly report, invoice, newsletter) at 680 and 390 px with the web fonts blocked, to check the Arial fallback. No overflow, and the tightest lines still fit.
- A static check of every file: the top comment and the footer notice; exactly one button (one VML shape and one HTML link); every image has `width`, `height`, `alt` and `display:block`, and every `src` resolves; no exclamation marks; none of the words PRODUCT.md bans; the name is always "Alliance AI Partners"; Ribbon Cyan only on navy.
- Contrast for every text pairing above, computed with the WCAG 2.x formula.
- The previews were rendered and reviewed by eye in two rounds. Round one fixed the crowded decimal point in large figures, the wrapping of reference lines on phones (now label and value rows), a question that sat in a check list, the spacing between stacked newsletter stories, and the logo size.

**Not tested**
- Any real email client: Outlook on Windows or Mac, Outlook.com, Gmail web and apps, Apple Mail, iOS Mail, Yahoo or Samsung Email. The VML and MSO code follows standard patterns but hasn't been rendered.
- Real sends, spam scoring, link tracking, image blocking and screen readers.
- Run every template through Litmus or Email on Acid before first use, and again after any structural change.

## Regenerate the previews

The previews use the brand kit's capture tool and an existing Playwright install. From the repository root, in Windows `cmd`:

```
set PLAYWRIGHT_PATH=C:/Users/dalig/Desktop/MaintainTech/MaintainOrg/suretraq-rpm/node_modules/playwright
node brand-kit/tools/capture.cjs brand-kit/emails/welcome.html brand-kit/emails/previews/welcome-desktop.png --width 1200 --height 900 --full
node brand-kit/tools/capture.cjs brand-kit/emails/welcome.html brand-kit/emails/previews/welcome-mobile.png --width 390 --height 844 --full
```

In Git Bash, all six at once:

```
export PLAYWRIGHT_PATH=C:/Users/dalig/Desktop/MaintainTech/MaintainOrg/suretraq-rpm/node_modules/playwright
for n in welcome check-up-booked proposal-ready monthly-report newsletter invoice-ready; do
  node brand-kit/tools/capture.cjs brand-kit/emails/$n.html brand-kit/emails/previews/$n-desktop.png --width 1200 --height 900 --full
  node brand-kit/tools/capture.cjs brand-kit/emails/$n.html brand-kit/emails/previews/$n-mobile.png --width 390 --height 844 --full
done
```

Without `PLAYWRIGHT_PATH`, run `npm i -D playwright` in a project and use that. The tool waits for the network to go idle and for `document.fonts.ready`, so Mona Sans is loaded before the shot.

## Production checklist

- [ ] Replace every placeholder with real, approved values. Never send `[PRICE]`, a bracketed result or a bracketed name.
- [ ] Map the merge tags and `data-merge` spans to your platform's syntax.
- [ ] Host the images on a CDN with absolute `https://` URLs.
- [ ] Host a WOFF2 subset of Mona Sans and Mona Sans Mono on the same CDN and update the two `@font-face` URLs, or delete the third style block. The relative paths work for previews and for the brand kit served with the repository, not in a sent email. Self-hosting also keeps readers' IP addresses away from a third-party font service.
- [ ] Fill in the social URLs once the accounts exist, and remove the icons for any that don't. The glyphs are simplified versions of third-party marks (`design-system/icons/icons.json`); use each platform's official asset where its brand rules require it.
- [ ] Replace `{{company_address}}` with the registered postal address. CAN-SPAM requires a valid postal address in commercial email, and the newsletter is commercial.
- [ ] Confirm the consent split with legal for the US (CAN-SPAM), the UK (PECR) and Australia (Spam Act 2003). The newsletter is marketing and carries Manage preferences and Unsubscribe; the other five are service messages about an engagement, a booking, a quote or an invoice, and carry Privacy policy and Terms.
- [ ] Format dates and times for each partner's country. The samples use US formats for a New York partner; UK and Australian partners read "17 November".
- [ ] Re-check the BLS figure and date in the newsletter against the latest release before each send.
- [ ] Remove the sample-content notice (the top comment and the footer line) only when the email carries real, approved content.
- [ ] Set the subject line and preheader in the platform, and keep the hidden preheader in sync.
- [ ] Send a plain-text part with every email (most platforms generate one).
- [ ] Test in Litmus or Email on Acid across Outlook on Windows, Gmail and Apple Mail, in light and dark mode, with images on and off.

## Design-system notes

- Resolved on 2026-11-02 by the finish review: `color.text.link` in `tokens.json` is now Partner Navy and always underlined, so the website and the emails follow the same rule.
- The email logo is a 440 px export (22 KB) of the 2278 px, 81 KB logo-kit master, made for email on 2026-11-02.
