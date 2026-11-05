import type { Metadata } from "next";

type PageMetadataInput = {
  /** The full title from the page record's seo.title, for example "The AI check-up | Alliance AI Partners". */
  title: string;
  /** The page record's seo.description. */
  description: string;
  /** The page's route, for the canonical link and social previews, for example "/ai-check-up". */
  path: string;
  /** Keep a template or sample page out of search results even after launch (job post, case study template). */
  noindex?: boolean;
};

/**
 * A page's metadata from its record in docs/website/pages/: the exact SEO title (not run through the layout's
 * "%s | Alliance AI Partners" template, since the records already carry the full title), the description, the
 * canonical link and the social preview text. The site-wide rules (search engines closed until launch) live in
 * app/layout.tsx.
 */
export function pageMetadata({ title, description, path, noindex = false }: PageMetadataInput): Metadata {
  return {
    title: { absolute: title },
    description,
    alternates: { canonical: path },
    openGraph: { type: "website", siteName: "Alliance AI Partners", locale: "en_US", url: path, title, description },
    twitter: { card: "summary", title, description },
    ...(noindex ? { robots: { index: false, follow: true } } : {}),
  };
}
