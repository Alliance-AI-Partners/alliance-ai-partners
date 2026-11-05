/*
 * Where the site lives, and whether search engines may index it. Both are read while the site is built, from
 * environment variables (set them in Vercel: Project Settings → Environment Variables, then redeploy).
 *
 * SITE_URL        The public address, for example https://www.allianceaipartners.com, once a custom domain is set.
 *                 Without it the site uses Vercel's production address, or http://localhost:3000 on your computer.
 * ALLOW_INDEXING  "true" lets search engines index the production site. Leave it unset until launch: the site still
 *                 shows [PRICE] placeholders and the example email address. Preview deployments are never indexed.
 */

function resolveSiteUrl() {
  if (process.env.SITE_URL) return new URL(process.env.SITE_URL);
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) return new URL(`https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`);
  return new URL("http://localhost:3000");
}

/** The site's public origin, used for canonical links, the sitemap and social previews. */
export const siteUrl = resolveSiteUrl();

/** True only on the production deployment, and only once ALLOW_INDEXING is "true". */
export const allowIndexing = process.env.VERCEL_ENV === "production" && process.env.ALLOW_INDEXING === "true";
