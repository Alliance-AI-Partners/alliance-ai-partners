import Image from "next/image";
import Link from "@/components/site-link";
import { Icon } from "@/components/icon";
import dawnWave from "@/design-system/imagery/backgrounds/dawn-wave.jpg";
import { contactEmail, primaryAction } from "@/lib/site";

/** Home: the closing band that leads to the AI check-up (Figma: Section · Closing CTA, IMG-01-5). */
export function ClosingCta() {
  return (
    <section
      aria-labelledby="cta-title"
      className="aap-surface-inverse relative isolate flex min-h-[680px] overflow-hidden lg:min-h-[600px] lg:items-center"
    >
      {/* The parallax layer reaches 24px past the band at the top and bottom, so it can drift without showing an edge. */}
      <div data-parallax aria-hidden="true" className="absolute inset-x-0 -top-6 -bottom-6 -z-20">
        <Image src={dawnWave} alt="" fill sizes="100vw" className="object-cover" />
      </div>
      <div aria-hidden="true" className="home-scrim-cta absolute inset-0 -z-10" />

      <div className="aap-container flex flex-col gap-6 py-16 lg:gap-7">
        <h2 id="cta-title" className="aap-display-lg max-w-[820px]">
          Not sure where to start? Start with a <span className="aap-accent">check-up.</span>
        </h2>
        <p className="max-w-[620px] text-body-lg text-ink-secondary">
          The AI check-up is a short first project. We{" "}
          <span className="hidden lg:inline">learn how your business works, </span>find where AI could save you time
          or money<span className="hidden lg:inline">,</span> and hand you a plan with a fixed quote. You decide what
          happens next.
        </p>
        <div className="flex flex-col items-start gap-6 lg:flex-row lg:items-center">
          <Link
            href={primaryAction.href}
            className="aap-button aap-button--primary aap-button--lg w-full lg:w-auto"
          >
            {primaryAction.label}
            <Icon name="arrow-right" />
          </Link>
          <p className="text-body-sm lg:text-body">
            Or email <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
          </p>
        </div>
      </div>
    </section>
  );
}
