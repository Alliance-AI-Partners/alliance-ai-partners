"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { headerNav } from "@/lib/site";

/** The desktop navigation. The link for the current section carries aria-current, which draws the ribbon underline. */
export function HeaderNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Main" className="aap-nav hidden lg:flex">
      {headerNav.map((item) => {
        const current = pathname === item.href || pathname.startsWith(`${item.href}/`);
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
