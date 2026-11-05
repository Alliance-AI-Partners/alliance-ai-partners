import type { CSSProperties, ReactNode } from "react";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

export type FaqItem = { question: string; answer: ReactNode };

type FaqListProps = {
  items: FaqItem[];
  /** Figma shows the first question open; pass false where the design shows them all closed. */
  firstOpen?: boolean;
  /** The questions' heading level. */
  headingLevel?: "h3" | "h4";
  className?: string;
};

/**
 * Questions and answers on the design system's accordion (Figma: Accordion › Accordion item). Native <details>, so
 * they open without JavaScript; the plus and close icons cross-fade as they turn (app/globals.css). An answer is one
 * paragraph unless it passes its own markup.
 */
export function FaqList({ items, firstOpen = true, headingLevel: Heading = "h3", className }: FaqListProps) {
  return (
    <div
      className={cn("border-t border-line", className)}
      data-reveal-group
      style={{ "--reveal-stagger": "40ms" } as CSSProperties}
    >
      {items.map((item, index) => (
        <details key={item.question} className="aap-accordion" open={firstOpen && index === 0} data-reveal-item>
          <summary>
            <Heading>{item.question}</Heading>
            <span className="site-accordion-icon">
              <Icon name="plus" className="site-icon-closed" />
              <Icon name="close" className="site-icon-open" />
            </span>
          </summary>
          <div className="aap-accordion__body">
            {typeof item.answer === "string" ? <p>{item.answer}</p> : item.answer}
          </div>
        </details>
      ))}
    </div>
  );
}
