// The sprite is a set of <symbol>s, not an image, so it is imported as a plain file URL (Turbopack's "asset" module
// type) instead of through next/image's static image import, which needs an image size.
import spriteUrl from "@/design-system/icons/sprite.svg";

/** Icons from the design system's sprite (design-system/icons/sprite.svg). They draw in currentColor. */
export type IconName =
  | "alert-triangle"
  | "arrow-left"
  | "arrow-right"
  | "arrow-up-right"
  | "calendar"
  | "check"
  | "check-circle"
  | "chevron-down"
  | "chevron-right"
  | "clock"
  | "close"
  | "copy"
  | "download"
  | "external-link"
  | "facebook"
  | "file"
  | "globe"
  | "info"
  | "instagram"
  | "link"
  | "linkedin"
  | "lock"
  | "mail"
  | "map-pin"
  | "menu"
  | "minus"
  | "phone"
  | "play"
  | "plus"
  | "search"
  | "x"
  | "x-circle"
  | "youtube";

type IconProps = {
  name: IconName;
  className?: string;
};

/**
 * A decorative icon: hidden from assistive technology, so the text next to it (or the control's aria-label)
 * carries the meaning. Size it with a class (`size-5`) or let the component it sits in size it.
 */
export function Icon({ name, className }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className={className}
      // The design system slides forward arrows 3px on hover.
      data-direction={name === "arrow-right" ? "forward" : undefined}
    >
      <use href={`${spriteUrl}#icon-${name}`} />
    </svg>
  );
}
