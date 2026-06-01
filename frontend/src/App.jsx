import { useState, useEffect, useRef, useCallback } from "react";

const SEVERITY_ORDER = { critical: 0, serious: 1, moderate: 2, minor: 3 };

function parseJson(raw) {
  try { return JSON.parse(raw || "[]"); } catch { return []; }
}
// Convert raw axe wcag_criteria tags to readable SC numbers: ["wcag2aa","wcag143"] → ["1.4.3"]
function formatWcagCriteria(raw) {
  return parseJson(raw)
    .filter((t) => t.startsWith("wcag") && /^\d{3,}$/.test(t.slice(4)))
    .map((t) => { const d = t.slice(4); return `${d[0]}.${d[1]}.${d.slice(2)}`; });
}
function parseUrls(text) {
  return text.split("\n").map((u) => u.trim()).filter((u) => u.length > 0);
}
function legalRisk(counts) {
  if (counts.critical > 0 || counts.serious >= 10) return "high";
  if (counts.serious > 0) return "medium";
  return "low";
}

const RULE_GUIDANCE = {
  "color-contrast": "Use browser devtools (Accessibility → Color Picker) or Colour Contrast Analyser. Measure the exact ratio between text and background.",
  "color-contrast-enhanced": "Check for 7:1 ratio (WCAG AAA). Confirm with a dedicated contrast tool.",
  "keyboard": "Disconnect your mouse. Navigate with Tab, Shift+Tab, Enter, Space, arrows. Every interactive element must be reachable.",
  "focus-trap": "Tab into the component. Verify focus cycles within it and Esc exits cleanly.",
  "focus-visible": "Tab to each interactive element. Every focused control must show a clearly visible focus ring.",
  "label": "Use a screen reader. Tab to each form input — verify the announced label describes its purpose.",
  "aria-required-attr": "Inspect with devtools and screen reader. Verify required ARIA attributes are present.",
  "image-alt": "Disable images or test with screen reader. Alt text must describe purpose, not appearance.",
  "link-name": "Tab to the link with screen reader. The announced name must describe the destination.",
  "button-name": "Tab to the button with screen reader. The announced name must describe what it does.",
  "video-caption": "Play the video muted. Verify captions are accurate, synchronized, include speaker ID.",
  "audio-caption": "Verify a text transcript is provided near the audio content.",
  "target-size": "On a touch device (or Chrome DevTools touch mode), verify tap targets are ≥24×24 px.",
  "link-in-text-block": "Verify inline links are distinguishable from surrounding text without relying on color.",
  "scrollable-region-focusable": "Tab to the scrollable container. Verify it receives focus and responds to arrow keys.",
  "td-headers-attr": "Navigate the table with screen reader. Each cell must announce its row and column headers.",
  "page-has-heading-one": "Verify the page has exactly one <h1>. Test with NVDA/JAWS heading navigation (H key).",
  "landmark-one-main": "Check that the page has exactly one <main> landmark.",
};
const DEFAULT_GUIDANCE =
  "Test with a screen reader (VoiceOver on Mac, NVDA on Windows) and keyboard-only navigation.";

// ── Theme toggle ──────────────────────────────────────────────────────────────

function useTheme() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem("a11y-theme") || "dark"; } catch { return "dark"; }
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme === "light" ? "light" : "");
    try { localStorage.setItem("a11y-theme", theme); } catch { /* ignore */ }
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "light" ? "dark" : "light")), []);
  return [theme, toggle];
}

function ThemeToggle({ theme, onToggle }) {
  return (
    <button
      className="theme-toggle"
      onClick={onToggle}
      aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
      title={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
    >
      {theme === "light" ? "○" : "●"}
    </button>
  );
}

// ── Badges ────────────────────────────────────────────────────────────────────

function ScoreBadge({ score }) {
  const tier = score >= 80 ? "good" : score >= 60 ? "warn" : "bad";
  return (
    <span className={`score-badge score-${tier}`} title="Release-readiness score">
      {score}<span className="score-denom">/100</span>
    </span>
  );
}

function LegalRiskBadge({ counts }) {
  const risk = legalRisk(counts);
  const label = { high: "⚠ High EAA/ADA Risk", medium: "EAA/ADA Risk", low: "✓ Low Legal Risk" }[risk];
  return <span className={`legal-risk-badge risk-${risk}`}>{label}</span>;
}

// ── Sitemap picker ────────────────────────────────────────────────────────────

function SitemapPicker({ urls, onSelect, onClose }) {
  const [checked, setChecked] = useState(() => new Set(urls.slice(0, 20)));
  const toggle = (u) => setChecked((s) => { const n = new Set(s); n.has(u) ? n.delete(u) : n.add(u); return n; });
  return (
    <div className="sitemap-overlay" onClick={onClose}>
      <div className="sitemap-modal" onClick={(e) => e.stopPropagation()}>
        <div className="sitemap-modal-header">
          <span>Found {urls.length} URLs</span>
          <div className="sitemap-actions">
            <button className="smap-btn" onClick={() => setChecked(new Set(urls))}>All</button>
            <button className="smap-btn" onClick={() => setChecked(new Set())}>None</button>
          </div>
          <button className="sitemap-close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="sitemap-list">
          {urls.map((u) => (
            <label key={u} className="sitemap-item">
              <input type="checkbox" checked={checked.has(u)} onChange={() => toggle(u)} />
              <span className="sitemap-url">{u}</span>
            </label>
          ))}
        </div>
        <div className="sitemap-footer">
          <button
            className="smap-btn smap-btn-primary"
            disabled={checked.size === 0}
            onClick={() => { onSelect([...checked]); onClose(); }}
          >
            Scan selected ({checked.size})
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Interactive sparkline ─────────────────────────────────────────────────────

function cubicBezierPath(points) {
  if (points.length < 2) return "";
  const d = [`M ${points[0][0].toFixed(1)} ${points[0][1].toFixed(1)}`];
  for (let i = 1; i < points.length; i++) {
    const [x0, y0] = points[i - 1];
    const [x1, y1] = points[i];
    const cpx = (x0 + x1) / 2;
    d.push(`C ${cpx.toFixed(1)} ${y0.toFixed(1)}, ${cpx.toFixed(1)} ${y1.toFixed(1)}, ${x1.toFixed(1)} ${y1.toFixed(1)}`);
  }
  return d.join(" ");
}

function ScoreSparkline({ history, large }) {
  const W = large ? 600 : 320;
  const H = large ? 120 : 64;
  const PAD = large ? 16 : 12;
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  const n = history.length;
  if (n < 2) return null;

  const xs = history.map((_, i) => PAD + (i / (n - 1)) * (W - 2 * PAD));
  const ys = history.map((h) => H - PAD - (h.score / 100) * (H - 2 * PAD));
  const pts = xs.map((x, i) => [x, ys[i]]);

  const latest = history[n - 1].score;
  const colorVar = latest >= 80 ? "var(--color-success)" : latest >= 60 ? "var(--color-warning)" : "var(--color-danger)";
  const fillColorVar = latest >= 80 ? "var(--color-success-bg)" : latest >= 60 ? "var(--color-warning-bg)" : "var(--color-danger-bg)";

  const pathD = cubicBezierPath(pts);
  // Close the gradient fill area by going down and back
  const fillD = pathD + ` L ${xs[n - 1].toFixed(1)} ${H} L ${xs[0].toFixed(1)} ${H} Z`;

  const gradientId = `sg-${large ? "l" : "s"}`;

  const handleMouseMove = (e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * W;
    let closest = 0;
    let minDist = Infinity;
    xs.forEach((x, i) => {
      const dist = Math.abs(x - mouseX);
      if (dist < minDist) { minDist = dist; closest = i; }
    });
    const h = history[closest];
    setTooltip({
      index: closest,
      x: (xs[closest] / W) * 100,
      y: (ys[closest] / H) * 100,
      data: h,
    });
  };

  return (
    <div
      className="history-sparkline-container"
      style={{ position: "relative", display: "inline-block", width: large ? "100%" : `${W}px` }}
      onMouseLeave={() => setTooltip(null)}
    >
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        className={large ? "score-sparkline-large" : "score-sparkline"}
        aria-hidden="true"
        onMouseMove={handleMouseMove}
        style={{ display: "block", width: large ? "100%" : `${W}px`, height: `${H}px` }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={colorVar} stopOpacity="0.25" />
            <stop offset="100%" stopColor={colorVar} stopOpacity="0.03" />
          </linearGradient>
        </defs>
        {/* Gradient fill */}
        <path d={fillD} fill={`url(#${gradientId})`} />
        {/* Animated line */}
        <path
          d={pathD}
          className="sparkline-path"
          fill="none"
          stroke={colorVar}
          strokeWidth={large ? "2.5" : "2"}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {/* Data points */}
        {history.map((h, i) => (
          <circle
            key={i}
            cx={xs[i].toFixed(1)}
            cy={ys[i].toFixed(1)}
            r={tooltip?.index === i ? (large ? 6 : 5) : (large ? 3.5 : 3)}
            fill={tooltip?.index === i ? colorVar : fillColorVar}
            stroke={colorVar}
            strokeWidth="1.5"
            style={{ transition: "r .1s" }}
          >
            <title>Scan #{h.id} — {h.score}/100 ({h.total} issues)</title>
          </circle>
        ))}
        {/* Y-axis labels for large variant */}
        {large && (
          <>
            <text x={PAD - 4} y={PAD} textAnchor="end" fontSize="9" fill="var(--color-text-faint)">100</text>
            <text x={PAD - 4} y={H / 2} textAnchor="end" fontSize="9" fill="var(--color-text-faint)" dominantBaseline="middle">50</text>
            <text x={PAD - 4} y={H - PAD} textAnchor="end" fontSize="9" fill="var(--color-text-faint)" dominantBaseline="auto">0</text>
            <line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD} stroke="var(--color-border)" strokeWidth="1" />
            <line x1={PAD} y1={H / 2} x2={W - PAD} y2={H / 2} stroke="var(--color-border)" strokeWidth="0.5" strokeDasharray="3,3" />
          </>
        )}
      </svg>
      {tooltip && (
        <div
          className="sparkline-tooltip"
          style={{ left: `${tooltip.x}%`, top: `${tooltip.y}%` }}
          aria-hidden="true"
        >
          <div className="sparkline-tooltip-title">Scan #{tooltip.data.id}</div>
          <div className="sparkline-tooltip-row">
            <span>Score</span>
            <span className="sparkline-tooltip-val">{tooltip.data.score}/100</span>
          </div>
          {tooltip.data.completed_at && (
            <div className="sparkline-tooltip-row">
              <span>Date</span>
              <span className="sparkline-tooltip-val">
                {new Date(tooltip.data.completed_at).toLocaleDateString()}
              </span>
            </div>
          )}
          {tooltip.data.critical != null && (
            <div className="sparkline-tooltip-row">
              <span>Critical</span>
              <span className="sparkline-tooltip-val" style={{ color: "var(--color-critical-text)" }}>
                {tooltip.data.critical}
              </span>
            </div>
          )}
          {tooltip.data.serious != null && (
            <div className="sparkline-tooltip-row">
              <span>Serious</span>
              <span className="sparkline-tooltip-val" style={{ color: "var(--color-serious-text)" }}>
                {tooltip.data.serious}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── History view ──────────────────────────────────────────────────────────────

function HistoryView({ history, diff, currentScanId }) {
  if (!history || history.length === 0)
    return (
      <div className="tab-empty">
        <span className="tab-empty-title">No scan history yet</span>
        <p className="tab-empty-desc">History and regression tracking will appear after your first completed scan.</p>
      </div>
    );
  return (
    <div className="history-view">
      <div className="history-header">
        <div style={{ flex: 1, minWidth: 260 }}>
          <ScoreSparkline history={history} large />
        </div>
        {diff?.has_baseline && (
          <div className={`diff-card ${diff.fixed_count >= diff.new_count ? "diff-improving" : "diff-regressing"}`}>
            <span className="diff-stat diff-fixed">↓ {diff.fixed_count} fixed</span>
            <span className="diff-stat diff-new">↑ {diff.new_count} new</span>
            <span className="diff-baseline">vs scan #{diff.baseline_scan_id}</span>
          </div>
        )}
        {diff && !diff.has_baseline && (
          <div className="diff-card diff-first">First scan — no baseline yet.</div>
        )}
      </div>
      <table className="history-table">
        <thead>
          <tr><th>Scan</th><th>Date</th><th>Score</th><th>Total</th><th>Critical</th><th>Serious</th><th>Mod.</th><th>Minor</th></tr>
        </thead>
        <tbody>
          {[...history].reverse().map((h) => (
            <tr key={h.id} className={h.id === currentScanId ? "history-row-current" : ""}>
              <td className="mono">#{h.id}{h.id === currentScanId ? " ●" : ""}</td>
              <td className="small">{h.completed_at ? new Date(h.completed_at).toLocaleString() : "—"}</td>
              <td><ScoreBadge score={h.score} /></td>
              <td>{h.total}</td>
              <td className={h.critical > 0 ? "count-critical" : ""}>{h.critical}</td>
              <td className={h.serious > 0 ? "count-serious" : ""}>{h.serious}</td>
              <td>{h.moderate}</td>
              <td>{h.minor}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Backlog view ──────────────────────────────────────────────────────────────

function BacklogSection({ priority, label, sublabel, components, issueCount, emptyMsg, legalBadge }) {
  const isEmpty = components.length === 0;
  const cls = { P0: "critical", P1: "serious", P2: "moderate" }[priority] ?? "minor";
  return (
    <div className={`backlog-section backlog-${cls}`}>
      <div className="backlog-section-header">
        <span className={`priority-badge priority-${cls}`}>{priority}</span>
        <div className="backlog-section-title">
          <strong>{label}</strong>
          <span className="backlog-sublabel">{sublabel}</span>
        </div>
        {!isEmpty && legalBadge && <span className="legal-badge">{legalBadge}</span>}
        <span className="backlog-count">
          {isEmpty ? "0 issues" : `${issueCount} ${issueCount === 1 ? "issue" : "issues"} · ${components.length} ${components.length === 1 ? "component" : "components"}`}
        </span>
      </div>
      {isEmpty ? (
        <p className="backlog-empty">{emptyMsg}</p>
      ) : (
        <div className="backlog-items">
          {components.map((c) => (
            <div key={c.id} className="backlog-item">
              <span className={`badge badge-sev-${c.top_severity} backlog-item-sev`}>{c.top_severity}</span>
              <span className="backlog-item-name">{c.name}</span>
              <span className="backlog-item-issues">{c.issue_count} {c.issue_count === 1 ? "issue" : "issues"}</span>
              <span className="backlog-item-rules">{parseJson(c.rule_ids).join(" · ")}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BacklogView({ components, allIssues }) {
  const p0 = components.filter((c) => c.top_severity === "critical");
  const p1 = components.filter((c) => c.top_severity === "serious");
  const p2 = components.filter((c) => c.top_severity === "moderate" || c.top_severity === "minor");
  const count = (sev) => allIssues.filter((i) => i.severity === sev).length;
  if (components.length === 0) {
    return (
      <div className="tab-empty">
        <span className="tab-empty-title">No components found</span>
        <p className="tab-empty-desc">Run a scan to see component-level accessibility issues grouped by priority.</p>
      </div>
    );
  }
  return (
    <div className="backlog">
      <BacklogSection priority="P0" label="Fix Before Shipping"
        sublabel="Critical WCAG Level A violations — functional blockers for assistive technology users"
        components={p0} issueCount={count("critical")} emptyMsg="✓ No critical violations found." />
      <BacklogSection priority="P1" label="Fix This Sprint"
        sublabel="Serious WCAG 2.2 AA violations — EAA compliance risk and ADA Title III"
        components={p1} issueCount={count("serious")} emptyMsg="✓ No serious violations found." legalBadge="EAA · ADA" />
      <BacklogSection priority="P2" label="Schedule in Backlog"
        sublabel="Moderate & minor issues — quality improvements and broader coverage"
        components={p2} issueCount={count("moderate") + count("minor")} emptyMsg="✓ No moderate or minor issues found." />
    </div>
  );
}

// ── Components view ───────────────────────────────────────────────────────────

function ComponentsView({ components }) {
  if (!components || components.length === 0)
    return (
      <div className="tab-empty">
        <span className="tab-empty-title">No components detected</span>
        <p className="tab-empty-desc">Run a scan first to see components ranked by accessibility debt.</p>
      </div>
    );
  const maxDebt = Math.max(...components.map((c) => c.debt_score), 1);
  return (
    <div className="components-list">
      {components.map((c, idx) => {
        const rules = parseJson(c.rule_ids);
        const pct = Math.round((c.debt_score / maxDebt) * 100);
        return (
          <div key={c.id} className={`component-card top-sev-${c.top_severity}`}>
            <div className="component-rank">#{idx + 1}</div>
            <div className="component-body">
              <div className="component-header">
                <span className="component-name">{c.name}</span>
                <span className={`badge badge-sev-${c.top_severity}`}>{c.top_severity}</span>
                <span className="component-stats">{c.issue_count} {c.issue_count === 1 ? "issue" : "issues"} · {c.pages_affected} {c.pages_affected === 1 ? "page" : "pages"}</span>
                <span className="debt-score">debt {c.debt_score}</span>
              </div>
              <div className="debt-bar"><div className="debt-bar-fill" style={{ width: `${pct}%` }} /></div>
              <div className="component-meta">
                <span className="mono small truncate" title={c.sample_selector}>{c.sample_selector}</span>
                {rules.length > 0 && <span className="rule-list">{rules.join(" · ")}</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── WCAG context block ────────────────────────────────────────────────────────

function WcagContextBlock({ chunks }) {
  const [open, setOpen] = useState(false);
  if (!chunks || chunks.length === 0) return null;
  return (
    <div className="wcag-context-block">
      <button className="wcag-toggle" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        {open ? "▾" : "▸"} WCAG Sources ({chunks.length})
      </button>
      {open && (
        <div className="wcag-chunks">
          {chunks.map((c) => (
            <div key={c.criterion_id} className="wcag-chunk">
              <div className="wcag-chunk-header">
                <span className="wcag-sc-id">SC {c.criterion_id}</span>
                <span className="wcag-sc-title">{c.title}</span>
                <span className={`wcag-level wcag-level-${c.level.toLowerCase()}`}>Level {c.level}</span>
              </div>
              <pre className="wcag-chunk-text">{c.text}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Holistic AI review ────────────────────────────────────────────────────────

const DIMENSION_ICONS = {
  plain_language: "📖",
  cognitive_load: "🧠",
  form_usability: "📝",
  navigation_structure: "🧭",
  content_organization: "📐",
};

const HOLISTIC_STEPS = [
  { key: "plain_language",       label: "Plain language & reading level" },
  { key: "cognitive_load",       label: "Cognitive load & decision complexity" },
  { key: "form_usability",       label: "Form usability & error prevention" },
  { key: "navigation_structure", label: "Navigation structure & heading hierarchy" },
  { key: "content_organization", label: "Content organization & scanability" },
];

function HolisticProgress() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (activeStep >= HOLISTIC_STEPS.length) return;
    const delay = 2000 + Math.random() * 1500;
    const t = setTimeout(() => setActiveStep((s) => s + 1), delay);
    return () => clearTimeout(t);
  }, [activeStep]);

  return (
    <div className="holistic-progress">
      <div className="holistic-progress-title">Running AI review… (may take 10–20 s)</div>
      <div className="holistic-progress-steps" role="status" aria-label="Analysis progress">
        {HOLISTIC_STEPS.map((step, i) => {
          const isDone = i < activeStep;
          const isActive = i === activeStep;
          return (
            <div
              key={step.key}
              className={`holistic-progress-step${isDone ? " step-done" : isActive ? " step-active" : ""}`}
            >
              <span className="step-icon" aria-hidden="true">
                {isDone ? <span className="step-check">✓</span> : isActive ? <span className="spinner" /> : <span style={{ color: "var(--color-border)" }}>○</span>}
              </span>
              <span>{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ScoreRing({ score }) {
  const cls = score >= 8 ? "dim-score-good" : score >= 6 ? "dim-score-warn" : "dim-score-bad";
  return (
    <span className={`dim-score ${cls}`}>{score}<span className="dim-denom">/10</span></span>
  );
}

// ── Shared AI error state ─────────────────────────────────────────────────────
// Distinguishes three failure modes so the message is actionable:
//   1. missing / invalid key  → tell the user to set GROQ_API_KEY
//   2. rate limit (429)        → tell them the daily limit is hit + when to retry
//   3. anything else           → generic inline error with retry

function AiError({ error, onRetry }) {
  const lower = (error || "").toLowerCase();

  if (lower.includes("groq_api_key") || lower.includes("not set") || lower.includes("invalid")) {
    return (
      <div className="groq-callout">
        <div className="groq-callout-title">AI features need a key</div>
        <p className="groq-callout-body">
          AI features require a <code>GROQ_API_KEY</code>. Get a free key at{" "}
          <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer">
            console.groq.com
          </a>
          , then set it in your environment and restart the server.
        </p>
      </div>
    );
  }

  if (lower.includes("rate limit") || error.includes("429")) {
    return (
      <div className="groq-callout groq-callout-limit">
        <div className="groq-callout-title">Daily AI limit reached</div>
        <p className="groq-callout-body">{error}</p>
        {onRetry && <button className="inline-error-retry" onClick={onRetry}>Try again</button>}
      </div>
    );
  }

  return (
    <div className="inline-error">
      <span>Error: {error}</span>
      {onRetry && <button className="inline-error-retry" onClick={onRetry}>Retry</button>}
    </div>
  );
}

function HolisticView({ scanId, review, loading, onRun, error }) {
  if (loading) return <HolisticProgress />;

  if (error) return <AiError error={error} onRetry={onRun} />;

  if (!review) return (
    <div className="holistic-empty">
      <p>AI holistic review evaluates what axe-core cannot detect:</p>
      <ul>
        <li>Plain language &amp; reading level</li>
        <li>Cognitive load &amp; decision complexity</li>
        <li>Form usability &amp; error prevention</li>
        <li>Navigation structure &amp; heading hierarchy</li>
        <li>Content organization &amp; scanability</li>
      </ul>
      <button className="holistic-run-btn" onClick={onRun}>Run AI Review</button>
    </div>
  );

  if (review.error) return <AiError error={review.error} onRetry={onRun} />;

  const overall = review.overall ?? 0;
  const overallCls = overall >= 70 ? "holistic-overall-good" : overall >= 50 ? "holistic-overall-warn" : "holistic-overall-bad";

  return (
    <div className="holistic-view">
      <div className="holistic-header">
        <div className="holistic-overall">
          <span className={`holistic-score ${overallCls}`}>{overall}</span>
          <span className="holistic-score-label">/100 overall</span>
        </div>
        <div className="holistic-summary-block">
          <p className="holistic-summary">{review.summary}</p>
          {review.top_issue && (
            <div className="holistic-top-issue">
              <span className="holistic-top-label">Top issue:</span> {review.top_issue}
            </div>
          )}
        </div>
      </div>

      <div className="dimension-grid">
        {(review.dimensions || []).map((d) => {
          const barCls = d.score >= 8 ? "dimension-bar-good" : d.score >= 6 ? "dimension-bar-warn" : "dimension-bar-bad";
          return (
            <div key={d.key} className="dimension-card">
              <div className="dimension-header">
                <span className="dimension-icon" aria-hidden="true">{DIMENSION_ICONS[d.key] || "●"}</span>
                <span className="dimension-name">{d.name}</span>
                <ScoreRing score={d.score} />
              </div>
              <div className="dimension-bar-track">
                <div className={`dimension-bar-fill ${barCls}`} style={{ width: `${d.score * 10}%` }} />
              </div>
              <p className="dimension-finding">{d.finding}</p>
              <div className="dimension-rec">
                <span className="dimension-rec-label">Rec:</span> {d.recommendation}
              </div>
            </div>
          );
        })}
      </div>

      <button className="holistic-rerun-btn" onClick={onRun}>Re-run Review</button>
    </div>
  );
}

// ── Issues table ──────────────────────────────────────────────────────────────

function IssuesView({ pages, fixSuggestions, fixLoading, fixErrors, onGetFix, scanStatus }) {
  if (scanStatus === "running") {
    return (
      <div style={{ paddingTop: "var(--space-4)" }}>
        <div className="skeleton-row" />
        <div className="skeleton-row" />
        <div className="skeleton-row" />
      </div>
    );
  }

  const allEmpty = pages?.every((p) => p.issues.length === 0);
  if (!pages || pages.length === 0 || allEmpty) {
    return (
      <div className="tab-empty">
        <span className="tab-empty-title">No issues found on scanned pages</span>
        <p className="tab-empty-desc">All pages passed automated accessibility checks. Run a manual review for deeper coverage.</p>
      </div>
    );
  }

  return pages.map((page) => {
    const sorted = [...page.issues].sort(
      (a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4)
    );
    return (
      <div key={page.id} className="page-block">
        <h2 className="page-url">{page.url}</h2>
        {sorted.length === 0 ? <p className="muted">No issues on this page.</p> : (
          <table>
            <thead>
              <tr><th>Rule</th><th>Severity</th><th>WCAG</th><th>Selector</th><th>Coverage</th><th></th></tr>
            </thead>
            <tbody>
              {sorted.map((issue) => {
                const fix = fixSuggestions[issue.id];
                const loading = fixLoading[issue.id];
                const fixErr = fixErrors?.[issue.id];
                return [
                  <tr key={issue.id} className={`sev-${issue.severity}`}>
                    <td><a href={issue.help_url} target="_blank" rel="noopener noreferrer">{issue.rule_id}</a></td>
                    <td><span className={`badge badge-sev-${issue.severity}`}>{issue.severity}</span></td>
                    <td className="mono small">{formatWcagCriteria(issue.wcag_criteria).join(" ") || "—"}</td>
                    <td className="mono small truncate">{issue.selector}</td>
                    <td>
                      <span className={`badge ${issue.verification === "auto" ? "badge-auto" : "badge-manual"}`}>
                        {issue.verification === "auto" ? "auto" : "needs review"}
                      </span>
                    </td>
                    <td>
                      {loading ? (
                        <span className="skeleton-fix" />
                      ) : (
                        <button className={`get-fix-btn${fix ? " got-fix" : ""}`}
                          onClick={() => !fix && onGetFix(issue.id)}
                          disabled={loading || !!fix} title="Get AI fix suggestion">
                          {fix ? "✦" : "Fix"}
                        </button>
                      )}
                    </td>
                  </tr>,
                  fixErr && (
                    <tr key={`${issue.id}-err`} className="fix-row">
                      <td colSpan={6}>
                        <div className="inline-error">
                          <span>{fixErr}</span>
                          <button className="inline-error-retry" onClick={() => onGetFix(issue.id)}>Retry</button>
                        </div>
                      </td>
                    </tr>
                  ),
                  fix && (
                    <tr key={`${issue.id}-fix`} className="fix-row">
                      <td colSpan={6}>
                        <div className="fix-suggestion">
                          <span className="fix-label">✦ AI Fix</span>
                          <span className="fix-text">{fix.text}</span>
                        </div>
                        <WcagContextBlock chunks={fix.wcag} />
                      </td>
                    </tr>
                  ),
                ];
              })}
            </tbody>
          </table>
        )}
      </div>
    );
  });
}

// ── Review queue ──────────────────────────────────────────────────────────────

function ReviewView({ allIssues, issueStatuses, onStatusChange, fixSuggestions, fixLoading, fixErrors, onGetFix }) {
  const items = allIssues.filter((i) => i.verification === "needs_manual");
  if (items.length === 0)
    return (
      <div className="tab-empty">
        <span className="tab-empty-title">No manual review items</span>
        <p className="tab-empty-desc">All issues were auto-verified. No manual testing required for this scan.</p>
      </div>
    );
  const reviewed = items.filter((i) => (issueStatuses[i.id] ?? i.status) !== "open").length;
  const pct = Math.round((reviewed / items.length) * 100);
  return (
    <div className="review-queue">
      <div className="review-progress-row">
        <div className="review-progress-track">
          <div className="review-progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="review-progress-label">{reviewed} of {items.length} reviewed</span>
      </div>
      {items.map((issue) => {
        const status = issueStatuses[issue.id] ?? issue.status;
        const wcag = formatWcagCriteria(issue.wcag_criteria);
        const isDone = status !== "open";
        const fix = fixSuggestions[issue.id];
        const loading = fixLoading[issue.id];
        const fixErr = fixErrors?.[issue.id];
        return (
          <div key={issue.id} className={`review-item${isDone ? ` review-item-${status}` : ""}`}>
            <div className="review-item-header">
              <span className={`review-dot dot-${status}`} aria-hidden="true" />
              <a href={issue.help_url} target="_blank" rel="noopener noreferrer" className="review-rule-id">{issue.rule_id}</a>
              {wcag.length > 0 && <span className="mono small review-wcag">{wcag.join(" ")}</span>}
              <span className="mono small truncate review-selector" title={issue.selector}>{issue.selector}</span>
            </div>
            <p className="review-description">{issue.description}</p>
            <div className="review-guidance">
              <span className="review-guidance-label">How to test:</span> {RULE_GUIDANCE[issue.rule_id] || DEFAULT_GUIDANCE}
            </div>
            {issue.html_snippet && (
              <details className="review-snippet">
                <summary>HTML snippet</summary>
                <pre className="review-snippet-code">{issue.html_snippet}</pre>
              </details>
            )}
            {fixErr && (
              <div className="inline-error">
                <span>{fixErr}</span>
                <button className="inline-error-retry" onClick={() => onGetFix(issue.id)}>Retry</button>
              </div>
            )}
            {fix && (
              <>
                <div className="fix-suggestion fix-suggestion-review">
                  <span className="fix-label">✦ AI Fix</span>
                  <span className="fix-text">{fix.text}</span>
                </div>
                <WcagContextBlock chunks={fix.wcag} />
              </>
            )}
            <div className="review-actions">
              {!isDone ? (
                <>
                  <button className="review-btn btn-pass" onClick={() => onStatusChange(issue.id, "fixed")}>✓ Pass</button>
                  <button className="review-btn btn-flag" onClick={() => onStatusChange(issue.id, "wont_fix")}>⚑ Flag</button>
                </>
              ) : (
                <>
                  <span className={`review-result result-${status}`}>{status === "fixed" ? "✓ Passed" : "⚑ Flagged"}</span>
                  <button className="review-btn btn-undo" onClick={() => onStatusChange(issue.id, "open")}>Undo</button>
                </>
              )}
              {!fix && (
                <button className="review-btn btn-fix-ai" onClick={() => onGetFix(issue.id)} disabled={loading}>
                  {loading ? "Getting fix…" : "✦ Get Fix"}
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Manual testing checklist ──────────────────────────────────────────────────

const CATEGORY_ICONS = {
  "Screen Reader": "🔊",
  "Keyboard": "⌨",
  "Visual": "👁",
  "Forms": "📋",
  "Cognitive": "🧠",
  "Mobile": "📱",
};

function ManualChecklistView({ scanId, checklist, loading, checklistError, checklistStatuses, onGenerate, onStatusChange }) {
  if (loading) {
    return (
      <div style={{ paddingTop: "var(--space-4)" }}>
        <div className="skeleton-card" />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
      </div>
    );
  }

  if (checklistError) return <AiError error={checklistError} onRetry={onGenerate} />;

  if (checklist.length === 0)
    return (
      <div className="checklist-empty">
        <p>AI generates a targeted manual testing checklist covering what axe-core cannot detect:</p>
        <ul>
          <li>Meaningful alt text quality (not just presence)</li>
          <li>Logical keyboard focus order and no focus traps</li>
          <li>Screen reader announcements of dynamic content</li>
          <li>Color not used as the only means of conveying information</li>
          <li>Form error messages and recovery instructions</li>
          <li>Page usability at 400% zoom</li>
        </ul>
        <button className="checklist-generate-btn" onClick={onGenerate}>Generate Checklist</button>
      </div>
    );

  const categories = [...new Set(checklist.map((c) => c.category))];
  const done = checklist.filter((c) => (checklistStatuses[c.id] ?? c.status) !== "pending").length;
  const pct = Math.round((done / checklist.length) * 100);

  return (
    <div className="checklist-view">
      <div className="checklist-progress-row">
        <div className="checklist-progress-track">
          <div className="checklist-progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <span className="checklist-progress-label">{done}/{checklist.length} tested</span>
        <button className="checklist-regen-btn" onClick={onGenerate}>Regenerate</button>
      </div>

      {categories.map((cat) => {
        const items = checklist.filter((c) => c.category === cat);
        return (
          <div key={cat} className="checklist-category">
            <div className="checklist-cat-header">
              <span className="checklist-cat-icon" aria-hidden="true">{CATEGORY_ICONS[cat] || "●"}</span>
              <span className="checklist-cat-name">{cat}</span>
              <span className="checklist-cat-count">{items.length} {items.length === 1 ? "item" : "items"}</span>
            </div>
            {items.map((item) => {
              const status = checklistStatuses[item.id] ?? item.status;
              return (
                <div key={item.id} className={`checklist-item checklist-item-${status}`}>
                  <div className="checklist-item-meta">
                    {item.criterion_id && <span className="checklist-sc">SC {item.criterion_id}</span>}
                    <span className="checklist-tools">{item.tools_needed}</span>
                  </div>
                  <p className="checklist-description">{item.description}</p>
                  {item.steps && (
                    <details className="checklist-steps">
                      <summary>Testing steps</summary>
                      <pre className="checklist-steps-text">{item.steps}</pre>
                    </details>
                  )}
                  <div className="checklist-actions">
                    {status === "pending" ? (
                      <>
                        <button className="check-btn check-pass" onClick={() => onStatusChange(item.id, "pass")}>✓ Pass</button>
                        <button className="check-btn check-fail" onClick={() => onStatusChange(item.id, "fail")}>✗ Fail</button>
                        <button className="check-btn check-skip" onClick={() => onStatusChange(item.id, "skip")}>— Skip</button>
                      </>
                    ) : (
                      <>
                        <span className={`check-result result-${status}`}>
                          {status === "pass" ? "✓ Passed" : status === "fail" ? "✗ Failed" : "— Skipped"}
                        </span>
                        <button className="check-btn check-undo" onClick={() => onStatusChange(item.id, "pending")}>Undo</button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

// ── Compliance report ─────────────────────────────────────────────────────────

function ComplianceReportView({ report, loading, reportError, onGenerate }) {
  const copy = (text) => navigator.clipboard.writeText(text).catch(() => {});

  if (loading) {
    return (
      <div style={{ paddingTop: "var(--space-4)" }}>
        <div className="skeleton-card" style={{ height: 60 }} />
        <div className="skeleton-card" />
        <div className="skeleton-card" />
      </div>
    );
  }

  if (reportError) return <AiError error={reportError} onRetry={onGenerate} />;

  if (!report)
    return (
      <div className="report-empty">
        <p>AI writes a compliance report in plain language for non-technical stakeholders:</p>
        <ul>
          <li>Executive summary — board / legal / C-suite language, no jargon</li>
          <li>WCAG Level A and AA conformance breakdown</li>
          <li>Developer-facing remediation priorities</li>
          <li>Sprint-based remediation timeline</li>
          <li>Ready-to-copy WCAG conformance statement for EAA / ADA documents</li>
        </ul>
        <button className="report-generate-btn" onClick={onGenerate}>Generate Report</button>
      </div>
    );

  if (report.error) return <AiError error={report.error} onRetry={onGenerate} />;

  const scoreCls = report.score >= 80 ? "report-score-good" : report.score >= 60 ? "report-score-warn" : "report-score-bad";
  const riskCls = { HIGH: "report-risk-high", MEDIUM: "report-risk-medium", LOW: "report-risk-low" }[report.risk] || "";

  return (
    <div className="report-view">
      <div className="report-header">
        <div className="report-meta-row">
          <span className="report-project-name">{report.project_name}</span>
          <span className="report-meta-sep">·</span>
          <span className="report-date">{report.scan_date}</span>
          <span className="report-meta-sep">·</span>
          <span className={`report-score-inline ${scoreCls}`}>{report.score}/100</span>
          <span className={`report-risk-inline ${riskCls}`}>{report.risk} risk</span>
        </div>
        <div className="report-counts-row">
          <span className="count-critical">{report.counts?.critical ?? 0} critical</span>
          <span className="count-serious">{report.counts?.serious ?? 0} serious</span>
          <span className="count-moderate">{report.counts?.moderate ?? 0} moderate</span>
          <span className="count-minor">{report.counts?.minor ?? 0} minor</span>
          <span className="report-pages">{report.pages_scanned} page{report.pages_scanned !== 1 ? "s" : ""}</span>
        </div>
      </div>

      <section className="report-section">
        <div className="report-section-header">
          <h3 className="report-section-title">Executive Summary</h3>
          <button className="copy-btn" onClick={() => copy(report.executive_summary)} title="Copy to clipboard">Copy</button>
        </div>
        <p className="report-text report-executive">{report.executive_summary}</p>
      </section>

      <section className="report-section">
        <h3 className="report-section-title">WCAG Conformance</h3>
        <div className="wcag-level-grid">
          <div className={`wcag-level-card ${report.failing_level_a > 0 ? "level-failing" : "level-passing"}`}>
            <span className="wcag-level-label">Level A</span>
            <span className="wcag-level-num">{report.failing_level_a}</span>
            <span className="wcag-level-sub">criteria failing</span>
          </div>
          <div className={`wcag-level-card ${report.failing_level_aa > 0 ? "level-failing" : "level-passing"}`}>
            <span className="wcag-level-label">Level AA</span>
            <span className="wcag-level-num">{report.failing_level_aa}</span>
            <span className="wcag-level-sub">criteria failing</span>
          </div>
        </div>
        {report.failing_criteria?.length > 0 && (
          <div className="failing-criteria-list">
            {report.failing_criteria.map((c, i) => (
              <span key={i} className="criteria-tag">{c}</span>
            ))}
          </div>
        )}
      </section>

      <section className="report-section">
        <h3 className="report-section-title">For Developers</h3>
        <p className="report-text">{report.for_developers}</p>
      </section>

      <section className="report-section">
        <h3 className="report-section-title">Remediation Timeline</h3>
        <p className="report-text">{report.remediation_timeline}</p>
      </section>

      <section className="report-section report-section-statement">
        <div className="report-section-header">
          <h3 className="report-section-title">Conformance Statement</h3>
          <button className="copy-btn" onClick={() => copy(report.wcag_conformance_statement)} title="Copy to clipboard">Copy</button>
        </div>
        <p className="report-text report-statement">{report.wcag_conformance_statement}</p>
      </section>

      <button className="report-rerun-btn" onClick={onGenerate}>Regenerate</button>
    </div>
  );
}

// ── Main app ──────────────────────────────────────────────────────────────────

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [urlsText, setUrlsText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [scanId, setScanId] = useState(null);
  const [scan, setScan] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [view, setView] = useState("backlog");
  const [issueStatuses, setIssueStatuses] = useState({});
  const [fixSuggestions, setFixSuggestions] = useState({});
  const [fixLoading, setFixLoading] = useState({});
  const [fixErrors, setFixErrors] = useState({});
  const [history, setHistory] = useState([]);
  const [diff, setDiff] = useState(null);
  const [holisticReview, setHolisticReview] = useState(null);
  const [holisticLoading, setHolisticLoading] = useState(false);
  const [holisticError, setHolisticError] = useState(null);
  // Checklist
  const [checklist, setChecklist] = useState([]);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const [checklistError, setChecklistError] = useState(null);
  const [checklistStatuses, setChecklistStatuses] = useState({});
  // Compliance report
  const [complianceReport, setComplianceReport] = useState(null);
  const [complianceReportLoading, setComplianceReportLoading] = useState(false);
  const [reportError, setReportError] = useState(null);
  // Sitemap
  const [sitemapLoading, setSitemapLoading] = useState(false);
  const [sitemapUrls, setSitemapUrls] = useState(null);
  const [sitemapError, setSitemapError] = useState(null);
  // Auth / advanced
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [cookies, setCookies] = useState("");

  const urls = parseUrls(urlsText);

  const handleDiscover = async () => {
    const first = urls[0] || urlsText.trim();
    if (!first) return;
    setSitemapLoading(true);
    setSitemapError(null);
    setSitemapUrls(null);
    try {
      const res = await fetch(`/api/sitemap?url=${encodeURIComponent(first)}`);
      if (!res.ok) {
        const e = await res.json().catch(() => ({ detail: "Not found" }));
        throw new Error(e.detail);
      }
      const { urls: found } = await res.json();
      setSitemapUrls(found);
    } catch (err) {
      setSitemapError(err.message);
    } finally {
      setSitemapLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (urls.length === 0) return;
    setSubmitting(true);
    setSubmitError(null);
    setScan(null);
    setScanId(null);
    setView("backlog");
    setIssueStatuses({});
    setFixSuggestions({});
    setFixLoading({});
    setFixErrors({});
    setHistory([]);
    setDiff(null);
    setHolisticReview(null);
    setHolisticError(null);
    setChecklist([]);
    setChecklistStatuses({});
    setChecklistError(null);
    setComplianceReport(null);
    setReportError(null);
    try {
      let baseUrl = urls[0];
      try { baseUrl = new URL(urls[0]).origin; } catch { /* as-is */ }
      const projRes = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Quick scan", base_url: baseUrl }),
      });
      if (!projRes.ok) throw new Error(`Project creation failed: ${projRes.status}`);
      const proj = await projRes.json();
      const body = { project_id: proj.id, urls };
      if (cookies.trim()) body.cookies = cookies.trim();
      const scanRes = await fetch("/api/scans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!scanRes.ok) throw new Error(`Scan start failed: ${scanRes.status}`);
      const { id } = await scanRes.json();
      setScanId(id);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!scanId) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`/api/scans/${scanId}`);
        const data = await res.json();
        setScan(data);
        if (data.status === "done" || data.status === "failed") clearInterval(timer);
      } catch { clearInterval(timer); }
    }, 2000);
    return () => clearInterval(timer);
  }, [scanId]);

  useEffect(() => {
    if (!scan || scan.status !== "done" || !scan.project_id) return;
    Promise.all([
      fetch(`/api/projects/${scan.project_id}/history`).then((r) => r.json()),
      fetch(`/api/scans/${scanId}/diff`).then((r) => r.json()),
      fetch(`/api/scans/${scanId}/manual-checklist`).then((r) => r.json()),
    ]).then(([hist, diffData, checklistData]) => {
      setHistory(hist);
      setDiff(diffData);
      setChecklist(checklistData.items || []);
    }).catch(() => {});
  }, [scan?.status, scanId]);

  const handleIssueStatus = async (issueId, newStatus) => {
    setIssueStatuses((p) => ({ ...p, [issueId]: newStatus }));
    try {
      await fetch(`/api/issues/${issueId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
    } catch {
      setIssueStatuses((p) => ({ ...p, [issueId]: "open" }));
    }
  };

  const handleGetFix = async (issueId) => {
    setFixLoading((p) => ({ ...p, [issueId]: true }));
    setFixErrors((p) => { const n = { ...p }; delete n[issueId]; return n; });
    try {
      const res = await fetch(`/api/issues/${issueId}/suggest-fix`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
      }
      const data = await res.json();
      setFixSuggestions((p) => ({ ...p, [issueId]: { text: data.suggestion, wcag: data.wcag_context || [] } }));
    } catch (err) {
      setFixErrors((p) => ({ ...p, [issueId]: err.message }));
    } finally {
      setFixLoading((p) => ({ ...p, [issueId]: false }));
    }
  };

  const handleHolisticReview = async () => {
    setHolisticLoading(true);
    setHolisticError(null);
    try {
      const res = await fetch(`/api/scans/${scanId}/holistic-review`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
      }
      setHolisticReview(await res.json());
    } catch (err) {
      setHolisticError(err.message);
    } finally {
      setHolisticLoading(false);
    }
  };

  const handleGenerateChecklist = async () => {
    setChecklistLoading(true);
    setChecklistError(null);
    try {
      const res = await fetch(`/api/scans/${scanId}/manual-checklist`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
      }
      const data = await res.json();
      setChecklist(data.items || []);
    } catch (err) {
      setChecklistError(err.message);
    } finally {
      setChecklistLoading(false);
    }
  };

  const handleChecklistStatus = async (checkId, newStatus) => {
    setChecklistStatuses((p) => ({ ...p, [checkId]: newStatus }));
    try {
      await fetch(`/api/manual-checks/${checkId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
    } catch {
      setChecklistStatuses((p) => ({ ...p, [checkId]: "pending" }));
    }
  };

  const handleGenerateComplianceReport = async () => {
    setComplianceReportLoading(true);
    setReportError(null);
    try {
      const res = await fetch(`/api/scans/${scanId}/compliance-report`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
      }
      setComplianceReport(await res.json());
    } catch (err) {
      setReportError(err.message);
    } finally {
      setComplianceReportLoading(false);
    }
  };

  const allIssues = scan?.pages?.flatMap((p) => p.issues) ?? [];
  const counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  allIssues.forEach((i) => counts[i.severity] != null && counts[i.severity]++);
  const needsManual = allIssues.filter((i) => i.verification === "needs_manual").length;
  const components = scan?.components ?? [];
  const isDone = scan?.status === "done";

  const checklistDone = checklist.filter((c) => (checklistStatuses[c.id] ?? c.status) !== "pending").length;

  const tabs = [
    { id: "backlog",     label: "Backlog" },
    { id: "components",  label: `Components (${components.length})` },
    { id: "issues",      label: `Issues (${allIssues.length})` },
    { id: "review",      label: `Review (${needsManual})` },
    { id: "ai-review",   label: "AI Review" },
    { id: "checklist",   label: `Checklist${checklist.length > 0 ? ` (${checklistDone}/${checklist.length})` : ""}` },
    { id: "report",      label: "Report" },
    { id: "history",     label: `History${history.length > 1 ? ` (${history.length})` : ""}` },
  ];

  return (
    <div className="container">
      <ThemeToggle theme={theme} onToggle={toggleTheme} />

      <h1>Accessibility Compliance Copilot</h1>
      <p className="tagline">Component-level a11y audit — honest about what automation can and can&apos;t cover.</p>

      <form onSubmit={handleSubmit} className="scan-form">
        <div className="scan-inputs">
          <div className="url-row">
            <textarea
              placeholder={"https://example.com\nhttps://example.com/about"}
              value={urlsText}
              onChange={(e) => setUrlsText(e.target.value)}
              rows={3}
              disabled={submitting}
              aria-label="URLs to scan, one per line"
            />
            <button type="submit"
              disabled={submitting || urls.length === 0 || (scan && scan.status === "running")}>
              {submitting ? (
                <span style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                  <span className="spinner" />
                  Starting…
                </span>
              ) : scan?.status === "running" ? "Scanning…"
                : urls.length > 1 ? `Scan (${urls.length})` : "Scan"}
            </button>
          </div>

          <div className="scan-tools-row">
            <button type="button" className="discover-btn"
              onClick={handleDiscover} disabled={sitemapLoading || urls.length === 0}>
              {sitemapLoading ? "Discovering…" : "⊕ Discover sitemap"}
            </button>
            {sitemapError && <span className="sitemap-error">{sitemapError}</span>}
            <button type="button" className="advanced-toggle"
              onClick={() => setShowAdvanced((v) => !v)}
              aria-expanded={showAdvanced}>
              {showAdvanced ? "▾ Advanced" : "▸ Advanced"}
            </button>
          </div>

          {showAdvanced && (
            <div className="advanced-section">
              <label className="advanced-label">
                Session cookies
                <span className="advanced-hint">JSON array or "name=val; name2=val2" — for scanning authenticated pages</span>
              </label>
              <textarea
                className="cookies-input"
                placeholder={'[{"name":"session","value":"abc","domain":"example.com","path":"/"}]'}
                value={cookies}
                onChange={(e) => setCookies(e.target.value)}
                rows={3}
              />
            </div>
          )}
        </div>
      </form>

      {sitemapUrls && (
        <SitemapPicker
          urls={sitemapUrls}
          onSelect={(selected) => setUrlsText(selected.join("\n"))}
          onClose={() => setSitemapUrls(null)}
        />
      )}

      {submitError && (
        <div className="scan-error-card" role="alert">
          <p className="scan-error-message">Scan failed: {submitError}</p>
          <button className="scan-error-retry" onClick={() => setSubmitError(null)}>
            Try again
          </button>
        </div>
      )}

      {scan && scan.status === "queued" && (
        <div className="status-row status-running">
          <div className="status-queued-row">
            <span className="spinner" />
            <span>Setting up scan…</span>
          </div>
        </div>
      )}

      {scan && scan.status !== "queued" && (
        <div className="results">
          <div className={`status-row status-${scan.status}`}>
            <span className="status-label">Status: <strong>{scan.status}</strong></span>
            {isDone && scan.release_score !== undefined && <ScoreBadge score={scan.release_score} />}
            {isDone && <LegalRiskBadge counts={counts} />}
            {isDone && diff?.has_baseline && (
              <span className="status-diff">
                {diff.fixed_count > 0 && <span className="diff-fixed-inline">↓ {diff.fixed_count} fixed</span>}
                {diff.new_count > 0 && <span className="diff-new-inline">↑ {diff.new_count} new</span>}
              </span>
            )}
            {isDone && (
              <span className="counts">
                <span className="count-critical">{counts.critical} critical</span>
                <span className="count-serious">{counts.serious} serious</span>
                <span className="count-moderate">{counts.moderate} moderate</span>
                <span className="count-minor">{counts.minor} minor</span>
                <span className="count-manual">{needsManual} need manual review</span>
              </span>
            )}
            {scan.status === "failed" && (
              <span className="error">
                {scan.error ? ` — ${scan.error}` : " — Scan failed"}
              </span>
            )}
            {scan.status === "running" && (
              <span className="status-queued-row">
                <span className="spinner" aria-hidden="true" />
              </span>
            )}
          </div>

          {scan.status === "failed" && (
            <div className="scan-error-card" role="alert">
              <p className="scan-error-message">
                {scan.error || "The scan encountered an error. Check that all URLs are reachable and try again."}
              </p>
              <button className="scan-error-retry" onClick={() => { setScan(null); setScanId(null); }}>
                Try again
              </button>
            </div>
          )}

          {isDone && (
            <div className="toolbar">
              <div className="toolbar-top">
                <div className="export-row">
                  <a href={`/api/scans/${scanId}/export/csv`} className="export-btn" download>CSV</a>
                  <a href={`/api/scans/${scanId}/export/markdown`} className="export-btn" download>MD</a>
                  <a href={`/api/scans/${scanId}/export/pdf`} className="export-btn export-btn-pdf" download>PDF</a>
                </div>
              </div>
              <div className="view-tabs" role="tablist">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    role="tab"
                    aria-selected={view === t.id}
                    className={`tab-btn${view === t.id ? " active" : ""}`}
                    onClick={() => setView(t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {isDone && view === "backlog" && <BacklogView components={components} allIssues={allIssues} />}
          {isDone && view === "components" && <ComponentsView components={components} />}
          {view === "issues" && (
            <IssuesView
              pages={scan.pages}
              fixSuggestions={fixSuggestions}
              fixLoading={fixLoading}
              fixErrors={fixErrors}
              onGetFix={handleGetFix}
              scanStatus={scan.status}
            />
          )}
          {isDone && view === "review" && (
            <ReviewView
              allIssues={allIssues}
              issueStatuses={issueStatuses}
              onStatusChange={handleIssueStatus}
              fixSuggestions={fixSuggestions}
              fixLoading={fixLoading}
              fixErrors={fixErrors}
              onGetFix={handleGetFix}
            />
          )}
          {isDone && view === "ai-review" && (
            <HolisticView
              scanId={scanId}
              review={holisticLoading ? null : holisticReview}
              loading={holisticLoading}
              error={holisticError}
              onRun={handleHolisticReview}
            />
          )}
          {isDone && view === "checklist" && (
            <ManualChecklistView
              scanId={scanId}
              checklist={checklist}
              loading={checklistLoading}
              checklistError={checklistError}
              checklistStatuses={checklistStatuses}
              onGenerate={handleGenerateChecklist}
              onStatusChange={handleChecklistStatus}
            />
          )}
          {isDone && view === "report" && (
            <ComplianceReportView
              report={complianceReportLoading ? null : complianceReport}
              loading={complianceReportLoading}
              reportError={reportError}
              onGenerate={handleGenerateComplianceReport}
            />
          )}
          {isDone && view === "history" && (
            <HistoryView history={history} diff={diff} currentScanId={scanId} />
          )}
        </div>
      )}
    </div>
  );
}
