import { cn } from "@/lib/cn";

/**
 * The swallow mascot (Figma: Graphic/Swallow, from design-system/imagery/graphics/mascot-swallow-mono-black.svg),
 * drawn in the text colour: Partner Navy on Daylight, Daylight on a Partner Navy chapter. The viewBox keeps the
 * component's padding, so a 240 x 192 box matches Figma's frame. Decorative.
 */
export function Swallow({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 592 473"
      aria-hidden="true"
      focusable="false"
      className={cn("block aspect-[592/473] h-auto fill-current", className)}
    >
      <path d="M95.48,55.98l273.75,90.75,65.62,94.13-18.17-45.22,41.65-13.93,19.18-4.9,28.17,6.5,11.19,13.32,26.88,11.71-27.24,10.09-83.45,98.7-15.2,17.48-33.08-53.09-11.91,12.33,27.81,46.5-18.62,6.28-109,11,24.66-39.91,131.14-74.01-53.42,21.73-32.73-52.98-89.65,147.4-129.62,64.52,50.62-55.25-126.06,14.56,175.88-67.88,37.39-40.66L70.12,48l25.36,7.98ZM112.69,122.57l-63.88-17.88,122.25,111.5,43.91,12.91-102.28-106.53ZM317.62,285.2l24.12-41.12,17.17,27.7-44.86,18.73,3.57-5.31Z" />
    </svg>
  );
}
