import type { CSSProperties } from "react";
import { ArrowLink } from "@/components/arrow-link";
import { Icon } from "@/components/icon";

/* The four questions buyers ask first. The first answer is the Figma copy; the others are the approved answers on the
   Questions buyers ask page (docs/website/pages/questions-buyers-ask.json). The outsourcing answer stops before its
   sourced sentence about the Data Privacy Act, which is cited on that page; the link below leads there. */
const questions = [
  {
    question: "Does cheaper mean lower quality?",
    answer: "AI takes over the repetitive hours, and a person still reviews every piece of work before it reaches you.",
  },
  {
    question: "Where is your team?",
    answer:
      "In the Philippines. Sydney is two hours ahead of us, or three during Australian daylight saving. For US partners, we work while you sleep: brief us before you log off, and you’ll see progress when you log on. For UK partners, our afternoon is your morning.",
  },
  {
    question: "Isn’t outsourcing risky?",
    answer:
      "You see progress every week, a person reviews every piece of work, and your data stays in your systems wherever possible.",
  },
  {
    question: "What happens to our data?",
    answer:
      "We work inside your systems wherever we can, take only the access a job needs, and never use your data to train anything you don’t own.",
  },
];

/** Home: questions buyers ask (Figma: Section · Questions). Native <details>, so they work without JavaScript. */
export function Questions() {
  return (
    <section aria-labelledby="questions-title" className="aap-section">
      <div className="aap-container grid gap-6 lg:grid-cols-[minmax(0,440fr)_minmax(0,800fr)] lg:items-start lg:gap-20">
        <div className="flex flex-col gap-6">
          <h2 id="questions-title" className="aap-h2">
            Questions buyers ask
          </h2>
          <p className="text-body text-ink-secondary">
            Straight answers to what founders ask us first.
            <span className="hidden lg:inline"> If yours isn’t here, ask us directly.</span>
          </p>
          <ArrowLink href="/faq" className="hidden self-start lg:inline-flex">
            Read all the questions
          </ArrowLink>
        </div>

        <div
          className="border-t border-line"
          data-reveal-group
          style={{ "--reveal-stagger": "40ms" } as CSSProperties}
        >
          {questions.map((item, index) => (
            <details key={item.question} className="aap-accordion" open={index === 0} data-reveal-item>
              <summary>
                <h3>{item.question}</h3>
                <span className="site-accordion-icon">
                  <Icon name="plus" className="site-icon-closed" />
                  <Icon name="close" className="site-icon-open" />
                </span>
              </summary>
              <div className="aap-accordion__body">
                <p>{item.answer}</p>
              </div>
            </details>
          ))}
        </div>

        {/* On phones the link follows the questions. */}
        <ArrowLink href="/faq" className="justify-self-start lg:hidden">
          Read all the questions
        </ArrowLink>
      </div>
    </section>
  );
}
