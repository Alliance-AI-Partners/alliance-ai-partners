import Image from "next/image";
import { ArrowLink } from "@/components/arrow-link";
import { ButtonLink } from "@/components/button-link";
import threePaths from "@/design-system/imagery/website/IMG-02-1.jpg";

const facts = [
  { value: "From [PRICE]", caption: "The whole check-up, at a fixed price" },
  { value: "[two weeks]", caption: "From the first call to your written plan" },
];

/**
 * AI check-up hero (Figma: Section · Hero, IMG-02-1). From 1024px the text (1.08fr) sits beside the image; the facts
 * come before the actions. On phones the actions come first, the facts follow as stacked rows, then the image at 4:5.
 */
export function Hero() {
  return (
    <section aria-labelledby="hero-title" className="pt-(--site-hero-padding-top) pb-section">
      <div className="aap-container grid items-center gap-7 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)] lg:gap-16">
        <div className="flex flex-col gap-7 lg:gap-8">
          <div className="flex flex-col gap-5 lg:contents">
            <h1 id="hero-title" className="aap-display-xl">
              Start where AI saves the <span className="aap-accent">most.</span>
            </h1>
            <p className="text-body-lg text-ink-secondary lg:max-w-[600px]">
              The AI check-up is our usual first project. We learn how your team works, find where AI could save you
              time or money, and hand you a written plan with a fixed quote for the first fix.
            </p>
          </div>

          <dl className="order-2 grid border-t border-line lg:order-1 lg:max-w-[600px] lg:grid-cols-2 lg:border-b">
            {facts.map((fact, index) => (
              <div
                key={fact.value}
                className={
                  index === 0
                    ? "flex flex-col gap-1 border-b border-line py-4 lg:border-b-0 lg:py-5 lg:pr-6"
                    : "flex flex-col gap-1 border-b border-line py-4 lg:border-b-0 lg:border-l lg:py-5 lg:pl-6"
                }
              >
                <dt className="sr-only">{index === 0 ? "Price" : "Time"}</dt>
                <dd className="site-mono-clock">{fact.value}</dd>
                <dd className="text-body-sm text-ink-secondary">{fact.caption}</dd>
              </div>
            ))}
          </dl>

          <div className="order-1 flex flex-col items-center gap-4 lg:order-2 lg:flex-row lg:gap-6">
            <ButtonLink href="#book" variant="primary" size="lg" className="w-full lg:w-auto">
              Book your AI check-up
            </ButtonLink>
            <ArrowLink href="/ai-check-up/sample">Read a sample report</ArrowLink>
          </div>
        </div>

        <div className="aap-media relative aspect-[358/448] lg:aspect-[604/600]">
          <Image
            src={threePaths}
            alt="A ribbon path splits into three; the shortest branch ends at a young sapling."
            fill
            loading="eager"
            sizes="(min-width: 1024px) 42vw, 100vw"
            className="object-cover"
          />
        </div>
      </div>
    </section>
  );
}
