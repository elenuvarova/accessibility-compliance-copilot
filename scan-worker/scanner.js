import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { lookup } from "dns/promises";
import net from "net";

const args = process.argv.slice(2);
const url = args[0];
const cookiesIdx = args.indexOf("--cookies");
const cookiesStr = cookiesIdx !== -1 ? args[cookiesIdx + 1] : null;

if (!url) {
  process.stderr.write("Usage: node scanner.js <url> [--cookies <json>]\n");
  process.exit(1);
}

// SSRF guard (defense in depth — the API also validates before spawning).
// Block non-http(s) schemes and hostnames that resolve to non-public IPs,
// re-checked after navigation since a page can redirect to an internal host.
function ipIsBlocked(ip) {
  if (net.isIPv4(ip)) {
    const o = ip.split(".").map(Number);
    if (o[0] === 10) return true;
    if (o[0] === 127) return true;
    if (o[0] === 0) return true;
    if (o[0] === 169 && o[1] === 254) return true; // link-local / metadata
    if (o[0] === 172 && o[1] >= 16 && o[1] <= 31) return true;
    if (o[0] === 192 && o[1] === 168) return true;
    if (o[0] >= 224) return true; // multicast / reserved
    return false;
  }
  const v = ip.toLowerCase();
  if (v === "::1" || v === "::") return true;
  if (v.startsWith("fe80") || v.startsWith("fc") || v.startsWith("fd")) return true;
  return false;
}

async function assertUrlSafe(rawUrl) {
  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch {
    throw new Error("invalid URL");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("blocked URL scheme");
  }
  const host = parsed.hostname;
  if (net.isIP(host)) {
    if (ipIsBlocked(host)) throw new Error("blocked non-public address");
    return;
  }
  const results = await lookup(host, { all: true });
  for (const { address } of results) {
    if (ipIsBlocked(address)) throw new Error("blocked non-public address");
  }
}

try {
  await assertUrlSafe(url);
} catch (err) {
  process.stderr.write("URL rejected: " + err.message + "\n");
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

  // Redirects may have landed us on an internal host — re-validate the final URL.
  await assertUrlSafe(page.url());

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
