import { ArrowLink } from "@/components/arrow-link";
import { FaqList } from "@/components/blocks/faq-list";

const questions = [
  {
    question: "How long does it take?",
    answer:
      "About [two weeks] from the first call to your written plan. Most of that time is ours: your team joins the first call and a few short interviews.",
  },
  {
    question: "What does it cost?",
    answer:
      "From [PRICE]. We confirm the fixed price on the first call, before any work starts, and any change is quoted before we do it.",
  },
  {
    question: "Do we have to hire you to build the fixes?",
    answer:
      "No. The plan is yours. Build the fixes with your own team, with someone else, or with us at the price in your fixed quote.",
  },
  {
    question: "What if AI is not the answer?",
    answer: "Then we say so, and tell you what would work better, even when it means less work for us.",
  },
  {
    question: "What do you need from us?",
    answer:
      "An hour for the first call, a few short interviews with the people who do the work, and a look at the tools you use. No passwords or customer data before we meet.",
  },
];

/**
 * AI check-up: questions about the check-up (Figma: Section · Questions). From 1024px the title and lead sit side by
 * side like a section head, and the questions sit under the lead column; on phones everything stacks 24px apart.
 */
export function Questions() {
  return (
    <section aria-labelledby="questions-title" className="aap-section">
      <div className="aap-container grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-x-12 lg:gap-y-12">
        <h2 id="questions-title" className="aap-h2 lg:self-end">
          Questions about
          <br /> the check-up
        </h2>
        <p className="text-body-lg text-ink-secondary lg:self-end">
          Short answers to what founders ask before they book. Anything else, ask us on the first call.
        </p>
        <div className="flex flex-col gap-6 lg:col-start-2 lg:gap-8">
          <FaqList items={questions} />
          <ArrowLink href="/faq" className="self-start">
            Read all the questions
          </ArrowLink>
        </div>
      </div>
    </section>
  );
}
