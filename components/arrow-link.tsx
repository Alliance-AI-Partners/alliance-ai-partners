import Link from "@/components/site-link";
import type { ReactNode } from "react";
import { isExternalHref } from "@/components/button-link";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

type ArrowLinkProps = {
  href: string;
  children: ReactNode;
  className?: string;
};

/**
 * The design system's text link with a forward arrow (Figma: Link). `aap-link--standalone` gives it a 44px touch
 * target without moving the layout. In a flex column, pass `self-start` so the link does not stretch. Internal links
 * go through the site link (the page loading bar runs); mail, phone and outside addresses are plain anchors.
 */
export function ArrowLink({ href, children, className }: ArrowLinkProps) {
  const classes = cn("aap-link aap-link--standalone", className);
  // Mail, phone and outside addresses skip the client-side router, as in ButtonLink.
  if (isExternalHref(href)) {
    return (
      <a href={href} className={classes}>
        {children}
        <Icon name="arrow-right" />
      </a>
    );
  }
  return (
    <Link href={href} className={classes}>
      {children}
      <Icon name="arrow-right" />
    </Link>
  );
}
