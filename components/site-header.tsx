import Link from "next/link";
import { HeaderNav } from "@/components/header-nav";
import { Logo } from "@/components/logo";
import { MobileMenu } from "@/components/mobile-menu";
import { primaryAction } from "@/lib/site";

/**
 * The sticky site header (Figma: Header). From 1024px it shows the navigation and the Secondary SM action; below
 * that, the logo and a menu button. The design system switches at 640px; the site switches at 1024px so the bar never
 * overflows on tablets.
 */
export function SiteHeader() {
  return (
    <header className="aap-header">
      <div className="aap-container aap-header__bar">
        <Link href="/" className="shrink-0 rounded-sm no-underline">
          <Logo eager />
        </Link>

        <div className="flex items-center gap-8">
          <HeaderNav />
          <Link href={primaryAction.href} className="aap-button aap-button--sm hidden lg:inline-flex">
            {primaryAction.label}
          </Link>
          <MobileMenu />
        </div>
      </div>
    </header>
  );
}
