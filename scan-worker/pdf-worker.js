import { chromium } from "playwright";
import { readFileSync } from "fs";

const htmlFile = process.argv[2];
if (!htmlFile) {
  process.stderr.write("Usage: node pdf-worker.js <html-file>\n");
  process.exit(1);
}

const html = readFileSync(htmlFile, "utf-8");

const browser = await chromium.launch({
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});

try {
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: "domcontentloaded" });
  const pdf = await page.pdf({
    format: "A4",
    printBackground: false,
    margin: { top: "18mm", bottom: "18mm", left: "15mm", right: "15mm" },
  });
  process.stdout.write(pdf);
} catch (err) {
  process.stderr.write(err.message + "\n");
  process.exit(1);
} finally {
  await browser.close();
}
