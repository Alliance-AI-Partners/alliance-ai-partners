import type { CSSProperties, ReactNode } from "react";
import { Icon, type IconName } from "@/components/icon";
import { cn } from "@/lib/cn";

export type CheckListItem = { id: string; text: ReactNode; icon?: IconName };

type CheckListProps = {
  items: CheckListItem[];
  /** The 20px icon at the start of each row (Figma: Icon · check, or Icon · arrow-right for "skip it if" rows). */
  icon?: IconName;
  /** The icon's colour; it follows the text by default. */
  iconClassName?: string;
  /** Row spacing. Figma's rows are 14px tall padding with a 16px gap from 1024px and a 12px gap on phones. */
  itemClassName?: string;
  /** The text's type style (Figma: Body/Default, Text/Primary). */
  textClassName?: string;
  className?: string;
  /** Rise into view row by row (app/globals.css). */
  reveal?: boolean;
};

/**
 * A list of short statements, each on a hairline row with an icon in front (Figma: Rows › Item). Used for "a good fit
 * if" lists, promises and things to have ready. The rows carry a bottom hairline only; give the list `border-t
 * border-line` when the design draws a line above the first row too.
 */
export function CheckList({
  items,
  icon = "check",
  iconClassName,
  itemClassName = "gap-3 py-3.5 lg:gap-4",
  textClassName = "text-body",
  className,
  reveal = true,
}: CheckListProps) {
  return (
    <ul
      className={className}
      data-reveal-group={reveal ? "" : undefined}
      style={reveal ? ({ "--reveal-stagger": "40ms" } as CSSProperties) : undefined}
    >
      {items.map((item) => (
        <li
          key={item.id}
          className={cn("flex items-start border-b border-line", itemClassName)}
          data-reveal-item={reveal ? "" : undefined}
        >
          <Icon name={item.icon ?? icon} className={cn("mt-[3px] size-5 shrink-0", iconClassName)} />
          <span className={textClassName}>{item.text}</span>
        </li>
      ))}
    </ul>
  );
}
