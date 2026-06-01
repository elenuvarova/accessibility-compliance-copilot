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
        "title": "Focus Appearance",
        "chunk_text": """WCAG 2.2 SC 2.4.11: Focus Appearance (Level AA, WCAG 2.2 new)

Requirement: When a UI component is focused, the focus indicator must have an area of at least the perimeter of the unfocused component × 2 CSS pixels, and a contrast ratio of at least 3:1.

Why it matters: This is new in WCAG 2.2 and strengthens the focus visible requirement with specific minimum size and contrast values.

Fix techniques:
- Use outline: 3px solid #005fcc; outline-offset: 2px as a solid baseline
- The focus ring must be visible all the way around the component
- Ensure the ring color achieves 3:1 contrast against both the component and the page background
- Browser default focus rings often meet this, but custom styles may not

Related axe-core rules: focus-visible""",
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
]
