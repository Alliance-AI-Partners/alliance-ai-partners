import localFont from "next/font/local";

/*
 * Mona Sans and Mona Sans Mono, self-hosted from the design system's font folder (SIL OFL 1.1).
 * next/font serves the files from this site, preloads them and makes a size-matched fallback,
 * so text does not jump when the web font arrives. It does not subset local fonts.
 *
 * Only the upright Mona Sans file is loaded. The brand never sets type in italics, and every
 * file listed here is preloaded on every page, so the 749 KB italic master stays out until a
 * page needs it. To add it, add a second `src` entry with `style: "italic"`.
 */
export const monaSans = localFont({
  src: "../design-system/fonts/mona-sans/MonaSansVF-wdth-opsz-wght.ttf",
  style: "normal",
  weight: "200 900",
  variable: "--font-mona-sans",
  display: "swap",
  // The width axis has to be declared, or the browser clamps font-stretch to 100% and the
  // Expanded display type (125%) falls back to normal width.
  declarations: [{ prop: "font-stretch", value: "75% 125%" }],
});

export const monaSansMono = localFont({
  src: "../design-system/fonts/mona-sans/MonaSansMonoVF-wght.ttf",
  style: "normal",
  weight: "200 900",
  variable: "--font-mona-sans-mono",
  display: "swap",
});
