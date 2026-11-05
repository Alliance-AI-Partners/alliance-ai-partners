import Link from "@/components/site-link";
import { BookingForm } from "@/components/ai-check-up/booking-form";
import { CheckList } from "@/components/blocks/check-list";
import { Icon } from "@/components/icon";
import { formsDemo } from "@/lib/forms-mode";
import { contactEmail } from "@/lib/site";

/**
 * AI check-up: the booking form, the hero's #book target (Figma: Section · Booking form). From 1024px the text
 * column (520) sits beside the form (736). On phones the form follows the head, and what to have ready, the data
 * note and the email line come after it; the text column is `display: contents` below 1024px so `order` can do that.
 */
export function Booking() {
  return (
    <section id="book" aria-labelledby="book-title" className="aap-section">
      <div className="aap-container grid gap-7 lg:grid-cols-[minmax(0,520fr)_minmax(0,736fr)] lg:items-start lg:gap-16">
        <div className="contents lg:flex lg:flex-col lg:gap-8">
          <div className="order-1 flex flex-col gap-4 lg:gap-8">
            <h2 id="book-title" className="aap-h2">
              Book your AI check-up.
            </h2>
            <p className="text-body-lg text-ink-secondary">
              Tell us a little about your team and pick a time for the first call. It is a one-hour video call, and we
              spend most of it listening.
            </p>
          </div>

          <div className="order-3 flex flex-col gap-1">
            <h3 className="aap-h4">What to have ready</h3>
            <CheckList
              itemClassName="gap-3 py-3 lg:gap-4 lg:py-3.5"
              items={[
                {
                  id: "tasks",
                  text: "The two or three tasks that take your team the most time each week. Rough hours are fine.",
                },
                { id: "tools", text: "The tools you use today, such as your CRM, help desk or accounting software." },
                { id: "colleague", text: "A colleague who does the work day to day, if they can join." },
              ]}
            />
          </div>

          <div className="order-4 flex items-start gap-3 rounded-md bg-sunken p-4 lg:px-5">
            <Icon name="lock" className="mt-1 size-4 shrink-0 text-ink-secondary lg:mt-0.5 lg:size-5" />
            <p className="text-body-sm text-ink-secondary">
              Please don’t send passwords or customer data. We agree on access together, and your data stays in your
              systems wherever possible. Read <Link href="/trust">how we handle data</Link>.
            </p>
          </div>

          <p className="order-5 text-body text-ink-secondary">
            Prefer email? Write to <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
          </p>
        </div>

        <div className="order-2 lg:order-none">
          <BookingForm demo={formsDemo} />
        </div>
      </div>
    </section>
  );
}
