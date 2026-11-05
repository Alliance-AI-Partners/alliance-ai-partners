"use client";

import Link from "@/components/site-link";
import { type CSSProperties, useEffect, useRef } from "react";
import { Icon } from "@/components/icon";
import { Logo } from "@/components/logo";
import { contactEmail, mobileMenuNav, primaryAction } from "@/lib/site";

/**
 * The menu button and the full-screen menu sheet shown below 1024px (Figma: Header, Viewport=Mobile, and
 * Home — Mobile · Menu open). The sheet is a native modal <dialog>: it traps focus, closes on Escape, and the
 * browser returns focus to the menu button when it closes.
 */
export function MobileMenu() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const openButtonRef = useRef<HTMLButtonElement>(null);

  const open = () => dialogRef.current?.showModal();
  const close = () => dialogRef.current?.close();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    // Return focus to the menu button, also in browsers that do not restore it themselves.
    const onClose = () => openButtonRef.current?.focus({ preventScroll: true });
    dialog.addEventListener("close", onClose);

    // The desktop header shows the full navigation, so close the sheet if the window grows past 1024px.
    const desktop = window.matchMedia("(min-width: 1024px)");
    const onResize = (event: MediaQueryListEvent) => {
      if (event.matches && dialog.open) dialog.close();
    };
    desktop.addEventListener("change", onResize);

    return () => {
      dialog.removeEventListener("close", onClose);
      desktop.removeEventListener("change", onResize);
    };
  }, []);

  return (
    <>
      <button
        ref={openButtonRef}
        type="button"
        className="aap-button aap-header__menu inline-flex w-11 px-0 lg:hidden"
        aria-haspopup="dialog"
        aria-label="Open menu"
        onClick={open}
      >
        <Icon name="menu" className="size-6" />
      </button>

      <dialog
        ref={dialogRef}
        aria-label="Menu"
        className="site-menu m-0 h-dvh max-h-none w-full max-w-none overflow-y-auto overscroll-contain border-0 bg-page p-0 text-ink backdrop:bg-transparent"
      >
        <div className="flex min-h-full flex-col">
          <div className="aap-container flex min-h-[72px] items-center justify-between gap-8">
            <Link href="/" onClick={close} className="shrink-0 rounded-sm no-underline">
              <Logo />
            </Link>
            <button
              type="button"
              className="aap-button inline-flex w-11 px-0"
              aria-label="Close menu"
              onClick={close}
            >
              <Icon name="close" className="size-6" />
            </button>
          </div>

          <nav aria-label="Main" className="aap-container pt-2">
            <ul>
              {mobileMenuNav.map((item, index) => (
                <li key={item.href} className="site-menu__item" style={{ "--item-index": index } as CSSProperties}>
                  <Link
                    href={item.href}
                    onClick={close}
                    className="aap-h3 flex min-h-16 items-center justify-between gap-4 border-b border-line text-ink no-underline"
                  >
                    {item.label}
                    <Icon name="chevron-right" className="size-6 shrink-0 text-ink-secondary" />
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className="aap-container mt-auto flex flex-col items-start gap-4 pt-4 pb-10">
            <Link
              href={primaryAction.href}
              onClick={close}
              className="aap-button aap-button--primary aap-button--lg w-full"
            >
              {primaryAction.label}
              <Icon name="arrow-right" />
            </Link>
            <a
              href={`mailto:${contactEmail}`}
              className="text-[0.875rem] leading-[1.55] font-medium"
            >
              {contactEmail}
            </a>
          </div>
        </div>
      </dialog>
    </>
  );
}
