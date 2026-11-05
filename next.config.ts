import type { NextConfig } from "next";
import { allowIndexing } from "./lib/site-url";

/* Sent with every response. No Content-Security-Policy for scripts yet: Next.js inlines its own scripts, so a strict
   policy needs per-request nonces, which would turn the static pages dynamic. frame-ancestors alone is safe. */
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), browsing-topics=()" },
];

/* Until launch (ALLOW_INDEXING, see lib/site-url.ts) every response asks search engines not to index it. */
const indexingHeaders = allowIndexing ? [] : [{ key: "X-Robots-Tag", value: "noindex, nofollow" }];

const nextConfig: NextConfig = {
  // Don't advertise the framework in an X-Powered-By header.
  poweredByHeader: false,
  cacheComponents: true,
  partialPrefetching: true,
  // Tailwind CSS v4 runs as a Turbopack loader (the Next.js 16.4 default), so no PostCSS config is needed.
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
      // The icon sprite is a set of <symbol>s, not an image: import it as a plain file URL for <use href>.
      "*.svg": [{ condition: { path: /design-system[\\/]icons[\\/]sprite\.svg$/ }, type: "asset" }],
    },
  },
  images: {
    formats: ["image/avif", "image/webp"],
  },
  async headers() {
    return [{ source: "/:path*", headers: [...securityHeaders, ...indexingHeaders] }];
  },
};

export default nextConfig;
