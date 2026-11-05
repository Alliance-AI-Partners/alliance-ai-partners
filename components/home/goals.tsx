import Image, { type StaticImageData } from "next/image";
import type { ReactNode } from "react";
import { ArrowLink } from "@/components/arrow-link";
import { SectionHead } from "@/components/section-head";
import aiStrategyIcon from "@/design-system/icons/brand/ai-strategy-mono.svg";
import automationIcon from "@/design-system/icons/brand/automation-mono.svg";
import growthIcon from "@/design-system/icons/brand/growth-mono.svg";
import scaleImage from "@/design-system/imagery/website/IMG-01-2.jpg";
import { cn } from "@/lib/cn";

type Tag = { label: string; desktopOnly?: boolean };

/** Home: the three goals every service sits under (Figma: Section · Three goals). */
export function Goals() {
  return (
    <section aria-labelledby="goals-title" className="aap-section">
      <div className="aap-container flex flex-col gap-6 lg:gap-12">
        <SectionHead
          id="goals-title"
          title={
            <>
              Start with what you
              <br /> want to <span className="aap-accent">change.</span>
            </>
          }
          lead={
            <>
              Every service sits under one of three goals. Pick the one that sounds like your week
              <span className="hidden lg:inline">, and we’ll take it from there</span>.
            </>
          }
        />

        <div className="grid gap-6 lg:grid-cols-2" data-reveal-group>
          {/* The large card: full-bleed image on top, then the body. */}
          <article className="aap-card flex flex-col gap-4 overflow-hidden p-0 lg:gap-5" data-reveal-item>
            <div className="relative aspect-[356/224] lg:aspect-[646/340]">
              <Image
                src={scaleImage}
                alt="A row of faceted saplings growing taller along a ribbon path."
                fill
                sizes="(min-width: 1024px) 45vw, 100vw"
                className="object-cover"
              />
            </div>
            <div className="flex flex-col gap-4 px-6 pt-1 pb-6 lg:px-8 lg:pt-2 lg:pb-8">
              <GoalBody
                icon={aiStrategyIcon}
                title="Scale AI"
                text="Plan, build and run AI across the company, with your people trained to use it."
                tags={[
                  { label: "Strategy and leadership" },
                  { label: "Training and adoption" },
                  { label: "Software and product engineering" },
                  { label: "Running AI for you" },
                  { label: "Talent and teams", desktopOnly: true },
                ]}
                href="/services/scale-ai"
              />
            </div>
          </article>

          <div className="flex flex-col gap-6">
            <article className="aap-card flex flex-1 flex-col gap-4 p-6 lg:p-8" data-reveal-item>
              <GoalBody
                icon={automationIcon}
                title="Solve problems with AI"
                text={
                  <>
                    Fix the jobs that slow your team down: the copying, chasing and checking
                    <span className="hidden lg:inline"> that fill a week</span>.
                  </>
                }
                tags={[
                  { label: "Automation and AI agents" },
                  { label: "Customer support" },
                  { label: "Knowledge and data" },
                  { label: "Design", desktopOnly: true },
                  { label: "Security and risk", desktopOnly: true },
                ]}
                href="/services/solve-problems-with-ai"
              />
            </article>
            <article className="aap-card flex flex-1 flex-col gap-4 p-6 lg:p-8" data-reveal-item>
              <GoalBody
                icon={growthIcon}
                title="Grow"
                text="Win more customers, with AI doing the repetitive part of your marketing and sales."
                tags={[{ label: "Marketing" }, { label: "Sales and go-to-market" }, { label: "Online stores" }]}
                href="/services/grow"
              />
            </article>
          </div>
        </div>
      </div>
    </section>
  );
}

type GoalBodyProps = {
  icon: StaticImageData;
  title: string;
  text: ReactNode;
  tags: Tag[];
  href: string;
};

/** A goal card's contents: icon and title, the line, the service tags (some only from 1024px) and the link. */
function GoalBody({ icon, title, text, tags, href }: GoalBodyProps) {
  return (
    <>
      <div className="flex items-center gap-3 lg:gap-4">
        <Image src={icon} alt="" className="size-8 shrink-0 lg:size-10" />
        <h3 className="aap-h3">{title}</h3>
      </div>
      <p className="text-body text-ink-secondary">{text}</p>
      <ul className="flex flex-wrap gap-2" aria-label={`${title} services`}>
        {tags.map((tag) => (
          <li key={tag.label} className={cn("aap-tag", tag.desktopOnly && "hidden lg:inline-flex")}>
            {tag.label}
          </li>
        ))}
      </ul>
      <ArrowLink href={href} className="self-start">
        Explore {title}
      </ArrowLink>
    </>
  );
}
