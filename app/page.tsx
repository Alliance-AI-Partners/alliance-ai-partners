import type { Metadata } from "next";
import { ClosingCta } from "@/components/home/closing-cta";
import { CostOfHiring } from "@/components/home/cost-of-hiring";
import { Goals } from "@/components/home/goals";
import { HonestPricing } from "@/components/home/honest-pricing";
import { Hero } from "@/components/home/hero";
import { HowWeWork } from "@/components/home/how-we-work";
import { OvernightBand } from "@/components/home/overnight-band";
import { Pitch } from "@/components/home/pitch";
import { Questions } from "@/components/home/questions";
import { TimeZones } from "@/components/home/time-zones";
import { siteDescription, siteTitle } from "@/lib/site";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "Alliance AI Partners",
    locale: "en_US",
    url: "/",
    title: siteTitle,
    description: siteDescription,
  },
  twitter: { card: "summary", title: siteTitle, description: siteDescription },
};

/**
 * Home (Figma: 01 · Home, frames Home — Desktop 26:186 and Home — Mobile 30:420; record:
 * docs/website/pages/home.json). The title and description are the site defaults (lib/site.ts).
 */
export default function HomePage() {
  return (
    <>
      <Hero />
      <Pitch />
      <Goals />
      <HowWeWork />
      <HonestPricing />
      <CostOfHiring />
      <OvernightBand />
      <TimeZones />
      <Questions />
      <ClosingCta />
    </>
  );
}
