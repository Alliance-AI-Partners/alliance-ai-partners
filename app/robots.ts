import type { MetadataRoute } from "next";
import { allowIndexing, siteUrl } from "@/lib/site-url";

/** /robots.txt: closed to crawlers until launch (see lib/site-url.ts), then open with the sitemap. */
export default function robots(): MetadataRoute.Robots {
  if (!allowIndexing) {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: new URL("/sitemap.xml", siteUrl).href,
  };
}
