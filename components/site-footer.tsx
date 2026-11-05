import Link from "next/link";
import { Icon } from "@/components/icon";
import { Logo } from "@/components/logo";
import { contactEmail, footerColumns, socialProfiles } from "@/lib/site";

/** The site footer, a Partner Navy chapter (Figma: Footer). */
export function SiteFooter() {
  return (
    <footer className="aap-footer aap-surface-inverse">
      <div className="aap-container">
        <div className="aap-footer__grid lg:grid-cols-[minmax(0,1.8fr)_repeat(4,minmax(0,1fr))]">
          {/* On tablets (two columns) the brand block spans both, then the link columns sit two by two. */}
          <div className="flex flex-col items-start gap-5 sm:col-span-2 lg:col-span-1">
            <Link href="/" className="shrink-0 rounded-sm no-underline">
              <Logo ground="dark" />
            </Link>
            <p className="max-w-[320px] text-body-sm text-ink-secondary">
              An embedded AI team for companies in the United States, Australia and the United Kingdom. Based in the
              Philippines.
            </p>
            <a href={`mailto:${contactEmail}`} className="text-body-sm font-medium">
              {contactEmail}
            </a>
          </div>

          {footerColumns.map((column) => (
            <div key={column.heading}>
              <h2 className="aap-footer__heading">
                {column.heading}
              </h2>
              <ul className="aap-footer__list">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href}>{link.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="aap-footer__base">
          <p>© 2026 Alliance AI Partners. [Registered address]. [Company number].</p>
          <ul className="flex items-center gap-4 text-ink-secondary">
            {socialProfiles.map((profile) => (
              <li key={profile.name} className="flex">
                {profile.href ? (
                  <a href={profile.href} className="flex rounded-sm" aria-label={`Alliance AI Partners on ${profile.name}`}>
                    <Icon name={profile.icon} className="size-5" />
                  </a>
                ) : (
                  // No profile address yet (docs/website/README.md, question 16): drawn as in Figma, not a link.
                  <Icon name={profile.icon} className="size-5" />
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}
