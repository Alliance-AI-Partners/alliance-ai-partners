import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type SectionHeadProps = {
  /** The heading's id, for the section's aria-labelledby. */
  id: string;
  title: ReactNode;
  lead?: ReactNode;
  /** The heading's type style; section titles are Heading 2 unless the design says otherwise. */
  titleClassName?: string;
  /** The heading level: h2 for a section, h1 when the head opens the page. */
  as?: "h1" | "h2";
  className?: string;
};

/**
 * A section head (Figma: Section head, the page toolkit's K.head): the title and the lead side by side from 1024px
 * (title 0.9fr, lead 1.1fr, 48px apart, aligned to the bottom), stacked 16px apart below that.
 */
export function SectionHead({ id, title, lead, titleClassName = "aap-h2", as: Heading = "h2", className }: SectionHeadProps) {
  return (
    <div className={cn("grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-end lg:gap-12", className)}>
      <Heading id={id} className={titleClassName}>
        {title}
      </Heading>
      {lead ? <p className="text-body-lg text-ink-secondary">{lead}</p> : null}
    </div>
  );
}
