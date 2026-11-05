import Image, { type StaticImageData } from "next/image";
import type { ReactNode } from "react";
import Link from "@/components/site-link";
import { cn } from "@/lib/cn";

type ArticleCardProps = {
  href: string;
  title: string;
  /** The kind and reading time, for example "Guide · 6 min read". */
  meta: ReactNode;
  image: StaticImageData;
  alt: string;
  /** The image box's aspect ratio: Figma's card image is 420 x 263. */
  imageClassName?: string;
  sizes?: string;
  headingLevel?: "h2" | "h3";
  className?: string;
};

/** An article teaser (Figma: Article card): the image, then the title in Heading 4 and the meta caption. */
export function ArticleCard({
  href,
  title,
  meta,
  image,
  alt,
  imageClassName = "aspect-[420/263]",
  sizes = "(min-width: 1024px) 30vw, 100vw",
  headingLevel: Heading = "h3",
  className,
}: ArticleCardProps) {
  return (
    <article className={cn("group relative flex flex-col", className)}>
      <div className={cn("aap-media relative border border-line", imageClassName)}>
        <Image src={image} alt={alt} fill sizes={sizes} className="object-cover" />
      </div>
      <Heading className="aap-h4 mt-4">
        {/* The title's link covers the whole card, so the card is one target and one tab stop. */}
        <Link href={href} className="text-ink no-underline after:absolute after:inset-0 group-hover:underline">
          {title}
        </Link>
      </Heading>
      <p className="mt-4 text-caption text-ink-tertiary">{meta}</p>
    </article>
  );
}

type PersonTileProps = {
  name: ReactNode;
  role: ReactNode;
  /** A photograph; until one exists the tile shows the "Photo to come" placeholder from Figma. */
  photo?: StaticImageData;
  alt?: string;
  className?: string;
};

/** A team member (Figma: Person tile): a 4:5 photo, the name in Heading 4 and the role in Body/SM. */
export function PersonTile({ name, role, photo, alt = "", className }: PersonTileProps) {
  return (
    <div className={cn("flex flex-col", className)}>
      {photo ? (
        <div className="aap-media relative aspect-[300/375] border border-line">
          <Image src={photo} alt={alt} fill sizes="(min-width: 1024px) 22vw, 50vw" className="object-cover" />
        </div>
      ) : (
        <div className="grid aspect-[300/375] place-items-center rounded-lg border border-dashed border-line bg-sunken">
          <span className="text-caption text-ink-tertiary">Photo to come</span>
        </div>
      )}
      <p className="aap-h4 mt-3">{name}</p>
      <p className="mt-3 text-body-sm text-ink-secondary">{role}</p>
    </div>
  );
}
