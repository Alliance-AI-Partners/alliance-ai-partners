import type { CSSProperties, ReactNode } from "react";
import Link from "@/components/site-link";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

export type ServiceRowItem = { title: string; text: ReactNode; price: ReactNode; href: string };

type ServiceRowsProps = {
  rows: ServiceRowItem[];
  /** The titles' heading level. */
  headingLevel?: "h3" | "h4";
  /** Draw a hairline above the first row too. */
  ruled?: boolean;
  className?: string;
};

/**
 * Linked service rows (Figma: Service row): the title and line on the left, the starting price in mono and an arrow
 * on the right from 1024px; on phones the price and arrow sit on their own line under the text. The whole row is the
 * link. Rows are 24px above and below from 1024px, 20px on phones.
 */
export function ServiceRows({ rows, headingLevel: Heading = "h3", ruled = false, className }: ServiceRowsProps) {
  return (
    <ul
      className={cn(ruled && "border-t border-line", className)}
      data-reveal-group
      style={{ "--reveal-stagger": "40ms" } as CSSProperties}
    >
      {rows.map((row) => (
        <li key={row.title} data-reveal-item>
          <Link
            href={row.href}
            className="group flex flex-col gap-2 border-b border-line py-5 text-ink no-underline lg:flex-row lg:items-center lg:gap-8 lg:py-6"
          >
            <div className="flex flex-col gap-2 lg:flex-1 lg:gap-1">
              <Heading className="aap-h4">{row.title}</Heading>
              <p className="text-body-sm text-ink-secondary lg:max-w-[504px]">{row.text}</p>
            </div>
            <div className="flex items-center justify-between gap-4 lg:justify-start">
              <span className="aap-mono">{row.price}</span>
              <Icon
                name="arrow-right"
                className="size-5 shrink-0 transition-transform duration-(--aap-duration-base) ease-spring group-hover:translate-x-[3px] motion-reduce:group-hover:translate-x-0"
              />
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
