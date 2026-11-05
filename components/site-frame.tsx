import type { ReactNode } from "react";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

/**
 * The site's frame around a page: the skip link, the sticky header, the page's content in <main id="main"> and the
 * footer. Every page uses it through app/(site)/layout.tsx, and the not-found page uses it directly. Pages designed
 * without it (the digital business card) live outside the (site) route group.
 */
export function SiteFrame({ children }: { children: ReactNode }) {
  return (
    <>
      <a href="#main" className="aap-skip-link">
        Skip to content
      </a>
      <SiteHeader />
      <main id="main">{children}</main>
      <SiteFooter />
    </>
  );
}
