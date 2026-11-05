import Image, { type StaticImageData } from "next/image";
import automationIcon from "@/design-system/icons/brand/automation-mono.svg";
import launchIcon from "@/design-system/icons/brand/launch-mono.svg";
import partnershipIcon from "@/design-system/icons/brand/partnership-mono.svg";
import busyworkImage from "@/design-system/imagery/website/IMG-01-1.jpg";

const outcomes: { icon: StaticImageData; title: string; text: string }[] = [
  {
    icon: automationIcon,
    title: "Automate the slow work",
    text: "Quotes, data entry and reports that eat your week, handled by AI and checked by a person.",
  },
  {
    icon: launchIcon,
    title: "Build the tools you’re missing",
    text: "AI assistants, support tools and software, built for how your team already works.",
  },
  {
    icon: partnershipIcon,
    title: "Add hands when you need them",
    text: "A developer from our team joins yours full time and works inside your tools.",
  },
];

/**
 * Home pitch (Figma: Section · Pitch). From 1024px the image sits left of the text. On phones the image moves
 * between the lead and the outcomes: the text column becomes `display: contents`, so its children join the grid and
 * `order` places the image among them.
 */
export function Pitch() {
  return (
    <section aria-labelledby="pitch-title" className="aap-section">
      <div className="aap-container grid gap-7 lg:grid-cols-[minmax(0,640fr)_minmax(0,600fr)] lg:items-center lg:gap-20">
        <div className="contents lg:flex lg:flex-col lg:gap-8">
          <h2 id="pitch-title" className="aap-h2 order-1">
            Less busywork.
            <br className="lg:hidden" /> More <span className="aap-accent">growth.</span>
          </h2>
          <p className="order-2 text-body-lg text-ink-secondary">
            Most companies know AI could help them grow, but they don’t have the time or the people to make it happen.
            Alliance AI Partners becomes that team.
          </p>
          <ul className="order-4 flex flex-col gap-7 lg:gap-6">
            {outcomes.map((outcome) => (
              <li key={outcome.title} className="flex items-start gap-4 lg:gap-5">
                <Image src={outcome.icon} alt="" className="size-8 shrink-0 lg:size-10" />
                <div className="flex flex-col gap-1">
                  <h3 className="aap-h4">{outcome.title}</h3>
                  <p className="text-body text-ink-secondary">{outcome.text}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="order-5 text-body font-semibold">
            Where most agencies hand over the project and move on, we stay to keep everything running and help you win
            more customers.
          </p>
        </div>

        <div className="aap-media relative order-3 aspect-[358/448] lg:order-first lg:aspect-[640/760]">
          <Image
            src={busyworkImage}
            alt="Tangled ribbons straightening into one smooth ribbon."
            fill
            sizes="(min-width: 1024px) 45vw, 100vw"
            className="object-cover"
          />
        </div>
      </div>
    </section>
  );
}
