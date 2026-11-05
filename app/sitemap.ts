import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site-url";

/**
 * The site's pages, from the page table in docs/website/README.md. Add each new page here.
 *
 * Left out on purpose: the samples and templates, which are marked noindex (the sample Insights article, the sample
 * job post, the case study template, the digital business card), the newsletter confirmation (/insights/subscribed,
 * reached from the opt-in email), and /case-studies, which stays unlisted until the first approved case study exists
 * (docs/website/README.md).
 */
const routes = [
  "/",
  "/ai-check-up",
  "/ai-check-up/sample",
  "/services",
  "/services/scale-ai",
  "/services/solve-problems-with-ai",
  "/services/grow",
  "/services/embedded-developers",
  "/services/ai-automation",
  "/services/websites",
  "/pricing",
  "/how-we-work",
  "/about",
  "/trust",
  "/trust/subprocessors",
  "/security",
  "/faq",
  "/contact",
  "/privacy",
  "/terms",
  "/cookies",
  "/accessibility",
  "/insights",
  "/industries",
  "/industries/finance-and-accounting",
  "/industries/healthcare-and-clinics",
  "/industries/online-stores-and-retail",
  "/industries/home-services-and-local-businesses",
  "/why-the-philippines",
  "/au",
  "/us",
  "/uk",
  "/for-agencies",
  "/careers",
  "/brand",
  "/compare",
];

/** /sitemap.xml */
export default function sitemap(): MetadataRoute.Sitemap {
  return routes.map((route) => ({ url: new URL(route, siteUrl).href }));
}
