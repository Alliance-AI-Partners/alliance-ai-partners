"use client";

import { inView } from "motion/react";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

/**
 * Scroll reveals for the page (plans/004), triggered by Motion's inView. It renders nothing.
 *
 * Reveals: a `[data-reveal-group]` that starts below the fold has its `[data-reveal-item]`s (or itself, when it carries
 * `data-reveal-item`) held at the first frame of a paused rise: 12px down and transparent. When the group scrolls into
 * view the rises play, one item after another: 400ms (`--aap-duration-slow`), `translate` on `--aap-easing-out` and
 * `opacity` on `--aap-easing-standard`, items `--reveal-stagger` apart (60ms unless the group sets it) after
 * `--reveal-delay`. The steps' ribbon (`.aap-steps::before`) grows from the left over the ribbon's 1.4s, or from the
 * top on phones, where it runs down the side.
 *
 * The motion uses the browser's animation API on the elements, never their attributes or inline styles: React may
 * still be hydrating part of the page when this runs (a page's content can hydrate after the layout), and changing
 * attributes there would not match the server HTML. The server HTML is never hidden; groups already in view are left
 * alone, so nothing flashes. Under prefers-reduced-motion nothing is hidden and nothing moves, and print shows
 * everything (app/globals.css). The layout survives client navigation, so the effect runs again for each new page.
 */
export function ScrollEffects() {
  const pathname = usePathname();

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const root = getComputedStyle(document.documentElement);
    const token = (name: string) => root.getPropertyValue(name).trim();
    const slow = parseFloat(token("--aap-duration-slow")) || 400;
    const ribbon = parseFloat(token("--aap-duration-ribbon")) || 1400;
    const easeOut = token("--aap-easing-out") || "ease-out";
    const easeStandard = token("--aap-easing-standard") || "ease";
    const phone = window.matchMedia("(max-width: 767px)").matches;

    const stops: VoidFunction[] = [];
    const animations: Animation[] = [];

    for (const group of document.querySelectorAll<HTMLElement>("[data-reveal-group]")) {
      if (overlapsViewport(group)) continue;
      const items = group.hasAttribute("data-reveal-item")
        ? [group]
        : [...group.querySelectorAll<HTMLElement>("[data-reveal-item]")];
      const style = getComputedStyle(group);
      const stagger = parseFloat(style.getPropertyValue("--reveal-stagger")) || 60;
      const delay = parseFloat(style.getPropertyValue("--reveal-delay")) || 0;

      // Paused at time 0 with backwards fill, each animation holds its item at the first keyframe until it plays.
      const held: Animation[] = [];
      items.forEach((item, index) => {
        const timing = { duration: slow, delay: delay + index * stagger, fill: "backwards" as const };
        held.push(item.animate([{ opacity: 0 }, { opacity: 1 }], { ...timing, easing: easeStandard }));
        held.push(item.animate([{ translate: "0 12px" }, { translate: "0 0" }], { ...timing, easing: easeOut }));
      });
      if (group.classList.contains("aap-steps")) {
        held.push(
          group.animate([{ scale: phone ? "1 0" : "0 1" }, { scale: "1 1" }], {
            duration: ribbon,
            easing: easeOut,
            fill: "backwards",
            pseudoElement: "::before",
          }),
        );
      }
      held.forEach((animation) => animation.pause());
      animations.push(...held);

      stops.push(
        inView(group, () => held.forEach((animation) => animation.play()), { margin: "0px 0px -10% 0px" }),
      );
    }

    return () => {
      stops.forEach((stop) => stop());
      animations.forEach((animation) => animation.cancel());
    };
  }, [pathname]);

  return null;
}

/** True when any part of the element is inside the window. */
function overlapsViewport(element: Element) {
  const rect = element.getBoundingClientRect();
  return rect.bottom > 0 && rect.top < window.innerHeight;
}
