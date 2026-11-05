import type { ReactNode } from "react";
import Link from "@/components/site-link";
import { Icon, type IconName } from "@/components/icon";
import { cn } from "@/lib/cn";

type ButtonLinkProps = {
  href: string;
  children: ReactNode;
  /** Figma: Button, Variant. Primary is the one committing action per view; Secondary is the outline. */
  variant?: "primary" | "secondary" | "quiet";
  /** Figma: Button, Size (SM 36px, MD 44px, LG 52px). */
  size?: "sm" | "md" | "lg";
  /** The icon after the label. Primary buttons carry the forward arrow unless this says otherwise; null for none. */
  icon?: IconName | null;
  className?: string;
};

const variants = { primary: "aap-button--primary", secondary: "", quiet: "aap-button--quiet" };
const sizes = { sm: "aap-button--sm", md: "", lg: "aap-button--lg" };

/** True for addresses that leave the site (mail, phone, other sites), which skip the client-side router. */
export function isExternalHref(href: string) {
  return /^(https?:|mailto:|tel:)/.test(href);
}

/**
 * A link styled as the design system's button (Figma: Button). Internal links go through the site link, so the page
 * loading bar runs; mail, phone and outside links are plain anchors. In a flex column, pass `self-start` (or a width)
 * so the button does not stretch.
 */
export function ButtonLink({ href, children, variant = "secondary", size = "md", icon, className }: ButtonLinkProps) {
  const iconName = icon === undefined ? (variant === "primary" ? "arrow-right" : null) : icon;
  const classes = cn("aap-button", variants[variant], sizes[size], className);
  const content = (
    <>
      {children}
      {iconName ? <Icon name={iconName} /> : null}
    </>
  );

  if (isExternalHref(href)) {
    return (
      <a href={href} className={classes}>
        {content}
      </a>
    );
  }
  return (
    <Link href={href} className={classes}>
      {content}
    </Link>
  );
}
