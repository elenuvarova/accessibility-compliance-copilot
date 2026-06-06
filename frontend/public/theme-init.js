// Pre-paint theme: apply stored theme before React mounts to avoid a flash.
// External (not inline) so a strict CSP (script-src 'self') allows it.
// Mirrors useTheme() in App.jsx — key "a11y-theme", light => data-theme="light", dark => "".
(function () {
  try {
    var t = localStorage.getItem("a11y-theme") || "dark";
    document.documentElement.setAttribute("data-theme", t === "light" ? "light" : "");
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "");
  }
})();
