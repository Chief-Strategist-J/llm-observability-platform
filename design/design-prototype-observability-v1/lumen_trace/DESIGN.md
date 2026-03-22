# Design System Document

## 1. Overview & Creative North Star: "The Obsidian Lens"

This design system is built for the high-stakes world of LLM Observability. In an industry where "noise" is the enemy, our interface must act as a precision instrument—a lens that clarifies rather than a screen that clutter. 

Our Creative North Star is **The Obsidian Lens**. It represents a shift away from "SaaS-standard" dashboards toward a high-end, editorial approach to technical data. We reject the rigid, boxed-in layouts of legacy observability tools. Instead, we embrace a "No-Line" philosophy where hierarchy is defined by tonal depth, intentional asymmetry, and sophisticated typography. The result is an environment that feels like a premium terminal: authoritative, expansive, and surgically precise.

---

## 2. Colors & Surface Philosophy

The palette is a sophisticated interplay of deep charcoals and electric "Logic Greens," designed to maximize legibility during long debugging sessions.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to section off the UI. Containers must never be defined by outlines. Instead, use background color shifts (e.g., a `surface_container_low` section sitting on a `surface` background) to create boundaries. This creates a seamless, "molded" look rather than a fragmented grid.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of materials. 
- **Base Layer:** `surface` (#0f1419) – The foundation.
- **Structural Zones:** `surface_container_low` (#171c22) – Navigation and sidebars.
- **Interactive Modules:** `surface_container` (#1b2026) – The main work areas.
- **Active Focus:** `surface_container_highest` (#30353b) – Pop-overs and active states.

### Glass & Gradient Rule
To prevent the dark theme from feeling "flat," use Glassmorphism for floating panels (e.g., Command Palettes or Tooltips). Use `surface_bright` at 60% opacity with a `backdrop-blur` of 12px. Main CTAs should utilize a subtle linear gradient from `primary` (#6bde80) to `primary_container` (#2fa54f) at a 135° angle to provide tactile "soul."

---

## 3. Typography: The Editorial Tech-Stack

We pair **Space Grotesk** (Display/Headline) with **Inter** (UI/Body) to balance high-tech personality with utilitarian readability.

- **The Display Scale:** Use `display-lg` for high-level metrics (e.g., Total Tokens). These should feel like an editorial headline—bold and unapologetic.
- **The Logic Scale:** Use `ui-monospace` for all logs, code snippets, and trace IDs. This font is the "source of truth" and should always be set with slightly increased line-height (1.6) for readability.
- **Contrast as Hierarchy:** Headlines use `on_surface` (#dee3eb) for maximum contrast. Labels and secondary data points use `on_surface_variant` (#bdcaba) to recede into the background, allowing the user's eye to skip directly to the primary information.

---

## 4. Elevation & Depth: Tonal Layering

We convey importance through **Tonal Layering** rather than traditional drop shadows or structural lines.

- **The Layering Principle:** Depth is achieved by "stacking." A `surface_container_lowest` card placed on a `surface_container_low` background creates a natural visual "pocket" for data without needing a shadow.
- **Ambient Shadows:** For floating elements (Modals), use an extra-diffused shadow: `offset-y: 24px, blur: 48px, color: rgba(0, 0, 0, 0.4)`. The shadow must feel like ambient occlusion, not a hard drop shadow.
- **The "Ghost Border" Fallback:** If a separation is mathematically required for accessibility, use the `outline_variant` token at 15% opacity. High-contrast, 100% opaque borders are strictly prohibited.
- **Glassmorphism:** Apply a semi-transparent `surface_variant` to floating headers. This allows trace data to "ghost" beneath the header as the user scrolls, maintaining a sense of spatial awareness.

---

## 5. Components

### Buttons
- **Primary:** Gradient-fill (`primary` to `primary_container`). `rounded-sm`. No border.
- **Secondary:** Surface-fill (`surface_container_high`). Subtle `outline_variant` (20% opacity) "Ghost Border."
- **Tertiary:** Text-only in `primary_fixed_dim`. Used for low-priority actions like "Cancel" or "Docs."

### Chips (The Status Indicator)
- **Trace Status:** Use `primary` for "Success," `error` for "Fail," and `secondary` for "Pending." 
- **Styling:** Small caps, `label-sm`, with a subtle background tint of the status color (10% opacity). No hard outlines.

### Input Fields
- **Search/Logs:** Use `surface_container_lowest` with a "Ghost Border." Upon focus, the border transitions to 100% `primary` opacity, and the background subtly shifts to `surface_container`.

### Cards & Data Lists
- **Rule:** Forbid divider lines.
- **Spacing:** Use `spacing-6` (1.3rem) to separate log entries.
- **Groupings:** Use a background shift to `surface_container_low` to group related traces.

### Specialized Components: The Trace Waterfall
- **Visuals:** Use horizontal bars with varying `primary` and `primary_container` tints to show LLM latency. Use `ui-monospace` for timestamp labels.
- **Interaction:** On hover, a "Glass" tooltip appears with `backdrop-blur`, revealing the raw JSON prompt.

---

## 6. Do’s and Don’ts

### Do
- **Do** use `spacing-10` or `spacing-12` for large section breaks. White space is a functional tool.
- **Do** use the `primary` green (#6bde80) sparingly for "Success" and "Action"—it should feel like a signal light in a dark room.
- **Do** align all text to a strict vertical rhythm to maintain the "Editorial" feel.

### Don't
- **Don't** use pure black (#000000) for surfaces; it kills the sense of depth. Use `surface` (#0f1419).
- **Don't** use standard 1px borders between sidebar items; use vertical padding and `surface` shifts for hover states.
- **Don't** mix font families within a single data string; keep metrics in `Inter` and data in `Monospace`.

---

## 7. Spacing & Roundedness

- **Radius:** We use a "Technical Sharp" approach. Use `sm` (0.125rem) for small UI elements and `md` (0.375rem) for main containers. Avoid `full` or `xl` unless it's a specific floating action button.
- **Density:** This is a data-heavy platform. Use `spacing-2` and `spacing-3` for internal card padding, but `spacing-8` for the "macro" layout to prevent cognitive overload.