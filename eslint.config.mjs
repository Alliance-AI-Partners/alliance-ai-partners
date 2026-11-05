import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // The brand repository around the site: build scripts, Figma toolkits and records, not part of the app.
    "docs/**",
    "brand-kit/**",
    "design-system/**",
    "AllianceAIPartners/**",
    ".impeccable/**",
    ".claude-flow/**",
  ]),
]);

export default eslintConfig;
