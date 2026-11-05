import Image from "next/image";
import daybreakSwallows from "@/design-system/imagery/backgrounds/daybreak-swallows.jpg";

/**
 * Home: the time difference as a benefit, a full-bleed band (Figma: Section · Overnight band, IMG-01-4). The image is
 * decorative. A Partner Navy scrim keeps the text readable: from the left from 1024px, from the top on phones, where
 * the image is cropped to the open sky.
 */
export function OvernightBand() {
  return (
    <section
      aria-labelledby="overnight-title"
      className="aap-surface-inverse relative isolate flex min-h-[600px] overflow-hidden lg:min-h-[640px] lg:items-center"
    >
      {/* The parallax layer reaches 24px past the band at the top and bottom, so it can drift without showing an edge. */}
      <div data-parallax aria-hidden="true" className="absolute inset-x-0 -top-6 -bottom-6 -z-20">
        <Image
          src={daybreakSwallows}
          alt=""
          fill
          sizes="100vw"
          className="object-cover object-[20%_50%] lg:object-center"
        />
      </div>
      <div aria-hidden="true" className="home-scrim-overnight absolute inset-0 -z-10" />

      <div className="aap-container flex flex-col gap-5 py-16 lg:gap-6">
        <h2 id="overnight-title" className="aap-display-lg max-w-[640px]">
          Brief us before
          <br /> you log off.
          <br /> See <span className="aap-accent">progress</span>
          <br /> when you log on.
        </h2>
        <p className="max-w-[560px] text-body-lg text-ink-secondary">
          For US partners, our day starts as yours ends, so work moves forward while you sleep. In the UK, our
          afternoon is your morning. In Australia, our working days overlap.
        </p>
      </div>
    </section>
  );
}
