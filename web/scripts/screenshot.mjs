// A4 screenshot: 1920 x 1080 CSS px at device scale 2 -> 3840 x 2160 PNG.
// Needs `npm run build` and a running `npm run preview` (port 4173), or pass a URL:
//   node scripts/screenshot.mjs [url] [out.png]
// Uses the Playwright-managed Chromium; set CHROMIUM_PATH to use another binary.
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const url = process.argv[2] ?? "http://localhost:4173/?present=1&shot=1";
const out = process.argv[3] ?? path.resolve(here, "../../assets/A4_dashboard.png");

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
const errors = [];
page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") errors.push(`${m.type()}: ${m.text()}`); });
page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
await page.goto(url, { waitUntil: "networkidle" });
await page.waitForFunction(() => window.__READY === true, null, { timeout: 180000 });
await page.waitForTimeout(1500);
await page.screenshot({ path: out });
await browser.close();
console.log(`saved ${out}`);
if (errors.length) {
  console.log(`console messages (${errors.length}):`);
  for (const e of errors) console.log("  " + e);
  process.exitCode = errors.some((e) => e.startsWith("error") || e.startsWith("pageerror")) ? 2 : 0;
} else console.log("no console errors or warnings");
