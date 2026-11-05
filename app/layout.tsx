import type { Metadata, Viewport } from "next";
import { monaSans, monaSansMono } from "@/app/fonts";
import { NavigationProgress } from "@/components/navigation-progress";
import { ScrollEffects } from "@/components/scroll-effects";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import appleTouchIcon from "@/design-system/logos/app-icons/apple-touch-icon.png";
import faviconIco from "@/design-system/logos/app-icons/favicon.ico";
import faviconSvg from "@/design-system/logos/app-icons/favicon.svg";
import { siteDescription, siteTitle } from "@/lib/site";
import { allowIndexing, siteUrl } from "@/lib/site-url";
import "./globals.css";

export const metadata: Metadata = {
  // Absolute URLs for canonical links and social previews (lib/site-url.ts).
  metadataBase: siteUrl,
  title: {
    default: siteTitle,
    template: "%s | Alliance AI Partners",
  },
  description: siteDescription,
  applicationName: "Alliance AI Partners",
  // Closed to search engines until launch; see lib/site-url.ts.
  robots: allowIndexing ? { index: true, follow: true } : { index: false, follow: false },
  openGraph: { type: "website", siteName: "Alliance AI Partners", locale: "en_US" },
  twitter: { card: "summary" },
  icons: {
    icon: [
      { url: faviconIco.src, sizes: "32x32" },
      { url: faviconSvg.src, type: "image/svg+xml" },
    ],
    apple: [{ url: appleTouchIcon.src, sizes: "180x180" }],
  },
};

export const viewport: Viewport = {
  // The page ground, Daylight, so the browser's own bars match the header.
  themeColor: "#F4F7FB",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // The font classes define --font-mona-sans and --font-mona-sans-mono, which the design tokens point at.
    <html lang="en" className={`${monaSans.variable} ${monaSansMono.variable}`}>
      <body>
        <NavigationProgress />
        <a href="#main" className="aap-skip-link">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main">{children}</main>
        <SiteFooter />
        <ScrollEffects />
      </body>
    </html>
  );
}
