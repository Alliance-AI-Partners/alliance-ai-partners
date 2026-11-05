import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

type RibbonProps = {
  /** Unique on the page: the id of the gradient inside this SVG. */
  id: string;
  /** The path, in the coordinates of `viewBox`. */
  d: string;
  /** The path's bounding box, so the drawn line fills the element exactly; the stroke overflows it by half its width. */
  viewBox: string;
  /** The gradient runs from x1 to x2, the left and right ends of the path. */
  x1: number;
  x2: number;
  /** Stroke width in px (default 3). */
  strokeWidth?: number;
  className?: string;
};

/**
 * The ribbon in its line form: a Daybreak stroke (Partner Navy to Alliance Blue to Ribbon Cyan). It uses the design
 * system's `.aap-ribbon`, which draws the line as it scrolls into view; the gradient lives inside the same SVG because
 * Chrome does not paint gradients referenced from a hidden SVG. Decorative, so it is hidden from assistive technology.
 */
export function Ribbon({ id, d, viewBox, x1, x2, strokeWidth = 3, className }: RibbonProps) {
  return (
    <svg
      className={cn("aap-ribbon", className)}
      viewBox={viewBox}
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      style={{ "--aap-ribbon-width": strokeWidth } as CSSProperties}
    >
      <defs>
        <linearGradient id={id} x1={x1} y1="0" x2={x2} y2="0" gradientUnits="userSpaceOnUse">
          <stop offset="0" style={{ stopColor: "var(--aap-color-brand-partner-navy)" }} />
          <stop offset="0.54" style={{ stopColor: "var(--aap-color-brand-alliance-blue)" }} />
          <stop offset="1" style={{ stopColor: "var(--aap-color-brand-ribbon-cyan)" }} />
        </linearGradient>
      </defs>
      <path d={d} pathLength={1} stroke={`url(#${id})`} />
    </svg>
  );
}
