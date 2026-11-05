import { ArrowLink } from "@/components/arrow-link";
import { SectionHead } from "@/components/section-head";
import { ServiceIcon, type ServiceIconName } from "@/components/service-icon";
import { cn } from "@/lib/cn";

const ranked = [
  { n: 1, task: "Order entry from email", saving: "Saves [hours a week]" },
  { n: 2, task: "Matching supplier invoices", saving: "Saves [hours a week]" },
  { n: 3, task: "Repeat customer questions", saving: "Saves [hours a week]" },
];

const smallCards: { icon: ServiceIconName; title: string; text: string }[] = [
  {
    icon: "launch",
    title: "A fixed quote for the first fix",
    text: "One price for the fix we recommend first, listing everything it includes. Changes are quoted before we do them.",
  },
  {
    icon: "advisory",
    title: "Honest advice when AI is not the answer",
    text: "If a simpler fix or a tool you already pay for would do the job, we say so, even when it means less work for us.",
  },
];

/**
 * AI check-up: the three things you keep (Figma: Section · What you get). From 1024px a bento: the written plan card
 * with a preview of the sample report on the left, two cards stacked on the right, sharing its height.
 */
export function WhatYouGet() {
  return (
    <section aria-labelledby="get-title" className="aap-section">
      <div className="aap-container flex flex-col gap-8 lg:gap-12">
        <SectionHead
          id="get-title"
          title={
            <>
              A plan, a price
              <br className="hidden lg:inline" /> and a straight answer.
            </>
          }
          lead="At the end of the check-up you get three things, in writing. They are yours to keep, whatever you decide next."
        />

        <div className="grid gap-4 lg:grid-cols-2 lg:gap-6" data-reveal-group>
          <article className="aap-card flex flex-col gap-0 overflow-hidden p-0" data-reveal-item>
            <ReportPreview />
            <div className="flex flex-col gap-3 px-6 pt-5 pb-6 lg:p-8">
              <h3 className="aap-h3">A written plan, ranked by what it saves</h3>
              <p className="text-body text-ink-secondary">
                Every opportunity we found, ordered by the time or money it would save and the work it would take, with
                the fix we recommend for each.
              </p>
              <ArrowLink href="/ai-check-up/sample" className="self-start lg:mt-2">
                Read a sample report
              </ArrowLink>
            </div>
          </article>

          <div className="flex flex-col gap-4 lg:gap-6">
            {smallCards.map((card) => (
              <article
                key={card.title}
                className="aap-card flex flex-col gap-3 p-6 lg:flex-1 lg:gap-4 lg:p-8"
                data-reveal-item
              >
                <ServiceIcon name={card.icon} className="size-8 lg:size-10" />
                <h3 className="aap-h3">{card.title}</h3>
                <p className="text-body text-ink-secondary">{card.text}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/**
 * A page of the sample report in a sunken well (Figma: Well · Sample report preview). From 1024px the page is 536px
 * wide and runs past the well's foot, which clips it; on phones it is narrower, rounded at the top only, and each
 * row's saving moves under its task. Decorative: the real sample report is one link away.
 */
function ReportPreview() {
  return (
    <div
      aria-hidden="true"
      className="flex h-[432px] flex-col overflow-hidden bg-sunken px-4 pt-6 lg:h-[340px] lg:items-center lg:px-14 lg:pt-10"
    >
      <div className="flex w-full shrink-0 flex-col gap-3 rounded-t-md border border-line-subtle bg-raised px-4 pt-4 pb-2 shadow-md lg:max-w-[536px] lg:gap-4 lg:rounded-md lg:px-8 lg:py-7">
        <div className="flex flex-col items-start gap-3 lg:flex-row lg:items-center">
          <span className="aap-tag">Sample report</span>
          <span className="aap-mono text-ink-secondary lg:flex-1 lg:text-right">AI check-up · [Partner name]</span>
        </div>
        <p className="aap-h4">Where AI could save [Partner name] time</p>
        <ol className="border-t border-line">
          {ranked.map((row) => (
            <li
              key={row.n}
              className={cn(
                "flex items-start gap-3 border-b border-line px-2 py-2.5 lg:items-center lg:px-3",
                row.n === 1 && "bg-ribbon-cyan/10",
              )}
            >
              <span className="aap-mono w-4 shrink-0 text-ink-secondary">{row.n}</span>
              <span className="flex flex-1 flex-col gap-0.5 lg:flex-row lg:items-center lg:gap-3">
                <span className="text-body-sm lg:flex-1">{row.task}</span>
                <span className="aap-mono text-ink-secondary lg:text-ink">{row.saving}</span>
              </span>
            </li>
          ))}
        </ol>
        <div className="flex items-center gap-3 px-2 py-3 lg:px-3 lg:pt-1 lg:pb-0">
          <span className="flex-1 text-body-sm text-ink-secondary">Fixed quote for the first fix</span>
          <span className="aap-mono">[PRICE]</span>
        </div>
      </div>
    </div>
  );
}
