import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { lookup } from "dns/promises";
import net from "net";
import { PNG } from "pngjs";

// ── WCAG contrast helpers (pure functions) ─────────────────────────────────────
// sRGB channel (0–255) → linearized value per WCAG 2.x relative-luminance formula.
function srgbChannelToLinear(c) {
  const cs = c / 255;
  return cs <= 0.03928 ? cs / 12.92 : Math.pow((cs + 0.055) / 1.055, 2.4);
}

// Relative luminance of an {r,g,b} colour (0–255 channels) per WCAG.
function relativeLuminance(r, g, b) {
  const R = srgbChannelToLinear(r);
  const G = srgbChannelToLinear(g);
  const B = srgbChannelToLinear(b);
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

// Contrast ratio between two luminances per WCAG: (Lmax+0.05)/(Lmin+0.05).
function contrastRatio(l1, l2) {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Parse "rgb(r, g, b)" / "rgba(r, g, b, a)" → {r,g,b} or null.
function parseRgb(str) {
  if (!str) return null;
  const m = str.match(/rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/i);
  if (!m) return null;
  return { r: Math.round(+m[1]), g: Math.round(+m[2]), b: Math.round(+m[3]) };
}

const MAX_CONTRAST_NODES = 80;
const MAX_SAMPLED_PIXELS = 5000;
const ANIMATED_FRAMES = 3;
const FRAME_DELAY_MS = 250;

// Given a decoded PNG of the background behind text and the text luminance,
// return the 5th-percentile-worst contrast (95% of bg pixels meet at least this).
function worstContrastFromPng(png, textLum) {
  const { width, height, data } = png;
  const total = width * height;
  // Downsample stride so we sample at most ~MAX_SAMPLED_PIXELS pixels.
  const stride = Math.max(1, Math.floor(Math.sqrt(total / MAX_SAMPLED_PIXELS)));
  const contrasts = [];
  for (let y = 0; y < height; y += stride) {
    for (let x = 0; x < width; x += stride) {
      const idx = (width * y + x) << 2;
      const alpha = data[idx + 3];
      if (alpha <= 10) continue; // skip transparent pixels
      const bgLum = relativeLuminance(data[idx], data[idx + 1], data[idx + 2]);
      contrasts.push(contrastRatio(textLum, bgLum));
    }
  }
  if (contrasts.length === 0) return null;
  contrasts.sort((a, b) => a - b);
  const i = Math.floor(0.05 * contrasts.length);
  return contrasts[Math.min(i, contrasts.length - 1)];
}

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

  // ── Pixel-level contrast measurement for "incomplete" color-contrast nodes ──
  // axe flags text over a canvas/image/gradient/translucency as "incomplete"
  // because it cannot read the effective background. We screenshot the region
  // behind the text and measure the real contrast ratio to resolve PASS/FAIL.
  const contrastChecks = [];
  let measuredCount = 0;
  let skippedForCap = 0;

  // Let the hero/canvas animation reach a stable rendered state before we start
  // sampling backgrounds, so a single just-loaded frame isn't measured.
  await page.waitForTimeout(600);

  for (const item of results.incomplete || []) {
    if (item.id !== "color-contrast") continue;
    for (const node of item.nodes || []) {
      const target = node.target || [];
      const key = target.join(", ");
      // Only same-document, single-selector targets. Multi-element targets are
      // iframe paths — leave those as needs_manual.
      if (target.length !== 1) continue;
      if (measuredCount >= MAX_CONTRAST_NODES) {
        skippedForCap++;
        continue;
      }
      measuredCount++;
      const sel = target[0];

      const locator = page.locator(sel).first();
      try {
        // (a) Gather text color, font, geometry, and whether the element sits
        //     over animated content (canvas/video). We use a Playwright locator
        //     so the screenshot step (below) auto-scrolls the exact element box
        //     into view and captures only that box — robust to fixed headers,
        //     below-the-fold content, and virtual/transform-based scrolling.
        const info = await locator.evaluate((el) => {
          const r = el.getBoundingClientRect();
          if (r.width < 1 || r.height < 1) return { ok: false };
          const cs = getComputedStyle(el);
          if (cs.visibility === "hidden" || cs.display === "none") {
            return { ok: false };
          }
          // Is the element painted over a canvas/video? Hit-testing alone misses
          // a full-bleed background canvas (e.g. a WebGL particle field) that
          // shows through transparent ancestors but is not hit-test-reachable,
          // so also flag any visible CANVAS/VIDEO whose box overlaps this element.
          const cx = r.left + r.width / 2;
          const cy = r.top + r.height / 2;
          const stack = document.elementsFromPoint(cx, cy) || [];
          let animated = stack.some(
            (e) => e.tagName === "CANVAS" || e.tagName === "VIDEO"
          );
          if (!animated) {
            for (const media of document.querySelectorAll("canvas, video")) {
              const mr = media.getBoundingClientRect();
              if (mr.width < 1 || mr.height < 1) continue;
              const ms = getComputedStyle(media);
              if (ms.visibility === "hidden" || ms.display === "none") continue;
              const overlaps =
                mr.left < r.right &&
                mr.right > r.left &&
                mr.top < r.bottom &&
                mr.bottom > r.top;
              if (overlaps) {
                animated = true;
                break;
              }
            }
          }
          return {
            ok: true,
            color: cs.color,
            fontPx: parseFloat(cs.fontSize) || 0,
            weight: parseInt(cs.fontWeight, 10) || 400,
            animated,
          };
        });

        if (!info || !info.ok) continue;

        const textColor = parseRgb(info.color);
        if (!textColor) continue;
        const textLum = relativeLuminance(textColor.r, textColor.g, textColor.b);

        // (b) AA threshold: large text → 3.0, else 4.5.
        const large =
          info.fontPx >= 24 || (info.fontPx >= 18.66 && info.weight >= 700);
        const threshold = large ? 3.0 : 4.5;

        const frameCount = info.animated ? ANIMATED_FRAMES : 1;
        const framePcts = []; // per-frame 5th-percentile-worst contrast
        let framesMeasured = 0;

        for (let f = 0; f < frameCount; f++) {
          if (f > 0) await page.waitForTimeout(FRAME_DELAY_MS);
          // (c) Hide the element's own text so the screenshot captures only the
          //     background behind it, then restore inline styles immediately.
          await locator.evaluate((el) => {
            el.dataset.__prevColor = el.style.getPropertyValue("color");
            el.dataset.__prevColorPrio = el.style.getPropertyPriority("color");
            el.dataset.__prevShadow = el.style.getPropertyValue("text-shadow");
            el.dataset.__prevShadowPrio =
              el.style.getPropertyPriority("text-shadow");
            el.style.setProperty("color", "transparent", "important");
            el.style.setProperty("text-shadow", "none", "important");
          });

          let buf;
          try {
            // locator.screenshot scrolls the element into view and clips to its
            // exact box — captures only the background behind this element.
            buf = await locator.screenshot({ timeout: 5000 });
          } finally {
            // Restore inline color/text-shadow no matter what.
            await locator.evaluate((el) => {
              el.style.removeProperty("color");
              el.style.removeProperty("text-shadow");
              if (el.dataset.__prevColor) {
                el.style.setProperty(
                  "color",
                  el.dataset.__prevColor,
                  el.dataset.__prevColorPrio
                );
              }
              if (el.dataset.__prevShadow) {
                el.style.setProperty(
                  "text-shadow",
                  el.dataset.__prevShadow,
                  el.dataset.__prevShadowPrio
                );
              }
              delete el.dataset.__prevColor;
              delete el.dataset.__prevColorPrio;
              delete el.dataset.__prevShadow;
              delete el.dataset.__prevShadowPrio;
            });
          }

          const png = PNG.sync.read(buf);
          const c = worstContrastFromPng(png, textLum);
          if (c == null) continue;
          framesMeasured++;
          framePcts.push(c);
        }

        if (framePcts.length === 0) continue; // no measurable pixels → needs_manual

        // Across frames take the WORST (minimum) 5th-percentile contrast, so an
        // animated background is judged at its least-favorable measured moment.
        // (Non-animated nodes have a single frame, so this is just that p5.)
        framePcts.sort((a, b) => a - b);
        const worst = framePcts[0];
        const contrast = Math.round(worst * 100) / 100;
        contrastChecks.push({
          key,
          measured: true,
          contrast,
          threshold,
          pass: contrast >= threshold,
          animated: !!info.animated,
          frames: framesMeasured,
        });
      } catch {
        // One node's failure must not abort the scan; omit it (stays needs_manual).
        continue;
      }
    }
  }

  const passN = contrastChecks.filter((c) => c.pass).length;
  const failN = contrastChecks.length - passN;
  process.stderr.write(
    `contrast measured: ${contrastChecks.length}, pass: ${passN}, fail: ${failN}` +
      (skippedForCap ? ` (capped, skipped ${skippedForCap})` : "") +
      "\n"
  );

  process.stdout.write(
    JSON.stringify({
      meta,
      violations: results.violations,
      incomplete: results.incomplete,
      contrastChecks,
    })
  );
} catch (err) {
  process.stderr.write(err.message + "\n");
  process.exit(1);
} finally {
  await browser.close();
}
