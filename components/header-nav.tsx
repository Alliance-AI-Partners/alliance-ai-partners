"use client";

import Link from "@/components/site-link";
import { usePathname } from "next/navigation";
import { headerNav, isCurrentNav } from "@/lib/site";

/** The desktop navigation. The link for the current section carries aria-current, which draws the ribbon underline. */
export function HeaderNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Main" className="aap-nav hidden lg:flex">
      {headerNav.map((item) => {
        const current = isCurrentNav(item, pathname);
        return (
          <Link
            key={item.href}
            href={item.href}
            className="aap-nav__link"
            aria-current={current ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
