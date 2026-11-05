import type { ReactNode } from "react";
import { ArrowLink } from "@/components/arrow-link";
import { Icon } from "@/components/icon";
import { cn } from "@/lib/cn";

type JobRowProps = {
  title: string;
  /** Where and how much, for example "Remote, Philippines · Full time". */
  meta: ReactNode;
  href: string;
  linkLabel?: string;
  headingLevel?: "h3" | "h4";
  className?: string;
};

/**
 * An open role (Figma: Job row): the title and meta on the left, "View the role" on the right, 24px above and below
 * on a bottom hairline. Figma has no phone variant; below 768px the link moves under the text (docs/website/README.md).
 */
export function JobRow({ title, meta, href, linkLabel = "View the role", headingLevel: Heading = "h3", className }: JobRowProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 border-b border-line py-6 md:flex-row md:items-center md:justify-between md:gap-8",
        className,
      )}
    >
      <div className="flex flex-col gap-1">
        <Heading className="aap-h4">{title}</Heading>
        <p className="text-body-sm text-ink-secondary">{meta}</p>
      </div>
      <ArrowLink href={href} className="self-start md:self-center">
        {linkLabel}
        <span className="sr-only">: {title}</span>
      </ArrowLink>
    </div>
  );
}

type DownloadRowProps = {
  name: string;
  /** The formats and size, in mono, for example "SVG and PNG · ZIP · [size]". */
  meta: ReactNode;
  /** The file's address; without one the row shows the action as unavailable. */
  href?: string;
  className?: string;
};

/**
 * A file to download (Figma: Download row): a file icon, the name in Body/Strong and the meta in mono, and a Quiet SM
 * "Download" button. In code the whole row is the link, so the target is the full row (docs/website/README.md).
 */
export function DownloadRow({ name, meta, href, className }: DownloadRowProps) {
  const body = (
    <>
      <span className="flex items-center gap-4">
        <Icon name="file" className="size-6 shrink-0" />
        <span className="flex flex-col gap-1">
          <span className="text-body font-semibold">{name}</span>
          <span className="aap-mono text-ink-tertiary">{meta}</span>
        </span>
      </span>
      <span className="aap-button aap-button--quiet aap-button--sm shrink-0" aria-hidden={href ? undefined : true}>
        Download
        <Icon name="download" />
      </span>
    </>
  );
  const rowClass = cn("flex items-center justify-between gap-4 border-b border-line py-4 text-ink no-underline", className);

  if (!href) {
    return (
      <div className={cn(rowClass, "opacity-60")} aria-disabled="true">
        {body}
      </div>
    );
  }
  return (
    <a href={href} download className={rowClass}>
      {body}
    </a>
  );
}
