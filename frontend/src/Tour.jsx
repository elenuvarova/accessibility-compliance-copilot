import { useState, useEffect, useRef, useCallback, useLayoutEffect } from "react";

// ── Guided product tour ───────────────────────────────────────────────────────
// A custom, dependency-free coachmark/spotlight tour of the landing screen.
// Built in-house (rather than a generic library) so it can be exemplary for
// accessibility — this is an accessibility tool, after all:
//   • popover is role="dialog" aria-modal with labelled title + described body
//   • focus moves into the popover and is trapped within its buttons
//   • Esc closes/skips and restores focus to the trigger
//   • ArrowRight/ArrowLeft step forward/back; Enter/Space activate buttons
//   • the current target is spotlit with an outline ring (not colour alone)
//   • prefers-reduced-motion is honoured (see styles.css)
//   • the popover is clamped within the viewport (bottom-sheet at narrow widths)

export const TOUR_SEEN_KEY = "a11y-tour-seen";

// Steps describe the landing screen. `target` is a CSS selector resolved at
// render time; a null target renders a centered, untethered card.
export const TOUR_STEPS = [
  {
    target: null,
    title: "Welcome to a11yscan",
    body: "Here's a 20-second tour of how an audit works.",
  },
  {
    target: 'textarea[aria-label="URLs to scan, one per line"]',
    title: "Add your URLs",
    body: "Paste one or more URLs to audit — one per line.",
  },
  {
    target: ".layer-strip",
    title: "Three honest layers",
    body: "Every audit has three honest layers: automated (axe-core), AI review for what scanners miss, and a guided manual checklist.",
  },
  {
    target: ".discover-btn",
    title: "Discover a whole site",
    body: "Or give a root URL and auto-discover every page from its sitemap.",
  },
  {
    target: ".advanced-toggle",
    title: "Scanning behind a login?",
    body: "Add session cookies under Advanced to audit authenticated pages.",
  },
  {
    target: null,
    title: "You're ready",
    body: "Hit Scan to get a prioritized, WCAG 2.2-mapped backlog with a release-readiness score. Replay this tour anytime from the Tour button.",
  },
];

const POPOVER_MARGIN = 16; // viewport gutter the popover never crosses
const TARGET_GAP = 12;     // space between target and popover

// Resolve a step's target element and its viewport rect. Returns null for
// untethered (centered) steps or when the element can't be found.
function getTargetRect(target) {
  if (!target) return null;
  const el = document.querySelector(target);
  if (!el) return null;
  return el.getBoundingClientRect();
}

// Compute the popover's fixed position. On wide screens it sits just below the
// target (or above if there's no room), clamped to the viewport. On narrow
// screens it anchors to the bottom as a sheet. Returns inline styles only.
function computePopoverStyle(targetRect, popoverSize, viewport) {
  const { width: vw, height: vh } = viewport;
  const isNarrow = vw <= 560;

  // Bottom-sheet for narrow viewports or untethered steps without a target.
  if (isNarrow) {
    return {
      left: POPOVER_MARGIN,
      right: POPOVER_MARGIN,
      bottom: POPOVER_MARGIN,
      maxWidth: "none",
    };
  }

  if (!targetRect) {
    // Centered card.
    return {
      left: "50%",
      top: "50%",
      transform: "translate(-50%, -50%)",
    };
  }

  const pw = popoverSize.width || 320;
  const ph = popoverSize.height || 160;

  // Prefer below the target; flip above if it would overflow the bottom.
  const spaceBelow = vh - targetRect.bottom;
  const placeBelow = spaceBelow >= ph + TARGET_GAP + POPOVER_MARGIN || spaceBelow >= targetRect.top;
  const top = placeBelow
    ? targetRect.bottom + TARGET_GAP
    : Math.max(POPOVER_MARGIN, targetRect.top - ph - TARGET_GAP);

  // Align left edge to the target, then clamp within the viewport gutters.
  const rawLeft = targetRect.left;
  const maxLeft = vw - pw - POPOVER_MARGIN;
  const left = Math.max(POPOVER_MARGIN, Math.min(rawLeft, maxLeft));

  return { left, top };
}

export default function Tour({ steps, onClose, returnFocusRef }) {
  const [index, setIndex] = useState(0);
  const [targetRect, setTargetRect] = useState(null);
  const [popoverStyle, setPopoverStyle] = useState({});
  const popoverRef = useRef(null);
  const nextBtnRef = useRef(null);
  const cleanupRef = useRef(null);

  const step = steps[index];
  const isFirst = index === 0;
  const isLast = index === steps.length - 1;
  const titleId = "tour-title";
  const bodyId = "tour-body";

  const close = useCallback(() => {
    onClose();
    // Restore focus to the element that opened the tour.
    const node = returnFocusRef?.current;
    if (node && typeof node.focus === "function") node.focus();
  }, [onClose, returnFocusRef]);

  const goNext = useCallback(() => {
    setIndex((i) => Math.min(i + 1, steps.length - 1));
  }, [steps.length]);
  const goBack = useCallback(() => setIndex((i) => Math.max(i - 1, 0)), []);

  // On each step change: scroll the target into view, then measure it. We
  // measure after layout so the spotlight ring and popover line up exactly.
  useLayoutEffect(() => {
    const el = step.target ? document.querySelector(step.target) : null;
    if (el) {
      el.scrollIntoView({ block: "center", inline: "nearest", behavior: "auto" });
    }
    const measure = () => {
      const rect = getTargetRect(step.target);
      setTargetRect(rect);
      const popEl = popoverRef.current;
      const popoverSize = popEl
        ? { width: popEl.offsetWidth, height: popEl.offsetHeight }
        : { width: 320, height: 160 };
      setPopoverStyle(
        computePopoverStyle(rect, popoverSize, {
          width: window.innerWidth,
          height: window.innerHeight,
        })
      );
    };
    // Two frames: one to let scrollIntoView settle, one to size the popover.
    const raf1 = requestAnimationFrame(() => {
      measure();
      const raf2 = requestAnimationFrame(measure);
      cleanupRef.current = () => cancelAnimationFrame(raf2);
    });
    return () => {
      cancelAnimationFrame(raf1);
      cleanupRef.current?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  // Keep the highlight + popover aligned if the user resizes or scrolls.
  useEffect(() => {
    const reposition = () => {
      const rect = getTargetRect(step.target);
      setTargetRect(rect);
      const popEl = popoverRef.current;
      const popoverSize = popEl
        ? { width: popEl.offsetWidth, height: popEl.offsetHeight }
        : { width: 320, height: 160 };
      setPopoverStyle(
        computePopoverStyle(rect, popoverSize, {
          width: window.innerWidth,
          height: window.innerHeight,
        })
      );
    };
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);
    return () => {
      window.removeEventListener("resize", reposition);
      window.removeEventListener("scroll", reposition, true);
    };
  }, [step.target]);

  // Lock body scroll while the tour is open; always restore on close.
  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prevOverflow; };
  }, []);

  // Move focus into the popover on open and on every step change.
  useEffect(() => {
    nextBtnRef.current?.focus();
  }, [index]);

  // Keyboard: Esc closes; Tab/Shift+Tab trap within the popover; arrows step.
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        isLast ? close() : goNext();
        return;
      }
      if (e.key === "ArrowLeft") {
        if (isFirst) return;
        e.preventDefault();
        goBack();
        return;
      }
      if (e.key !== "Tab") return;
      const node = popoverRef.current;
      if (!node) return;
      const focusable = [...node.querySelectorAll("button:not([disabled])")]
        .filter((el) => el.offsetParent !== null);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [close, goNext, goBack, isFirst, isLast]);

  // Spotlight ring rectangle (padded a touch beyond the target).
  const ringStyle = targetRect
    ? {
        left: targetRect.left - 6,
        top: targetRect.top - 6,
        width: targetRect.width + 12,
        height: targetRect.height + 12,
      }
    : null;

  return (
    <div className={`tour-root${ringStyle ? " has-ring" : ""}`}>
      {/* Backdrop dims the page. Clicking it skips the tour. */}
      <div className="tour-backdrop" onClick={close} />

      {/* Spotlight ring around the current target (outline, not colour alone). */}
      {ringStyle && <div className="tour-ring" style={ringStyle} aria-hidden="true" />}

      <div
        className="tour-popover"
        ref={popoverRef}
        style={popoverStyle}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={bodyId}
      >
        <div className="tour-popover-head">
          <span className="tour-step-count" aria-hidden="true">
            {index + 1} of {steps.length}
          </span>
          <button
            type="button"
            className="tour-skip"
            onClick={close}
            aria-label="Skip tour"
          >
            Skip
          </button>
        </div>

        <h2 id={titleId} className="tour-title">{step.title}</h2>
        <p id={bodyId} className="tour-body">{step.body}</p>

        <div className="tour-actions">
          <button
            type="button"
            className="tour-btn tour-btn-ghost"
            onClick={goBack}
            disabled={isFirst}
          >
            Back
          </button>
          <button
            type="button"
            className="tour-btn tour-btn-primary"
            ref={nextBtnRef}
            onClick={isLast ? close : goNext}
          >
            {isLast ? "Done" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
