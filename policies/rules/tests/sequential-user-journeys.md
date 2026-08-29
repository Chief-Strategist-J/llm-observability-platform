# Master Policy — Language-Agnostic Sequential Production User Journeys, UI Element Discovery & End-to-End Execution Rules

## Table of Contents
1. [Purpose & Core Philosophy](#1-purpose--core-philosophy)
2. [Language-Agnostic Architecture & Directory Structure](#2-language-agnostic-architecture--directory-structure)
3. [Strict Sequential Execution Controls](#3-strict-sequential-execution-controls)
4. [UI Component Element Searching & Discovery Taxonomy](#4-ui-component-element-searching--discovery-taxonomy)
   - 4.1 [Universal Locator Discovery & Searching Priority Hierarchy](#41-universal-locator-discovery--searching-priority-hierarchy)
   - 4.2 [Buttons & Action Triggers](#42-buttons--action-triggers)
   - 4.3 [Dropdowns, Selects & Autocomplete Comboboxes](#43-dropdowns-selects--autocomplete-comboboxes)
   - 4.4 [Dialogs, Modals, Overlays & Alert Popups](#44-dialogs-modals-overlays--alert-popups)
   - 4.5 [Radio Buttons & Radio Groups](#45-radio-buttons--radio-groups)
   - 4.6 [Checkboxes & Toggle Switches](#46-checkboxes--toggle-switches)
   - 4.7 [Inputs, Textfields & Search Controls](#47-inputs-textfields--search-controls)
   - 4.8 [Data Tables & Dynamic Grids](#48-data-tables--dynamic-grids)
   - 4.9 [Tabs, Accordions, Toasts & Tooltips](#49-tabs-accordions-toasts--tooltips)
5. [Comprehensive Test Case Coverage Taxonomy](#5-comprehensive-test-case-coverage-taxonomy)
   - 5.1 [Double-Tap, Rapid Re-Click & Debounce Protection](#51-double-tap-rapid-re-click--debounce-protection)
   - 5.2 [Input Validation & Wrong Data Boundary Coverage](#52-input-validation--wrong-data-boundary-coverage)
   - 5.3 [Security Specialist Data & Vulnerability Test Payloads](#53-security-specialist-data--vulnerability-test-payloads)
   - 5.4 [Master 20 Critical Edge Cases Matrix](#54-master-20-critical-edge-cases-matrix)
   - 5.5 [Master Data Validation Edge Cases Taxonomy (OWASP & Industry Standards)](#55-master-data-validation-edge-cases-taxonomy-owasp--industry-standards)
6. [Domain-Agnostic Production Lifecycle Phase Matrix](#6-domain-agnostic-production-lifecycle-phase-matrix)
7. [Anti-Patterns & Automatic Rejection Rules](#7-anti-patterns--automatic-rejection-rules)
8. [Universal Page & Component Object Abstraction Rules](#8-universal-page--component-object-abstraction-rules)
   - 8.1 [Universal Page Object Architectural Blueprint](#81-universal-page-object-architectural-blueprint)
   - 8.2 [Component Objects for Reusable Complex UI Widgets](#82-component-objects-for-reusable-complex-ui-widgets)
   - 8.3 [Page Object Scoping & Design Rules](#83-page-object-scoping--design-rules)
9. [State Preservation & Diagnostic Logging](#9-state-preservation--diagnostic-logging)
10. [Language-Agnostic Code Patterns & Generic Templates](#10-language-agnostic-code-patterns--generic-templates)
11. [Multi-Stack CLI Command Registry & Execution References](#11-multi-stack-cli-command-registry--execution-references)

---

## 1. Purpose & Core Philosophy

Isolated unit, integration, or single-endpoint tests verify individual API routes or components in isolation. They **do not prove** that a real user can navigate a multi-screen flow, interact with dynamic UI controls (buttons, dropdowns, dialogs, radio groups), trigger background pipelines, encounter validation guards, authenticate, view telemetry, and manage organization settings in sequence.

A **Sequential User Journey** tests the cumulative, end-to-end lifecycle of a user across multiple services, UI routes, dynamic modal transitions, and persistent backend state changes in any software application domain.

### Key Principles:
- **Language-Agnostic & Stack-Agnostic**: These rules apply identically whether your test automation harness is built in Node.js/TypeScript, Python, Java/Kotlin, Go, C#, or uses engines like Playwright, Cypress, Selenium, Appium, PyTest, or Cucumber BDD.
- **Generic & Extensible Design**: All architecture rules, page objects, and test phases MUST be fully generic so they can be implemented for ANY application domain (SaaS, E-Commerce, Healthcare, AI Agents, Financial, Analytics, Workflow Automation).
- **Robust UI Locating & Finding**: Tests MUST discover and target UI controls using semantic accessibility attributes, explicit test IDs, or visible labels—NEVER fragile DOM indexing or CSS styling selectors.
- **State-Verified Transitions**: Every interaction (clicking a button, selecting a radio option, confirming a dialog) MUST verify state changes before proceeding to the next step.

---

## 2. Language-Agnostic Architecture & Directory Structure

All sequential user journeys MUST be stored in a dedicated, unified automation directory structure regardless of programming language or framework.

```
tests/automation/e2e/
├── journeys/                               # BDD Gherkin Feature Scenarios (What is tested)
│   ├── sequential-user-flow.feature
│   └── <domain>-user-flow.feature
├── step-definitions/                       # Language-Specific Step Glue (TypeScript/Python/Java)
│   └── journeys_steps.[ts|py|java]
├── page-objects/                           # Extensible Page & Component Abstractions
│   ├── base_page.[ts|py|java]             # Universal Abstract Base Class
│   ├── components/                         # Embedded Reusable Widgets
│   │   ├── modal_component.[ts|py|java]
│   │   └── data_table_component.[ts|py|java]
│   └── <domain>/                           # Domain-Specific Page Objects
│       ├── <feature>_page.[ts|py|java]
│       └── <subfeature>_page.[ts|py|java]
├── support/                                # Journey State Context & Diagnostic Handlers
│   └── journey_context.[ts|py|java]
└── runners/                                # Serial Execution Specs / Test Suites
    └── <journey_name>.journey.[spec.ts|test.py|Test.java]
```

### Naming Conventions:
- **Feature Specification**: `<journey-name>.feature`
- **Serial Runner File**: `<journey-name>.journey.[spec.ts|test.py|Test.java]`
- **Mandatory Scenario Tagging**: Every sequential journey scenario MUST be tagged `@e2e @sequential-journey @critical`.

---

## 3. Strict Sequential Execution Controls

To prevent race conditions, test thread shuffling, or cross-environment data contamination, all sequential journeys MUST follow these execution rules:

1. **Strict Serial Runner Execution**:
   - Every sequential journey MUST execute steps strictly in serial sequence.
   - If Step $N$ fails, subsequent dependent steps in the journey MUST be immediately halted with a dependent failure status, preventing noise cascades.

2. **Single Thread / Single Worker Limit (`workers = 1`)**:
   - Sequential journeys MUST execute on a single worker thread (`--workers=1`, `pytest -n 0`, `parallel=false`) to guarantee thread-safe state continuity.

3. **Collision-Free Deterministic Test Data**:
   - All user emails, usernames, and organization names generated during a journey MUST use dynamic collision-free generators (e.g. `generate_unique_email("prod_admin")`).

4. **Dual Verification Rule (UI State + Backend API State)**:
   - Every phase in the journey MUST verify both the UI state transition (e.g., table updated, dialog closed) and the server API/DB state before advancing.

---

## 4. UI Component Element Searching & Discovery Taxonomy

Modern web applications use complex dynamic components (modal dialogs, styled ARIA comboboxes, custom radio buttons, slide-over drawers). Locating and interacting with these elements reliably requires standard searching strategies.

### 4.1 Universal Locator Discovery & Searching Priority Hierarchy

When locating any UI component, test harnesses MUST evaluate locator strategies in the following strict priority order:

| Priority | Strategy | Example Selector Concept | Reason |
|---|---|---|---|
| **1 (Highest)** | Accessible Role & Name | `role="button"`, `name="Submit Order"` | Mirrors screen-reader accessibility; resistant to UI re-styling |
| **2** | Associated Form Label | `label="Email Address"`, `for="user-email"` | Direct human-perceived label association |
| **3** | Dedicated Test Attribute | `data-testid="submit-btn"`, `data-cy="role-radio"` | Explicit test contract resilient to structural DOM refactoring |
| **4** | Container-Scoped Text | `dialog.find_by_text("Confirm Delete")` | Scopes search inside specific modal/card boundary |
| **BANNED** | DOM Index / Position | `tr:nth-child(3) > td:nth-child(5) > button` | Breaks immediately on row insert/delete or sorting |
| **BANNED** | Styling CSS Classes | `.btn.btn-primary.blue-500` | Breaks whenever visual styling changes |
| **BANNED** | Auto-Generated Dynamic IDs | `#input-x92f-a3` | Re-generated on every framework re-render |

---

### 4.2 Buttons & Action Triggers

Buttons initiate actions, submit forms, or open overlays. They exist as standard HTML `<button>`, `<input type="submit">`, or custom `role="button"` elements.

```
+-------------------------------------------------------+
|  [Icon] Submit Action  [Spinner / Disabled]           |
+-------------------------------------------------------+
```

#### Searching & Finding Rules:
- **Search Strategy**: Search primarily by accessible role and visible text/name (e.g. `get_by_role("button", name="Submit Action")`).
- **Icon / Unlabeled Buttons**: Search by `aria-label`, `title`, or explicit `data-testid` (e.g. `data-testid="close-dialog-btn"`).
- **Loading / Disabled State Verification**:
  - BEFORE clicking, assert the button is **visible** and **enabled** (`not disabled` and `aria-disabled != "true"`).
  - If a spinner/loading indicator is active inside the button (`.is-loading`, `aria-busy="true"`), wait for the loading state to clear before clicking.
- **Post-Click Checkpoint**: Assert the button state changes (e.g., disabled during API call) or the expected target UI transition (e.g. modal opens, route changes) occurs immediately.

---

### 4.3 Dropdowns, Selects & Autocomplete Comboboxes

Dropdowns fall into two distinct structural categories: Native `<select>` elements and Custom ARIA Listbox/Combobox controls.

```
Native Select:             Custom ARIA Combobox:
+-------------------+      +--------------------------------+
| Select Option  v |      | Choose Item: [ Selected    v ] |
+-------------------+      +--------------------------------+
                             | [Search items...           ] |
                             | > Option 1                   |
                             |   Option 2                   |
                             +------------------------------+
```

#### Searching & Finding Rules:
1. **Native `<select>` Elements**:
   - Locate by associated `<label>` or accessible name.
   - Interact directly via option value or label (e.g. `select_option(label="Option 1")`). Do NOT attempt to click to open native select menus.
2. **Custom ARIA Comboboxes / Styled Dropdowns**:
   - **Step 1: Open Trigger**: Locate the dropdown trigger element by label or `role="combobox"` / `role="button"` and click it to expand.
   - **Step 2: List Visibility Checkpoint**: Explicitly wait and assert that the popup option container (`role="listbox"`, `role="menu"`, or `[aria-expanded="true"]`) is **visible** before searching for options.
   - **Step 3: Searchable Dropdowns (Typeahead)**: If the dropdown contains a search filter input, locate the search input inside the popup container, enter query text, and wait for filtered options to render.
   - **Step 4: Option Selection**: Locate the desired option inside the container by `role="option"` and accessible text (e.g. `listbox.get_by_role("option", name="Option 1")`) and click it.
   - **Step 5: Dropdown Closure Checkpoint**: Assert that the dropdown list container closes AND the trigger control reflects the selected value text.

---

### 4.4 Dialogs, Modals, Overlays & Alert Popups

Modals interrupt normal execution to require user input or confirmation.

```
+-------------------------------------------------------+
|  Confirmation Modal                               [X] |
+-------------------------------------------------------+
|  Are you sure you want to proceed with this action?   |
|                                                       |
|  [ Cancel ]                     [ Confirm Action ]    |
+-------------------------------------------------------+
```

#### Searching & Finding Rules:
1. **Native Browser Dialogs (`alert`, `confirm`, `prompt`)**:
   - MUST register event handlers (e.g. `page.on("dialog", accept)`) **BEFORE** triggering the action that opens the native alert.
2. **Custom DOM Modals & Slide-Over Drawers (`role="dialog"`)**:
   - **Step 1: Container Scoping**: Once opened, locate the modal root container using `role="dialog"` or `role="alertdialog"`.
   - **Step 2: Animation Stability Assertion**: Assert the modal container is **visible** AND its entry animation (fade-in, slide-in) has completed before interacting with internal controls.
   - **Step 3: Action Scoping**: Search for elements inside the modal using container-scoped locators (e.g. `modal.get_by_role("button", name="Confirm Action")`). NEVER search for modal buttons globally on the page.
   - **Step 4: Dismissal Checkpoint**: After clicking confirm/cancel or close `[X]`, explicitly assert that the modal overlay container is **hidden/removed from DOM** before interacting with the main page behind it.

---

### 4.5 Radio Buttons & Radio Groups

Radio buttons allow selecting a single option from a mutually exclusive set.

```
Select Option Group:
 (o) Primary Option ($99/mo)
 ( ) Secondary Option ($29/mo)
```

#### Searching & Finding Rules:
- **Container Scoping**: Locate the group container via `role="radiogroup"` or associated fieldset legend (e.g. `get_by_role("radiogroup", name="Select Option Group")`).
- **Radio Selection**: Locate the individual radio option by accessible label or `role="radio"` and click it (e.g. `radiogroup.get_by_label("Primary Option ($99/mo)")`).
- **State Checkpoint**: Assert that the clicked radio has state `checked = true` (`aria-checked="true"` or `:checked`), and all sibling radio options in the group have `checked = false`.

---

### 4.6 Checkboxes & Toggle Switches

Checkboxes and toggle switches control independent boolean options.

```
[X] Enable Option Feature
Toggle: [ ON  | off ]  Receive Notifications
```

#### Searching & Finding Rules:
- **Searching**: Locate by associated label text or `role="checkbox"` / `role="switch"`.
- **State Checkpoint Before Click**: Check the current state (`is_checked()`) before clicking. Do NOT click blindly if the checkbox is already in the desired target state.
- **State Verification**: After clicking, assert that `checked` state toggles accurately (`aria-checked` flips from `false` to `true` or vice versa).

---

### 4.7 Inputs, Textfields & Search Controls

Text inputs accept user strings, passwords, numbers, and search queries.

```
Search Records: [ Type search query...            ] [Clear (X)]
```

#### Searching & Finding Rules:
- **Searching**: Locate inputs by associated `<label>` text, `placeholder`, or `role="textbox"` / `role="searchbox"`.
- **Text Clearing Protocol**: ALWAYS clear existing text content before filling new values into an input field to prevent string concatenation bugs.
- **Masked / Password Fields**: For password inputs, verify that input attribute `type="password"` is set. If testing password visibility toggle buttons (eye icon), verify field type toggles between `"password"` and `"text"`.
- **Search Inputs with Live Results**: When entering text into a live search box, wait for the network request / debounced search results panel to render before asserting search results.

---

### 4.8 Data Tables & Dynamic Grids

Data tables list rows of records with action menus, column sorting, and pagination.

```
+-------------------+-----------------+----------------+-----------------+
| Record Identifier | Property Field  | Status Badge   | Actions         |
+-------------------+-----------------+----------------+-----------------+
| Primary Record 1  | Value Alpha     | Active         | [Edit] [Delete] |
| Secondary Record  | Value Beta      | Pending        | [Edit] [Delete] |
+-------------------+-----------------+----------------+-----------------+
| < Previous  Page 1 of 5  Next >                                        |
+------------------------------------------------------------------------+
```

#### Searching & Finding Rules:
- **Row-Scoped Locator Strategy**:
  1. Locate the target row by searching for cell text inside the table: `table.get_by_role("row").filter(has_text="Primary Record 1")`.
  2. Locate action buttons/dropdowns **within that specific row boundary**: `target_row.get_by_role("button", name="Delete")`.
- **Column Header Sorting**: Locate column headers by `role="columnheader"`, click to sort, and assert `aria-sort` changes (`ascending` / `descending`).
- **Pagination Controls**: Locate pagination buttons (`Next`, `Previous`, `Page Number`) by accessible name, click, and assert table row content updates to reflect the new page.

---

### 4.9 Tabs, Accordions, Toasts & Tooltips

Dynamic UI feedback elements require precise timing assertions.

```
Tabs: [ General ] [ Security* ] [ Billing ]
Toast Alert: (v) Operation completed successfully [X]
Tooltip: (i) [ Explanatory help tooltip text ]
```

#### Searching & Finding Rules:
- **Tabs (`role="tablist"`)**:
  - Locate tabs by `role="tab"` and text. Click target tab.
  - Assert target tab has `aria-selected="true"` and target tab panel (`role="tabpanel"`) becomes visible.
- **Accordions / Collapsible Sections**:
  - Locate trigger by `role="button"` or `aria-controls`. Click to expand.
  - Assert trigger `aria-expanded="true"` and section content is visible.
- **Toast Notifications (`role="alert"` / `role="status"`)**:
  - Toast alerts are transient. Locate immediately using `role="alert"` or `role="status"`.
  - Assert toast text matches expected outcome string.
  - If testing auto-dismissal, assert toast disappears within the configured timeout window.
- **Hover Tooltips**:
  - Trigger tooltips by focusing or hovering over the target element (`element.hover()`).
  - Locate tooltip container by `role="tooltip"` and assert text content is visible.

---

## 5. Comprehensive Test Case Coverage Taxonomy

Every enterprise sequential journey MUST explicitly include scenarios across these critical testing vectors:

```
                                  TEST CASE TAXONOMY
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
5.1 Double-Tap & Debounce     5.2 Validation & Wrong Data       5.3 Security Specialist Data
  - Rapid double-click          - Boundary value limits           - XSS sanitization payloads
  - Immediate button disable    - Required field omission         - SQL/NoSQL injection payloads
  - Single-request guarantee    - Type coercion & format errors   - Path traversal payloads
  - Backend idempotency check   - Password strength validation    - RBAC & IDOR cross-tenant access
```

---

### 5.1 Double-Tap, Rapid Re-Click & Debounce Protection

Submitting forms, processing payments, or triggering workflow actions must be resilient to user double-clicking or rapid tapping.

#### Required Test Scenarios:
1. **Immediate UI Disable Check**:
   - Upon the first click on an action button (e.g. "Submit Payment", "Create Workspace"), assert that the button immediately flips to a disabled state (`disabled` or `aria-disabled="true"`) and shows a busy loading indicator (`aria-busy="true"`).
2. **Rapid Double-Tap Simulation**:
   - Fire two rapid consecutive click events on the submit button (`button.dblclick()` or two clicks within 50ms).
3. **Single API Request & Exactly-Once Execution Assertion**:
   - Intercept network traffic during the double-tap. Assert that **exactly one HTTP request** is dispatched to the backend service endpoint.
   - Assert that the backend database record is created **exactly once** (no duplicate records).
4. **Idempotency Key Reuse Verification**:
   - If the endpoint accepts an idempotency key, verify that sending duplicate requests with the same key returns the cached original result without re-executing the operation.

---

### 5.2 Input Validation & Wrong Data Boundary Coverage

Sequential journeys MUST test that invalid inputs, missing fields, and out-of-boundary values are caught cleanly both client-side and server-side.

#### Required Validation Categories:
1. **Required Field Omission**:
   - Leave required form inputs blank (e.g. empty email, blank organization name). Click submit.
   - Assert that inline field validation error messages appear immediately (e.g. `"Field is required"`), and form submission is blocked.
2. **Boundary Value & Constraint Violation Checks**:
   - **Length Boundaries**: Test string inputs at `min_length - 1` (too short) and `max_length + 1` (too long). Assert specific boundary error text.
   - **Format Constraints**: Enter malformed formats (e.g. `"not-an-email"`, `"ftp://invalid-url"`, `"123-abc-phone"`). Assert format validation blocks submission.
   - **Weak Credentials**: Test password fields with weak inputs (e.g. `"123"`, `"password"`). Assert weak password strength warnings are displayed.
3. **Wrong Data & Mismatched Input Scenarios**:
   - **Invalid Password Sign-In**: Attempt authentication using a valid user email but an incorrect password. Assert error message `"Invalid email or password"` (ensure message does not leak whether the email exists).
   - **Stale / Expired Authentication Tokens**: Attempt API interactions using an expired token or revoked session cookie. Assert system redirects to sign-in with a 401 Unauthorized state.
   - **Mismatched Confirmation Inputs**: Enter differing values in `"Password"` and `"Confirm Password"` fields. Assert mismatch alert prevents form submission.
4. **Dual Validation Assertion (Client UI + Direct API Bypass)**:
   - For every input constraint, verify that submitting invalid data directly via HTTP API client (bypassing the UI) is independently rejected with a 400 Bad Request status.

---

### 5.3 Security Specialist Data & Vulnerability Test Payloads

Enterprise sequential journeys MUST incorporate security specialist test payloads to verify that the application handles hostile or malicious inputs safely without security breaches.

#### Required Security Test Categories:

| Security Vector | Example Test Payload | Expected Safe System Behavior |
|---|---|---|
| **Cross-Site Scripting (XSS)** | `<script>alert('xss')</script>`<br>`"><img src=x onerror=alert(1)>`<br>`javascript:alert(1)` | Value is HTML-escaped/sanitized when displayed in UI. No JavaScript executes. No unhandled browser dialog appears. |
| **SQL Injection (SQLi)** | `' OR '1'='1`<br><code>'; DROP TABLE users; --</code><br>`admin' --` | Database queries use parameterized statements. Input is treated as literal string. No SQL syntax error exposed; no unauthorized records returned. |
| **NoSQL Injection** | `{"$gt": ""}`<br>`{"$ne": null}` | JSON inputs are validated against strict schema types. Operator injection is rejected with 400 Bad Request. |
| **Command Injection / Traversal** | `../../etc/passwd`<br>`127.0.0.1; cat /etc/passwd`<br>`file.txt\0.pdf` | Path traversal and shell characters are rejected. System blocks file disclosure and returns safe error response. |
| **IDOR & Cross-Tenant Access** | Accessing Resource ID `org_123` while authenticated as Tenant `org_999` | Server checks authorization context and returns 403 Forbidden. Zero cross-tenant data leaked. |
| **Sensitive Data Exposure** | Passwords, Auth Tokens, SSNs, API Secret Keys | Password input fields use `type="password"`. Sensitive secrets are masked (`****`) in UI, DOM attributes, network payloads, and browser logs. |

---

### 5.4 Master 20 Critical Edge Cases Matrix

All automated sequential journey suites MUST include explicit test assertions for at least the following 20 critical edge cases:

| # | Critical Edge Case Category | Trigger Condition / Input Vector | Expected Safe Outcome & Required Assertion |
|---|---|---|---|
| 1 | **Rapid Double-Tap / Double-Submit** | Rapid consecutive double-click on submit button (`dblclick()`) | Button disables immediately on tap 1; exactly 1 network request fired; 0 duplicate DB records created. |
| 2 | **Mid-Journey Session Expiry** | Auth token / session cookie expires between multi-screen steps | App captures unsaved state, redirects to login, and returns user to exact step after re-auth without 500 crash. |
| 3 | **Cross-Tenant IDOR Parameter Tampering** | Logged-in user in `org_A` manually alters URL parameter `orgId=org_B` | API rejects with 403 Forbidden; zero cross-tenant data visible; security audit alert logged. |
| 4 | **Stored / Reflected XSS Payload Injection** | Input `<script>alert(1)</script>` or `"><img src=x onerror=alert(1)>` in text fields | Input is sanitized/escaped when rendered in DOM; 0 script elements instantiated; clean browser console. |
| 5 | **SQL / NoSQL Injection Attack Vectors** | Input `' OR '1'='1` or `{"$gt": ""}` into telemetry filter or search inputs | Parameterized query protects DB; input treated as literal string or rejected with 400 Bad Request. |
| 6 | **Concurrent Duplicate Record Invites** | Two admin users invite the exact same email address simultaneously | Concurrency lock / unique index handles race condition; 1 invite succeeds, 2nd receives clean conflict alert. |
| 7 | **Browser Back-Button Form Re-submission** | User completes Step 4, presses "Back" button to Step 3 form, and resubmits | SPA handles state reset cleanly; does not corrupt existing record or throw unhandled state exception. |
| 8 | **Downstream Microservice Timeout / 504** | Telemetry / analytics microservice times out during dashboard query step | UI displays graceful fallback banner ("Service unavailable, retry later"); retry button active; session preserved. |
| 9 | **Whitespace-Only Input Manipulation** | Filling required text inputs with spaces `"   "` or zero-width spaces (`\u200B`) | Input validator trims whitespace, treats field as empty, blocks submission with "Field required" message. |
| 10 | **Payload Boundary Limit Overflow** | Uploading 50MB file or submitting 10,000+ character string into text field | Enforces client-side limit; server returns 413 Payload Too Large without crashing process memory. |
| 11 | **Network Offline / Reconnection Recovery** | Network drops while clicking "Save Settings", then restores 5 seconds later | App displays "Offline" toast, queues action or retries on reconnect without duplicating state. |
| 12 | **Role Demotion Mid-Session (RBAC Revocation)** | User's role is demoted from Admin to Member while actively viewing admin settings | Next API action rejected with 403 Forbidden; UI updates available navigation routes immediately. |
| 13 | **Unicode, Emoji & International Input** | Entering characters (`Müller`, `张伟`, `éàç`), emojis (`🚀🔥`), or RTL text | Full UTF-8 handling end-to-end; no database truncation (`?`) or broken UI component rendering. |
| 14 | **Stale Modal Form State Re-opening** | Filling half a modal form, closing via `[X]`, then re-opening the modal | Form fields reset to clean initial state; no stale residual data from cancelled attempt. |
| 15 | **Soft-Deleted Record Access Re-attempt** | Attempting to view/update a record soft-deleted by another session seconds prior | Returns 404 Not Found with clean message ("Record no longer exists"); removes item from directory table. |
| 16 | **Idempotency Key Reuse Payload Mismatch** | Re-using an Idempotency Key with a modified request payload | Server rejects with 400 Bad Request ("Idempotency key payload mismatch") to prevent payload tampering. |
| 17 | **Partial Failure Workflow Saga Rollback** | In a 3-step provisioning flow (Create Org -> Provision DB -> Assign Role), Step 2 fails | Saga compensation triggers; orphaned Org is cleaned up so backend state remains consistent. |
| 18 | **Hidden / Custom Scrollbar Container Click** | Target dropdown option or table action button is inside an overflow-scroll container | Harness explicitly scrolls custom container into view, asserts element visibility, then clicks. |
| 19 | **Slow Network 3G Out-of-Order Search Race** | Fast typing in dynamic autocomplete dropdown; search responses arrive out of order | UI displays results matching the LAST typed query string, ignoring stale out-of-order network responses. |
| 20 | **Sensitive Data Masking in UI & Logs** | Typing passwords, credit card numbers, or API secret keys into form inputs | Field uses `type="password"`; values masked (`••••`) in UI, DOM, browser console, and network payload logs. |

---

### 5.5 Master Data Validation Edge Cases Taxonomy (OWASP & Industry Standards)

Data validation is the primary line of defense for application security, data integrity, and system stability. Grounded in **OWASP Input Validation Guidelines** and **Boundary Value Analysis (BVA)**, automated tests MUST verify data validation across 8 critical data categories:

```
                            DATA VALIDATION MATRIX
                                      │
     ┌──────────┬──────────┬──────────┼──────────┬──────────┬──────────┐
     ▼          ▼          ▼          ▼          ▼          ▼          ▼
  Strings     Emails    Numbers     Dates      JSON       Files     Allowlisting
```

#### 1. Text & String Input Edge Cases
- **Whitespace-Only Strings**: Test inputs filled with spaces (`"   "`), tabs (`"\t"`), newlines (`"\n"`), or zero-width non-breaking spaces (`"\uFEFF"`, `"\u200B"`). Validator MUST trim whitespace and treat empty result as invalid for required fields.
- **Unicode Homoglyph Attacks**: Test visually identical characters from different alphabets (e.g. Cyrillic 'а' vs Latin 'a'). Applications MUST apply **Unicode Normalization (NFC / NFKC)** before string comparison/storage to prevent account spoofing or filter bypasses.
- **Control & Non-Printable Characters**: Input strings containing null bytes (`\0`), ANSI escape codes (`\x1b[31m`), or ASCII bell characters (`\x07`). Application MUST strip or reject non-printable control characters.
- **Extreme Length Boundaries**: Test string inputs at `min_length - 1` (too short), `max_length` (exact edge), `max_length + 1` (just over edge), and 10,000+ character stress payloads to prevent buffer overflows or truncated database writes.

#### 2. Email Address Validation Edge Cases
- **Subdomains, Tags & Special Characters**: Verify support for legitimate complex emails: `user+tag@domain.com`, `admin@sub.department.co.uk`, `user.name@domain.io`.
- **Case Normalization**: Verify domain parts are case-normalized (`ADMIN@DOMAIN.COM` $\rightarrow$ `admin@domain.com`) to prevent duplicate account creation via casing tricks.
- **Invalid Email Formats**: Reject missing `@`, consecutive dots (`user..name@domain.com`), leading/trailing dots (`.user@domain.com`), and trailing spaces.
- **OWASP Rule**: Avoid overly restrictive custom regexes that reject valid international emails. Use standard RFC 5322 validation libraries.

#### 3. Numeric, Currency & Floating-Point Precision Edge Cases
- **Floating-Point Precision Errors**: In financial, pricing, or telemetry calculations, test `0.1 + 0.2` rounding edge cases. System MUST use fixed-precision decimal types or integer representation (e.g. cents) to prevent precision drift (`0.30000000000000004`).
- **Negative & Zero Values**: Test `-1`, `-0.01`, and `0` in quantity, pricing, age, or pagination limit inputs. Ensure negative values are rejected where positive values are required.
- **Integer Boundary Overflow/Underflow**: Test 32-bit (`2,147,483,647`) and 64-bit (`9,223,372,036,854,775,807`) integer max boundaries + 1 to prevent integer overflow crashes.
- **Non-Numeric Character Coercion**: Test inputs containing scientific notation (`12e3`), `NaN`, `Null`, `Infinity`, or hexadecimal (`0x1A`) in numeric fields. Validator MUST reject invalid numeric coercion.

#### 4. Date, Time & Timezone Validation Edge Cases
- **Strict Format Enforcement**: Enforce standard ISO 8601 strings (`YYYY-MM-DD` / `YYYY-MM-DDTHH:mm:ssZ`). Reject ambiguous regional formats (`MM/DD/YYYY` vs `DD/MM/YYYY`).
- **Leap Year & Calendar Edge Cases**: Test invalid leap year dates (e.g. `2025-02-29` on a non-leap year) and out-of-bound dates (`2026-04-31`, `2026-13-01`).
- **Semantic Date Logic**: Test logic constraints: "Start Date" MUST be before "End Date", birthdate MUST NOT be in the future, event date MUST NOT be >100 years in the future.
- **Timezone Drift & DST Transitions**: Test date entries during Daylight Saving Time (DST) 23-hour and 25-hour transition days to prevent off-by-one day bugs when converting between client local time and server UTC.

#### 5. JSON Payload & API Schema Validation Edge Cases
- **Null vs Empty String vs Absent Field**: System MUST distinguish between `{"key": null}` (explicit null), `{"key": ""}` (empty string), and `{}` (absent key).
- **Unexpected Extra Fields (Mass Assignment Protection)**: Submit unexpected keys in request JSON (e.g. `{"name": "Alice", "isAdmin": true, "role": "owner"}`). Server schema validator (e.g. Zod, Joi, Valibot) MUST strip or reject unauthorized fields.
- **Type Coercion Mismatch**: Submit wrong data types for schema fields (e.g. passing a string `"true"` for boolean, or array `[1, 2]` for string). Validator MUST reject with a 400 Bad Request schema error.
- **Deeply Nested JSON (DoS Vector)**: Test JSON objects nested 50+ levels deep (`{"a":{"b":{"c":...}}}`). Parser MUST enforce max nesting depth limits to prevent stack overflow DoS.

#### 6. File Upload & Binary Payload Edge Cases
- **MIME-Type vs Extension Mismatch**: Test uploading a executable script renamed to `.png` (`script.php` renamed to `script.png`). Server MUST inspect magic byte headers (content sniffing), not just file extensions.
- **Double File Extensions**: Test files named `invoice.pdf.exe` or `avatar.png.php`.
- **Zero-Byte & Oversized Files**: Test 0-byte empty file uploads AND files exceeding maximum byte limits (>10MB).
- **Path Traversal Filenames**: Test uploading files with names containing path traversal (`../../../../etc/cron.d/malware.sh`). Filename MUST be sanitized to a clean safe basename before storage.

#### 7. Phone Number & International Format Edge Cases
- **International Prefixes**: Test international prefix formats (`+1-555-0199`, `+44 20 7946 0958`, `0033123456789`).
- **Non-Numeric Character Stripping**: Input containing spaces, hyphens, or parentheses `(555) 019-9999` MUST be normalized to standard E.164 numeric format (`+15550199999`) while preserving the leading `+`.

#### 8. OWASP Security Validation Rules
- **Allowlisting (Positive Validation) Over Denylisting**: Define explicit allowed character sets/regexes (e.g. `^[a-zA-Z0-9_-]+$`) rather than attempting to filter out "bad" characters. Denylists are easily bypassed with encoding tricks.
- **Early Client-Side UX + Independent Server-Side Security**: Client-side validation provides instant feedback to users; server-side validation strictly enforces constraints for all incoming API requests without exception.

---

## 6. Domain-Agnostic Production Lifecycle Phase Matrix

Every complete enterprise user journey MUST execute sequentially through these 6 lifecycle phases (adaptable to ANY application domain):

```
Phase 1: Initial Registration & Input Validation Guards
  ├── 1.1 Input Format & Constraint Validation Check
  ├── 1.2 Boundary Value & Weak Credential Check
  ├── 1.3 Security Specialist Payload Check (XSS/SQLi)
  └── 1.4 Valid Account & Resource Registration

Phase 2: Duplicate Prevention & Double-Tap Protection
  ├── 2.1 Rapid Double-Tap Submit -> verify button disables & single record created
  └── 2.2 Re-attempt registering exact same entity -> verify rejection & conflict alert

Phase 3: Authentication & Security Guards
  ├── 3.1 Invalid Password / Bad Credential Sign-In Attempt -> verify rejection alert
  ├── 3.2 Expired Token / Revoked Session Guard -> verify redirect to authentication
  └── 3.3 Valid Credential Authentication -> authenticate registered user

Phase 4: Primary Domain Workspace & Feature Actions
  ├── 4.1 Feature Navigation & Route Access Verification
  ├── 4.2 Primary Domain Pipeline / Search Query Execution
  └── 4.3 Data Table / Dataset View Check

Phase 5: Entity Administration & RBAC Permissions
  ├── 5.1 Navigate to Resource Administration / Settings Screen
  ├── 5.2 Invite Secondary Team Member / Provision Secondary Entity
  ├── 5.3 Cross-Tenant Authorization Guard Check (IDOR attempt on unowned resource) -> 403 Forbidden
  └── 5.4 Verify Secondary Entity Listing in Directory Table

Phase 6: Audit Logging & Clean Session Termination
  └── 6.1 Verify Security Audit Log Trail & Clean Session Termination
```

---

## 7. Anti-Patterns & Automatic Rejection Rules

| Anti-Pattern | Why It Is Banned | Mandatory Correct Requirement |
|---|---|---|
| Parallel execution of sequential specs | Causes state collision and flaky failures | ALWAYS enforce `--workers=1` / serial execution |
| Arbitrary fixed sleep timeouts (`sleep(5000)`) | Causes slow, flaky runs and timing bugs | Use state-based waits (`wait_until_visible`, `wait_for_network_idle`) |
| Raw CSS/XPath selectors in spec files | Breaks tests when DOM layout changes | ALL locators MUST live inside Page/Screen Objects |
| Trusting UI success toast without backend state check | UI toast can show success even if DB write fails | Re-verify state via secondary route or direct API check |
| Hardcoded static emails/usernames | Causes duplicate record conflicts on re-runs | Generate unique collision-free data dynamically |
| Searching for modal elements globally on page | Clicks wrong button outside active modal | Scope element search inside modal container (`role="dialog"`) |
| Un-scoped table button clicks | Clicks edit/delete on wrong table record row | Scope search inside specific table row (`filter(has_text=...)`) |
| Ignoring double-click / rapid-tap protection | Causes duplicate DB writes & order glitches | Test button double-tap and verify single API request |
| Skipping security payload checks in form inputs | Leaves XSS and injection vulnerabilities untested | Include security specialist payloads (XSS/SQLi) in inputs |
| Relying solely on client-side validation | API bypass can post invalid/malicious data | Enforce server-side validation on ALL incoming endpoints |
| Hardcoding domain page names in test policies | Prevents implementing tests for other domains | Use generic Page Object patterns extending `BasePage` |

---

## 8. Universal Page & Component Object Abstraction Rules

No raw element locator or low-level framework call (e.g. `page.locator()`, `driver.find_element()`) may appear directly inside a journey spec file or step definition. All UI locators and screen interactions MUST be encapsulated inside Page Objects / Screen Abstractions using a modular, domain-agnostic hierarchy.

### 8.1 Universal Page Object Architectural Blueprint

Every test automation suite MUST implement a two-tier Object-Oriented or Functional Screen Abstraction model:

```
                          UNIVERSAL PAGE OBJECT HIERARCHY
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
             BasePage / BaseScreen                    ComponentObjects / Widgets
        (Abstract Universal Base Class)          (Reusable Embedded UI Widgets)
                   │                                           │
  ┌────────────────┼────────────────┐                          │
  ▼                ▼                ▼                          ▼
AuthPages       AdminPages       CustomDomainPages    (DataTable, Combobox, Modal)
 (Registration,  (Settings,       (Catalog, Orders,
  Login, Reset)   Directory)       Workflows, Analytics)
```

#### Tier 1: Abstract Base Class (`BasePage` / `BaseScreen`)
The foundational abstract class inherited by every page object in the application. It encapsulates universal engine capabilities:
- **Navigation & URL Verification**: Base route navigation, relative URL assertions, and route transition checkpoints.
- **Global Toast & Dialog Handlers**: Methods to assert and handle alert popups (`role="alert"`), native browser dialogs, and toast notifications.
- **Console & Error Cleanliness**: Automatic assertions verifying no uncaught JS exceptions or 5xx network errors occurred.
- **Security & Payload Helpers**: Helper methods to inject XSS, SQLi, and unicode test strings into inputs and assert safe DOM rendering.
- **Wait Condition Facades**: Named state-based wait helpers (`wait_until_visible`, `wait_for_enabled`, `wait_for_network_idle`).

#### Tier 2: Extensible Feature Page Objects (`<Domain><Feature>Page`)
Domain-specific screen classes extending `BasePage`. EVERY screen, multi-step wizard step, or major view in ANY domain MUST have its own dedicated Page Object.

##### Generic Naming & Categorization Patterns Across Application Domains:
- **Authentication & Onboarding Domain**: `RegistrationPage`, `AuthenticationPage`, `PasswordResetPage`, `MfaVerificationPage`.
- **User & Organization Administration**: `OrganizationSettingsPage`, `UserDirectoryPage`, `RolePermissionPage`, `AuditLogsPage`.
- **Analytics & Data Dashboards**: `MetricsDashboardPage`, `TelemetryGridPage`, `ReportBuilderPage`, `LogViewerPage`.
- **E-Commerce & Financial Systems**: `ProductCatalogPage`, `CartCheckoutPage`, `PaymentGatewayPage`, `InvoiceHistoryPage`.
- **AI & Workflow Builder Systems**: `WorkflowCanvasPage`, `AgentExecutionPage`, `PromptTemplatePage`.
- **Healthcare & EHR Systems**: `PatientDirectoryPage`, `MedicalRecordPage`, `PrescriptionPage`.
- **SaaS File & Cloud Storage**: `DirectoryBrowserPage`, `FileUploaderPage`, `PermissionAccessPage`.

---

### 8.2 Component Objects for Reusable Complex UI Widgets

When a UI widget appears on multiple screens (e.g. dynamic data tables, search comboboxes, confirmation modals, notification toasts), do NOT duplicate locator code across Page Objects. Encapsulate the widget into a **Component Object** and embed it inside Page Objects.

```typescript
// Component Object Example: Encapsulates reusable ARIA Modal Widget across any domain
export class ModalComponent {
  constructor(private rootLocator: Locator) {}
  
  public get title() { return this.rootLocator.getByRole('heading'); }
  public get confirmButton() { return this.rootLocator.getByRole('button', { name: /confirm|submit|save/i }); }
  public get cancelButton() { return this.rootLocator.getByRole('button', { name: /cancel|close/i }); }
  
  public async confirm(): Promise<void> {
    await this.confirmButton.click();
    await expect(this.rootLocator).toBeHidden();
  }
}
```

---

### 8.3 Page Object Scoping & Design Rules

1. **One Page Object per Distinct View/Route**: If a route or wizard step has a distinct DOM structure or form fields, create a dedicated Page Object for it extending `BasePage`.
2. **Encapsulate Locators as Private/Protected Properties**: Spec files call high-level action methods (e.g. `page.submitRegistration(data)`), NEVER raw locator queries.
3. **Fluent State Transitions**: Methods that cause a screen transition MUST return the target Page Object or verify the target screen is ready before returning control.
4. **Zero Assertion-less Actions**: Action methods on Page Objects MUST include internal visibility/enabled state checks before attempting clicks or inputs.

---

## 9. State Preservation & Diagnostic Logging

When a multi-step sequential journey encounters a failure at Step $N$, the automation framework MUST preserve diagnostic state and identify the exact step failure.

### `JourneyContext` Responsibilities:
1. **State Preservation**: Carries `userId`, `userEmail`, `orgId`, `authToken`, and active transaction tokens across journey steps.
2. **Diagnostic Artifact Capture**: On step failure, automatically capture:
   - DOM Screenshot at exact moment of failure.
   - Network API Request/Response Log Trace.
   - Browser Console Error Log Dump.
   - Journey Step Identifier & Service Name.

---

## 10. Language-Agnostic Code Patterns & Generic Templates

Below are generic, framework-agnostic examples demonstrating how sequential user journeys and page objects MUST be written.

### 10.1 Gherkin BDD Feature Template (`sequential-user-flow.feature`)

```gherkin
@e2e @sequential-journey @critical
Feature: Production Enterprise User Sequential Journey

  Scenario: Full Enterprise User Lifecycle & Security Validation
    # Phase 1: Registration & Security Payload Checks
    Given the user navigates to the registration screen
    When the user attempts registration with XSS string "<script>alert(1)</script>" as name
    Then the input is safely sanitized and raw script execution is blocked
    When the user submits registration with a unique email and strong password
    Then registration succeeds and a new workspace is created

    # Phase 2: Duplicate & Double-Tap Protection
    When the user rapid double-taps the registration submit button
    Then the submit button immediately disables and exactly one account is created
    When the user re-attempts registration with the exact same email
    Then duplicate registration is rejected with an error alert

    # Phase 3: Authentication & Wrong Data Guards
    When the user attempts sign in with an incorrect password
    Then sign in is rejected with an invalid credentials error
    When the user signs in with valid credentials
    Then authentication succeeds and redirects to the main dashboard

    # Phase 4: Primary Feature Action
    When the user executes the primary domain search query "latency"
    Then the data table updates to display filtered records

    # Phase 5: Member Invite & RBAC
    When the user navigates to resource settings
    And invites team member "member@domain.io" with role "Member"
    Then the new member appears in the directory table

    # Phase 6: Logout & Clean Session
    When the user logs out of the workspace
    Then the session is cleanly terminated and redirected to sign-in
```

---

### 10.2 Page Object Pseudocode / Multi-Language Template

```typescript
// Extensible Feature Page Object Example (TypeScript / Playwright / Selenium compatible)
export class RegistrationPage extends BasePage {
  private get nameInput() { return this.page.getByLabel('Full Name'); }
  private get emailInput() { return this.page.getByLabel('Email Address'); }
  private get submitButton() { return this.page.getByRole('button', { name: 'Create Account' }); }

  public async testDoubleTapSubmit(accountData: any): Promise<void> {
    await this.nameInput.fill(accountData.name);
    await this.emailInput.fill(accountData.email);
    
    // Simulate rapid double tap
    await this.submitButton.dblclick();
    
    // Assert immediate button disable / busy loading state
    await expect(this.submitButton).toBeDisabled();
  }

  public async submitSecurityPayload(payload: string): Promise<void> {
    await this.nameInput.fill(payload);
    await this.submitButton.click();
    
    // Assert sanitized rendering in DOM (no script tags instantiated)
    const scriptElements = this.page.locator('script:has-text("alert")');
    await expect(scriptElements).toHaveCount(0);
  }
}
```

```python
# Extensible Feature Page Object Example (Python / PyTest / Selenium / Playwright)
class RegistrationPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.name_input = page.get_by_label("Full Name")
        self.email_input = page.get_by_label("Email Address")
        self.submit_button = page.get_by_role("button", name="Create Account")

    def test_double_tap_submit(self, account_data: dict) -> None:
        self.name_input.fill(account_data["name"])
        self.email_input.fill(account_data["email"])
        
        # Simulate rapid double tap
        self.submit_button.dblclick()
        
        # Assert immediate button disable state
        expect(self.submit_button).to_be_disabled()

    def submit_security_payload(self, payload: str) -> None:
        self.name_input.fill(payload)
        self.submit_button.click()
        
        # Assert safe rendering without script execution
        script_elements = self.page.locator("script:has-text('alert')")
        expect(script_elements).to_have_count(0)
```

---

## 11. Multi-Stack CLI Command Registry & Execution References

Depending on the underlying tech stack of your automation suite, sequential user journeys MUST be executed with single-worker, serial flags enabled.

### Multi-Language Command Reference:

| Stack / Engine | Command Syntax | Serial / Single-Worker Flags | Mode |
|---|---|---|---|
| **Node.js / Playwright** | `npm run test:e2e:sequential` | `--workers=1 --project=chromium` | Visual / Headed |
| **Node.js / Playwright** | `npm run test:e2e:sequential:headless` | `--workers=1` | Headless CI |
| **Python / PyTest** | `pytest tests/automation/e2e/runners/ --serial -n 0` | `-n 0` (Single-threaded) | Headless CI |
| **Java / Maven + JUnit** | `mvn test -Dtest=*JourneyTest -Dparallel=none` | `-Dparallel=none` | Headless CI |
| **Go / Rod / Chromedp** | `go test -v ./tests/automation/e2e/... -p 1` | `-p 1` (Single process) | Headless CI |
| **Cypress** | `npx cypress run --spec "tests/automation/e2e/**/*.journey.cy.ts"` | Cypress native serial spec runner | Headless CI |

---

### Command Execution Best Practices:
1. **Local Headed Debugging**: When writing or debugging a sequential journey locally, run in visual headed mode to visually observe element finding and modal transitions.
2. **CI Pipeline Execution**: In CI/CD pipelines, execute in headless mode with artifact capturing enabled (`--reporter=allure`, screenshots on failure).
3. **Non-Zero Exit Code**: Any step failure in a sequential journey MUST fail the CI pipeline build immediately with a non-zero exit code.
