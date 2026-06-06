WCAG_CHUNKS = [
    {
        "criterion_id": "1.1.1",
        "level": "A",
        "title": "Non-text Content",
        "chunk_text": """WCAG 2.2 SC 1.1.1: Non-text Content (Level A)

Requirement: All non-text content (images, icons, charts, diagrams) must have a text alternative that serves the same purpose.

Why it matters: Screen reader users hear the text alternative instead of seeing the image. Without alt text, images are announced as the filename or URL, which is meaningless.

Fix techniques:
- Add alt attribute to <img>: <img src="logo.png" alt="Company logo">
- Decorative images use empty alt: <img src="divider.png" alt="">
- Complex images (charts, diagrams): provide description via aria-describedby or visible caption
- Image buttons: <input type="image" alt="Submit form">
- Icon fonts: add aria-label to container, hide icon with aria-hidden="true"

Common failures:
- Missing alt attribute entirely
- alt="image" or alt="photo" (non-descriptive)
- Using the filename as alt text
- Decorative images with non-empty alt causing unnecessary announcements

Related axe-core rules: image-alt, input-image-alt, object-alt, role-img-alt, svg-img-alt""",
    },
    {
        "criterion_id": "1.3.1",
        "level": "A",
        "title": "Info and Relationships",
        "chunk_text": """WCAG 2.2 SC 1.3.1: Info and Relationships (Level A)

Requirement: Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text.

Why it matters: Screen readers understand semantic HTML. If structure is conveyed only visually (e.g., bold text as a heading, table-like layout without actual tables), assistive technology users miss it.

Fix techniques:
- Use proper heading hierarchy (<h1>–<h6>) for document structure
- Use <label> elements explicitly associated with form inputs via for/id
- Use semantic list elements <ul>/<ol>/<li> for lists
- Use <table> with <th> and scope for data tables
- Use ARIA roles where semantic HTML isn't available

Common failures:
- Headings styled as bold text without heading tags
- Form inputs without associated labels
- Tables used for layout without aria-presentation
- List items not wrapped in <ul> or <ol>

Related axe-core rules: label, heading-order, list, listitem, definition-list, table-duplicate-name, td-headers-attr, th-has-data-cells, empty-heading""",
    },
    {
        "criterion_id": "1.4.1",
        "level": "A",
        "title": "Use of Color",
        "chunk_text": """WCAG 2.2 SC 1.4.1: Use of Color (Level A)

Requirement: Color must not be the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element.

Why it matters: Users with color blindness or low vision cannot distinguish colors reliably. Links that are only blue (no underline) are indistinguishable from regular text by colorblind users.

Fix techniques:
- Add underline to inline links (text-decoration: underline)
- Use icons, patterns, or text labels in addition to color for status
- For charts: add patterns, labels, or shapes to distinguish data series
- Error states: combine red color with an icon and text message

Common failures:
- Links distinguished from body text only by color
- Required form fields indicated only by a colored asterisk
- Charts using color alone to distinguish series

Related axe-core rules: link-in-text-block""",
    },
    {
        "criterion_id": "1.4.3",
        "level": "AA",
        "title": "Contrast (Minimum)",
        "chunk_text": """WCAG 2.2 SC 1.4.3: Contrast Minimum (Level AA)

Requirement: Text and images of text must have a contrast ratio of at least 4.5:1. Large text (18pt/24px or 14pt/18.67px bold) requires 3:1.

Why it matters: Low contrast makes text illegible for users with low vision, elderly users, or anyone in bright sunlight. This is one of the most commonly violated WCAG criteria.

Fix techniques:
- Use a contrast checker (WebAIM, browser devtools) to measure ratio
- Darken text color or lighten background to achieve 4.5:1
- Common safe combinations: #333 on white (12.6:1), #767676 on white (4.54:1)
- For dark backgrounds: ensure light text is bright enough
- CSS: color: #333; (not #999 or #aaa on white)

Common failures:
- Light gray text on white background (#999 on #fff = 2.85:1 — fail)
- White text on light blue buttons
- Placeholder text styled same as normal text (placeholders exempt but often confused)
- Text overlaid on images without a solid backing

Related axe-core rules: color-contrast, color-contrast-enhanced""",
    },
    {
        "criterion_id": "1.4.4",
        "level": "AA",
        "title": "Resize Text",
        "chunk_text": """WCAG 2.2 SC 1.4.4: Resize Text (Level AA)

Requirement: Text can be resized up to 200% without assistive technology and without loss of content or functionality.

Why it matters: Users with low vision zoom their browsers to 200% or use OS-level text size increases. Content must reflow, not overflow or become clipped.

Fix techniques:
- Use relative units (rem, em, %) instead of fixed px for font sizes
- Set base font size on <html> using rem so users' browser preferences scale everything
- Ensure containers don't have fixed heights that clip text
- Test at 200% zoom in Chrome DevTools

Common failures:
- Fixed pixel font sizes that ignore OS text size settings
- Containers with overflow:hidden and fixed heights that clip zoomed text
- Horizontal scrolling required when text is zoomed""",
    },
    {
        "criterion_id": "1.4.10",
        "level": "AA",
        "title": "Reflow",
        "chunk_text": """WCAG 2.2 SC 1.4.10: Reflow (Level AA)

Requirement: Content can be presented without loss of information or functionality, and without requiring scrolling in two dimensions at a viewport width of 320px.

Why it matters: Users who need to zoom to 400% effectively get a viewport of ~320px. Two-dimensional scrolling (both horizontal and vertical) is extremely difficult for motor-impaired users.

Fix techniques:
- Use responsive CSS with flexbox or grid
- Avoid fixed-width containers wider than 320px
- Use CSS media queries to reflow content at narrow widths
- Test at 320px viewport width (or 400% browser zoom)

Common failures:
- Fixed-width tables or images that force horizontal scroll
- Side-by-side columns that don't stack on narrow viewports
- Navigation bars that don't collapse into a hamburger menu

Related axe-core rules: scrollable-region-focusable""",
    },
    {
        "criterion_id": "1.4.11",
        "level": "AA",
        "title": "Non-text Contrast",
        "chunk_text": """WCAG 2.2 SC 1.4.11: Non-text Contrast (Level AA)

Requirement: UI components (buttons, inputs, checkboxes) and informational graphics must have a contrast ratio of at least 3:1 against adjacent colors.

Why it matters: Users with low vision need to see the boundaries of interactive components (where does a text field begin?), not just their labels.

Fix techniques:
- Ensure button borders/backgrounds achieve 3:1 against page background
- Form input borders must be visible: border: 1px solid #767676 on white (4.5:1)
- Focus indicators need 3:1 contrast against adjacent colors
- Don't use background-only to indicate a text field (add a visible border)

Common failures:
- Text inputs with very light gray border on white background
- Buttons with no visible border and same background as page
- Custom checkboxes/radios with insufficient border contrast

Related axe-core rules: color-contrast""",
    },
    {
        "criterion_id": "1.4.12",
        "level": "AA",
        "title": "Text Spacing",
        "chunk_text": """WCAG 2.2 SC 1.4.12: Text Spacing (Level AA)

Requirement: No loss of content when the user applies: line-height ≥1.5×, letter-spacing ≥0.12em, word-spacing ≥0.16em, paragraph spacing ≥2em.

Why it matters: Users with dyslexia or cognitive disabilities often apply custom spacing via user stylesheets or browser extensions. Content must not break or become unreadable.

Fix techniques:
- Avoid fixed heights on text containers; use min-height
- Don't use CSS that would override user-applied spacing (avoid !important on spacing)
- Test with a Text Spacing bookmarklet or browser extension that applies the above values
- Use flexible layouts that accommodate expanded text""",
    },
    {
        "criterion_id": "2.1.1",
        "level": "A",
        "title": "Keyboard",
        "chunk_text": """WCAG 2.2 SC 2.1.1: Keyboard (Level A)

Requirement: All functionality must be operable through a keyboard interface without requiring specific timings for individual keystrokes.

Why it matters: Millions of users with motor disabilities, power users, and screen reader users navigate entirely by keyboard. If something requires a mouse, they're excluded.

Fix techniques:
- Ensure all interactive elements are focusable (use <button>, <a>, <input>, or tabindex="0")
- Implement keyboard handlers alongside mouse handlers (keydown/keyup for click functionality)
- For drag-and-drop: provide a keyboard alternative (e.g., cut/paste or move buttons)
- Custom widgets: follow ARIA Authoring Practices Guide keyboard patterns

Common failures:
- Custom div/span click handlers without keyboard equivalents
- Mouse-only features (drag-and-drop with no keyboard fallback)
- JavaScript that moves focus away unexpectedly
- Mouse hover tooltips not accessible via keyboard focus

Related axe-core rules: keyboard""",
    },
    {
        "criterion_id": "2.1.2",
        "level": "A",
        "title": "No Keyboard Trap",
        "chunk_text": """WCAG 2.2 SC 2.1.2: No Keyboard Trap (Level A)

Requirement: If keyboard focus can be moved to a component, focus must be movable away using only the keyboard (Tab, Shift+Tab, arrow keys, or Escape).

Why it matters: A keyboard trap prevents users from leaving a component and accessing the rest of the page. This is a critical blocker for keyboard users.

Fix techniques:
- Modals: trap focus within the modal intentionally (correct behavior), but Escape must close it and return focus to the trigger
- Date pickers: Escape closes the picker
- Custom widgets: ensure all keyboard entry points have exit points
- Test by tabbing into every interactive widget and verifying you can tab out

Common failures:
- Modal dialogs where Tab cycles through modal content but Escape doesn't close
- Embedded media players where focus enters but can't exit
- Custom autocomplete widgets that trap arrow key navigation

Related axe-core rules: focus-trap""",
    },
    {
        "criterion_id": "2.4.1",
        "level": "A",
        "title": "Bypass Blocks",
        "chunk_text": """WCAG 2.2 SC 2.4.1: Bypass Blocks (Level A)

Requirement: A mechanism must be available to bypass blocks of content repeated on multiple pages (navigation, headers).

Why it matters: Keyboard and screen reader users must Tab through every navigation link on every page unless a skip link is provided. On a site with 20 nav items, that's 20 extra Tab presses per page.

Fix techniques:
- Add a visually-hidden "Skip to main content" link as the first focusable element
- Link target: <main id="main-content"> or any landmark with id
- Make skip link visible on focus: .skip-link:focus { position: static; }
- Alternatively: use ARIA landmarks (nav, main, aside) which screen readers can jump between

Common failures:
- No skip link present
- Skip link present but href target doesn't exist
- Skip link not the first focusable element on the page

Related axe-core rules: skip-link, landmark-one-main""",
    },
    {
        "criterion_id": "2.4.2",
        "level": "A",
        "title": "Page Titled",
        "chunk_text": """WCAG 2.2 SC 2.4.2: Page Titled (Level A)

Requirement: Web pages must have titles that describe the topic or purpose.

Why it matters: The page title is the first thing a screen reader announces when a page loads or when switching browser tabs. Without a descriptive title, users don't know what page they're on.

Fix techniques:
- Set <title> in <head>: <title>Login — My App</title>
- Format: "Page Name — Site Name" or "Site Name | Page Name"
- Titles should be unique across pages
- For SPAs: update document.title dynamically when the route changes

Common failures:
- Missing <title> element
- Generic title like "Untitled" or same title on every page
- SPA that never updates the title after navigation

Related axe-core rules: document-title""",
    },
    {
        "criterion_id": "2.4.3",
        "level": "A",
        "title": "Focus Order",
        "chunk_text": """WCAG 2.2 SC 2.4.3: Focus Order (Level A)

Requirement: If a web page can be navigated sequentially, focusable components receive focus in an order that preserves meaning and operability.

Why it matters: If focus jumps around unpredictably (e.g., form submission sends focus to a random element), keyboard users lose their place and context.

Fix techniques:
- Ensure DOM order matches visual order; avoid using CSS to visually reorder elements (flex order, absolute positioning)
- Avoid positive tabindex values (tabindex="1", "2", etc.) which disrupt natural flow
- After modal open: move focus to modal heading or first focusable element
- After modal close: return focus to the element that opened it
- After dynamic content injection: move focus to new content or announce it via aria-live

Common failures:
- tabindex values > 0 creating unexpected tab order
- Modals that don't manage focus
- CSS-reordered content where tab order doesn't match visual order""",
    },
    {
        "criterion_id": "2.4.4",
        "level": "A",
        "title": "Link Purpose",
        "chunk_text": """WCAG 2.2 SC 2.4.4: Link Purpose (In Context) (Level A)

Requirement: The purpose of each link can be determined from the link text alone, or from the link text together with its programmatically determined context.

Why it matters: Screen reader users often navigate by jumping between links ("links list" mode). "Click here" or "Read more" repeated 10 times is meaningless without context.

Fix techniques:
- Descriptive link text: "Download accessibility report (PDF)" not "Click here"
- If short text is required visually, add aria-label: <a href="..." aria-label="Read more about pricing">Read more</a>
- Use aria-labelledby to reference visible text in context
- For icon-only links: add aria-label to the <a>

Common failures:
- "Click here", "Read more", "Learn more" without context
- Links with only an image and no alt text
- Identical link text pointing to different URLs

Related axe-core rules: link-name""",
    },
    {
        "criterion_id": "2.4.6",
        "level": "AA",
        "title": "Headings and Labels",
        "chunk_text": """WCAG 2.2 SC 2.4.6: Headings and Labels (Level AA)

Requirement: Headings and labels describe the topic or purpose of the section or control.

Why it matters: Screen reader users navigate pages by headings (H key in NVDA/JAWS). Empty or meaningless headings (e.g., empty <h2>) break this navigation pattern.

Fix techniques:
- Headings must contain meaningful text content
- Don't skip heading levels (h1 → h3 without h2)
- Each page should have exactly one h1
- Form labels must describe the input's purpose

Common failures:
- Empty heading elements: <h2></h2> or <h2> </h2>
- Headings used for visual styling only (bold, large)
- Skipped heading levels disrupting document outline
- "Label" that just says "Field" without context

Related axe-core rules: empty-heading, heading-order, page-has-heading-one""",
    },
    {
        "criterion_id": "2.4.7",
        "level": "AA",
        "title": "Focus Visible",
        "chunk_text": """WCAG 2.2 SC 2.4.7: Focus Visible (Level AA)

Requirement: Any keyboard operable user interface must have a mode of operation where the keyboard focus indicator is visible.

Why it matters: Keyboard users need to see where they are on the page. Removing the focus ring (outline: none) makes keyboard navigation impossible for sighted keyboard users.

Fix techniques:
- Never use outline: none or outline: 0 without providing a replacement focus style
- Provide a visible focus style: :focus { outline: 2px solid #005fcc; outline-offset: 2px; }
- Use :focus-visible for keyboard-only focus styles (hides on mouse click)
- Ensure focus color has 3:1 contrast against adjacent background

Common failures:
- CSS reset that removes all focus outlines globally
- outline: none on buttons/links without replacement
- Focus indicator with insufficient color contrast

Related axe-core rules: focus-visible""",
    },
    {
        "criterion_id": "2.4.11",
        "level": "AA",
        "title": "Focus Not Obscured (Minimum)",
        "chunk_text": """WCAG 2.2 SC 2.4.11: Focus Not Obscured (Minimum) (Level AA, WCAG 2.2 new)

Requirement: When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content (sticky headers, footers, cookie banners, or floating action buttons).

Why it matters: New in WCAG 2.2. Keyboard users must be able to see the element they have focused. Sticky headers and overlays commonly cover the focused element as the user tabs down the page, so they cannot tell where they are.

Fix techniques:
- Use scroll-padding-top on the scroll container equal to the sticky header height so focused elements scroll into a visible area: html { scroll-padding-top: 80px; }
- Ensure scroll-margin on focusable elements pushes them clear of fixed overlays
- Avoid full-width sticky footers that overlap the bottom row of focusable content; or reserve space for them
- Make cookie banners and dialogs trap focus first so subsequent tabbing isn't obscured behind them
- Test by tabbing through the entire page with a sticky header present and confirm each focused control is at least partially visible

Common failures:
- Sticky header covers the focused link as the user tabs past it
- Floating chat or "back to top" button hides the focused control underneath it
- Cookie consent bar at the bottom fully covers focused form controls

Related axe-core rules: (no dedicated axe-core rule; verify manually with keyboard testing)""",
    },
    {
        "criterion_id": "2.4.13",
        "level": "AAA",
        "title": "Focus Appearance",
        "chunk_text": """WCAG 2.2 SC 2.4.13: Focus Appearance (Level AAA, WCAG 2.2 new)

Requirement: When the keyboard focus indicator is visible, an area of the indicator is at least as large as a 2 CSS pixel thick perimeter of the unfocused component, and has a contrast ratio of at least 3:1 between the focused and unfocused states.

Why it matters: New in WCAG 2.2 (Level AAA). It strengthens Focus Visible (2.4.7) with measurable minimum size and contrast values so the focus indicator is reliably perceivable, not just technically present.

Fix techniques:
- Use a solid baseline: outline: 3px solid #005fcc; outline-offset: 2px;
- The focus ring must surround the component (or an equivalent area) and achieve 3:1 contrast against both the component and the page background
- Avoid thin 1px outlines that fail the 2px-perimeter area test
- Browser default focus rings often meet this; custom styles frequently do not

Common failures:
- Custom focus style that is a 1px outline or a faint glow below the contrast/area threshold
- Focus indicated only by a subtle background color change with no perimeter

Related axe-core rules: (no dedicated axe-core rule; verify manually)""",
    },
    {
        "criterion_id": "2.5.3",
        "level": "A",
        "title": "Label in Name",
        "chunk_text": """WCAG 2.2 SC 2.5.3: Label in Name (Level A)

Requirement: For UI components with labels that include text or images of text, the accessible name contains the visible label text.

Why it matters: Voice control users (Dragon NaturallySpeaking) say the visible label to activate a control. If the accessible name doesn't match, the command fails.

Fix techniques:
- Accessible name must START WITH or CONTAIN the visible label text
- Avoid aria-label that completely replaces visible text: if button says "Submit" don't set aria-label="Save form"
- If aria-label is needed for clarity, include visible text: aria-label="Submit contact form"
- Use aria-labelledby referencing the visible text element

Common failures:
- Icon button with aria-label that doesn't match the visible tooltip text
- Input with visible label "Email" but aria-label="Enter email address here"

Related axe-core rules: label-content-name-mismatch""",
    },
    {
        "criterion_id": "2.5.8",
        "level": "AA",
        "title": "Target Size (Minimum)",
        "chunk_text": """WCAG 2.2 SC 2.5.8: Target Size Minimum (Level AA, WCAG 2.2 new)

Requirement: The size of the target for pointer inputs is at least 24×24 CSS pixels, except where spacing is sufficient, the target is inline, or essential.

Why it matters: Small touch targets are difficult for users with motor impairments, tremors, or large fingers. This is new in WCAG 2.2.

Fix techniques:
- Minimum 24×24px clickable area (not just the visual element)
- Use padding to extend the clickable area without changing visual size
- Recommended: 44×44px targets (iOS/Android guidelines)
- CSS: min-height: 44px; min-width: 44px; padding: 10px;

Common failures:
- Icon buttons with no padding (16×16 icon with 0 padding)
- Close "×" buttons that are too small
- Navigation links with minimal padding

Related axe-core rules: target-size""",
    },
    {
        "criterion_id": "3.1.1",
        "level": "A",
        "title": "Language of Page",
        "chunk_text": """WCAG 2.2 SC 3.1.1: Language of Page (Level A)

Requirement: The default human language of each web page can be programmatically determined.

Why it matters: Screen readers use the page language to select the correct text-to-speech engine and pronunciation rules. Without lang attribute, English screen readers mispronounce French or German text.

Fix techniques:
- Set lang attribute on <html>: <html lang="en">
- Use BCP 47 language codes: en, fr, de, es, pt-BR, zh-Hans
- For multilingual pages: set lang on specific elements too

Common failures:
- Missing lang attribute on <html>
- Wrong language code (lang="english" instead of lang="en")
- Dynamic pages that don't update lang when language changes

Related axe-core rules: html-has-lang, html-lang-valid""",
    },
    {
        "criterion_id": "3.3.1",
        "level": "A",
        "title": "Error Identification",
        "chunk_text": """WCAG 2.2 SC 3.3.1: Error Identification (Level A)

Requirement: If an input error is automatically detected, the item in error is identified and the error is described to the user in text.

Why it matters: Error messages that appear only visually (red border) are missed by screen reader users who need text descriptions.

Fix techniques:
- Associate error messages with inputs: aria-describedby="email-error"
- Mark invalid fields: aria-invalid="true"
- Move focus to error summary or first error on form submission
- Error message: "Email address is required" not just "Required"

Common failures:
- Errors indicated only by red border with no text description
- Error text not associated with the input via aria-describedby
- Generic "Please fix the errors below" without identifying which fields

Related axe-core rules: aria-required-attr, aria-required-children""",
    },
    {
        "criterion_id": "3.3.2",
        "level": "A",
        "title": "Labels or Instructions",
        "chunk_text": """WCAG 2.2 SC 3.3.2: Labels or Instructions (Level A)

Requirement: Labels or instructions are provided when content requires user input.

Why it matters: Users need to understand what each form field expects before they fill it in. Placeholder text alone is not sufficient — it disappears on input.

Fix techniques:
- Every form input must have a persistent <label> (not just placeholder)
- <label for="email">Email address</label> <input id="email" type="email">
- Instructions for format requirements: "Password must be 8+ characters"
- Required fields: indicate in label or instructions, not just with color

Common failures:
- Using placeholder as the only label (disappears when typing)
- Labels that don't indicate format requirements (date, phone number)
- Input groups without group label (fieldset + legend)

Related axe-core rules: label""",
    },
    {
        "criterion_id": "4.1.1",
        "level": "A",
        "title": "Parsing",
        "chunk_text": """WCAG 2.2 SC 4.1.1: Parsing (Level A)

Requirement: In content implemented using markup languages, elements have complete start and end tags, are nested per spec, don't contain duplicate attributes, and IDs are unique.

Why it matters: Duplicate IDs break ARIA references (aria-labelledby, aria-describedby) because these reference elements by ID. If an ID isn't unique, screen readers pick the wrong element.

Fix techniques:
- Ensure all IDs on a page are unique: <input id="email"> appears only once
- Fix HTML validation errors (unclosed tags, invalid nesting)
- For dynamic content: generate unique IDs (e.g., email-1, email-2) or use aria-label

Common failures:
- Components copied into a page multiple times with the same id
- Form inputs duplicated in modals with same IDs as page inputs
- Template engines that repeat id="submit-btn" across multiple components

Related axe-core rules: duplicate-id, duplicate-id-active, duplicate-id-aria""",
    },
    {
        "criterion_id": "4.1.2",
        "level": "A",
        "title": "Name, Role, Value",
        "chunk_text": """WCAG 2.2 SC 4.1.2: Name, Role, Value (Level A)

Requirement: For all UI components, the name, role, and value can be programmatically determined; states, properties, and values that can be set can be programmatically set; and notification of changes is available to user agents including assistive technologies.

Why it matters: Screen readers need to know what each element is (role), what it's called (name), and what state it's in (checked, expanded, disabled). Without this, interactive elements are announced as generic or silent.

Fix techniques:
- Use semantic HTML (<button> not <div class="btn">)
- Add aria-label or aria-labelledby to elements without visible text labels
- For custom controls: add appropriate ARIA role + required states
  - Toggle: role="switch" aria-checked="true/false"
  - Accordion: aria-expanded="true/false" on trigger
  - Dialog: role="dialog" aria-modal="true" aria-labelledby="dialog-title"
- Update ARIA states dynamically when component changes

Common failures:
- <div> or <span> used as buttons without role="button" and keyboard support
- Icons without accessible names (aria-label or aria-hidden + visible text)
- Custom checkboxes without aria-checked
- Modals without role="dialog" and aria-labelledby

Related axe-core rules: button-name, aria-allowed-attr, aria-required-attr, aria-valid-attr, frame-title""",
    },
    {
        "criterion_id": "4.1.3",
        "level": "AA",
        "title": "Status Messages",
        "chunk_text": """WCAG 2.2 SC 4.1.3: Status Messages (Level AA)

Requirement: Status messages can be programmatically determined through role or properties so they can be presented to the user by assistive technologies without receiving focus.

Why it matters: When a form is submitted and "Saved successfully" appears, sighted users see it. Screen reader users won't hear it unless it's in an ARIA live region.

Fix techniques:
- Add role="status" or aria-live="polite" to containers that receive status updates
- Use aria-live="assertive" only for critical errors that require immediate attention
- The container must exist in DOM before content is injected (not created dynamically)
- For search results count: <div role="status">45 results found</div>

Common failures:
- Toast notifications that appear without ARIA live region
- Form success messages that don't announce to screen readers
- Loading spinners with no screen reader announcement when complete

Related axe-core rules: aria-live, scrollable-region-focusable""",
    },
    {
        "criterion_id": "1.4.13",
        "level": "AA",
        "title": "Content on Hover or Focus",
        "chunk_text": """WCAG 2.2 SC 1.4.13: Content on Hover or Focus (Level AA)

Requirement: When content appears on pointer hover or keyboard focus (tooltips, sub-menus), that content must be: dismissible (Escape closes it without moving focus), hoverable (pointer can move over the appeared content without it disappearing), and persistent (stays visible without requiring continuous hover/focus).

Why it matters: Users who zoom magnify the screen may accidentally hover outside a tooltip. Users with tremors need extra time to move their pointer over appeared content. Users should be able to dismiss unwanted content without losing their place.

Fix techniques:
- Tooltips: keep visible when pointer moves from trigger to tooltip
- Add Escape key handler to dismiss hover-triggered content
- Don't auto-dismiss after a timeout while pointer/focus is on triggered content
- CSS tooltips via :hover alone often fail — use JavaScript to manage visibility

Common failures:
- Tooltips that disappear when moving pointer off trigger toward tooltip content
- No way to dismiss appeared content via keyboard
- Sub-menus that close before user can move mouse to them""",
    },
    {
        "criterion_id": "1.3.4",
        "level": "AA",
        "title": "Orientation",
        "chunk_text": """WCAG 2.2 SC 1.3.4: Orientation (Level AA)

Requirement: Content does not restrict its view and operation to a single display orientation (portrait or landscape) unless essential.

Why it matters: Users with devices mounted in a fixed orientation (e.g., wheelchair-mounted tablet) cannot rotate their device. Locking to portrait or landscape excludes them.

Fix techniques:
- Don't use CSS to lock orientation (screen.orientation.lock only with justification)
- Test in both portrait and landscape and verify all content is accessible
- If orientation is essential (piano app, specific game), document the exception

Common failures:
- CSS that hides content in landscape mode with no alternative
- JavaScript that redirects users to a "mobile version" when in portrait""",
    },
    {
        "criterion_id": "2.5.1",
        "level": "A",
        "title": "Pointer Gestures",
        "chunk_text": """WCAG 2.2 SC 2.5.1: Pointer Gestures (Level A)

Requirement: All functionality that uses multipoint or path-based gestures (pinch zoom, swipe) can also be operated with a single pointer without a path-based gesture.

Why it matters: Users with motor impairments can often tap (single point, no path) but not swipe or pinch.

Fix techniques:
- Carousels with swipe: add Previous/Next buttons as single-tap alternatives
- Maps with pinch-to-zoom: add +/- buttons
- Drawing tools: provide straight-line tool as alternative to freehand path

Common failures:
- Swipe-only carousels with no button controls
- Custom sliders that require click-and-drag without keyboard/button alternative

Related axe-core rules: scrollable-region-focusable""",
    },
    {
        "criterion_id": "1.2.1",
        "level": "A",
        "title": "Audio-only and Video-only (Prerecorded)",
        "chunk_text": """WCAG 2.2 SC 1.2.1: Audio-only and Video-only (Prerecorded) (Level A)

Requirement: For prerecorded audio-only content, provide a text transcript. For prerecorded video-only content (no audio), provide either a text alternative or an audio track that presents equivalent information.

Why it matters: Deaf users cannot hear audio-only podcasts; blind users cannot see video-only animations. Each needs an equivalent in a perceivable form.

Fix techniques:
- Audio-only: publish a full text transcript adjacent to the player
- Video-only (silent demo, animation): provide a text description, or an audio narration track
- Link the transcript near the media: <a href="transcript.html">Read transcript</a>

Common failures:
- Podcast or audio clip with no transcript
- Silent product animation with no text description or audio equivalent

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.2.2",
        "level": "A",
        "title": "Captions (Prerecorded)",
        "chunk_text": """WCAG 2.2 SC 1.2.2: Captions (Prerecorded) (Level A)

Requirement: Captions are provided for all prerecorded audio content in synchronized media (video with sound).

Why it matters: Deaf and hard-of-hearing users rely on captions to access spoken dialogue and meaningful sounds in videos. Auto-generated captions are often inaccurate and may not meet this requirement on their own.

Fix techniques:
- Provide synchronized captions via <track kind="captions"> on <video>
  <video controls><source src="demo.mp4"><track kind="captions" src="demo.vtt" srclang="en" label="English"></video>
- Use WebVTT (.vtt) caption files with accurate timing
- Review and correct auto-generated captions for accuracy and speaker identification
- Caption meaningful non-speech sounds: [applause], [door slams]

Common failures:
- Video with spoken content and no caption track
- Relying solely on uncorrected auto-captions with significant errors
- Captions missing speaker identification or important sound effects

Related axe-core rules: video-caption""",
    },
    {
        "criterion_id": "1.2.3",
        "level": "A",
        "title": "Audio Description or Media Alternative (Prerecorded)",
        "chunk_text": """WCAG 2.2 SC 1.2.3: Audio Description or Media Alternative (Prerecorded) (Level A)

Requirement: For prerecorded synchronized media, provide either an audio description of the video, or a full text alternative (transcript including visual information).

Why it matters: Blind users miss visual information shown but not spoken (on-screen text, actions, scene changes). An audio description or descriptive transcript fills that gap.

Fix techniques:
- Provide a descriptive transcript that includes both dialogue and a description of important visuals
- Or provide an audio description track describing key visual content during pauses in dialogue
- Link the media alternative near the player

Common failures:
- Tutorial video where steps are shown but not narrated, with no transcript
- Transcript that contains only dialogue and omits on-screen visual information

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.3.2",
        "level": "A",
        "title": "Meaningful Sequence",
        "chunk_text": """WCAG 2.2 SC 1.3.2: Meaningful Sequence (Level A)

Requirement: When the sequence in which content is presented affects its meaning, a correct reading sequence can be programmatically determined.

Why it matters: Screen readers and other assistive technologies read content in DOM order. If CSS visually reorders content (flex order, absolute positioning, grid placement), the reading order may no longer make sense.

Fix techniques:
- Keep DOM order matching the intended reading order
- Avoid CSS order, flex-direction: row-reverse, or absolute positioning that visually reorders meaningful content away from DOM order
- For multi-column layouts, ensure the source order reads correctly when linearized
- Test by disabling CSS or reading the DOM order with a screen reader

Common failures:
- Visual columns whose DOM order interleaves unrelated content
- CSS order used to move a "submit" button before the fields it submits in the DOM
- Content positioned absolutely so the reading order is scrambled

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.3.3",
        "level": "A",
        "title": "Sensory Characteristics",
        "chunk_text": """WCAG 2.2 SC 1.3.3: Sensory Characteristics (Level A)

Requirement: Instructions for understanding and operating content do not rely solely on sensory characteristics such as shape, color, size, visual location, orientation, or sound.

Why it matters: Blind users cannot perceive "the button on the right" or "the round icon". Instructions must also reference a programmatically available characteristic such as the label or name.

Fix techniques:
- Combine sensory references with text labels: "Select Save (the green button on the right)"
- Refer to controls by their accessible name, not only position or color
- Avoid "click the icon below" without naming the control

Common failures:
- "Press the round button" with no label reference
- "Fields marked in red are required" relying on color only
- "See the menu on the left" with no name or landmark reference

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.3.5",
        "level": "AA",
        "title": "Identify Input Purpose",
        "chunk_text": """WCAG 2.2 SC 1.3.5: Identify Input Purpose (Level AA)

Requirement: The purpose of each input field collecting information about the user can be programmatically determined when the field serves a purpose identified in the HTML autocomplete list.

Why it matters: Users with cognitive disabilities benefit from browser autofill and personalized icons. Correct autocomplete tokens let the browser and assistive tech recognize and pre-fill common fields like name, email, and address.

Fix techniques:
- Add the appropriate autocomplete attribute to common personal-data inputs:
  <input name="email" type="email" autocomplete="email">
  <input name="fname" autocomplete="given-name">
  <input name="tel" type="tel" autocomplete="tel">
- Use the standard HTML autocomplete tokens (name, email, tel, street-address, postal-code, cc-number, etc.)
- Pair autocomplete with the correct input type

Common failures:
- Email or name fields with no autocomplete attribute
- Wrong or invented autocomplete token that doesn't match the field's purpose
- autocomplete="off" on fields that collect the user's own information

Related axe-core rules: autocomplete-valid""",
    },
    {
        "criterion_id": "1.4.2",
        "level": "A",
        "title": "Audio Control",
        "chunk_text": """WCAG 2.2 SC 1.4.2: Audio Control (Level A)

Requirement: If any audio plays automatically for more than 3 seconds, a mechanism is available to pause, stop, or control its volume independently of the overall system volume.

Why it matters: Auto-playing audio interferes with screen reader speech, making the page unusable for blind users until they can find and silence it. It also distracts users with cognitive disabilities.

Fix techniques:
- Avoid autoplay audio entirely where possible
- If audio autoplays, provide a clearly visible, keyboard-accessible pause/stop control near the top of the page
- Don't rely on the OS volume control as the only mechanism
- For background video, use muted autoplay: <video autoplay muted>

Common failures:
- Background music or video sound that autoplays with no on-page stop control
- Audio ads that play on load with no accessible mute

Related axe-core rules: no-autoplay-audio""",
    },
    {
        "criterion_id": "1.4.5",
        "level": "AA",
        "title": "Images of Text",
        "chunk_text": """WCAG 2.2 SC 1.4.5: Images of Text (Level AA)

Requirement: If the technologies can render the visual presentation, real text is used to convey information rather than images of text (except for logos or where a specific presentation is essential).

Why it matters: Images of text don't scale crisply when zoomed, can't be restyled by users (high contrast, custom fonts), and aren't selectable or translatable.

Fix techniques:
- Use real HTML text styled with CSS instead of text baked into images
- Use web fonts and CSS for custom typography rather than image headings
- Reserve images of text for logos and brand marks where presentation is essential
- For decorative banners, keep the meaningful text as real text overlaid with CSS

Common failures:
- Headings or buttons rendered as PNG/JPG images of text
- Marketing copy embedded in an image with no real-text equivalent
- Pricing tables built as images

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "2.2.1",
        "level": "A",
        "title": "Timing Adjustable",
        "chunk_text": """WCAG 2.2 SC 2.2.1: Timing Adjustable (Level A)

Requirement: For each time limit set by the content, the user can turn it off, adjust it, or extend it (to at least 10× the default), unless the limit is essential or longer than 20 hours.

Why it matters: Users with disabilities may need much more time to read content or complete forms. Hard session timeouts or auto-advancing content can lock them out or cause data loss.

Fix techniques:
- Before a session timeout, warn the user and offer an "extend session" control (at least 20 seconds to respond)
- Allow users to turn off or adjust auto-advancing carousels and slideshows
- Avoid auto-submitting forms after a fixed time
- Persist form data so a timeout doesn't lose entered information

Common failures:
- Session expires without warning or a way to extend
- Carousel auto-advances with no pause and no timing control
- Quiz or checkout that auto-submits when a hidden timer runs out

Related axe-core rules: meta-refresh, meta-refresh-no-exceptions""",
    },
    {
        "criterion_id": "2.2.2",
        "level": "A",
        "title": "Pause, Stop, Hide",
        "chunk_text": """WCAG 2.2 SC 2.2.2: Pause, Stop, Hide (Level A)

Requirement: For moving, blinking, or scrolling information that starts automatically, lasts more than 5 seconds, and is shown alongside other content, the user can pause, stop, or hide it. The same applies to auto-updating information.

Why it matters: Motion and blinking content distracts users with attention or cognitive disabilities and can be impossible to read for users who need more time. Auto-updating feeds can move content out from under a screen reader.

Fix techniques:
- Provide a visible, keyboard-accessible pause/stop control for carousels, marquees, and animations
- Respect prefers-reduced-motion: @media (prefers-reduced-motion: reduce) { animation: none; }
- Allow auto-refreshing content (live feeds) to be paused
- Avoid blinking content entirely

Common failures:
- Auto-rotating carousel with no pause button
- Animated background or marquee that cannot be stopped
- Live feed that auto-updates with no pause control

Related axe-core rules: marquee, blink""",
    },
    {
        "criterion_id": "2.3.1",
        "level": "A",
        "title": "Three Flashes or Below Threshold",
        "chunk_text": """WCAG 2.2 SC 2.3.1: Three Flashes or Below Threshold (Level A)

Requirement: Web pages do not contain anything that flashes more than three times in any one-second period, or the flash is below the general flash and red flash thresholds.

Why it matters: Flashing content can trigger seizures in people with photosensitive epilepsy. This is a safety-critical criterion.

Fix techniques:
- Avoid any content that flashes more than 3 times per second
- Keep flashing areas small and below the luminance/red flash thresholds
- For necessary animation, use slow transitions rather than rapid flashing
- Test with a tool such as PEAT (Photosensitive Epilepsy Analysis Tool)

Common failures:
- Rapidly flashing ads, banners, or transitions
- Strobe effects in videos or animated GIFs
- Saturated red flashing content

Related axe-core rules: (no automated axe-core rule; requires manual review with PEAT)""",
    },
    {
        "criterion_id": "2.4.5",
        "level": "AA",
        "title": "Multiple Ways",
        "chunk_text": """WCAG 2.2 SC 2.4.5: Multiple Ways (Level AA)

Requirement: More than one way is available to locate a web page within a set of pages, except where the page is the result of, or a step in, a process.

Why it matters: Different users navigate differently. Some prefer search, others a sitemap, a menu, or breadcrumbs. Offering multiple ways accommodates these differences.

Fix techniques:
- Provide at least two of: site search, a navigation menu, a sitemap, breadcrumb trails, or an A-Z index
- Ensure these mechanisms are consistently available across the site
- Steps within a checkout or wizard are exempt

Common failures:
- Site with only a single navigation menu and no search or sitemap
- Deep pages reachable only by one rigid path

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "2.5.2",
        "level": "A",
        "title": "Pointer Cancellation",
        "chunk_text": """WCAG 2.2 SC 2.5.2: Pointer Cancellation (Level A)

Requirement: For functionality operated with a single pointer, at least one of these is true: no down-event triggers the action; the action completes on the up-event and can be aborted or undone; or the up-event reverses the down-event.

Why it matters: Users with motor impairments may touch the wrong target. Triggering actions on the up-event (and allowing the pointer to move away to cancel) lets them recover from mistakes.

Fix techniques:
- Trigger actions on click / pointerup, not pointerdown / mousedown
- Allow the user to move the pointer off the target before releasing to cancel
- Provide undo for actions that must fire on down-event
- The native click event already satisfies this; avoid binding critical actions to mousedown/touchstart

Common failures:
- Action fires on mousedown/touchstart with no way to abort
- Drag handles that commit immediately on down-press

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "2.5.4",
        "level": "A",
        "title": "Motion Actuation",
        "chunk_text": """WCAG 2.2 SC 2.5.4: Motion Actuation (Level A)

Requirement: Functionality operated by device motion or user motion (shaking, tilting) can also be operated by UI components, and motion actuation can be disabled, unless motion is essential.

Why it matters: Users who cannot hold or move a device steadily, or who have it mounted, cannot perform shake or tilt gestures. They need a conventional control alternative.

Fix techniques:
- Provide a button alternative for any shake/tilt action (e.g., a "Undo" button alongside shake-to-undo)
- Allow motion-based features to be turned off in settings
- Don't rely on the device orientation/motion sensors as the only input

Common failures:
- Shake-to-undo with no button equivalent
- Tilt-to-scroll or step counters with no alternative and no way to disable

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "2.5.7",
        "level": "AA",
        "title": "Dragging Movements",
        "chunk_text": """WCAG 2.2 SC 2.5.7: Dragging Movements (Level AA, WCAG 2.2 new)

Requirement: All functionality that uses a dragging movement can be operated by a single pointer without dragging, unless dragging is essential.

Why it matters: New in WCAG 2.2. Users with motor impairments or tremors, and those using a head pointer or eye tracker, may be unable to perform sustained drag gestures. They need a tap/click alternative.

Fix techniques:
- For reorderable lists: add up/down move buttons or a "move to" menu as a non-drag alternative
- For sliders: allow clicking on the track and using arrow keys, not just dragging the thumb
- For drag-and-drop file upload: also provide a file input button
- For map panning: provide directional buttons or click-to-center

Common failures:
- Sortable list that can only be reordered by dragging
- Slider that responds only to drag, not click or keyboard
- Kanban board cards movable only by drag with no menu alternative

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.1.2",
        "level": "AA",
        "title": "Language of Parts",
        "chunk_text": """WCAG 2.2 SC 3.1.2: Language of Parts (Level AA)

Requirement: The human language of each passage or phrase in the content can be programmatically determined, except for proper names, technical terms, words of indeterminate language, and words that have become part of the surrounding text's vernacular.

Why it matters: When a passage is in a different language from the page default, screen readers need the lang attribute to switch pronunciation rules, otherwise foreign phrases are mispronounced.

Fix techniques:
- Mark inline foreign-language passages with lang: <span lang="fr">C'est la vie</span>
- Mark larger sections (blockquotes, articles) with lang on the wrapping element
- Use valid BCP 47 codes (fr, de, es, zh-Hans)
- The page-level <html lang="..."> covers the default; only deviations need marking

Common failures:
- A French quote in an English page with no lang="fr"
- A multilingual list where each item's language is not marked

Related axe-core rules: valid-lang""",
    },
    {
        "criterion_id": "3.2.1",
        "level": "A",
        "title": "On Focus",
        "chunk_text": """WCAG 2.2 SC 3.2.1: On Focus (Level A)

Requirement: When any UI component receives focus, it does not initiate a change of context (opening a new window, moving focus, submitting a form, or substantially changing the page).

Why it matters: Keyboard and screen reader users tab through controls to explore the page. If merely focusing a control navigates away or submits, they are disoriented and may lose work.

Fix techniques:
- Do not trigger navigation, submission, or popups on the focus event
- Reserve such actions for explicit activation (click, Enter)
- For dropdowns, don't auto-submit on focus; wait for selection + activation

Common failures:
- A select element that navigates to a new page on focus rather than on change/activation
- A field that opens a modal simply because it received focus
- Auto-advancing focus that surprises the user

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.2.2",
        "level": "A",
        "title": "On Input",
        "chunk_text": """WCAG 2.2 SC 3.2.2: On Input (Level A)

Requirement: Changing the setting of a UI component does not automatically cause a change of context unless the user has been advised of the behavior beforehand.

Why it matters: If selecting a value in a dropdown auto-navigates or auto-submits, users (especially screen reader and keyboard users) are taken somewhere unexpectedly, often before finishing their selection.

Fix techniques:
- Don't auto-submit a form when a checkbox, radio, or select changes; provide an explicit submit button
- If auto-action is intended, warn the user in advance via visible/accessible instructions
- For a jump-menu select, add a "Go" button instead of navigating on change

Common failures:
- A country dropdown that reloads the page on change with no warning
- A toggle that submits the form immediately on change
- Selecting a radio that navigates away

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.2.3",
        "level": "AA",
        "title": "Consistent Navigation",
        "chunk_text": """WCAG 2.2 SC 3.2.3: Consistent Navigation (Level AA)

Requirement: Navigational mechanisms repeated on multiple pages occur in the same relative order each time, unless a change is initiated by the user.

Why it matters: Users with cognitive and visual disabilities rely on predictable placement. If the main nav reorders itself page to page, they have to relearn the layout each time.

Fix techniques:
- Keep header, primary navigation, search, and footer links in the same order across pages
- Use a shared layout/template so navigation order is consistent
- New items may be added, but existing items should keep their relative order

Common failures:
- Navigation links appearing in a different order on different pages
- Search box moving location between pages
- Footer links reordered inconsistently

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.2.4",
        "level": "AA",
        "title": "Consistent Identification",
        "chunk_text": """WCAG 2.2 SC 3.2.4: Consistent Identification (Level AA)

Requirement: Components that have the same functionality within a set of web pages are identified consistently.

Why it matters: Users learn what an icon or label means once. If the same "Search" action is labeled "Search" on one page and "Find" on another, or uses different icons, users with cognitive disabilities are confused.

Fix techniques:
- Use the same accessible name and icon for the same function across pages (e.g., always "Download")
- Keep alt text consistent for the same icon used in multiple places
- Standardize button labels in a shared component library

Common failures:
- A "Print" function labeled differently on different pages
- The same icon given different alt text in different locations
- Inconsistent labels for the same action (Submit vs Send vs Go)

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.2.6",
        "level": "A",
        "title": "Consistent Help",
        "chunk_text": """WCAG 2.2 SC 3.2.6: Consistent Help (Level A, WCAG 2.2 new)

Requirement: If a web page contains help mechanisms (human contact details, a contact mechanism, self-help links, or an automated contact tool) repeated across multiple pages, they occur in the same relative order on each page, unless the user changes it.

Why it matters: New in WCAG 2.2. Users with cognitive disabilities who need help should find it in a predictable place. Inconsistent placement of help links or chat widgets makes assistance hard to relocate.

Fix techniques:
- Place help links (Contact, Support, Help, chat launcher) in the same relative location across pages
- Use a shared layout so the help mechanism's position is stable
- Keep the contact phone/email, support link, or chat widget in a consistent spot (e.g., header or footer)

Common failures:
- A "Contact us" link in the header on one page and only in the footer on another
- A chat widget that appears in different corners on different pages

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.3.3",
        "level": "AA",
        "title": "Error Suggestion",
        "chunk_text": """WCAG 2.2 SC 3.3.3: Error Suggestion (Level AA)

Requirement: If an input error is automatically detected and suggestions for correction are known, the suggestions are provided to the user, unless doing so would jeopardize security or purpose.

Why it matters: It is not enough to say a value is wrong; users (especially those with cognitive disabilities) need to know how to fix it. A suggested correction reduces frustration and abandonment.

Fix techniques:
- Provide specific, actionable error text: "Date must be in MM/DD/YYYY format" not "Invalid date"
- Suggest the expected value or format in the error message
- For known options, suggest the closest match ("Did you mean .com?")
- Associate the suggestion with the field via aria-describedby

Common failures:
- "Invalid input" with no guidance on the correct format
- Required-field error with no indication of what is expected
- Date/phone errors that don't show the accepted format

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.3.4",
        "level": "AA",
        "title": "Error Prevention (Legal, Financial, Data)",
        "chunk_text": """WCAG 2.2 SC 3.3.4: Error Prevention (Legal, Financial, Data) (Level AA)

Requirement: For pages that create legal commitments or financial transactions, modify/delete user-controllable data, or submit test responses, submissions are reversible, checked for errors with a chance to correct, or confirmed (the user can review and confirm before finalizing).

Why it matters: Mistakes in legal, financial, or data-deletion contexts can be costly and hard to undo. Users with disabilities are more prone to input slips and benefit from a confirmation step.

Fix techniques:
- Add a review/confirmation step before finalizing a purchase or legal submission
- Provide a way to cancel or reverse transactions where feasible
- Validate inputs and let the user correct them before final submit
- Add a confirmation dialog before deleting data: "Delete this account? This cannot be undone."

Common failures:
- One-click irreversible deletion with no confirmation
- Checkout that charges immediately with no review step
- Form submission with no error check or chance to correct

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.3.7",
        "level": "A",
        "title": "Redundant Entry",
        "chunk_text": """WCAG 2.2 SC 3.3.7: Redundant Entry (Level A, WCAG 2.2 new)

Requirement: Information previously entered by or provided to the user that is required again in the same process is either auto-populated or available for the user to select, except when re-entering it is essential (e.g., a password confirmation), the information is no longer valid, or it is needed for security.

Why it matters: New in WCAG 2.2. Re-typing the same information is taxing for users with cognitive or motor disabilities and increases error rates. Multi-step forms commonly ask for the same data twice.

Fix techniques:
- Auto-fill fields already collected earlier in the same flow (e.g., copy billing to shipping with a checkbox)
- Offer a "same as above" toggle to reuse prior entries
- Persist entered data across steps so users don't re-key it
- Pre-select previously chosen options where appropriate

Common failures:
- Checkout asking for an address already entered on a prior step
- Multi-step wizard re-prompting for the same email with no auto-fill or select
- No "same as billing" option for shipping

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "3.3.8",
        "level": "AA",
        "title": "Accessible Authentication (Minimum)",
        "chunk_text": """WCAG 2.2 SC 3.3.8: Accessible Authentication (Minimum) (Level AA, WCAG 2.2 new)

Requirement: A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in authentication, unless that step provides an alternative that does not rely on a cognitive function test, or a mechanism to assist (such as allowing password managers / copy-paste), or the test is object recognition or identifying non-text content the user provided.

Why it matters: New in WCAG 2.2. People with cognitive disabilities struggle to memorize passwords, transcribe one-time codes, or solve puzzle CAPTCHAs. Authentication must not depend on these without an accessible alternative.

Fix techniques:
- Allow password managers and copy-paste into username/password and OTP fields (do not block paste)
- Use autocomplete tokens so credentials autofill: autocomplete="current-password", autocomplete="one-time-code"
- Offer authentication that doesn't require memorization: email links, passkeys/WebAuthn, OAuth
- Avoid puzzle/text-transcription CAPTCHAs; if used, provide an accessible alternative

Common failures:
- Blocking paste on password or one-time-code fields
- Puzzle or distorted-text CAPTCHA with no accessible alternative
- Requiring users to retype a code from memory or another device with no copy/autofill path

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.2.4",
        "level": "AA",
        "title": "Captions (Live)",
        "chunk_text": """WCAG 2.2 SC 1.2.4: Captions (Live) (Level AA)

Requirement: Captions are provided for all live audio content in synchronized media (live video with sound, such as webinars and live streams).

Why it matters: Deaf and hard-of-hearing users need real-time captions to follow live events. Unlike prerecorded media, captions must be produced as the event happens.

Fix techniques:
- Use a real-time captioning service (CART) or live stenographer for important live events
- Enable platform live-caption features for webinars and streams
- Display captions synchronized with the live audio with minimal latency
- Review automated live captions for critical events; accuracy requirements still apply

Common failures:
- Live webinar or stream with audio and no live captions
- Caption latency so high the captions are unusable

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.2.5",
        "level": "AA",
        "title": "Audio Description (Prerecorded)",
        "chunk_text": """WCAG 2.2 SC 1.2.5: Audio Description (Prerecorded) (Level AA)

Requirement: Audio description is provided for all prerecorded video content in synchronized media.

Why it matters: Blind and low-vision users miss visual information (actions, scene changes, on-screen text) that is shown but not conveyed in the main audio. An audio description narrates this during natural pauses.

Fix techniques:
- Add an audio description track that narrates key visual information during pauses in dialogue
- Where pauses are insufficient, provide an extended-description or descriptive version of the video
- Offer a toggle to enable the described audio track
- Script visual-heavy content so essential visuals are also spoken in the main track where possible

Common failures:
- Tutorial or marketing video with important on-screen visuals and no audio description
- A described track that omits essential visual actions

Related axe-core rules: (no automated axe-core rule; requires manual review)""",
    },
    {
        "criterion_id": "1.4.6",
        "level": "AAA",
        "title": "Contrast (Enhanced)",
        "chunk_text": """WCAG 2.2 SC 1.4.6: Contrast (Enhanced) (Level AAA)

Requirement: Text and images of text have a contrast ratio of at least 7:1. Large text (18pt / 24px, or 14pt / 18.67px bold) requires at least 4.5:1.

Why it matters: This Level AAA criterion raises the bar above 1.4.3 to better serve users with moderately low vision (roughly 20/80) without assistive technology. Some organizations and regulated sectors target AAA contrast.

Fix techniques:
- Achieve at least 7:1 for normal text; e.g. #000 on #fff (21:1), #595959 on white (7.0:1)
- For large text, achieve at least 4.5:1
- Verify with a contrast checker that reports both AA and AAA thresholds
- Prefer near-black body text on white rather than mid-grays

Common failures:
- Body text at #767676 on white (4.54:1) passes AA but fails AAA 7:1
- Mid-gray secondary text that meets only the AA minimum

Related axe-core rules: color-contrast-enhanced""",
    },
    {
        "criterion_id": "2.5.5",
        "level": "AAA",
        "title": "Target Size (Enhanced)",
        "chunk_text": """WCAG 2.2 SC 2.5.5: Target Size (Enhanced) (Level AAA)

Requirement: The size of the target for pointer inputs is at least 44×44 CSS pixels, except when an equivalent target meets the size, the target is inline, the size is essential, or it is a user-agent default.

Why it matters: This Level AAA criterion sets a larger minimum than 2.5.8 (24×24) and aligns with iOS and Android platform guidance. Larger targets help users with tremors, limited dexterity, or touch on small devices.

Fix techniques:
- Make interactive targets at least 44×44px, including padding around small icons
- CSS: min-height: 44px; min-width: 44px; padding to extend the hit area
- Space out adjacent small controls so taps don't land on the wrong one
- Apply especially to primary touch targets: buttons, nav items, form controls

Common failures:
- Icon buttons or close "×" controls smaller than 44×44px
- Densely packed toolbar icons with no padding
- Small tappable links in mobile navigation

Related axe-core rules: target-size""",
    },
]
