import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site-url";

/** The pages that exist so far. Add each page here as it is built (routes: docs/website/README.md). */
const builtRoutes = ["/"];

/** /sitemap.xml */
export default function sitemap(): MetadataRoute.Sitemap {
  return builtRoutes.map((route) => ({ url: new URL(route, siteUrl).href }));
}
