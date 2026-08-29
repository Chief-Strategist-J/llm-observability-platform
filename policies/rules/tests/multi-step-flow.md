# Dynamic UI & Multi-Step Flow Reliability Rules — Addendum

> Addendum to the previous rule set. This addresses WHY automation runs fast without completing the real
> journey, and WHY dropdowns/dialogs/scrolling/multi-step flows fail intermittently. These are execution
> reliability rules — apply them inside every step definition/page object, regardless of feature.

---

## 1. The Core Rule Being Violated

**A test is only "complete" when it asserts the real end state of the journey — not when the last click
succeeds.** Playwright considers a script finished the instant every line executes without throwing. It
has no concept of "did the user's actual goal get accomplished." That gap is entirely the test author's
responsibility to close with assertions.

**Rule:** every transition between steps (page to page, step to step, dialog opened to dialog closed)
must have an explicit assertion that the NEXT expected state is visible/present BEFORE proceeding to
interact with it. Never chain "click → immediately act on the result" without a state check in between.

---

## 2. Dropdowns

There are two fundamentally different kinds — treat them differently, never with the same logic:

- **Native `<select>` elements:** interact via the value/label directly — do not click to "open" them
  first, native selects don't need a visibility wait for their options.
- **Custom dropdowns (styled div/list, most modern UI frameworks):**
  1. Click to open.
  2. **Assert the option-list container is visible** before doing anything else — this is the step
     almost every broken flow skips.
  3. Only then locate and click the specific option by its accessible role/text, not by position/index
     (position-based selection breaks the moment the list order changes).
  4. **Assert the dropdown closed and the selected value is now reflected in the trigger/input** before
     moving to the next field — this confirms the selection actually registered, not just that a click
     happened.

---

## 3. Dialogs — Two Different Things Often Confused

- **Native browser dialogs** (`alert`, `confirm`, `prompt`): these must have a handler registered
  *before* the action that triggers them, or the browser engine auto-dismisses them and your flow
  silently continues on a false assumption. If your flow includes any native browser dialog, the test
  must explicitly register how it will be handled (accept/dismiss/read the prompt value) as its own
  discrete step, immediately before the triggering action — never after.
- **In-page/custom modals** (a `<div>` overlay): these need their own actionable-state check —
  visible AND not mid-transition/animation. **Rule:** assert the modal is visible AND assert a stable
  element inside it (e.g. its submit button) is enabled before interacting — this avoids clicking during
  a fade-in/slide-in animation, which is one of the most common sources of "sometimes it works, sometimes
  it doesn't."
- **Rule for closing either kind:** always assert the dialog/modal is gone (not just that a "close" click
  happened) before asserting anything about the page underneath it — a modal that's visually closing but
  still intercepting clicks will cause the NEXT action to silently fail or hit the wrong element.

---

## 4. Scrolling

- Standard page-level scrolling is handled automatically before an action — you should rarely need to
  handle this yourself for elements in normal page flow.
- **Custom scrollable containers** (an inner `<div>` with its own scrollbar — common in dropdown lists,
  data tables, chat-style panels) are NOT automatically scrolled by the framework. **Rule:** any element
  inside a custom-scrolling container must be explicitly scrolled into view within that container before
  interaction is attempted — scrolling the outer page will not bring it into view.
- **Rule:** after scrolling, re-assert visibility before interacting — a scroll action completing is not
  proof the target element is now actually visible and interactable (it may be behind a sticky header,
  partially clipped, etc.).

---

## 5. Multi-Step / Multi-Page Flows (fill → next → dialog → submit → back → resubmit)

This is where most "generated" automation breaks, because it's usually written as one long linear script
instead of a state machine. Rules:

1. **Treat every page/step transition as a checkpoint, not a formality.** After any "Next"/navigation
   action, the FIRST thing the flow does is assert a unique marker element of the new step/page is
   visible — never assume the click worked and immediately try to fill the next form.
2. **Never reuse a locator captured before a navigation.** Once the page/step changes (even within the
   same SPA route), re-locate elements fresh in the new context. A locator reference held from before a
   transition is not guaranteed to point at the right (or any) element afterward.
3. **"Back" is a state reset, not a rewind.** When a flow goes back to a previous step and then submits
   different data, the test must NOT assume any previously entered values are still present/valid unless
   the app explicitly preserves them. Assert what's actually pre-filled (if anything) after going back,
   rather than assuming your prior input persisted.
4. **Each discrete step (page 1, dialog, page 2, back, resubmit) should be its own named action in the
   step definitions/page object — not inlined together.** This does two things: it makes the failure
   point obvious (which named step failed) instead of "the flow failed somewhere," and it forces an
   explicit "did this step's expected result actually appear" check at each boundary, which is exactly
   the check that's currently missing.
5. **The final assertion of a multi-step flow must verify the CUMULATIVE result**, not just that the last
   screen loaded. E.g., after "page 1 → dialog submit → page 2 → back → resubmit new data → final
   submit," the closing assertion must confirm the system's final state reflects the LAST submitted data
   specifically (not the first attempt, not a merge of both) — this is the same "silent failure" risk
   from Category E, applied to a multi-step context: the UI can show a generic "success" while having
   actually kept the wrong version of the data.
6. **If any step in the middle can fail without breaking the whole script (e.g. a dialog silently not
   opening), the test must still fail.** Add an explicit assertion after every intermediate step, even
   ones that "always work" — an intermediate step silently no-op'ing (e.g. clicking a dropdown that
   didn't actually open) is exactly what produces a fast, "successful," but incomplete run.

---

## 6. Diagnostic Checklist When a Flow "Runs but Doesn't Complete Properly"

Work through these in order before assuming it's a framework/tool problem:

1. Is there an explicit assertion for the FINAL expected state of the whole journey, tied to real data
   (not just "a success message appeared somewhere")? If not, add one — this alone often reveals the
   test was never actually verifying completion.
2. For each transition (click → next state), is there a visibility/state assertion for the next state
   BEFORE the next action is attempted? If any transition goes click → immediately interact with the
   result, that's the first place to add a checkpoint.
3. For any dropdown: is the option-list container's visibility asserted before clicking an option?
4. For any dialog/modal: is it a native browser dialog (needs a pre-registered handler) or a custom
   in-page modal (needs a visible + stable-and-enabled check)? Confirm you're handling the right kind.
5. For any scrolling issue: is the element inside a custom-scrolling container rather than the page
   body? If so, does the scroll target that specific container, not the page?
6. For "back then resubmit": is the test asserting what's actually present in the form after going back,
   rather than assuming prior data is still there?
7. Replay the failing run with the trace viewer and step through frame-by-frame — the exact moment the
   real app state diverges from what the script assumed will be visible in the trace's DOM snapshots.