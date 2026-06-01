import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";

const args = process.argv.slice(2);
const url = args[0];
const cookiesIdx = args.indexOf("--cookies");
const cookiesStr = cookiesIdx !== -1 ? args[cookiesIdx + 1] : null;

if (!url) {
  process.stderr.write("Usage: node scanner.js <url> [--cookies <json>]\n");
  process.exit(1);
}

function parseCookies(str, pageUrl) {
  try {
    return JSON.parse(str);
  } catch {
    const { hostname } = new URL(pageUrl);
    return str
      .split(";")
      .map((c) => c.trim())
      .filter(Boolean)
      .map((c) => {
        const eq = c.indexOf("=");
        return {
          name: c.slice(0, eq).trim(),
          value: c.slice(eq + 1).trim(),
          domain: hostname,
          path: "/",
        };
      });
  }
}

const browser = await chromium.launch({
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const context = await browser.newContext();

if (cookiesStr) {
  try {
    const cookies = parseCookies(cookiesStr, url);
    await context.addCookies(cookies);
  } catch (err) {
    process.stderr.write("Cookie warning: " + err.message + "\n");
  }
}

const page = await context.newPage();

try {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });

  const meta = await page.evaluate(() => {
    const headings = Array.from(
      document.querySelectorAll("h1,h2,h3,h4,h5,h6")
    )
      .map((h) => `${h.tagName}: ${h.textContent.trim().slice(0, 120)}`)
      .slice(0, 40)
      .join("\n");
    const bodyText = (document.body?.innerText || "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 3000);
    return { title: document.title, headings, bodyText };
  });

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();

  process.stdout.write(
    JSON.stringify({
      meta,
      violations: results.violations,
      incomplete: results.incomplete,
    })
  );
} catch (err) {
  process.stderr.write(err.message + "\n");
  process.exit(1);
} finally {
  await browser.close();
}
