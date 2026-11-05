import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/cn";

/** One source line. Where Figma words it differently on phones, give both and the right one shows at each width. */
export type Source = ReactNode | { phone: ReactNode; desktop: ReactNode };

function isByWidth(source: Source): source is { phone: ReactNode; desktop: ReactNode } {
  return typeof source === "object" && source !== null && "phone" in source && "desktop" in source;
}

type SourcesProps = {
  /** The id prefix shared with the SourceKeys that point here: item n gets the id `<id>-source-<n>`. */
  id: string;
  items: Source[];
  /** The number of the first item, where a section's notes continue an earlier list. */
  start?: number;
  className?: string;
};

/**
 * Numbered source notes in mono below a hairline (Figma: Sources, the page toolkit's K.sources). Every published
 * figure keys to one of these, with the date it was retrieved.
 */
export function Sources({ id, items, start = 1, className }: SourcesProps) {
  return (
    <ol
      className={cn("aap-sources", className)}
      style={start === 1 ? undefined : ({ counterReset: `aap-source ${start - 1}` } as CSSProperties)}
    >
      {items.map((source, index) => (
        <li key={index} id={`${id}-source-${start + index}`}>
          {isByWidth(source) ? (
            <span>
              <span className="lg:hidden">{source.phone}</span>
              <span className="hidden lg:inline">{source.desktop}</span>
            </span>
          ) : (
            <span>{source}</span>
          )}
        </li>
      ))}
    </ol>
  );
}

type SourceKeyProps = {
  /** The Sources list's id prefix. */
  id: string;
  n: number;
  /** Figma: Source key, Size MD (20px, beside a numeral) or SM (16px, inside text). */
  size?: "sm" | "md";
  className?: string;
};

/** The small boxed number that links a figure to its source note (Figma: Source key). */
export function SourceKey({ id, n, size = "md", className }: SourceKeyProps) {
  return (
    <a
      href={`#${id}-source-${n}`}
      aria-label={`Source ${n}`}
      className={cn(
        "inline-grid shrink-0 place-items-center rounded-sm border border-line px-[3px] font-mono text-[0.75rem] leading-none text-ink-secondary no-underline transition-colors hover:border-link hover:text-link",
        size === "md" ? "h-5 min-w-5" : "h-4 min-w-4",
        className,
      )}
    >
      {n}
    </a>
  );
}
