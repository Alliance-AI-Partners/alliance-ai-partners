import type { ReactNode } from "react";
import { SourceKey } from "@/components/blocks/sources";
import { cn } from "@/lib/cn";

type StatProps = {
  /** The figure, set in Data/Numeral. */
  value: ReactNode;
  /** The Sources list it keys to: its id prefix and the note number. */
  source?: { id: string; n: number };
  /** The caption under the figure (Body/SM, Text/Secondary). */
  children: ReactNode;
  className?: string;
};

/** A sourced figure (Figma: Stat): the numeral with its source key, then the caption 8px below. */
export function Stat({ value, source, children, className }: StatProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <p className="flex items-start gap-1">
        <span className="aap-numeral">{value}</span>
        {source ? <SourceKey id={source.id} n={source.n} /> : null}
      </p>
      <p className="text-body-sm text-ink-secondary">{children}</p>
    </div>
  );
}
