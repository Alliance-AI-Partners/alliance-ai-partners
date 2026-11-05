import { getImageProps } from "next/image";
import { ArrowLink } from "@/components/arrow-link";
import { Alert } from "@/components/blocks/alert";
import { StepMarker } from "@/components/blocks/icon-rows";
import { Icon } from "@/components/icon";
import emailDesktop from "@/brand-kit/emails/previews/check-up-booked-desktop.png";
import emailMobile from "@/brand-kit/emails/previews/check-up-booked-mobile.png";
import { contactEmail } from "@/lib/site";

const callTimes = [
  { label: "Your time · New York", day: "Tuesday, November 17", time: "5:00 to 6:00 pm EST" },
  { label: "Our time · Manila", day: "Wednesday, November 18", time: "6:00 to 7:00 am PHT" },
];

const nextSteps = [
  {
    title: "Check your inbox",
    text: "The email has the agenda, what to prepare and the video link. Please don’t send passwords or customer data before we meet.",
  },
  {
    title: "We listen first",
    text: "On the call, you walk us through a normal week. We ask questions and repeat the problem back in your words.",
  },
  {
    title: "Your plan in [two weeks]",
    text: "A written plan ranked by what each fix would save, with a fixed quote for the first fix. You decide what happens next.",
    link: { label: "Read a sample report", href: "/ai-check-up/sample" },
  },
];

/*
 * "Add to calendar" for the sample booking: a one-hour event at the sample time, as a calendar file. A booking service
 * would supply the real one (the page record's {{calendar_ics_url}}).
 */
const sampleEvent = [
  "BEGIN:VCALENDAR",
  "VERSION:2.0",
  "PRODID:-//Alliance AI Partners//AI check-up//EN",
  "BEGIN:VEVENT",
  "UID:sample-ai-check-up@allianceaipartners.example",
  "DTSTAMP:20261105T000000Z",
  "DTSTART:20261117T220000Z",
  "DTEND:20261117T230000Z",
  "SUMMARY:AI check-up: first call with Alliance AI Partners",
  "DESCRIPTION:Sample booking. A one-hour video call.",
  "END:VEVENT",
  "END:VCALENDAR",
].join("\r\n");

/**
 * The AI check-up once booked (Figma: AI check-up — Desktop · Booked, Section · Booked). It replaces the page's
 * sections when the form is sent (components/blocks/form-flow.tsx). The booking shown is the sample from the brand
 * kit's confirmation email, tagged as such.
 */
export function Booked() {
  return (
    <section aria-labelledby="booked-title" className="pt-10 pb-section lg:pt-24">
      <div className="aap-container grid gap-10 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)] lg:items-start lg:gap-16">
        <div className="flex flex-col gap-6 lg:gap-8">
          <div tabIndex={-1} data-form-flow-focus className="rounded-md outline-none">
            <Alert type="success" role="status" title="Your AI check-up is booked.">
              We sent the agenda and a calendar invite to [email address].
            </Alert>
          </div>

          <div className="flex flex-col items-start gap-4">
            <h1 id="booked-title" className="aap-h1">
              See you on Tuesday.
            </h1>
            <p className="text-body-lg text-ink-secondary">
              Your first call is a one-hour video call on Tuesday, November 17, at 5:00 pm EST. For us in Manila, that
              is 6:00 am on Wednesday.
            </p>
            <span className="aap-tag">Sample booking</span>
          </div>

          <dl className="aap-card grid gap-0 p-0 lg:grid-cols-2">
            {callTimes.map((item, index) => (
              <div
                key={item.label}
                className={
                  index === 0
                    ? "flex flex-col gap-1 px-6 py-5 lg:px-7 lg:py-6"
                    : "flex flex-col gap-1 border-t border-line-subtle px-6 py-5 lg:border-t-0 lg:border-l lg:px-7 lg:py-6"
                }
              >
                <dt className="text-caption text-ink-secondary">{item.label}</dt>
                <dd className="text-body font-semibold">{item.day}</dd>
                <dd className="aap-mono">{item.time}</dd>
              </div>
            ))}
          </dl>

          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-6">
            <a
              href={`data:text/calendar;charset=utf-8,${encodeURIComponent(sampleEvent)}`}
              download="ai-check-up.ics"
              className="aap-button aap-button--lg w-full lg:w-auto lg:min-h-11 lg:px-5 lg:text-[0.875rem]"
            >
              Add to calendar
              <Icon name="calendar" />
            </a>
            <p className="text-body text-ink-secondary">
              Need another time? Email <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
            </p>
          </div>

          <div className="flex flex-col gap-2 pt-2 lg:pt-4">
            <h2 className="aap-h2">What happens next</h2>
            <ol>
              {nextSteps.map((step, index) => (
                <li key={step.title} className="flex items-start gap-4 border-b border-line py-5">
                  <StepMarker n={index + 1} />
                  <div className="flex flex-col gap-1.5">
                    <h3 className="aap-h4">{step.title}</h3>
                    <p className="text-body text-ink-secondary lg:max-w-[568px]">{step.text}</p>
                    {step.link ? (
                      <ArrowLink href={step.link.href} className="self-start text-body-sm">
                        {step.link.label}
                      </ArrowLink>
                    ) : null}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>

        <figure className="flex flex-col gap-3">
          <EmailPreview />
          <figcaption className="aap-mono text-ink-secondary">Sample confirmation email from our templates.</figcaption>
        </figure>
      </div>
    </section>
  );
}

/** The confirmation email, anchored to its top: the desktop render from 1024px, the phone render below (IMG-02-3). */
function EmailPreview() {
  const common = {
    alt: "Sample confirmation email: the AI check-up is booked for Tuesday, November 17, with the agenda and what to prepare.",
    sizes: "(min-width: 1024px) 42vw, 100vw",
  };
  const {
    props: { srcSet: desktopSrcSet },
  } = getImageProps({ ...common, src: emailDesktop });
  const {
    props: { srcSet: mobileSrcSet, ...imgProps },
  } = getImageProps({ ...common, src: emailMobile });

  return (
    <div className="aap-media relative aspect-[358/520] lg:aspect-[604/760]">
      <picture className="block size-full">
        <source media="(min-width: 1024px)" srcSet={desktopSrcSet} sizes={common.sizes} />
        <img {...imgProps} srcSet={mobileSrcSet} alt={common.alt} className="size-full object-cover object-top" />
      </picture>
    </div>
  );
}
