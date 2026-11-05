"use client";

import { inView } from "motion/react";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

/**
 * Scroll reveals for the page (plans/004), triggered by Motion's inView. It renders nothing.
 *
 * Reveals: a `[data-reveal-group]` that starts below the fold is marked `data-revealed="false"`, so its
 * `[data-reveal-item]`s are hidden by CSS; when the group scrolls into view it turns "true" and the items rise and
 * fade in, in order. The motion itself is CSS on the design system's tokens (app/globals.css). Groups already in view
 * are left alone, so the server HTML is never hidden and nothing flashes.
 *
 * The band parallax (plans/006) is pure CSS on the browser's scroll timeline, so it needs no JavaScript here.
 *
 * Under prefers-reduced-motion nothing is hidden and nothing moves. The layout survives client navigation, so the
 * effect runs again for each new page.
 */
export function ScrollEffects() {
  const pathname = usePathname();

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const stops: VoidFunction[] = [];

    for (const group of document.querySelectorAll<HTMLElement>("[data-reveal-group]")) {
      if (overlapsViewport(group)) continue;
      const items = group.hasAttribute("data-reveal-item")
        ? [group]
        : [...group.querySelectorAll<HTMLElement>("[data-reveal-item]")];
      items.forEach((item, index) => item.style.setProperty("--reveal-index", String(index)));
      group.dataset.revealed = "false";
      stops.push(
        inView(
          group,
          () => {
            group.dataset.revealed = "true";
          },
          { margin: "0px 0px -10% 0px" },
        ),
      );
    }

    return () => stops.forEach((stop) => stop());
  }, [pathname]);

  return null;
}

/** True when any part of the element is inside the window. */
function overlapsViewport(element: Element) {
  const rect = element.getBoundingClientRect();
  return rect.bottom > 0 && rect.top < window.innerHeight;
}
