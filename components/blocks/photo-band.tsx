import Image, { type StaticImageData } from "next/image";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type PhotoBandProps = {
  /** The heading's id inside the band (used when the band is its own section). */
  labelledBy?: string;
  image: StaticImageData;
  /** Alt text; empty (the default) for a decorative background, which most bands are. */
  alt?: string;
  /** Crop: object-position classes, for example `object-[20%_50%] lg:object-center`. */
  imageClassName?: string;
  /**
   * The Partner Navy scrim: a class that paints the gradient(s) drawn in the Figma frame (usually from the top on
   * phones and from the reading edge from 1024px), defined in the page's CSS file. It must keep every line of text
   * over at least 80% navy.
   */
  scrimClassName: string;
  /** The band's own classes: its height (`min-h-[720px] lg:min-h-[680px]`) and how it places the content. */
  className?: string;
  /** Drift the photograph a little slower than the page (plans/006). On by default; off for bands at the very top. */
  parallax?: boolean;
  /** Load the image at once (loading="eager"): only for a band in the first screen. */
  eager?: boolean;
  /** "div" when the band is only part of a larger section (it then takes no aria-labelledby of its own). */
  as?: "section" | "div";
  children: ReactNode;
};

/**
 * A full-bleed Partner Navy band over a photograph (Figma: Section · <name> › Band, with an Image slot, one or two
 * Scrim rectangles and the text). The text sits in `children`, usually inside `.aap-container`.
 */
export function PhotoBand({
  labelledBy,
  image,
  alt = "",
  imageClassName,
  scrimClassName,
  className,
  parallax = true,
  eager = false,
  as: Tag = "section",
  children,
}: PhotoBandProps) {
  return (
    <Tag
      aria-labelledby={Tag === "section" ? labelledBy : undefined}
      className={cn("aap-surface-inverse relative isolate flex overflow-hidden", className)}
    >
      {/* The parallax layer reaches 24px past the band at the top and bottom, so it can drift without showing an edge. */}
      <div
        data-parallax={parallax ? "" : undefined}
        aria-hidden={alt ? undefined : true}
        className={cn("absolute inset-x-0 -z-20", parallax ? "-top-6 -bottom-6" : "inset-y-0")}
      >
        <Image
          src={image}
          alt={alt}
          fill
          sizes="100vw"
          loading={eager ? "eager" : undefined}
          className={cn("object-cover", imageClassName)}
        />
      </div>
      <div aria-hidden="true" className={cn("absolute inset-0 -z-10", scrimClassName)} />
      {children}
    </Tag>
  );
}
