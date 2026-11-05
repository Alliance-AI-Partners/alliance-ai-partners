import Link from "@/components/site-link";
import type { ReactNode } from "react";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

type ArrowLinkProps = {
  href: string;
  children: ReactNode;
  className?: string;
};

/**
 * The design system's text link with a forward arrow (Figma: Link). `aap-link--standalone` gives it a 44px touch
 * target without moving the layout. In a flex column, pass `self-start` so the link does not stretch.
 */
export function ArrowLink({ href, children, className }: ArrowLinkProps) {
  return (
    <Link href={href} className={cn("aap-link aap-link--standalone", className)}>
      {children}
      <Icon name="arrow-right" />
    </Link>
  );
}
