import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
};

export default nextConfig;
