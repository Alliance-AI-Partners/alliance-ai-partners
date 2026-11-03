#!/usr/bin/env node
/*
 * Render a brand-kit page to a PNG preview with Playwright (Chromium).
 *
 *   node brand-kit/tools/capture.cjs <page.html> <out.png> [--selector "#artefact"] [--width 1440] [--height 900] [--scale 2] [--full] [--hide ".aap-header"]
 *
 * With --selector (default "#artefact" when the page has one) the element alone is captured; otherwise the viewport,
 * or the whole page with --full. --hide takes a CSS selector to hide first, such as a sticky header that would paint over
 * an element capture. Fonts and images load from disk, so run it from anywhere.
 * Needs Playwright: `npm i -D playwright` in a project, or point PLAYWRIGHT_PATH at an existing node_modules/playwright.
 */
const path = require("path");
const { pathToFileURL } = require("url");

const { chromium } = require(process.env.PLAYWRIGHT_PATH || "playwright");

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  if (i === -1) return fallback;
  const v = process.argv[i + 1];
  return v === undefined || v.startsWith("--") ? true : v;
}

(async () => {
  const [page, out] = process.argv.slice(2).filter((a, i, all) => !a.startsWith("--") && !(all[i - 1] || "").startsWith("--"));
  if (!page || !out) {
    console.error("usage: capture.cjs <page.html> <out.png> [--selector css] [--width px] [--height px] [--scale n] [--full]");
    process.exit(2);
  }
  const width = Number(arg("width", 1440));
  const height = Number(arg("height", 900));
  const scale = Number(arg("scale", 1));
  let browser;
  try {
    browser = await chromium.launch();
  } catch {
    browser = await chromium.launch({ channel: "chrome" }); // the installed Chrome when no bundled browser is present
  }
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: scale, reducedMotion: "reduce" });
  const tab = await ctx.newPage();
  await tab.goto(pathToFileURL(path.resolve(page)).href, { waitUntil: "networkidle" });
  await tab.evaluate(async () => {
    // walk the page once so loading="lazy" images below the fold load before a full-page capture
    for (let y = 0; y < document.documentElement.scrollHeight; y += innerHeight) {
      scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 60));
    }
    scrollTo(0, 0);
    await Promise.all([...document.images].map((img) => (img.complete ? null : new Promise((r) => { img.onload = img.onerror = r; }))));
    await document.fonts.ready;
  });
  const hide = arg("hide", null);
  if (hide && hide !== true) await tab.addStyleTag({ content: `${hide} { visibility: hidden !important; }` });
  const selector = arg("selector", (await tab.$("#artefact")) ? "#artefact" : null);
  if (selector && selector !== true) {
    await tab.locator(selector).first().screenshot({ path: out, animations: "disabled" });
  } else {
    await tab.screenshot({ path: out, fullPage: Boolean(arg("full", false)), animations: "disabled" });
  }
  await browser.close();
  console.log(`${out} (${width}x${height} @${scale}x${selector && selector !== true ? `, ${selector}` : ""})`);
})().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
