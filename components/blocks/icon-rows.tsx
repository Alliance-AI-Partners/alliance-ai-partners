import type { ReactNode } from "react";
import { ServiceIcon, type ServiceIconName } from "@/components/service-icon";
import { cn } from "@/lib/cn";

export type IconRow = { icon: ServiceIconName; title: string; text: ReactNode };

type IconRowsProps = {
  rows: IconRow[];
  /** The rows' heading level: h3 under a section title, h4 under a step or card title. */
  headingLevel?: "h3" | "h4";
  /** mono on Daylight, dark on Partner Navy. */
  tone?: "mono" | "dark";
  /** The icon's size: 28px on phones, 32px from 1024px in Figma. */
  iconClassName?: string;
  className?: string;
  reveal?: boolean;
};

/**
 * Rows of a service icon beside a Heading 4 title and a Body/SM line, each on a bottom hairline, 20px above and below
 * (Figma: Rows › Row · <title>).
 */
export function IconRows({
  rows,
  headingLevel: Heading = "h3",
  tone = "mono",
  iconClassName = "size-7 lg:size-8",
  className,
  reveal = true,
}: IconRowsProps) {
  return (
    <ul className={className} data-reveal-group={reveal ? "" : undefined}>
      {rows.map((row) => (
        <li
          key={row.title}
          className="flex items-start gap-4 border-b border-line py-5"
          data-reveal-item={reveal ? "" : undefined}
        >
          <ServiceIcon name={row.icon} tone={tone} className={iconClassName} />
          <div className="flex min-w-0 flex-col gap-1">
            <Heading className="aap-h4">{row.title}</Heading>
            <p className="text-body-sm text-ink-secondary">{row.text}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

/**
 * A small numbered disc (Figma: Marker <n>): 28px (`size="sm"`: 24px), Control/Checked fill, the number in mono on the
 * page colour. Decorative: the step's own text carries its number for assistive technology.
 */
export function StepMarker({ n, size = "md", className }: { n: number; size?: "sm" | "md"; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "inline-grid shrink-0 place-items-center rounded-full bg-ink font-mono text-mono leading-none text-page",
        size === "md" ? "size-7" : "size-6",
        className,
      )}
    >
      {n}
    </span>
  );
}
