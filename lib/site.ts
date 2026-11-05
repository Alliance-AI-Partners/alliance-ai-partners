/*
 * Site-wide content: navigation, footer links and contact details, shared by every page.
 * Routes follow the page list in docs/website/README.md. Several of those pages are not built yet, so their links
 * show the not-found page until they are.
 */

export type NavLink = { label: string; href: string };

/** The site's default title and description (docs/website/pages/home.json, seo). */
export const siteTitle = "Alliance AI Partners | Put AI to work";
export const siteDescription =
  "An embedded AI team in the Philippines for companies in the US, Australia and the UK. We build the AI tools and software you need, then help you grow. Published starting prices.";

/** The primary action of the whole site (docs/website/pages/home.json, primaryAction). */
export const primaryAction: NavLink = { label: "See where AI can help", href: "/ai-check-up" };

/** Header navigation (Figma: Header, Viewport=Desktop). */
export const headerNav: NavLink[] = [
  { label: "Services", href: "/services" },
  { label: "Pricing", href: "/pricing" },
  { label: "How we work", href: "/how-we-work" },
  { label: "About", href: "/about" },
];

/** The mobile menu adds Contact to the header links (Figma: Header / Mobile menu). */
export const mobileMenuNav: NavLink[] = [...headerNav, { label: "Contact", href: "/contact" }];

/** The address in the mock-ups. `.example` is a reserved placeholder domain: replace it with the real inbox. */
export const contactEmail = "hello@allianceaipartners.example";

/**
 * The Contact form's topics (docs/website/pages/contact.json). Links preselect one with `?service=<value>`, for example
 * /contact?service=embedded-developers; build them with `contactHref`.
 */
export const contactTopics = [
  { value: "ai-check-up", label: "An AI check-up" },
  { value: "ai-automation", label: "AI automation" },
  { value: "websites", label: "A website or web app" },
  { value: "embedded-developers", label: "Embedded developers" },
  { value: "fixed-quote", label: "A fixed quote for a project" },
  { value: "something-else", label: "Something else" },
] as const;

export type ContactTopic = (typeof contactTopics)[number]["value"];

/** The Contact page with a topic preselected. */
export function contactHref(service: ContactTopic) {
  return `/contact?service=${service}`;
}

export const footerColumns: { heading: string; links: NavLink[] }[] = [
  {
    heading: "Services",
    links: [
      { label: "AI check-up", href: "/ai-check-up" },
      { label: "Embedded developers", href: "/services/embedded-developers" },
      { label: "AI automation", href: "/services/ai-automation" },
      { label: "Websites and web apps", href: "/services/websites" },
      { label: "Industries", href: "/industries" },
      { label: "All services", href: "/services" },
    ],
  },
  {
    heading: "Company",
    links: [
      { label: "How we work", href: "/how-we-work" },
      { label: "Pricing", href: "/pricing" },
      { label: "About", href: "/about" },
      { label: "Why the Philippines", href: "/why-the-philippines" },
      { label: "Insights", href: "/insights" },
      { label: "Careers", href: "/careers" },
      { label: "Brand and press", href: "/brand" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    heading: "Who we work with",
    links: [
      { label: "Australia", href: "/au" },
      { label: "United States", href: "/us" },
      { label: "United Kingdom", href: "/uk" },
      { label: "For agencies", href: "/for-agencies" },
    ],
  },
  {
    heading: "Trust",
    links: [
      { label: "Data and security", href: "/trust" },
      { label: "Subprocessors", href: "/trust/subprocessors" },
      { label: "Security", href: "/security" },
      { label: "Questions buyers ask", href: "/faq" },
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
      { label: "Cookies", href: "/cookies" },
      { label: "Accessibility", href: "/accessibility" },
    ],
  },
];

/**
 * Social profiles shown in the footer. Which profiles exist is still an open question (docs/website/README.md,
 * question 16), so no address is filled in. An icon without an address is drawn but is not a link; add the profile
 * URL to make it one, or remove the entry if there is no profile.
 */
export const socialProfiles: { name: string; icon: "linkedin" | "x" | "youtube"; href: string | null }[] = [
  { name: "LinkedIn", icon: "linkedin", href: null },
  { name: "X", icon: "x", href: null },
  { name: "YouTube", icon: "youtube", href: null },
];
