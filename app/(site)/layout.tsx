import type { ReactNode } from "react";
import { SiteFrame } from "@/components/site-frame";

/**
 * The layout of every site page: the header, the page in <main> and the footer (components/site-frame.tsx). The
 * route group "(site)" does not appear in addresses: app/(site)/pricing/page.tsx is /pricing.
 */
export default function SiteLayout({ children }: { children: ReactNode }) {
  return <SiteFrame>{children}</SiteFrame>;
}
