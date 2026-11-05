import Image from "next/image";
import Link from "next/link";
import { Icon } from "@/components/icon";
import { Ribbon } from "@/components/ribbon";
import logomark from "@/design-system/logos/marks/alliance-ai-partners-logomark-full-color-light.svg";
import { primaryAction } from "@/lib/site";

const baseLine = "Based in the Philippines. Working inside teams in the United States, Australia and the United Kingdom.";

/** Home hero (Figma: Section · Hero). Text and the 3D mark side by side from 1024px; stacked below. */
export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="pt-(--site-hero-padding-top) pb-section">
      <div className="aap-container grid items-center gap-7 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)] lg:gap-16">
        <div className="flex flex-col gap-7 lg:gap-8">
          <h1 id="hero-title" className="aap-display-xl">
            Put AI to <span className="aap-accent">work.</span>
          </h1>
          <p className="max-w-[560px] text-body-lg text-ink-secondary">
            We build the AI tools and software your business needs, then help you use them to grow.
          </p>
          <div className="flex flex-col items-center gap-4 lg:flex-row lg:gap-6">
            <Link
              href={primaryAction.href}
              className="aap-button aap-button--primary aap-button--lg w-full lg:w-auto"
            >
              {primaryAction.label}
              <Icon name="arrow-right" />
            </Link>
            <Link href="/pricing" className="aap-link aap-link--standalone">
              Read the price list
              <Icon name="arrow-right" />
            </Link>
          </div>
          <p className="hidden max-w-[480px] text-caption text-ink-tertiary lg:block">{baseLine}</p>
        </div>

        <HeroObject />

        {/* On phones the base line follows the mark. */}
        <p className="text-caption text-ink-tertiary lg:hidden">{baseLine}</p>
      </div>
    </section>
  );
}

/**
 * The 3D mark with the ribbon arcing over it. Positions are the Figma frame's, as percentages of the object box
 * (desktop 604 x 520, mobile 358 x 260), so the drawing keeps its proportions at every width. Neither box grows past
 * its Figma size (the desktop column tops out at 604px inside the 1320px container).
 */
function HeroObject() {
  return (
    <>
      <div className="relative hidden aspect-[604/520] lg:block">
        <Image
          src={logomark}
          alt=""
          loading="eager"
          className="home-hero-mark absolute top-[23.0769%] left-[15.2318%] h-[57.6923%] w-[72.2695%]"
        />
        <Ribbon
          id="hero-ribbon-desktop"
          className="home-hero-ribbon absolute top-[7.6923%] left-0 h-[77.0613%] w-full"
          viewBox="1.5 1.5 604 400.719"
          d="M1.5 402.219C91.5 402.219 121.5 28.2188 301.5 4.21882C471.5 -17.7812 561.5 102.219 605.5 60.2188"
          x1={1.5}
          x2={605.5}
        />
      </div>

      {/* Never wider than the Figma object (358px): the ribbon keeps a fixed stroke width, and the design system's
          draw-on dash only covers the whole line while the SVG is drawn at or below its viewBox size. */}
      <div className="relative mx-auto aspect-[358/260] w-full max-w-[358px] lg:hidden">
        <Image
          src={logomark}
          alt=""
          loading="eager"
          className="home-hero-mark absolute top-[23.0769%] left-[15.3631%] h-[65.3846%] w-[69.0933%]"
        />
        <Ribbon
          id="hero-ribbon-mobile"
          className="home-hero-ribbon absolute top-[3.8462%] left-0 h-[75.5431%] w-full"
          viewBox="1.25 1.25 358 196.412"
          d="M1.25 197.662C51.25 197.662 71.25 7.66154 181.25 1.66154C281.25 -4.33846 331.25 57.6615 359.25 31.6615"
          x1={1.25}
          x2={359.25}
          strokeWidth={2.5}
        />
      </div>
    </>
  );
}
