import { ArrowLink } from "@/components/arrow-link";
import { SectionHead } from "@/components/home/section-head";
import { cn } from "@/lib/cn";

/* Monthly cost of one full-time software developer to an employer, from the Brand DNA cost comparison. Each figure
   keys to a numbered source below it, with the date it was retrieved. */
const stats = [
  {
    value: "US$16,400",
    text: "A month in the United States: median pay of US$135,980 a year, plus benefits.",
  },
  {
    value: "£5,800",
    text: "A month in the United Kingdom: median pay of £59,863 a year, plus National Insurance and pension.",
  },
  {
    value: "A$12,300",
    text: "A month in Australia: median pay of about A$131,900 a year, plus superannuation.",
  },
];

const sources = [
  {
    desktop:
      "U.S. Bureau of Labor Statistics, software developers, median pay, May 2025; benefits are 30.8% of compensation for professional workers (June 2026). Retrieved 2026-11-02.",
    phone:
      "U.S. Bureau of Labor Statistics, software developers, median pay, May 2025; benefits 30.8% of compensation, professional workers (June 2026). Retrieved 2026-11-02.",
  },
  {
    desktop:
      "Office for National Statistics, Annual Survey of Hours and Earnings 2026 (provisional); employer National Insurance and pension at 2026-27 rates. Retrieved 2026-11-02.",
    phone:
      "Office for National Statistics, ASHE 2026 (provisional); employer National Insurance and pension, 2026-27 rates. Retrieved 2026-11-02.",
  },
  {
    desktop:
      "Jobs and Skills Australia, software and applications programmers (ABS data, May 2025); superannuation guarantee 12%. Retrieved 2026-11-02.",
    phone:
      "Jobs and Skills Australia, software and applications programmers (ABS, May 2025); super guarantee 12%. Retrieved 2026-11-02.",
  },
];

/** Home: what a developer costs to hire against our monthly price (Figma: Section · Cost of hiring). */
export function CostOfHiring() {
  return (
    <section aria-labelledby="cost-title" className="aap-section">
      <div className="aap-container flex flex-col gap-6 lg:gap-12">
        <SectionHead
          id="cost-title"
          title={
            <>
              The AI team you
              <br className="hidden lg:inline" /> don’t have to <span className="aap-accent">hire.</span>
            </>
          }
          lead="Roughly what one full-time software developer costs an employer each month, before recruiting, equipment and office space."
        />

        <ul className="grid lg:grid-cols-3 lg:border-y lg:border-line" data-reveal-group>
          {stats.map((stat, index) => (
            <li
              key={stat.value}
              data-reveal-item
              className={cn(
                "flex flex-col gap-2 border-t border-line py-6 lg:border-t-0 lg:p-8",
                index > 0 && "lg:border-l",
              )}
            >
              <p className="flex items-start gap-1">
                <span className="aap-numeral">{stat.value}</span>
                <a
                  href={`#cost-source-${index + 1}`}
                  aria-label={`Source ${index + 1}`}
                  className="inline-grid h-5 min-w-5 place-items-center rounded-sm border border-line px-[3px] font-mono text-[0.75rem] leading-none text-ink-secondary no-underline"
                >
                  {index + 1}
                </a>
              </p>
              <p className="text-body-sm text-ink-secondary">{stat.text}</p>
            </li>
          ))}
        </ul>

        <div
          className="aap-card flex flex-col gap-3 p-6 lg:flex-row lg:items-center lg:justify-between lg:gap-6 lg:p-8"
          data-reveal-group
          data-reveal-item
        >
          <div className="flex flex-col gap-3 lg:gap-2">
            <p className="aap-numeral">[PRICE]</p>
            <p className="max-w-[600px] text-body text-ink-secondary">
              A month for a full-time embedded developer from Alliance AI Partners.
              <br className="hidden lg:inline" /> You don’t pay for recruiting, benefits or equipment.
            </p>
          </div>
          <ArrowLink href="/compare" className="self-start lg:self-center">
            Compare the full costs
          </ArrowLink>
        </div>

        <ol className="aap-sources">
          {sources.map((source, index) => (
            <li key={index} id={`cost-source-${index + 1}`}>
              <span className="lg:hidden">{source.phone}</span>
              <span className="hidden lg:inline">{source.desktop}</span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
