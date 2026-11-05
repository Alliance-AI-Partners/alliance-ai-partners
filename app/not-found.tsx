import { SiteFrame } from "@/components/site-frame";

/**
 * The page for an unknown address, inside the site frame (the root layout has no header or footer of its own).
 * Temporary: the designed 404 (Figma: 17 · System pages, frames 64:1428 and 64:1596) replaces this content.
 */
export default function NotFound() {
  return (
    <SiteFrame>
      <section aria-labelledby="not-found-title" className="aap-section">
        <div className="aap-container">
          <h1 id="not-found-title" className="aap-h1">
            This page could not be found.
          </h1>
        </div>
      </section>
    </SiteFrame>
  );
}
