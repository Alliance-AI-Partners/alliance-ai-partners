import { getImageProps } from "next/image";
import Link from "@/components/site-link";
import type { CSSProperties, ReactNode } from "react";
import { Icon } from "@/components/icon";
import { SectionHead } from "@/components/home/section-head";
import invoiceDesktop from "@/brand-kit/emails/previews/invoice-ready-desktop.png";
import invoiceMobile from "@/brand-kit/emails/previews/invoice-ready-mobile.png";

/** Short and long wording where Figma words a line differently on phones and from 1024px. */
function ByWidth({ phone, desktop }: { phone: ReactNode; desktop: ReactNode }) {
  return (
    <>
      <span className="lg:hidden">{phone}</span>
      <span className="hidden lg:inline">{desktop}</span>
    </>
  );
}

const promises: { id: string; text: ReactNode }[] = [
  { id: "published", text: "Published starting prices for every core service." },
  {
    id: "fixed-quote",
    text: (
      <>
        A fixed quote before work starts. Changes are quoted <ByWidth phone="first" desktop="before we do them" />.
      </>
    ),
  },
  { id: "no-seat-fees", text: "No per-seat fees on the tools we build." },
  {
    id: "ai-at-cost",
    text: (
      <>
        AI usage passed on at cost
        <ByWidth phone="," desktop=" and" /> shown on your invoice.
      </>
    ),
  },
  {
    id: "cancel",
    text: (
      <ByWidth
        phone="Cancel monthly plans with [30] days’ notice."
        desktop="Monthly plans you can cancel with [30] days’ notice."
      />
    ),
  },
  { id: "ownership", text: "You own what we build." },
  { id: "cheaper-option", text: "If an off-the-shelf tool or a simpler fix costs you less, we say so." },
];

const startingPrices = [
  {
    title: "Websites and web apps",
    text: "A fast, accessible site or web app, built and kept running.",
    price: "From [PRICE]",
    href: "/services/websites",
  },
  {
    title: "The AI check-up",
    text: "A short first project that finds where AI could save you time or money.",
    price: "From [PRICE]",
    href: "/ai-check-up",
  },
  {
    title: "AI automation",
    text: "One slow process handled by AI and checked by a person.",
    price: "From [PRICE] a project",
    href: "/services/ai-automation",
  },
  {
    title: "Embedded developers",
    text: "A developer from our team works inside yours, full time.",
    price: "From [PRICE] a month",
    href: "/services/embedded-developers",
  },
];

/** Home: honest pricing, a Partner Navy chapter (Figma: Section · Honest pricing). */
export function HonestPricing() {
  return (
    <section aria-labelledby="pricing-title" className="aap-section aap-surface-inverse">
      <div className="aap-container flex flex-col gap-8 lg:gap-12">
        <SectionHead
          id="pricing-title"
          titleClassName="aap-h1"
          title={
            <>
              Honest prices, <span className="aap-accent">published</span> up front.
            </>
          }
          lead="You see what things cost before you talk to us. Then you get a fixed quote that lists everything we’ll charge."
        />

        <div className="grid gap-8 lg:grid-cols-[minmax(0,560fr)_minmax(0,696fr)] lg:items-start lg:gap-16">
          <ul
            className="border-t border-line lg:border-t-0"
            data-reveal-group
            style={{ "--reveal-stagger": "40ms" } as CSSProperties}
          >
            {promises.map((promise) => (
              <li
                key={promise.id}
                className="flex items-start gap-3 border-b border-line py-3.5 lg:gap-4 lg:py-4"
                data-reveal-item
              >
                <Icon name="check" className="size-5 shrink-0 text-ribbon-cyan" />
                <span className="text-body">{promise.text}</span>
              </li>
            ))}
          </ul>

          <div>
            <ul data-reveal-group>
              {startingPrices.map((row) => (
                <li key={row.title} data-reveal-item>
                  <Link
                    href={row.href}
                    className="group flex flex-col gap-2 border-b border-line py-5 text-ink no-underline lg:flex-row lg:items-center lg:gap-8 lg:py-6"
                  >
                    <div className="flex flex-col gap-2 lg:flex-1 lg:gap-1">
                      <h3 className="aap-h4">{row.title}</h3>
                      <p className="text-body-sm text-ink-secondary lg:max-w-[504px]">{row.text}</p>
                    </div>
                    <div className="flex items-center justify-between gap-4 lg:justify-start">
                      <span className="aap-mono">{row.price}</span>
                      <Icon
                        name="arrow-right"
                        className="size-5 shrink-0 transition-transform duration-(--aap-duration-base) ease-spring group-hover:translate-x-[3px] motion-reduce:group-hover:translate-x-0"
                      />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
            <div className="pt-8">
              <Link
                href="/pricing"
                className="aap-button aap-button--lg w-full lg:min-h-11 lg:w-auto lg:px-5 lg:text-[0.875rem]"
              >
                See all prices
                <Icon name="arrow-right" />
              </Link>
            </div>
          </div>
        </div>

        <figure className="flex flex-col gap-8 lg:gap-4" data-reveal-group data-reveal-item>
          <SampleInvoice />
          <figcaption className="text-caption text-ink-secondary">
            Sample invoice from our templates. AI usage is passed on at cost, on its own line.
          </figcaption>
        </figure>
      </div>
    </section>
  );
}

/**
 * The sample invoice from the email templates, anchored to its top: the desktop render from 1024px, the narrow
 * render on phones (Figma: IMG-01-3). Different files per width, so it uses <picture> with next/image's props.
 */
function SampleInvoice() {
  const common = {
    alt: "Sample invoice with AI usage on its own line, passed on at cost.",
    sizes: "(min-width: 1440px) 1320px, 92vw",
  };
  const {
    props: { srcSet: desktopSrcSet },
  } = getImageProps({ ...common, src: invoiceDesktop });
  const {
    props: { srcSet: mobileSrcSet, ...imgProps },
  } = getImageProps({ ...common, src: invoiceMobile });

  return (
    <div className="aap-media relative aspect-[358/560] lg:aspect-[1320/520]">
      <picture className="block size-full">
        <source media="(min-width: 1024px)" srcSet={desktopSrcSet} sizes={common.sizes} />
        <img {...imgProps} srcSet={mobileSrcSet} alt={common.alt} className="size-full object-cover object-top" />
      </picture>
    </div>
  );
}
