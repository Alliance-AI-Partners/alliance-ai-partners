import Image from "next/image";
import lockupOnDark from "@/design-system/logos/lockups/alliance-ai-partners-primary-horizontal-full-color-dark.svg";
import lockupOnLight from "@/design-system/logos/lockups/alliance-ai-partners-primary-horizontal-full-color-light.svg";

type LogoProps = {
  /** "light" for Daylight grounds, "dark" for Partner Navy grounds. */
  ground?: "light" | "dark";
  /** Load at once instead of lazily; for the header, which is always in view on load. */
  eager?: boolean;
};

/**
 * The primary horizontal lockup at the brand's screen minimum. `.aap-header__logo` sets it 76px tall: the SVG keeps
 * its clear space inside its viewBox, and negative margins let that space overlap the surrounding padding, so the
 * artwork (200 x 48 px) lines up with the content edge. Never type the company name in place of this file.
 */
export function Logo({ ground = "light", eager = false }: LogoProps) {
  return (
    <Image
      src={ground === "light" ? lockupOnLight : lockupOnDark}
      alt="Alliance AI Partners"
      // max-w-none: Tailwind's base styles cap images at their container's width, and the negative margin makes the
      // link 14px narrower than the image, which would squeeze the logo.
      className="aap-header__logo w-auto max-w-none"
      loading={eager ? "eager" : "lazy"}
    />
  );
}
