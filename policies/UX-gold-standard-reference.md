# UI/UX Gold-Standard Reference
### Tables · Charts · Inputs · Steppers · Multi-Button Groups · Three.js
*Strict, source-backed rules — not opinion. Every rule below traces to NN/g, Apple HIG, Material Design 3, WCAG 2.2, or a named library's documented behavior.*

---

## 0. Foundational System — everything else derives from this

Nothing below works if the base tokens are inconsistent. Fix these four first; component-level rules are just applications of them.

### 0.1 Spacing — 8pt grid + 4pt half-step
- Base unit: **8px**. Every margin, padding, gap, and component dimension is a multiple of 8: `8, 16, 24, 32, 40, 48, 64, 96`.
- Use **4px** only as a half-step for tight spots (icon-to-label gap, dense table cells).
- Why 8, not an arbitrary unit: it divides cleanly across device pixel ratios (1×, 1.5×, 2×, 3×) with no fractional-pixel rendering, and both Apple HIG and Material Design standardize on it — so framework defaults (Tailwind, Carbon, Ant Design) already comply if you don't override them.
- Token naming: `space-1=4px, space-2=8px, space-3=16px, space-4=24px, space-5=32px, space-6=48px, space-7=64px`. Never hand-type raw px values in component code — reference the token.
- **Internal ≤ External rule**: padding *inside* a component (internal spacing) must be ≤ the gap *between* that component and its neighbors (external spacing). This is what makes grouped elements read as a group rather than a uniform soup.

### 0.2 Typography
- One type scale, defined once, referenced everywhere. A defensible scale: `12 / 14 / 16 / 18 / 20 / 24 / 32 / 40 / 48` — each step ~1.2–1.25× the previous (minor third / major third ratio).
- Body text floor: **16px**. Never go below 12px for any UI text, and 12px is only acceptable for chart axis labels / table meta-text, never body copy or form labels.
- Line-height: 1.4–1.6× font size for body text; tighter (1.1–1.3×) for large display headings.
- Max line length: 45–75 characters for body paragraphs — beyond that, eyes lose the line on wrap.
- One typeface family for UI text, a second (optional) for display/marketing headlines. Mixing 3+ families in one interface is a tell of an undesigned product.
- Numeric alignment in tables/dashboards: use **tabular figures** (`font-variant-numeric: tabular-nums`) so digits don't shift width as values change.

### 0.3 Touch targets & spacing between them (WCAG 2.2, SC 2.5.8)
- **Legal minimum (Level AA, since June 2025 under the EU Accessibility Act)**: every interactive target ≥ **24×24 CSS px**, OR spaced so a 24px-diameter circle centered on it doesn't overlap a neighboring target's circle.
- **Practical/recommended**: **44×44px** (Apple HIG minimum) or **48×48dp** (Material Design minimum) for anything touch-primary. Treat 24px as the accessibility floor, not the design target.
- Icon-only buttons: hit area must be 44px even if the visible icon is 20px — pad the hitbox, don't scale the icon.
- Gap between adjacent targets in a button group/toolbar: minimum 8px (space-2).

### 0.4 Alignment — the one rule violated most often
- **Left-align text.** Matches natural reading flow; ragged-right edges are fine, ragged-left is not.
- **Right-align numbers** (in tables, forms, dashboards) so decimal/place values stack for scanning.
- **Never center-align body text or table cell content.** Centering forces the eye to re-locate the start of each line/word — it's acceptable only for short, isolated labels (badges, single-word buttons, headlines ≤ 2 lines).
- Baseline-align mixed-size elements in a row (icon + label + badge) rather than center-aligning them vertically by box — optical centering often beats geometric centering for icons next to text.

---

## 1. Tables

### 1.1 First principle: design for the task, not the data
NN/g's research identifies four things people do with a table — and your layout should be built around whichever is primary:
1. **Find** a record matching criteria → prioritize a visible, prominent filter/search.
2. **Compare** records → prioritize column alignment and vertical scanability.
3. **View/edit** a single row → prioritize a clear row-click target and inline edit affordance.
4. **Act** on data (bulk operate) → prioritize checkboxes, sticky bulk-action bar, and hover-revealed row actions.
Decide which of these four is dominant before choosing density, filter placement, or whether rows are clickable.

### 1.2 Alignment & typography (non-negotiable)
| Content type | Alignment | Notes |
|---|---|---|
| Text / labels / names | Left | Matches reading direction |
| Numbers / currency / counts | Right | Enables place-value comparison; use tabular-nums |
| Dates | Right or left, pick one and hold it | Right if often compared, left if scanned like text |
| Status / badges / short tags | Left (never center) | Center only if column is icon-only, fixed narrow width |
| Actions (icon buttons) | Right, pinned | Keep in a fixed-width trailing column |

### 1.3 Structure
- **Sticky header row** on any table taller than ~1 viewport.
- **Default sort** on the column most relevant to the primary task (usually recency or the sortable identifier) — never ship an unsorted table.
- **Row height**: base it on the 8pt grid — 40px (dense/data-grid), 48px (default), 56px (comfortable/touch). Keep one height per table; don't mix.
- **Zebra striping**: use sparingly and only for wide, low-contrast tables where row-tracking is hard; a 1px hairline row divider is usually sufficient and less noisy.
- **Filters**: place directly adjacent to (ideally above) the column headers they affect, not buried in a separate panel — proximity is what makes filter-to-column mapping obvious.
- **Column truncation**: truncate with ellipsis + full value on hover/tooltip; never silently clip without indicating truncation occurred.

### 1.4 Pagination vs. infinite scroll
- **Pagination**: use when users need to reference a specific position ("row 340") or return to the same spot — supports bookmarking/sharing state via URL params.
- **Infinite scroll**: use for exploratory/feed-like browsing where position doesn't matter; never for data users need to audit exhaustively (infinite scroll makes "have I seen everything" unanswerable).
- Either way, always show **total count** and a way to jump to first/last.

### 1.5 Small-screen / responsive strategy
Pick one, don't half-implement all three:
1. **Column priority/hide** — hide lowest-priority columns first, expose via a "more" toggle.
2. **Horizontal scroll** with a pinned first (identifier) column.
3. **Card/list transform** — each row becomes a stacked card below a breakpoint (best for ≤6 columns).

### 1.6 Anti-patterns
- Centering numeric or text columns.
- No default sort, or sort state that resets on navigation.
- Filters that live in a drawer disconnected from the columns they touch.
- Infinite scroll on data users must audit completely (compliance logs, invoices).
- Row actions that only appear on hover with no keyboard/touch equivalent (unusable without a mouse).

### 1.7 Libraries
| Library | Best for | Notes |
|---|---|---|
| **TanStack Table** (React/Vue/Solid) | Headless logic, full custom UI control | No styling opinions — pair with your own design system; industry standard for custom data tables |
| **AG Grid** | Enterprise-grade, huge datasets, Excel-like editing | Virtualized rendering, best-in-class performance at 100k+ rows; heavier bundle |
| **MUI X DataGrid** | Fast integration in a Material UI app | Free tier is limited; Pro/Premium unlock grouping, pivoting |
| **Ant Design Table** | Enterprise admin panels, fast to ship | Opinionated styling, good defaults for dense back-office UIs |
| **react-data-grid (Adazzle)** | Spreadsheet-like inline editing | Good for Excel-paste-in workflows |

---

## 2. Charts & Graphs

### 2.1 Chart-type decision tree
```
What's the message?
├─ Comparison across categories → Bar chart (horizontal if labels are long)
├─ Trend over time → Line chart (never bar for continuous time series)
├─ Part-to-whole, ≤5 slices → Pie/donut (past 5 slices → switch to bar)
├─ Distribution → Histogram / box plot
├─ Correlation between 2 variables → Scatter plot
├─ Only 1–2 values total → Skip the chart. Use a plain stat/table — a chart with 2 data points adds noise, not clarity.
```

### 2.2 Typography & labeling
- Minimum font size: **12px** for axis/tick labels, but prefer **16px** for anything a user is expected to read closely (titles, key callouts).
- Sans-serif only, one typeface, sentence case (not Title Case) for titles and labels.
- **Direct labeling beats legends** — label the line/bar/slice itself where space allows; legends require the eye to travel back and forth and hurt both clarity and accessibility.
- Chart title should state the *insight*, not just the metric name ("Revenue grew 34% in Q3" beats "Q3 Revenue").

### 2.3 Color
- **3–5 colors maximum** per chart. Beyond 5 categories, colors become indistinguishable — switch to small multiples or a table.
- Use a colorblind-safe palette (ColorBrewer, Okabe-Ito) and verify with a simulator.
- **Never encode meaning in color alone** — pair with pattern, shape, or direct label so red-green colorblind users (≈8% of men) aren't locked out.
- Diverging palettes (low–neutral–high) for data with a meaningful midpoint; sequential palettes for one-directional magnitude.

### 2.4 Gridlines, axes, chart junk
- Y-axis **starts at zero** for bar charts — truncated axes visually exaggerate differences and are a classic misleading-chart pattern. (Line charts tracking small fluctuations in a large-magnitude metric are the one defensible exception — label the break clearly if you do it.)
- Gridlines: thin, light gray, or omit entirely if direct labels make them redundant. Never heavy/dark gridlines.
- Remove: drop shadows, 3D effects, decorative backgrounds, redundant borders, unnecessary legends. Every non-data pixel competes with the data for attention.
- Test the design in **grayscale first** — if it's not legible without color, color is being used as a crutch, not an enhancement.

### 2.5 Accessibility
- Provide a **data table fallback** for every chart (visually hidden or in an expandable section) so screen reader users get the same information.
- Descriptive `alt` text stating the chart's takeaway, not just "bar chart of revenue."
- All interactive chart elements (tooltips, zoom, legend toggles) must be keyboard-operable.

### 2.6 Libraries
| Library | Best for | Notes |
|---|---|---|
| **Recharts** | React, declarative, common business charts | Fastest to ship line/bar/area/pie; built on D3 internals, React-friendly API |
| **visx (Airbnb)** | Full control, custom/novel chart types | Low-level D3 primitives as React components — more code, more freedom |
| **D3.js** | Bespoke, highly custom visualizations | The foundation everything else sits on; steepest learning curve, no ceiling |
| **Observable Plot** | Fast exploratory/analytical charting | Concise grammar-of-graphics API, great defaults, less UI customization |
| **ECharts (Apache)** | Dashboards, large datasets, built-in interactivity | Canvas-based, handles huge datasets well, strong out-of-box polish |
| **Nivo** | Pre-styled, good-looking charts fast | Built on D3 + React, more opinionated visual defaults than Recharts |
| **Chart.js** | Simple, lightweight, framework-agnostic | Canvas-based, minimal bundle size, good for simple dashboards |

---

## 3. Inputs & Forms

### 3.1 Label placement
- **Default: top-aligned labels**, directly above the field. NN/g usability studies consistently show this produces the fastest completion time and fewest errors — the eye moves straight down, no horizontal repositioning.
- Exception — side-by-side is acceptable **only** for tightly coupled field pairs treated as one unit: first/last name, expiry/CVV, city/postal code.
- **Never use placeholder text as a label.** It disappears the instant the user types, forcing reliance on memory — this is both a usability failure and a WCAG violation. Placeholders are only for format hints (`name@company.com`) shown *alongside* a real visible label.
- Floating labels (label starts inline, animates above on focus) are an acceptable middle ground if you need vertical density, but they cost extra motion/complexity for marginal gain over static top-aligned labels — default to static unless space is genuinely constrained.

### 3.2 Layout
- **Single column by default.** Multi-column forms increase completion time and error rate except for the tightly-coupled pairs above — the eye has to decide reading order.
- Group related fields with clear section headings and generous spacing (external gap between groups > internal gap between a group's own fields — see the 0.1 internal≤external rule).
- Every field you include costs conversion — audit ruthlessly, cut anything not essential to the immediate task. Use **conditional/branching logic** to hide irrelevant fields rather than showing everything up front.

### 3.3 Validation
- **Validate inline, after the user leaves the field (on blur)** — not on every keystroke (punishes mid-typing) and not only on submit (forces users to hunt for errors after the fact).
- Once an error is shown, re-validate on every keystroke as they fix it, so the error clears the moment it's resolved — that shift from "punish while typing" to "reward while fixing" is the actual UX win.
- Error messages: state what's wrong **and** how to fix it, positioned directly below the field, not in a summary banner disconnected from the field. Keep tone matter-of-fact, not apologetic.
- Use input masks for fixed-format fields (phone, card number, date) to prevent format errors before they happen.

### 3.4 Mobile & input types
- Use the correct HTML input type/`inputmode` so the OS shows the right keyboard: `type="email"`, `type="tel"`, `inputmode="numeric"` for numeric-only entry (PIN, OTP), `type="date"` for native date pickers.
- Minimum 44px touch height per field on mobile (ties back to §0.3).
- Enable autofill: correct `autocomplete` attributes (`name`, `email`, `street-address`, `cc-number`, etc.) — this alone removes significant friction on repeat forms.

### 3.5 Buttons & submission
- Button copy should be **action-specific**: "Create account" / "Start free trial" outperforms generic "Submit."
- Primary action button: one per form/screen, visually dominant. Secondary/cancel actions: visually recessive, never competing in size or color weight.
- Disable the submit button only after a clear reason is shown (not silently) — silent disabled states read as a bug.

### 3.6 Multi-step forms
See §4 (Steppers) — anything past 3 fields with logically distinct phases (e.g., account info → billing → confirmation) should become a stepper rather than one long scroll.

### 3.7 Anti-patterns
- Placeholder-as-label.
- Validating on every keystroke before the user has finished.
- Multi-column layout for unrelated fields.
- Generic "Submit" button copy.
- No visible labels for icon-only inputs (search fields need a visually-hidden `<label>` even if the placeholder shows "Search").

### 3.8 Libraries
| Library | Best for | Notes |
|---|---|---|
| **React Hook Form** | Performance-focused React forms | Uncontrolled-first, minimal re-renders, industry default for React forms |
| **Zod** (paired with RHF) | Schema-based validation | TypeScript-first, shared schema between client validation and API boundary |
| **Formik** | Simpler/older React forms | More re-renders than RHF; still fine for small forms, losing mindshare to RHF |
| **Radix UI (primitives)** | Unstyled, accessible form primitives | Correct ARIA/keyboard behavior out of the box — build your visual layer on top |
| **React Aria (Adobe)** | Accessibility-first primitive hooks | Deepest accessibility guarantees of any React primitive library |

---

## 4. Steppers / Wizards

### 4.1 When to use one
Use a stepper when a flow has **more than ~3 fields split across logically distinct phases** — onboarding, checkout, account setup. Below that, a single-page form is simpler and faster.

### 4.2 Step count
- **3–6 steps is the sweet spot.** Past 6, completion rates measurably drop — either simplify the flow or split it into separately-entered phases (each with its own short stepper), rather than one long stepper.

### 4.3 Pattern selection
| Pattern | Use when |
|---|---|
| **Horizontal step indicator** (numbered circles + connecting line) | 3–5 linear steps, desktop or tablet width |
| **Vertical stepper** | Longer flows, steps need room for sub-labels, or users may revisit earlier steps often |
| **Dots** | ≤5 steps, mobile, minimal chrome desired — but dots don't communicate "how many are left" once you're deep in, so cap at 5 |
| **Text stepper** ("Step 2 of 4") | Fastest to build, works at any width, always tells the user exactly where they are — underrated, hard to get wrong |
| **Thin progress bar, no step count** | Onboarding/quiz flows where you want attention on content, not mechanics |

### 4.4 Rules regardless of pattern
- Always show **explicit progress** (indicator visible at every step) — this is the single biggest anxiety-reducer in multi-step flows.
- **Back must always work**, and must preserve previously entered data — never force re-entry.
- Let users **review/edit completed steps** before final submit; don't make the flow strictly forward-only unless there's a hard business reason (e.g., payment already processed).
- Validate at the step level before allowing "Next," not only at final submit — catches errors immediately rather than dumping a wall of errors at the end.
- Each step needs a clear title and must be self-contained — a user should understand what a step is asking without needing context from other steps.
- Keyboard: the entire stepper must be operable without a mouse (Tab through fields, Enter to advance where appropriate).

### 4.5 Anti-patterns
- More than 6–7 steps in one stepper.
- No progress indicator (users don't know how much is left → highest abandonment driver).
- Back button that clears previously entered data.
- Steps that can't be reached via keyboard.
- Dots pattern used for 7+ steps (illegible progress once past ~5).

### 4.6 Libraries
| Library | Best for |
|---|---|
| **Radix UI + custom** | Full control, accessible primitives, build the visual stepper yourself |
| **MUI Stepper** | Fast integration in a Material UI app, both linear and non-linear modes built in |
| **Ant Design Steps** | Enterprise/admin flows, good default vertical + horizontal variants |
| **React Hook Form + step-state pattern** | Multi-step forms — keep one RHF instance across steps, gate `trigger()` validation per step before advancing |

---

## 5. Multi-Button Groups / Segmented Controls

### 5.1 Decision matrix — pick the right control, not just the right look
| Control | Selection behavior | Triggers immediate effect? | Use when |
|---|---|---|---|
| **Segmented control** | Single-select, mutually exclusive | Yes — changes view/state immediately | 2–5 options, all equally weighted, view/mode switch (e.g., list vs. grid) |
| **Radio group** | Single-select | No — requires explicit submit/confirm | Inside a form, needs review before applying (e.g., shipping method choice before checkout) |
| **Toggle/switch** | Binary on/off | Yes, immediately | Exactly 2 states that are true opposites (on/off), not "opposing options" needing a label per state |
| **Tabs** | Single-select, navigational | Yes — swaps displayed content | Options represent *separate views/content*, not settings — segmented control and tabs are often confused, but tabs imply navigation, segmented controls imply a setting |
| **Checkbox group / multi-select chips** | Multi-select | No, until submitted | Any case allowing more than one selection |

Apple's HIG defines a segmented control as a linear set of mutually-exclusive segments, each behaving like a button — functionally close to a radio group, but semantically for *immediate* state changes, not form fields awaiting submission. Don't use one for a decision that needs a "Save" step; use a radio group for that instead.

### 5.2 Rules
- **2–5 options only.** Past 5, switch to a dropdown/select — segmented controls that wrap or scroll horizontally have failed their purpose.
- All segments in one row share equal visual weight — a segmented control is wrong if one option should be visually dominant (that's a job for a primary/secondary button pair instead).
- Options must be genuinely mutually exclusive and roughly equal length — wildly uneven label lengths break the visual rhythm.
- Every segment meets the 44px touch target (§0.3), with segments visually connected (shared border/track) so the group reads as one control, not a row of separate buttons.
- Active segment needs a clear, high-contrast selected state — not just a subtle background shift; the whole point of the control is that state must be unambiguous at a glance.
- Keyboard: arrow keys move between segments, Enter/Space selects — this is standard ARIA `radiogroup`/`tablist` behavior; don't reinvent it.

### 5.3 Anti-patterns
- Segmented control used for a decision requiring an explicit "Save" (should be a radio group).
- More than 5 segments (should be a select/dropdown).
- Mixing a segmented control and a toggle button group with the same visual style in one product — users can't tell which mental model applies (immediate-effect vs. review-then-submit).
- Icon-only segments with no accessible label (needs `aria-label` per segment at minimum).

### 5.4 Libraries
| Library | Notes |
|---|---|
| **Radix UI Toggle Group** | Unstyled, correct ARIA (`role=radiogroup` or `role=group` depending on single/multi) — best starting primitive |
| **Ant Design Segmented** | Pre-styled, drop-in, matches Ant's design language |
| **MUI ToggleButtonGroup** | Pre-styled for Material UI apps, supports exclusive and multi-select modes |
| **shadcn/ui Toggle Group** | Radix-based, Tailwind-styled, easiest to restyle to a custom design system |

---

## 6. Three.js / React Three Fiber — Development Standards

### 6.1 Renderer setup (2026 baseline)
- Default to **WebGPU with automatic WebGL2 fallback** (available since Three.js r171; all major browsers support WebGPU as of late 2025).
```js
import { WebGPURenderer } from 'three/webgpu';
const renderer = new WebGPURenderer();
await renderer.init(); // mandatory before first render — silent failure if skipped
```
- If targeting custom shaders across both backends, write them in **TSL (Three Shader Language)** rather than raw GLSL — it compiles to both WebGPU and WebGL.

### 6.2 Draw-call discipline (the #1 performance lever)
- **Target under 100 draw calls** for smooth 60fps on mid-range hardware — this matters far more than raw triangle count.
- **Instance repeated geometry** — anything appearing more than a handful of times (particles, foliage, crowd members) goes through `InstancedMesh` or Drei's `<Instances>`, never individual meshes.
- **Merge static geometry** where objects don't move independently — combine into one `BufferGeometry` at build/load time rather than many draw calls.
- **Texture atlas** repeated materials to cut material-switch overhead.

### 6.3 React Three Fiber — the rules that actually matter
- **Mutate via refs inside `useFrame`, never via React state.** Calling `setState` every frame (60×/sec) will visibly tank frame rate — this is the single most common mistake React developers make moving into R3F.
```js
// Wrong — triggers a React re-render every frame
const [rotation, setRotation] = useState(0);
useFrame(() => setRotation(r => r + 0.01));

// Right — direct mutation, no React involvement
const meshRef = useRef();
useFrame((_, delta) => { meshRef.current.rotation.x += delta; }); // use delta, not a fixed increment
```
- Use `delta` (frame-time delta) for any per-frame increment, not a fixed step — otherwise animation speed varies with the user's frame rate/device.
- **`useMemo` every expensive geometry/material.** Without it, any parent re-render recreates the object from scratch and leaves the old one to be garbage-collected — GC pressure is a leading cause of stutter in R3F scenes.
```js
const geom = useMemo(() => new THREE.BoxGeometry(), []);
const mat = useMemo(() => new THREE.MeshStandardMaterial({ color: 'orange' }), []);
```
- **Dispose explicitly when you build geometry/materials imperatively.** R3F auto-disposes objects declared declaratively in JSX on unmount, but anything you construct yourself in a `useMemo`/`useLoader` needs a manual cleanup — the GPU has no garbage collector the way the DOM does.
```js
useEffect(() => () => geometry.dispose(), [geometry]);
```
- Avoid `useEffect` + `requestAnimationFrame` for animation — use `useFrame`, which plugs directly into R3F's render loop and handles cleanup for you.
- For state shared across many components without triggering React re-renders on every frame, use **Zustand** (or similar) read imperatively inside `useFrame` via `.getState()`, not via a subscribed hook that re-renders.

### 6.4 Lighting & environment
- Prefer **environment maps / IBL** (image-based lighting) over multiple dynamic lights — dynamic lights are one of the most expensive per-frame costs in a scene; fewer, baked, or environment-map-driven lighting scales far better.
- Bake what doesn't change: lightmaps, ambient occlusion, static shadows — don't recompute per frame what's static per scene.

### 6.5 Assets
- Compress geometry with **Draco**, textures with **KTX2/Basis** — both are standard, well-supported compression pipelines that dramatically cut load size and GPU memory.
- Implement **LOD** (level of detail) for anything viewed at varying distance — swap to lower-poly meshes as camera distance increases.
- Use **frustum culling** (on by default in Three.js, but verify large/merged meshes aren't disabling it) and consider occlusion culling for dense indoor scenes.

### 6.6 Rendering strategy
- Use **on-demand rendering** (`frameloop="demand"` in R3F) for static/UI-like scenes — only re-render when something actually changes, saving battery/CPU on mobile.
```js
const invalidate = useThree((state) => state.invalidate);
// after any state change that should trigger a redraw:
invalidate();
```
- Cap device pixel ratio (`Math.min(window.devicePixelRatio, 2)`) — rendering at native 3× DPR on high-end phones burns GPU budget for imperceptible sharpness gain.
- Disable antialiasing on mobile/low-power devices as a fallback tier.

### 6.7 Profiling — measure before optimizing
- **stats-gl** or **r3f-perf**: real-time FPS/draw-call/triangle overlay.
- `renderer.info` — programmatic access to draw calls, triangles, geometries, textures in memory.
- **Spector.js** — frame-by-frame WebGL call inspection for deep debugging.
- A practical pre-ship checklist:
  - [ ] Draw calls < 100 for complex scenes
  - [ ] Instancing used for all repeated objects
  - [ ] LOD applied to large/distant objects
  - [ ] Static geometry merged where possible
  - [ ] Textures compressed (KTX2/Basis)
  - [ ] DPR capped at 2
  - [ ] Heavy assets lazy-loaded behind `<Suspense>`
  - [ ] All manually-created geometries/materials disposed on unmount

### 6.8 Anti-patterns
- `setState` inside `useFrame`.
- Creating new `THREE.Vector3`/geometry/material instances inside the render loop instead of reusing memoized ones.
- One draw call per object when objects are visually identical (should be instanced).
- Multiple dynamic point/spot lights when an environment map would do the job.
- No `dispose()` calls on manually-constructed resources — silent VRAM leak until the tab crashes.
- Shipping uncompressed textures/geometry to production.

### 6.9 Libraries
| Library | Purpose |
|---|---|
| **three.js** | Core WebGL/WebGPU engine — the foundation |
| **@react-three/fiber** | React renderer for Three.js — declarative scene graph |
| **@react-three/drei** | Ready-made helpers: `<Instances>`, `<Environment>`, `useTexture`, `OrbitControls`, `Html`, LOD helpers |
| **@react-three/postprocessing** | Post-processing effect chains (bloom, DOF, SSAO) without hand-rolling shader passes |
| **Zustand** | Lightweight state store for scene state read imperatively in `useFrame` |
| **r3f-perf** | In-scene performance overlay (draw calls, FPS, memory) built for R3F |
| **stats-gl** | Modern replacement for the classic Stats.js FPS panel |
| **Draco / KTX2 loaders** (`three/examples/jsm/loaders`) | Geometry and texture compression pipelines |

---

## 7. Cross-Cutting Rules (apply to all of the above)

- **Reduced motion**: respect `prefers-reduced-motion` — disable non-essential animation (stepper transitions, chart entrance animations, 3D camera drift) for users who've opted out at the OS level.
- **Keyboard operability**: every interactive pattern above (table row actions, chart tooltips, stepper navigation, segmented controls, form fields) must be fully usable via keyboard alone — this isn't a nice-to-have, it's the baseline for WCAG 2.1 AA compliance and it's the fastest way to catch a broken component during dev (if you can't Tab through it, it's not done).
- **Contrast**: WCAG AA requires 4.5:1 for normal text, 3:1 for large text (≥18px/24px bold) and for UI component boundaries (input borders, button outlines).
- **Consistency over cleverness**: one spacing scale, one type scale, one button-group pattern per decision type, used identically everywhere. Inconsistency — not lack of polish — is what makes an interface feel undesigned.

---

## 8. Consolidated Library Reference

| Category | Recommended default | Alternatives |
|---|---|---|
| Tables (React) | TanStack Table | AG Grid (huge datasets), MUI X DataGrid, Ant Design Table |
| Charts (React) | Recharts | visx (custom), D3 (bespoke), ECharts (dashboards), Nivo, Chart.js |
| Forms | React Hook Form + Zod | Formik, React Aria, Radix primitives |
| Steppers | Radix UI + custom, or MUI Stepper | Ant Design Steps |
| Segmented/button groups | Radix UI Toggle Group / shadcn/ui | Ant Design Segmented, MUI ToggleButtonGroup |
| 3D | three.js + @react-three/fiber + @react-three/drei | Vanilla three.js (non-React contexts) |
| Accessible primitives (underlies most of the above) | Radix UI or React Aria | — |

---

### Sources consulted
- Nielsen Norman Group — data table task model, F-pattern scanning, form label research
- Apple Human Interface Guidelines — segmented controls, steppers, touch targets
- Material Design 3 — segmented buttons, spacing/grid conventions
- WCAG 2.2 Success Criterion 2.5.8 (Target Size Minimum) and 2.5.5 (Enhanced)
- W3C WAI guidance on multi-step forms and progress indicators
- React Three Fiber official docs (`r3f.docs.pmnd.rs`) — performance pitfalls
- Industry 2026 production guides on Three.js/WebGPU optimization (Utsubo, AppScale)