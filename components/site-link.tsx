import NextLink from "next/link";
import type { ComponentProps } from "react";
import { LinkPendingSignal } from "@/components/navigation-progress";

/**
 * next/link with the signal that drives the page-loading bar (components/navigation-progress.tsx). Use it for every
 * internal link; mailto and external links stay plain <a> elements.
 */
export default function Link({ children, ...props }: ComponentProps<typeof NextLink>) {
  return (
    <NextLink {...props}>
      {children}
      <LinkPendingSignal />
    </NextLink>
  );
}
