import { ArrowLink } from "@/components/arrow-link";
import { IconRows, StepMarker, type IconRow } from "@/components/blocks/icon-rows";
import { SectionHead } from "@/components/section-head";

const phases: { n: number; title: string; text: string; rows: IconRow[] }[] = [
  {
    n: 1,
    title: "Understand",
    text: "We learn how your business works and where it gets stuck.",
    rows: [
      {
        icon: "research-insights",
        title: "Interviews with your team",
        text: "We talk with the people who do the work, not only the managers, and repeat the problem back in their words.",
      },
      {
        icon: "cloud-integration",
        title: "A walk through your tools",
        text: "Your CRM, help desk, accounting software and spreadsheets: what each one does, and where work gets typed twice.",
      },
      {
        icon: "automation",
        title: "Your slowest processes, start to finish",
        text: "We follow each slow, manual step and note how long it takes and who it waits on.",
      },
    ],
  },
  {
    n: 2,
    title: "Plan",
    text: "We pick the right fix. Sometimes it does not involve AI at all.",
    rows: [
      {
        icon: "data-analytics",
        title: "Each opportunity, weighed",
        text: "We estimate the time or money each fix would save, from your own records where you have them, and the work it would take.",
      },
      {
        icon: "ai-strategy",
        title: "The simplest fix first",
        text: "AI, automation, better design or a tool you already pay for. We recommend the one that does the job.",
      },
      {
        icon: "partnership",
        title: "Checked with your team",
        text: "We walk you through what we found before we write it up, so nothing in the plan is a surprise.",
      },
    ],
  },
];

/**
 * AI check-up: the first two of the four steps, and what comes after (Figma: Section · What we look at). From 1024px a
 * rail runs over three columns (520, 520, 232): the ribbon rule over the two steps the check-up covers, with their
 * numbered markers, and a hairline over "After the check-up". On phones each step carries its own marker and rule.
 */
export function WhatWeLookAt() {
  return (
    <section aria-labelledby="look-title" className="aap-section">
      <div className="aap-container flex flex-col gap-10 lg:gap-12">
        <SectionHead
          id="look-title"
          title={
            <>
              We listen first,
              <br className="lg:hidden" /> then we <span className="aap-accent">plan.</span>
            </>
          }
          lead="The check-up covers the first two of our four steps. Building the fix is a separate decision, and the plan is yours either way."
        />

        <div className="flex flex-col gap-10 lg:grid lg:grid-cols-[minmax(0,520fr)_minmax(0,520fr)_minmax(0,232fr)] lg:gap-x-6 lg:gap-y-7">
          {/* The rail, from 1024px: the ribbon spans the first two columns and the gap between them. */}
          <div aria-hidden="true" className="hidden lg:col-span-3 lg:grid lg:grid-cols-subgrid lg:items-center">
            <span className="aap-ribbon-rule col-span-2 col-start-1 row-start-1 block" />
            <span className="col-start-3 row-start-1 -ml-6 block h-px bg-line" />
            <StepMarker n={1} className="relative col-start-1 row-start-1" />
            <StepMarker n={2} className="relative col-start-2 row-start-1" />
          </div>

          {phases.map((phase) => (
            <div key={phase.title} className="flex flex-col gap-3 lg:gap-6">
              <div aria-hidden="true" className="flex items-center gap-2 lg:hidden">
                <StepMarker n={phase.n} />
                <span className="aap-ribbon-rule block flex-1" />
              </div>
              <div className="flex flex-col gap-3 lg:gap-2">
                <h3 className="aap-h3">
                  <span className="sr-only">Step {phase.n}: </span>
                  {phase.title}
                </h3>
                <p className="text-body text-ink-secondary">{phase.text}</p>
              </div>
              <IconRows rows={phase.rows} headingLevel="h4" className="lg:border-t lg:border-line" />
            </div>
          ))}

          <div className="flex flex-col gap-2 lg:gap-6">
            <div className="flex flex-col gap-2">
              <h3 className="aap-h4 lg:text-ink-secondary">After the check-up</h3>
              <p className="text-body-sm text-ink-secondary">
                If you want us to build the first fix, you already have its fixed price. You can also take the plan to
                your own team, or to anyone else.
              </p>
            </div>
            <ArrowLink href="/how-we-work" className="self-start lg:text-body-sm">
              See how we work
            </ArrowLink>
          </div>
        </div>
      </div>
    </section>
  );
}
