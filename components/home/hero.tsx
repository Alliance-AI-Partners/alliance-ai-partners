import Link from "@/components/site-link";
import type { CSSProperties } from "react";
import { Icon } from "@/components/icon";
import { Ribbon } from "@/components/ribbon";
import { primaryAction } from "@/lib/site";

/** The order of a line in the hero entrance (plans/005): each starts 60ms after the one before. */
const rise = (index: number) => ({ "--rise-index": index }) as CSSProperties;

/**
 * Home hero (Figma: Section · Hero). From 1024px the headline holds the left column, with the base line at its foot,
 * and the introduction sits 96px lower in the right column, under the ribbon that leaves the headline's full stop.
 * Below 1024px it stacks in reading order: headline, introduction, actions, base line.
 */
export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="overflow-x-clip pt-(--home-hero-padding-top) pb-section">
      <div className="aap-container grid gap-7 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)] lg:gap-x-16 lg:gap-y-0">
        <h1 id="hero-title" className="aap-display-xl">
          Put AI
          <br />
          to <span className="aap-accent">work.</span>
          <HeroRibbon />
        </h1>

        <div className="flex flex-col gap-7 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:gap-8 lg:pt-24">
          <p className="home-hero-rise max-w-[560px] text-body-lg text-ink-secondary" style={rise(0)}>
            <span className="text-ink">Alliance AI Partners is the AI team that works inside yours.</span> We find
            where AI will save you time or money, build it, and keep it running, so you get more done without wearing
            out your people.
          </p>
          <div className="home-hero-rise flex flex-col items-center gap-4 lg:flex-row lg:gap-6" style={rise(1)}>
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
        </div>

        <p
          className="home-hero-rise max-w-[480px] text-caption text-ink-tertiary lg:col-start-1 lg:row-start-2 lg:self-end"
          style={rise(2)}
        >
          Based in the Philippines. Working with teams in the United States, Australia and the United Kingdom.
        </p>
      </div>
    </section>
  );
}

/**
 * The ribbon (Figma: Ribbon (line form)) leaves the headline's full stop, arcs over the introduction and runs off the
 * right edge, where the section clips it. It hangs from a zero-size anchor on the baseline after "work." and is sized
 * in em, so it starts at the full stop at every width. Both paths are the Figma vectors at the 92px headline, plus a
 * tail for wide screens, so the SVG is never drawn larger than its viewBox (the design system's draw-on dash only
 * covers the whole line at or below that size). x2 is where the Figma line meets the frame edge, so the gradient
 * reaches Ribbon Cyan there and the tail stays cyan.
 */
function HeroRibbon() {
  return (
    <span aria-hidden="true" className="relative inline-block size-0">
      <Ribbon
        id="hero-ribbon-desktop"
        className="home-hero-ribbon absolute bottom-0 left-[0.2391em] hidden h-[2.2196em] w-[17.7826em] lg:block"
        viewBox="0 0 1636 204.2"
        d="M0 204.2C98 204.2 238 34 538 20C738 10 884 80 1028 46C1172 12 1356 0 1636 0"
        x1={0}
        x2={1028}
      />
      <Ribbon
        id="hero-ribbon-mobile"
        className="home-hero-ribbon absolute bottom-0 left-[0.25em] h-[1.5346em] w-[10.1875em] lg:hidden"
        viewBox="0 0 937.25 141.18"
        d="M0 141.18C76.67 141.18 172.5 7.86 385.25 12.36C515.58 15.14 707.25 3.83 937.25 0"
        x1={0}
        x2={385.25}
        strokeWidth={2.5}
      />
    </span>
  );
}
