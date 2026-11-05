import { ArrowLink } from "@/components/arrow-link";
import { SectionHead } from "@/components/section-head";

const steps = [
  { title: "Understand", text: "We learn how your business works and where it gets stuck." },
  { title: "Plan", text: "We pick the right fix. Sometimes it doesn’t involve AI at all." },
  { title: "Build", text: "Our engineers and designers build it, on our own or inside your team." },
  { title: "Run and grow", text: "We keep it working, improve it over time, and help you win more customers." },
];

/** Home: the four steps (Figma: Section · How we work), on the design system's ribbon-threaded steps. */
export function HowWeWork() {
  return (
    <section aria-labelledby="how-title" className="aap-section">
      <div className="aap-container flex flex-col gap-10 lg:gap-12">
        <SectionHead
          id="how-title"
          title={
            <>
              We build it, run it,
              <br /> and help you <span className="aap-accent">grow.</span>
            </>
          }
          lead={
            <>
              Four steps, and the last one doesn’t stop at launch.
              <span className="hidden lg:inline"> You see progress every week, and a person reviews every piece of work.</span>
            </>
          }
        />
        <ol className="aap-steps" data-reveal-group>
          {steps.map((step) => (
            <li key={step.title} data-reveal-item>
              <h3 className="aap-steps__title">{step.title}</h3>
              <p className="aap-steps__text">{step.text}</p>
            </li>
          ))}
        </ol>
        <ArrowLink href="/how-we-work" className="self-start">
          See how we work
        </ArrowLink>
      </div>
    </section>
  );
}
