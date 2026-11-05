"use client";

import { useLinkStatus } from "next/link";
import { useEffect, useSyncExternalStore } from "react";

/*
 * The page-loading feedback (plans/007). Every internal link carries a LinkPendingSignal (components/site-link.tsx);
 * while a link's navigation is waiting for its page, the ribbon bar at the top of the window shows. The bar fades in
 * only after 150ms (app/globals.css, .site-loading-bar), so quick navigations never flash it. A route-level
 * loading.tsx was not used: it would put a loading state into the static HTML of every page (see the plan).
 */

let pendingLinks = 0;
const listeners = new Set<() => void>();

function changePending(delta: number) {
  pendingLinks = Math.max(0, pendingLinks + delta);
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Rendered inside a <Link>: reports while that link's navigation is pending. Renders nothing. */
export function LinkPendingSignal() {
  const { pending } = useLinkStatus();
  useEffect(() => {
    if (!pending) return;
    changePending(1);
    return () => changePending(-1);
  }, [pending]);
  return null;
}

/** The ribbon bar shown at the top of the window while a link's page is on its way. Decorative. */
export function NavigationProgress() {
  const active = useSyncExternalStore(
    subscribe,
    () => pendingLinks > 0,
    () => false,
  );
  return <div aria-hidden="true" className="site-loading-bar" data-active={active} />;
}
