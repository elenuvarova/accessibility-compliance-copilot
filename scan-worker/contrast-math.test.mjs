// Standalone sanity check for the WCAG luminance/contrast math used by the
// pixel-level contrast measurement in scanner.js. Run: node contrast-math.test.mjs
//
// These are the canonical reference values:
//   #000 vs #fff -> 21.00 (the maximum possible WCAG contrast)
//   #777 vs #fff -> 4.48  (the textbook "just under AA for normal text" value)
//
// The helpers are duplicated here (kept in sync with scanner.js) so this file is
// dependency-free and runnable on its own.

function srgbChannelToLinear(c) {
  const cs = c / 255;
  return cs <= 0.03928 ? cs / 12.92 : Math.pow((cs + 0.055) / 1.055, 2.4);
}
function relativeLuminance(r, g, b) {
  return (
    0.2126 * srgbChannelToLinear(r) +
    0.7152 * srgbChannelToLinear(g) +
    0.0722 * srgbChannelToLinear(b)
  );
}
function contrastRatio(l1, l2) {
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}

function approx(label, got, want, tol = 0.01) {
  const ok = Math.abs(got - want) <= tol;
  console.log(`${ok ? "PASS" : "FAIL"} ${label}: ${got.toFixed(2)} (expect ${want})`);
  if (!ok) process.exitCode = 1;
}

const black = relativeLuminance(0, 0, 0);
const white = relativeLuminance(255, 255, 255);
const grey = relativeLuminance(0x77, 0x77, 0x77);

approx("#000 vs #fff", contrastRatio(black, white), 21.0);
approx("#777 vs #fff", contrastRatio(grey, white), 4.48);
