import type { Metadata, Viewport } from "next";
import { monaSans, monaSansMono } from "@/app/fonts";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import appleTouchIcon from "@/design-system/logos/app-icons/apple-touch-icon.png";
import faviconIco from "@/design-system/logos/app-icons/favicon.ico";
import faviconSvg from "@/design-system/logos/app-icons/favicon.svg";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Alliance AI Partners | Put AI to work",
    template: "%s | Alliance AI Partners",
  },
  description:
    "An embedded AI team in the Philippines for companies in the US, Australia and the UK. We build the AI tools and software you need, then help you grow. Published starting prices.",
  applicationName: "Alliance AI Partners",
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
        <a href="#main" className="aap-skip-link">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
