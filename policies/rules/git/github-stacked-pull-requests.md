# GitHub Stacked Pull Requests — Complete Reference
### `gh stack` CLI · REST · Async Merge API · Webhooks · GraphQL
### Public Preview — shipped 30 Jul 2026

> Requires `gh` CLI ≥ 2.90.0 and Git ≥ 2.20. Everything below is pulled from GitHub's live docs and the `gh-stack` extension's own reference site — not from training memory, since this shipped after most models' cutoffs.

---

## Table of Contents

1. [Mental model + ASCII diagrams](#1-mental-model--ascii-diagrams)
2. [Install](#2-install)
3. [CLI — every command, in depth](#3-cli--every-command-in-depth)
4. [REST API](#4-rest-api)
5. [Async Merge API](#5-async-merge-api)
6. [Webhooks](#6-webhooks)
7. [GraphQL API](#7-graphql-api)
8. [End-to-end workflows](#8-end-to-end-workflows)
9. [Strictly unavoidable rules](#9-strictly-unavoidable-rules)
10. [Decision tree](#10-decision-tree)
11. [Troubleshooting map](#11-troubleshooting-map)

---

## 1. Mental Model + ASCII Diagrams

### 1.1 Basic anatomy

A stack is an ordered chain of branches/PRs in **one repository**. Every PR targets the branch immediately below it — not `main` — except the bottom one.

```
                     ┌─────────────────────────────┐
  layer 3 (top)      │ PR #52  feat/frontend        │  base → feat/api-endpoints
                     └──────────────┬──────────────┘
                                    │ depends on
                     ┌──────────────┴──────────────┐
  layer 2            │ PR #51  feat/api-endpoints   │  base → feat/auth-layer
                     └──────────────┬──────────────┘
                                    │ depends on
                     ┌──────────────┴──────────────┐
  layer 1 (bottom)   │ PR #50  feat/auth-layer      │  base → main
                     └──────────────┬──────────────┘
                                    │
                              ══════╧══════
                                  main                 ← trunk
```

`stack.position` is 1-based from the bottom: layer 1 = position 1, layer 2 = position 2, layer 3 = position 3. `up` in the CLI always means "away from trunk, toward position N+1." `down` means the opposite.

### 1.2 Dependency rule, drawn out

```
   ALLOWED                              FORBIDDEN
   ───────                              ─────────
   layer 2 code uses                    layer 1 code uses
   a type defined in layer 1            a function defined in layer 2

   ┌──────────┐                         ┌──────────┐
   │ layer 2  │ ──uses──┐               │ layer 1  │◄───uses────┐
   └──────────┘         │               └──────────┘            │
   ┌──────────┐         │               ┌──────────┐            │
   │ layer 1  │◄────────┘               │ layer 2  │────────────┘
   └──────────┘                         └──────────┘
        │                                     │
      main                                  main
                                     ✗ breaks the stack: a lower
                                       layer can never reach up
                                       into a higher one
```

### 1.3 Partial merge — what actually happens on disk

Merging is bottom-up. Merging a mid-stack PR takes everything below it with it; everything above it survives and auto-retargets.

```
BEFORE merging PR #51                AFTER merging PR #51
                                      (PR #50 and #51 both land)

  PR #52 → base: feat/api-endpoints    PR #52 → base: main   ← auto-retargeted
  PR #51 → base: feat/auth-layer       PR #51 → MERGED
  PR #50 → base: main                  PR #50 → MERGED
      │                                    │
    main                                 main  (now contains #50 + #51's commits)
```

The next unmerged PR is rebased automatically to sit directly on the stack's base — it effectively becomes the new bottom.

### 1.4 Diverged stack (what `gh stack sync` has to reconcile)

```
   LOCAL (yours)              REMOTE (GitHub)
   ──────────────             ────────────────
   layer 3: docs              layer 3: frontend    ← different PR added
   layer 2: api               layer 2: api         ← common ancestor
   layer 1: auth               layer 1: auth        ← common ancestor
       │                           │
      main                       main

   Neither is a prefix of the other above layer 2 → TRUE DIVERGENCE
   gh stack sync cannot auto-merge this; you choose:
   remote-as-truth | delete remote stack | cancel
```

A **clean** remote-ahead case (remote has your stack plus new PRs stacked on top, nothing local-only) is not divergence — `sync` pulls it down automatically, no prompt.

### 1.5 Merge queue grouping

```
Stack of 5 PRs entering a queue with max group size = 4

   merge group 1        merge group 2
  ┌───┬───┬───┬───┐    ┌───┐
  │P1 │P2 │P3 │P4 │    │P5 │
  └───┴───┴───┴───┘    └───┘
   ▲ queue allowed to grow this group by
     up to 50% (→ 6) to try to fit all 5
     in one group; here it still didn't
     fit, so P5 spills into group 2
```

If a PR anywhere in the queued stack gets ejected (failed check, manual removal), every PR **above** it in the stack is ejected too — group boundaries don't protect against this.

---

## 2. Install

```bash
gh extension install github/gh-stack          # the CLI extension itself
gh skill install github/gh-stack               # matching skill for Copilot / coding agents
gh auth login                                  # if not already authenticated
gh stack alias                                 # optional: installs `gs` as a short alias
```

Reuses your existing `gh` auth — no separate credential step.

---

## 3. CLI — Every Command, In Depth

### 3.1 Stack management

#### `gh stack init [flags] [branches...]`

Sets up local tracking for a stack. No args → interactive prompt (offers current branch as layer one). Named branches: existing ones are adopted as-is, missing ones are created fresh. Trunk = repo default branch unless overridden.

**Side effect:** turns on `git rerere` for the whole repo the first time you run it, so resolved conflicts get remembered and auto-replayed on future rebases of the same conflict.

| Flag | Meaning |
|---|---|
| `-b, --base <branch>` | trunk branch for this stack (default: repo's default branch) |

```bash
gh stack init                                      # interactive
gh stack init feature-auth                         # one branch, explicit
gh stack init --base develop feature-auth           # non-standard trunk
gh stack init feature-auth feature-api feature-ui   # adopt/create 3 layers at once
```

#### `gh stack add [flags] [branch]`

Cuts a new branch at current HEAD, stacks it on top, checks it out. **Must be run from the current top of the stack** — you can't insert mid-stack this way (use `modify` for that). Optionally commits staged/unstaged work in the same call.

| Flag | Meaning |
|---|---|
| `-A, --all` | stage everything, tracked + untracked (requires `-m`) |
| `-u, --update` | stage tracked files only (requires `-m`) |
| `-m, --message <s>` | commit with this message before branching |

`-A`/`-u` are mutually exclusive. `-m` with no branch name → auto-generated name in `MM-DD-slug` format.

```bash
gh stack add api-routes
gh stack add -Am "Add login endpoint"                 # stage all + commit + auto-name
gh stack add -um "Fix auth bug"                        # tracked-only + commit + auto-name
gh stack add -Am "Add tests" test-layer                # explicit branch name
gh stack add -m "Add user model"                        # commit already-staged changes
```

#### `gh stack view [flags]`

```bash
gh stack view              # full detail, piped through pager ($GIT_PAGER/$PAGER, default less -R)
gh stack view --short      # branch names only
gh stack view --json       # machine-readable, for scripting/dashboards
```

#### `gh stack checkout [<stack#> | <pr#> | <pr-url> | <branch>]`

A bare number resolves as a stack/PR number first, falls back to branch name if nothing matches. Targeting a remote-only stack clones it locally. If local/remote compositions differ, you're prompted to reconcile (same logic as `sync`'s divergence handling). No args → interactive picker with **All/Local/Remote** tabs, `/` to filter, fully-merged stacks hidden.

```bash
gh stack checkout 7                                                    # by stack number
gh stack checkout 42                                                   # by PR number
gh stack checkout https://github.com/owner/repo/pull/42                # by PR URL
gh stack checkout feature-auth                                         # by branch (local only)
gh stack checkout                                                      # interactive picker
```

#### `gh stack modify [flags]`

Full-screen interactive editor — the canonical way to reorder, split, fold, insert, drop, or rename layers after creation.

**Preconditions (checked before it will even open):**
1. active stack checked out
2. clean working tree
3. no rebase in progress
4. no PR in the stack queued to merge
5. linear history, no merge commits, no diverged branches

**Key bindings (all staged, nothing applies until `Ctrl+S`):**

| Key | Operation | Effect |
|---|---|---|
| `x` | Drop | remove branch+commits from the stack; branch and its PR are kept, just detached |
| `d` | Fold down | absorb this branch's commits into the one below, toward trunk |
| `u` | Fold up | absorb into the branch above, away from trunk |
| `i` | Insert below | new empty branch under the cursor, toward trunk |
| `I` | Insert above | new empty branch above the cursor, away from trunk |
| `Shift+↓` | Move down | reorder toward trunk |
| `Shift+↑` | Move up | reorder away from trunk |
| `r` | Rename | inline prompt |
| `z` | Undo | undo last staged op |
| `Ctrl+S` | Apply | runs the cascading rebase that realizes everything staged |

On conflict during apply: resolve → `git add` → `gh stack modify --continue`, or bail entirely with `gh stack modify --abort` (restores the pre-modify snapshot).

If the stack was already submitted, run `gh stack submit` again afterward — it pushes the new shape and transparently replaces the old stack on GitHub.

```bash
gh stack modify
gh stack modify --continue
gh stack modify --abort
```

#### `gh stack unstack [<stack#>] [flags]` — alias `gh stack delete`

No args → operates on whatever stack the checked-out branch belongs to. With a stack number, it's a pure remote/API call — works regardless of local checkout state. Merged, merging, or merge-queued PRs are **never removed**; if only those remain, the stack dissolves and local tracking clears, otherwise the stack persists with its remaining PRs.

| Flag | Meaning |
|---|---|
| `--local` | only drop local tracking, leave the stack on GitHub untouched |

```bash
gh stack unstack
gh stack unstack 7
gh stack unstack --local
```

### 3.2 Remote operations

#### `gh stack submit [flags]`

Pushes every branch, opens PRs for the ones without one, links them into a stack on GitHub. If the current stack is already fully merged, `submit` transparently starts a **new** stack off trunk for your remaining branches — the merged stack is left alone.

Interactive: a two-pane editor. Left pane lists unopened branches, all pre-selected; deselecting one cascades and deselects everything above it that depends on it (re-selecting re-includes what it depends on below). Branches with existing PRs show as locked read-only cards (`o` opens in browser). Right pane: title/description editor for whichever branch has focus, pre-filled from your PR template, with `$EDITOR` escape and markdown preview.

| Flag | Meaning |
|---|---|
| `--auto` | skip the editor, use auto-generated titles (implied in CI/non-interactive contexts) |
| `--open` | new PRs open ready-for-review instead of draft; also flips already-open PRs to ready |
| `--remote <name>` | override auto-detected git remote |

Default new-PR state: ready-for-review in the interactive editor; **draft** with `--auto` unless `--open` is also passed.

```bash
gh stack submit
gh stack submit --auto
gh stack submit --open
gh stack submit --auto --open --remote upstream
```

#### `gh stack sync [flags]`

One call, eight steps, run in order:

```
1. fetch origin
2. reconcile remote stack (pull down clean remote-ahead additions automatically;
   prompt on true divergence in interactive terminals, abort silently otherwise)
3. fast-forward trunk (skipped if diverged)
4. cascading rebase — only if trunk moved
5. push (force-with-lease if step 4 rebased anything)
6. sync PR state from GitHub, report status per PR
7. link open PRs into a stack object on GitHub (creates it if missing; never opens new PRs)
8. prune merged local branches (prompt interactively, or automatic with --prune)
```

| Flag | Meaning |
|---|---|
| `--remote <name>` | override remote for fetch+push |
| `--prune` | auto-delete local branches whose PR merged |

```bash
gh stack sync
gh stack sync --prune
```

⚠️ **In a non-interactive terminal, a true divergence aborts silently** — exit 0, nothing pushed, nothing updated. Don't wire this into CI assuming a clean exit means it actually synced.

#### `gh stack rebase [flags] [branch]`

Cascading rebase, trunk upward: fetches, then ensures every branch has the tip of the branch below it in its history. If a branch's PR already merged, that layer auto-switches to `--onto` semantics so commits replay correctly on top of the real merge target instead of a stale local ref.

| Flag | Meaning |
|---|---|
| `--downstack` | only rebase trunk → current branch |
| `--upstack` | only rebase current branch → top |
| `--no-trunk` | skip fetch + trunk rebase; only re-stack branches on each other |
| `--continue` | resume after resolving a conflict |
| `--abort` | restore every branch to its pre-rebase state |
| `--remote <name>` | override remote |
| `--committer-date-is-author-date` (alias `--preserve-dates`) | keep original authored timestamps on the committer field |

```bash
gh stack rebase
gh stack rebase --downstack
gh stack rebase --upstack
gh stack rebase --no-trunk
gh stack rebase --continue
gh stack rebase --abort
gh stack rebase --committer-date-is-author-date
```

#### `gh stack push [flags]`

Pushes every active (non-merged, non-queued) branch in one `git push`, with a **per-branch** `--force-with-lease` check. **Not atomic** — a lease rejection on one branch doesn't roll back branches that already succeeded; re-run after fixing the rejected one. Doesn't touch PR objects at all — that's what `submit` is for.

```bash
gh stack push
gh stack push --remote upstream
```

#### `gh stack link [flags] <stack# | branch-or-pr> <branch-or-pr> [...]`

For people driving branches with a different local tool (Jujutsu, Sapling, git-town) who still want native GitHub stacking. Creates **zero** local tracking state — pure GitHub-side operation. Args are bottom-to-top; unpushed branches get pushed first; branches without a PR get one created with correct base chaining; PRs with a wrong base get corrected automatically. Purely additive — never drops existing PRs from a stack.

Pass a **stack number** as the first arg to grow an existing stack without re-listing what's already in it.

| Flag | Meaning |
|---|---|
| `--base <branch>` | trunk override (ignored when appending to an existing stack) |
| `--open` | mark new + existing PRs ready-for-review |
| `--remote <name>` | override remote |

```bash
gh stack link feature-auth feature-api feature-ui                       # branches → new stack
gh stack link 10 20 30                                                  # existing PR numbers
gh stack link https://github.com/o/r/pull/10 https://github.com/o/r/pull/20
gh stack link 42 43 feature-auth                                        # mixed PRs + branch
gh stack link 7 48 feature-ui                                           # append to stack #7
gh stack link --base develop --open feat-a feat-b feat-c
```

#### `gh stack merge [<stack#> | <pr#>]`

Merges bottom-up, up to and including the target, as **one atomic operation** — all lands or none does. No arg = active local stack. Stack number = pure remote op on a stack you don't have checked out. PR number = merge up through that layer specifically.

Only shape (open, not draft) is pre-checked client-side; branch protection and rulesets are evaluated live by GitHub when the merge actually runs.

| Flag | Meaning |
|---|---|
| `--merge-method <m>` | `merge` \| `squash` \| `rebase` |
| `--merge` / `--squash` / `--rebase` | shorthand equivalents |
| `-y, --yes` | skip confirmation |

If the base branch requires a merge queue, the whole selection is queued instead of merged directly — the queue picks the method, so method flags are ignored (with a warning), and PRs may land across separate queue groups rather than simultaneously (see §1.5).

```bash
gh stack merge
gh stack merge 7
gh stack merge 42
gh stack merge --yes --squash
gh stack merge 42 --merge-method rebase
```

### 3.3 Navigation

All clamp at stack bounds — moving past either end is a no-op with a message, not an error.

```bash
gh stack switch      # interactive picker, top→bottom with position numbers
gh stack up [n]        # default n=1, away from trunk (higher position)
gh stack down [n]      # default n=1, toward trunk (lower position)
gh stack top          # jump straight to the topmost branch
gh stack bottom       # jump straight to the bottommost branch
gh stack trunk        # jump to the stack's trunk (e.g. main)
```

Example `switch` picker output:
```
Select a branch in the stack to switch to
  5. frontend
  4. api-endpoints
  3. auth-layer
  2. db-schema
  1. config-setup
```

### 3.4 Utilities

```bash
gh stack alias              # installs `gs` wrapper into ~/.local/bin (manual steps printed on Windows)
gh stack alias gst          # custom alias name
gh stack alias --remove
gh stack alias --remove gst
gh stack feedback
gh stack feedback "Support for reordering branches"    # opens a discussion in github/gh-stack
```

### 3.5 Environment variables

| Variable | Values | Purpose |
|---|---|---|
| `GH_STACK_THEME` | `auto` (default) / `light` / `dark` | forces the color palette for `submit`/`modify`/`view` TUIs when your terminal doesn't report its background (common over SSH/tmux) |

```bash
GH_STACK_THEME=light gh stack view
```

### 3.6 Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | generic error |
| 2 | not in a stack / stack not found |
| 3 | rebase conflict |
| 4 | GitHub API failure |
| 5 | invalid arguments/flags |
| 6 | branch belongs to multiple stacks — disambiguation required |
| 7 | rebase already in progress |
| 8 | stack locked by another process |
| 9 | stacked PRs not enabled for this repository |
| 10 | interrupted `modify` session — recovery required (`--abort`) |

---

## 4. REST API

### 4.1 `stack` object on pull request resources

Every PR returned by any pull-request-returning REST endpoint (`GET /repos/{owner}/{repo}/pulls`, `GET /repos/{owner}/{repo}/pulls/{pull_number}`, etc.) carries a `stack` object when it belongs to one. `null` for standalone PRs.

```bash
gh api /repos/OWNER/REPO/pulls/42 --jq '.stack'
```

```json
{
  "id": 123456,
  "number": 50,
  "size": 5,
  "position": 2,
  "base": { "ref": "main", "sha": "def456..." }
}
```

| Field | Type | Meaning |
|---|---|---|
| `stack.id` | integer | global stack identifier |
| `stack.number` | integer | repo-scoped stack number (matches the number shown in the UI) |
| `stack.size` | integer | total PRs in the stack |
| `stack.position` | integer | 1-based position, bottom = 1 |
| `stack.base.ref` | string | the branch the **whole stack** ultimately targets |
| `stack.base.sha` | string | HEAD SHA of that branch |

Important distinction: the PR's own `base.ref` is its **direct** parent (the branch below it), while `stack.base.ref` is the stack's **ultimate** target. These only match for the bottom PR.

### 4.2 Stacks API

Addressed by **stack number** (repo-scoped, same value as `stack.number`). Returns `404` if stacked PRs aren't enabled for the repo.

#### List stacks
```bash
GET /repos/{owner}/{repo}/stacks
```
| Param | In | Type | Meaning |
|---|---|---|---|
| `pull_request` | query | integer | filter to the stack containing this PR number |
| `per_page` | query | integer | max 100 |
| `page` | query | integer | pagination |

```bash
gh api repos/OWNER/REPO/stacks
gh api "repos/OWNER/REPO/stacks?pull_request=102"
```

#### Get a stack
```bash
GET /repos/{owner}/{repo}/stacks/{stack_number}
```
```bash
gh api repos/OWNER/REPO/stacks/42
```

#### Create a stack
```bash
POST /repos/{owner}/{repo}/stacks
```
Chains an ordered list of **existing** PR numbers, bottom → top. Each PR's base must match the previous PR's head — GitHub validates the chain, doesn't build it for you.

| Body field | Type | Meaning |
|---|---|---|
| `pull_requests` | array[integer] | bottom-to-top order, min 2, max 100 |

```bash
echo '{"pull_requests": [101, 102, 103]}' | \
  gh api --method POST repos/OWNER/REPO/stacks --input -
```

#### Add PRs to a stack
```bash
POST /repos/{owner}/{repo}/stacks/{stack_number}/add
```
Appends onto the **top** only — provide just the delta, and the first new PR's base must match the current top PR's head.

| Body field | Type | Meaning |
|---|---|---|
| `pull_requests` | array[integer] | new layers, current-top → upward, min 1, max 100 |

```bash
echo '{"pull_requests": [104]}' | \
  gh api --method POST repos/OWNER/REPO/stacks/42/add --input -
```

#### Unstack
```bash
POST /repos/{owner}/{repo}/stacks/{stack_number}/unstack
```
No body. Removes unmerged PRs from the stack; merged/merging/queued PRs are left in place. `200` + updated stack if anything remains; `204 No Content` if the stack fully dissolves.

```bash
gh api --method POST repos/OWNER/REPO/stacks/42/unstack
```

#### Stack resource shape

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | global identifier |
| `number` | integer | repo-scoped number, used to address it |
| `node_id` | string | GraphQL global node ID |
| `url` | string | API URL |
| `base.ref` | string | the branch the stack targets |
| `open` | boolean | `false` once every PR is merged or closed |
| `created_at` | string | ISO 8601 |
| `pull_requests` | array | bottom-to-top, each `{number, state, draft, merged_at, head.ref, head.sha}` |

---

## 5. Async Merge API

Stacked PRs **cannot** use the legacy synchronous merge endpoint or the `mergePullRequest` GraphQL mutation — a stack merge is atomic and can take a few minutes, so it's submit-then-poll.

### 5.1 Submit
```bash
PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge-async
```
Merges the target PR and everything below it. All body fields optional.

| Body field | Type | Meaning |
|---|---|---|
| `merge_method` | string | `merge` \| `squash` \| `rebase` (default: merge commit); ignored on `merge_queue` actions |
| `merge_action` | string | `default` (recommended — auto-picks direct merge or queue as required) \| `direct_merge` \| `merge_queue` |
| `commit_title` | string | ignored on `merge_queue` actions |
| `commit_message` | string | appended detail; ignored on `merge_queue` actions |
| `sha` | string | required head SHA — merge rejected if it doesn't match, protects against racing pushes |

```bash
echo '{"merge_method": "squash", "merge_action": "default"}' | \
  gh api --method PUT repos/OWNER/REPO/pulls/102/merge-async --input -
```

| HTTP | Meaning | body `status` |
|---|---|---|
| `202 Accepted` | accepted, running in background | `pending` (includes `uuid` to poll) |
| `200 OK` | was already merged | `merged` |
| `409 Conflict` | a merge request already exists for this PR (returns its existing `uuid`) | `pending` |
| `400 Bad Request` | not mergeable — closed or draft | `failed` |
| `404 Not Found` | async merge unavailable, or PR not found | — |
| `422 Unprocessable Entity` | invalid `merge_method`/`merge_action` | — |

```json
// 202 Accepted
{
  "status": "pending",
  "details": {
    "message": "Merge request enqueued.",
    "uuid": "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42",
    "merge_method": "squash",
    "merge_action": "default",
    "expected_head_sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e"
  }
}
```

### 5.2 Poll for result
```bash
GET /repos/{owner}/{repo}/pulls/{pull_number}/merge-async/{uuid}
```
Always `200 OK` for a valid `uuid`; check `status`. Poll roughly once a second. Result is retained **24 hours** after last update — after that, `404` on that `uuid`.

```bash
gh api repos/OWNER/REPO/pulls/102/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42
```

| `status` | Meaning |
|---|---|
| `pending` | still running — keep polling |
| `merged` | landed directly; `details.sha` = resulting merge commit |
| `enqueued` | added to the merge queue — this is terminal for the *merge request*; track the queue separately for the real outcome |
| `failed` | could not complete (conflict, unmet rule); `details.message` explains why; atomic, so nothing merged |

### 5.3 Hard limitations of this endpoint

- **No bypass.** Admin privileges cannot skip branch protection or rulesets for a stack merge — every PR in it must independently satisfy requirements.
- **No auto-merge.** A stacked PR cannot be set to merge automatically once checks pass — you must explicitly call this endpoint (or use `gh stack merge` / the UI button) each time.

---

## 6. Webhooks

### 6.1 `stack` object nested in `pull_request` payloads

Present on every `pull_request` lifecycle event (`opened`, `synchronize`, `closed`, etc.) whenever the PR belongs to a stack; `null` otherwise.

```json
{
  "action": "synchronize",
  "pull_request": {
    "number": 42,
    "title": "Add API routes",
    "base": { "ref": "feat/auth-layer", "sha": "abc123..." },
    "stack": {
      "id": 123456,
      "number": 50,
      "size": 5,
      "position": 2,
      "base": { "ref": "main", "sha": "def456..." }
    }
  }
}
```

Same field semantics as the REST `stack` object (§4.1) — `pull_request.base.ref` is the direct parent, `pull_request.stack.base.ref` is the stack's ultimate target.

### 6.2 The `stacked` action

Fires specifically when a PR **joins** a stack (since the PR exists before it's stacked, this is the event to catch that exact moment). Uniquely among `pull_request` actions, it carries the stack **twice** — once at the top level, once nested — both identical, read whichever's convenient.

```json
{
  "action": "stacked",
  "number": 42,
  "stack": { "id": 123456, "number": 50, "size": 5, "position": 2,
             "base": { "ref": "main", "sha": "def456..." } },
  "pull_request": {
    "number": 42, "title": "Add API routes",
    "base": { "ref": "feat/auth-layer", "sha": "abc123..." },
    "stack": { "id": 123456, "number": 50, "size": 5, "position": 2,
               "base": { "ref": "main", "sha": "def456..." } }
  }
}
```

### 6.3 GitHub Actions integration

Workflows trigger off the stack's **base** branch automatically — a workflow set to run on PRs targeting `main` runs for every layer of any stack targeting `main`, with zero config changes. Stack metadata is available inside workflow expressions via `github.event.pull_request.stack`.

---

## 7. GraphQL API

Read-only. There are **no stack mutations** in GraphQL — creating/modifying a stack is REST-only (§4.2). The `PullRequest` type exposes two relevant fields: `stack` and `stackEntry`, mirroring the REST/webhook shape (id, number, size, position, base ref/sha).

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        number
        title
        stackEntry {
          position
        }
        stack {
          number
          size
          base {
            ref
          }
        }
      }
    }
  }
' -F owner=OWNER -F repo=REPO -F number=42
```

Use this for read-heavy dashboards/bots where you're already on GraphQL for other PR data — anything that needs to *change* stack composition still has to drop down to REST.

---

## 8. End-to-End Workflows

### 8.1 First stack, start to merge

```bash
gh extension install github/gh-stack
gh stack init                                   # layer 1
# ...code...
gh stack add -Am "Add DB schema" db-schema       # layer 2
# ...code...
gh stack add -Am "Add API routes" api-routes     # layer 3
gh stack submit                                  # push, open PRs, link stack
# ...reviews happen...
gh stack merge --yes --squash                    # land the whole stack, bottom-up
```

### 8.2 Grow an existing stack later

```bash
gh stack checkout <stack#>          # or `gh stack switch` then `gh stack top`
gh stack add -Am "Add frontend" frontend
gh stack submit
```

### 8.3 Keep in sync with upstream `main`

```bash
gh stack sync                       # fetch, reconcile, rebase, push, prune (prompted)
gh stack sync --prune               # same, auto-delete merged local branches
```

### 8.4 Fix a bug in a lower layer without breaking the ones above it

```bash
gh stack down N                     # or gh stack checkout <lower-branch>
# fix, commit
gh stack rebase --upstack           # propagate the fix upward through dependents
gh stack push
gh stack switch                     # jump back to where you were working
```

### 8.5 Restructure a submitted stack (drop/insert/reorder)

```bash
gh stack modify                     # x/d/u/i/I/Shift+↑/Shift+↓/r as needed, Ctrl+S to apply
gh stack submit                     # re-push + re-link the new shape
```

### 8.6 CI bot merging via API instead of CLI

```bash
UUID=$(echo '{"merge_action":"default"}' | \
  gh api --method PUT repos/OWNER/REPO/pulls/102/merge-async --input - --jq '.details.uuid')

# poll until status != pending
while true; do
  STATUS=$(gh api repos/OWNER/REPO/pulls/102/merge-async/$UUID --jq '.status')
  [ "$STATUS" != "pending" ] && break
  sleep 1
done
echo "final status: $STATUS"
```

### 8.7 Adopting stacks without the local `gh stack` tracking model (e.g. from `jj`)

```bash
gh stack link feature-auth feature-api feature-ui
# or, to extend later without re-listing what's already stacked:
gh stack link 7 feature-payments
```

---

## 9. Strictly Unavoidable Rules

🔴 CRITICAL = corrupts your workflow silently or hard-blocks merges · 🟠 HIGH = explicit hard error · 🟡 MEDIUM = behavioral gotcha, not a hard stop.

### Tier 1 — Structural (no override exists)

| # | Rule | Sev |
|---|---|---|
| 1 | All branches must live in **one repository** — no cross-fork stacks, no flag around it. | 🔴 |
| 2 | Dependency direction is one-way only: a lower layer can never reach into a higher one. | 🔴 |
| 3 | Merges are **bottom-up only** — never merge a PR while one below it in the chain is still open. | 🔴 |
| 4 | A PR merges only when it **and everything below it** pass required reviews/checks, and history is linear. | 🔴 |
| 5 | GitHub Desktop has zero stacked-PR support. | 🟠 |
| 6 | `gh stack modify` refuses to open unless all 5 preconditions hold (§3.1) — no partial bypass. | 🟠 |
| 7 | Admin privileges cannot bypass branch protection for a stack merge via CLI, UI, or API. | 🔴 |

### Tier 2 — Merge-time behavior

| # | Rule | Sev |
|---|---|---|
| 8 | Every PR's merge requirements are inherited from the **bottom** PR's base branch — CODEOWNERS/protection applies to mid-stack PRs too. | 🔴 |
| 9 | Default-branch CI triggers fire for **every** layer, not just the bottom PR. | 🟠 |
| 10 | `gh stack merge` / `merge-async` is atomic for the selected range: partial failure = nothing merges. | 🔴 |
| 11 | If a queued/interactive merge does fail partway (race, flake), already-merged lower PRs stay merged; retry lands the rest. | 🟡 |
| 12 | One PR ejected from the merge queue ejects **every PR above it**. | 🔴 |
| 13 | A merge group may exceed its configured max size by up to 50% to keep a stack together; oversized stacks still split across groups. | 🟡 |
| 14 | Programmatic merges of a stack **must** use `PUT .../merge-async` — the legacy synchronous merge endpoint and the `mergePullRequest` GraphQL mutation both reject stacks. | 🔴 |
| 15 | **Auto-merge is unsupported for stacked PRs**, in the UI, CLI, and API alike — plan an explicit merge step. | 🟠 |
| 16 | Closing a mid-stack PR blocks everything above it from merging; recovery requires unstacking + rebuilding, not just reopening. | 🔴 |

### Tier 3 — History & signing

| # | Rule | Sev |
|---|---|---|
| 17 | Server-side (PR-UI-triggered) rebases produce **unsigned** commits. Signed-commit repos must rebase via `gh stack rebase` locally, then `gh stack push`. | 🔴 |
| 18 | `gh stack push` is **not atomic** across branches — a rejected lease on one branch doesn't roll back others already pushed. | 🟠 |
| 19 | `gh stack init` silently enables `git rerere` repo-wide on first run. | 🟡 |

### Tier 4 — Divergence & sync

| # | Rule | Sev |
|---|---|---|
| 20 | `gh stack sync` in a non-interactive terminal **silently aborts** on true divergence — exit 0, nothing pushed. Don't trust green CI as proof of a real sync. | 🔴 |
| 21 | True divergence requires an explicit choice (remote-as-truth / delete remote stack / cancel) — never auto-resolved. | 🟠 |
| 22 | An interrupted `gh stack modify` session is recoverable **only** via `gh stack modify --abort` (cached pre-modify snapshot) — no other recovery path exists. | 🟠 |

### Tier 5 — API/webhook specifics

| # | Rule | Sev |
|---|---|---|
| 23 | GraphQL is **read-only** for stacks — all creation/mutation goes through REST. | 🔴 |
| 24 | Merge-async results expire after **24 hours** — poll promptly or you'll get a `404` on a valid-looking `uuid`. | 🟡 |
| 25 | The Stacks API's `create`/`add` endpoints validate the PR chain (`base` must match the previous PR's `head`) but don't construct it for you — malformed chains are rejected, not auto-fixed. | 🟠 |
| 26 | Stacks API endpoints 404 outright if stacked PRs aren't enabled on the repo — don't confuse this with "stack not found." | 🟡 |

### Tier 6 — Workflow discipline (unenforced by tooling, but load-bearing)

| # | Rule | Sev |
|---|---|---|
| 27 | Never hand-edit a stacked PR's base branch on the GitHub web UI outside the stack tooling — it desyncs local tracking from GitHub's stack object until the next `sync` catches it. | 🟡 |
| 28 | Fix bugs in the layer they belong to and cascade the rebase upward (`--upstack`) — patching forward in the top branch defeats the entire "each layer independently reviewable" premise. | 🟡 |
| 29 | Don't rely on auto-merge anywhere in a stacked workflow — it's unsupported end-to-end (rule 15); build an explicit merge step into your process/bots. | 🟠 |

---

## 10. Decision Tree

```
Starting fresh work?
├─ First branch in a brand-new stack ───────────► gh stack init
├─ Adding the next unit on top of an open stack ─► gh stack add -Am "..."
└─ Wiring branches made by another tool
   (jj / Sapling / git-town) ────────────────────► gh stack link

Need to inspect state?
├─ Full detail, human-readable ─────────────────► gh stack view
├─ Quick branch list ────────────────────────────► gh stack view --short
├─ Scripting / dashboards ───────────────────────► gh stack view --json
├─ REST, PR-scoped ───────────────────────────────► GET /pulls/{n} → .stack
├─ REST, stack-scoped ────────────────────────────► GET /repos/{o}/{r}/stacks/{num}
└─ GraphQL (read-heavy bot/dashboard) ───────────► pullRequest.stack / .stackEntry

Need to move around locally?
├─ Know the exact target ────────────────────────► gh stack checkout <target>
├─ Don't remember the name ──────────────────────► gh stack switch
└─ Just N steps up/down ─────────────────────────► gh stack up|down [n]

Upstream moved, or teammates added PRs?
└─ gh stack sync   (--prune to also clean merged branches)

Just want branches re-lined-up, no fetch/push?
├─ Whole stack ───────────────────────────────────► gh stack rebase
├─ Only below current ────────────────────────────► gh stack rebase --downstack
├─ Only above current ────────────────────────────► gh stack rebase --upstack
└─ No trunk involvement ──────────────────────────► gh stack rebase --no-trunk

Ready to open/update PRs?
└─ gh stack submit   (--auto for CI, --open for ready-for-review)

Need to reshape (drop/fold/insert/reorder/rename)?
└─ gh stack modify   → then gh stack submit if already pushed

Ready to land?
├─ Interactively, whole stack ────────────────────► gh stack merge
├─ A stack you don't have checked out ────────────► gh stack merge <stack#>
├─ Up to a specific layer ────────────────────────► gh stack merge <pr#>
└─ Programmatically / from a bot ─────────────────► PUT .../merge-async → poll
```

---

## 11. Troubleshooting Map

| Symptom | Fix |
|---|---|
| Rebase conflict | resolve markers → `git add .` → `gh stack rebase --continue` (or `--abort`) |
| `sync` aborted on conflict | `gh stack rebase` directly, then `gh stack push` |
| `modify` won't open | check the 5 preconditions in §3.1 |
| `modify` interrupted | `gh stack modify --abort`, or resolve + `--continue` |
| PR won't merge despite green checks | history isn't linear — `gh stack rebase` then `gh stack push`, or click "Rebase stack" in the merge box |
| Merge stalled mid-stack | fix the failed PR, retry — lower merged PRs are unaffected |
| PR ejected from merge queue | everything above it was ejected too — re-queue the whole remainder once fixed |
| Closed a mid-stack PR by mistake | unstack (web UI or `gh stack modify`) and rebuild — merged/queued PRs survive, open/draft/closed ones drop |
| Commits unsigned after rebase | you rebased server-side; use `gh stack rebase` locally instead, then push |
| Tried a cross-fork stack | not supported — consolidate into one repo |
| `merge-async` returns 404 on a known `uuid` | result expired past the 24-hour retention window — you missed the poll |
| Stacks API returns 404 unexpectedly | stacked PRs likely aren't enabled on that repo, not a missing-stack error |
| `create`/`add` on Stacks API rejects your PR list | chain validation failed — each PR's `base` must exactly match the previous PR's `head` |

---

*Compiled from GitHub's official docs and the `gh-stack` extension's own reference site (public preview, retrieved Aug 2026). Preview features change before GA — recheck `docs.github.com/en/pull-requests` and `github.github.com/gh-stack` before wiring this into permanent team process docs.*