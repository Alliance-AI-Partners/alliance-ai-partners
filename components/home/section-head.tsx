import type { ReactNode } from "react";

type SectionHeadProps = {
  /** The heading's id, for the section's aria-labelledby. */
  id: string;
  title: ReactNode;
  lead: ReactNode;
  /** The heading's type style; section titles are Heading 2 unless the design says otherwise. */
  titleClassName?: string;
};

/**
 * A section head: the title and the lead side by side from 1024px (title 0.9fr, lead 1.1fr, 48px apart, aligned to
 * the bottom), stacked 16px apart below that. Figma: Section head.
 */
export function SectionHead({ id, title, lead, titleClassName = "aap-h2" }: SectionHeadProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-end lg:gap-12">
      <h2 id={id} className={titleClassName}>
        {title}
      </h2>
      <p className="text-body-lg text-ink-secondary">{lead}</p>
    </div>
  );
}
