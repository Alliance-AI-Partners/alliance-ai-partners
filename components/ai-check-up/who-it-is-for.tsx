import Image from "next/image";
import Link from "@/components/site-link";
import { CheckList } from "@/components/blocks/check-list";
import facetedLeaves from "@/design-system/imagery/backgrounds/faceted-leaves.jpg";
import { contactHref } from "@/lib/site";

/**
 * AI check-up: who it suits and who should skip it, a Partner Navy chapter (Figma: Section · Who it is for, IMG-02-2).
 * From 1024px the image (560 x 680) sits left of the text. On phones the head comes first, then the image cropped
 * square, then the two lists. The text column is `display: contents` below 1024px so `order` can place the image.
 */
export function WhoItIsFor() {
  return (
    <section aria-labelledby="who-title" className="aap-section aap-surface-inverse">
      <div className="aap-container grid gap-7 lg:grid-cols-[minmax(0,560fr)_minmax(0,680fr)] lg:items-center lg:gap-20">
        <div className="relative order-2 aspect-square overflow-hidden rounded-lg lg:order-first lg:aspect-[560/680]">
          <Image
            src={facetedLeaves}
            alt=""
            fill
            sizes="(min-width: 1024px) 40vw, 100vw"
            className="object-cover object-[20%_50%]"
          />
        </div>

        <div className="contents lg:flex lg:flex-col lg:gap-8">
          <div className="order-1 flex flex-col gap-4 lg:gap-8">
            <h2 id="who-title" className="aap-h1">
              For teams that know AI could <span className="aap-accent">help.</span>
            </h2>
            <p className="text-body-lg text-ink-secondary">
              It suits companies whose teams are buried in slow, manual work and who want a clear plan before they
              spend.
            </p>
          </div>

          <div className="order-3 flex flex-col gap-1">
            <h3 className="aap-h4">A good fit if</h3>
            <CheckList
              iconClassName="text-ribbon-cyan"
              items={[
                { id: "typing", text: "Your team types the same information into more than one system." },
                { id: "repeats", text: "The same questions, quotes or reports come back every week." },
                { id: "plan", text: "You want a plan and a fixed price before you commit to a build." },
                { id: "people", text: "You can bring the people who do the work into a few short interviews." },
              ]}
            />
          </div>

          <div className="order-4 flex flex-col gap-1">
            <h3 className="aap-h4">Skip it if</h3>
            <CheckList
              icon="arrow-right"
              iconClassName="text-ink-secondary"
              items={[
                {
                  id: "quote",
                  text: (
                    <>
                      You already know what you want built.{" "}
                      <Link href={contactHref("fixed-quote")}>Ask us for a fixed quote</Link> instead.
                    </>
                  ),
                },
                {
                  id: "developer",
                  text: (
                    <>
                      You need a developer on your team now. Read about{" "}
                      <Link href="/services/embedded-developers">embedded developers</Link>.
                    </>
                  ),
                },
              ]}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
