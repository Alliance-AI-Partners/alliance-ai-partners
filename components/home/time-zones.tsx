import { SectionHead } from "@/components/home/section-head";
import { LiveTimeZones } from "@/components/home/live-time-zones";

const sources = [
  {
    desktop: "NSW Government, Daylight saving (Sydney is UTC+10, or UTC+11 in daylight saving). Retrieved 2026-11-02.",
    phone: "NSW Government, Daylight saving. Retrieved 2026-11-02.",
  },
  {
    desktop: "NIST, Local time FAQs (US time zones and daylight saving). Retrieved 2026-11-02.",
    phone: "NIST, Local time FAQs. Retrieved 2026-11-02.",
  },
];

/** Home: our day next to yours, with live clocks (Figma: Section · Time zones). */
export function TimeZones() {
  return (
    <section aria-labelledby="zones-title" className="aap-section">
      <div className="aap-container flex flex-col gap-6 lg:gap-10">
        <SectionHead
          id="zones-title"
          title={
            <>
              Our day, next to <span className="aap-accent">yours.</span>
            </>
          }
          lead="Sydney is two hours ahead of us, or three during Australian daylight saving. The US is 12 to 16 hours behind, and the UK is seven or eight."
        />
        <LiveTimeZones />
        <ol className="aap-sources">
          {sources.map((source, index) => (
            <li key={index} id={`zones-source-${index + 1}`}>
              <span className="lg:hidden">{source.phone}</span>
              <span className="hidden lg:inline">{source.desktop}</span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
