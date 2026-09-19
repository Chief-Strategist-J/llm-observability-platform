"""
SELF_DEVELOPMENT_SPECIFICATION_AND_LLM_PROMPT:

SYSTEM ROLE:
You are an autonomous senior systems architect and software engineer maintaining and extending this Git submodule orchestration engine.

ARCHITECTURE INVARIANTS:
1. PURE FUNCTIONAL PARADIGM:
   - Functions must be pure, deterministic, and composable.
   - Use immutable data structures (Tuple, Path, Mapping).
   - No mutable global state, no class instances with state, no side effects outside designated execution boundaries.

2. CODE STYLE RESTRICTIONS:
   - DO NOT USE HASH COMMENTS ANYWHERE IN THIS FILE.
   - DO NOT USE PRINT STATEMENTS ANYWHERE IN THIS FILE.
   - Return status codes, CompletedProcess instances, or structured immutable tuples.

3. ARCHITECTURAL PRINCIPLES:
   - SINGLE RESPONSIBILITY: Each function must perform exactly one atomic task.
   - DRY (DON'T REPEAT YOURSELF): All system process executions MUST route exclusively through execute_git.
   - HIERARCHICAL RECURSION: Submodules are multi-level (Level 0 Root -> Level 1 Packages -> Level 2 Services).
   - BOTTOM-UP ORDER FOR COMMITS: All cascades MUST traverse in depth-descending order (deepest leaves first, then parents, then root).
   - TOP-DOWN ORDER FOR SYNC: Remote pulls and submodules updates initialize downwards.
   - ATOMIC CONFLICT PREVENTION: Every push or pull operation on any repository MUST execute the stash-rebase-pop lifecycle (stash_push -> pull_rebase -> stash_pop) to avoid non-fast-forward push rejections and protect uncommitted work.

BACKWARD COMPATIBILITY CONTRACT:
1. COMMAND SIGNATURE PRESERVATION:
   - "sync" and "pull": Rebase root, update recursive submodules, safe-pull all submodules.
   - "push [message]": Bottom-up cascade push with auto-stash, rebase, and commit.
   - "push-module <module> [message] [files...]": Targeted push with selective file staging and upward ancestor cascade.
   - "checkout": Switch all recursive submodules to main branch.
   - "setup": Recursive initialization and branch checkout.
2. DISPATCHER INTERFACE:
   - Dispatch table must always map string command identifiers to Callables taking (root: Path, args: Sequence[str]) and returning Tuple[CompletedProcess, ...].
   - main() must return integer exit code 0 on all returncode == 0, else 1.

EXTENSION INSTRUCTIONS FOR FUTURE LLMs:
When encountering an edge case or new requirement that cannot be handled by the current implementation:
1. Identify the atomic responsibility needed and create a new pure function for it.
2. Adhere strictly to the zero-comment, zero-print, and DRY rules.
3. Integrate the new capability additively without altering existing command signatures or breaking callers.
4. Update this prompt string to document the newly supported feature, invariant, or edge-case resolution.

HUMAN-IN-THE-LOOP AND DECISION ESCALATION MANDATE:
When facing special requirements, ambiguous situations, non-trivial edge cases, or tasks where multiple valid implementation paths or architectural trade-offs exist:
1. STRICT PROHIBITION OF ASSUMPTIONS:
   - Never assume user intent, repository policies, or destructive actions.
   - Do not unilaterally write or execute code when architectural trade-offs exist (such as conflict resolution strategies, force-pushing, discarding stashes, shallow vs full depth cloning, or branch divergence policies).
2. INTERACTIVE HUMAN CONSULTATION:
   - The agent MUST halt and present clear, structured choices with explicit trade-offs and risks to the human user.
   - The agent MUST wait for explicit human guidance and approval before generating or executing the corresponding code.

RESEARCH AND VERIFICATION GUARDRAILS:
Before generating code, making modifications, or adopting architectural decisions:
1. ZERO UNVERIFIED ASSUMPTIONS:
   - Never assume tool flags, Git behaviors, API contracts, or system dependencies without factual verification.
   - Prior to writing code, verify requirements, library behaviors, and command options against official documentation and authoritative technical sources.
   - Cross check with internet with latest information to respective date not old data
2. EVIDENCE-BASED IMPLEMENTATION:
   - Every implementation step must be grounded in verified, accurate data aligned with repository standards.
   - Never write speculative or exploratory code without first consulting verified documentation.
"""

import os
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

def execute_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )

def resolve_root() -> Path:
    return Path(__file__).resolve().parent.parent

def query_submodules(root: Path) -> Tuple[Path, ...]:
    result = execute_git(root, "submodule", "foreach", "--recursive", "--quiet", "pwd")
    paths = tuple(
        Path(line.strip())
        for line in result.stdout.splitlines()
        if line.strip()
    )
    return paths

def sort_by_depth_descending(paths: Sequence[Path]) -> Tuple[Path, ...]:
    return tuple(sorted(paths, key=lambda p: len(p.parts), reverse=True))

def sort_by_depth_ascending(paths: Sequence[Path]) -> Tuple[Path, ...]:
    return tuple(sorted(paths, key=lambda p: len(p.parts), reverse=False))

def is_dirty(repo_path: Path) -> bool:
    status = execute_git(repo_path, "status", "--porcelain")
    return bool(status.stdout.strip())

def read_branch(repo_path: Path) -> str:
    branch = execute_git(repo_path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    return "main" if branch == "HEAD" or not branch else branch

def stash_push(repo_path: Path) -> subprocess.CompletedProcess:
    return execute_git(repo_path, "stash", "push", "-u", "-m", "submodule-manager-autostash")

def stash_pop(repo_path: Path) -> subprocess.CompletedProcess:
    return execute_git(repo_path, "stash", "pop")

def pull_rebase(repo_path: Path, branch: str) -> subprocess.CompletedProcess:
    return execute_git(repo_path, "pull", "--rebase", "origin", branch)

def safe_pull_repo(repo_path: Path) -> Tuple[subprocess.CompletedProcess, ...]:
    branch = read_branch(repo_path)
    if is_dirty(repo_path):
        push_res = stash_push(repo_path)
        pull_res = pull_rebase(repo_path, branch)
        pop_res = stash_pop(repo_path)
        return (push_res, pull_res, pop_res)
    return (pull_rebase(repo_path, branch),)

def checkout_branch(repo_path: Path, branch: str = "main") -> subprocess.CompletedProcess:
    execute_git(repo_path, "checkout", branch)
    return execute_git(repo_path, "pull", "--ff-only", "origin", branch)

def stage_files(repo_path: Path, files: Sequence[str]) -> subprocess.CompletedProcess:
    return execute_git(repo_path, "add", *files) if files else execute_git(repo_path, "add", "-A")

def stage_and_commit(repo_path: Path, message: str, files: Sequence[str] = ()) -> subprocess.CompletedProcess:
    stage_files(repo_path, files)
    return execute_git(repo_path, "commit", "-m", message)

def push_repo(repo_path: Path) -> subprocess.CompletedProcess:
    branch = read_branch(repo_path)
    return execute_git(repo_path, "push", "origin", f"HEAD:{branch}")

def process_repo_push(repo_path: Path, message: str, files: Sequence[str] = ()) -> Tuple[subprocess.CompletedProcess, ...]:
    pull_actions = safe_pull_repo(repo_path)
    commit_actions = []
    if is_dirty(repo_path):
        commit_actions.append(stage_and_commit(repo_path, message, files))
    push_actions = [push_repo(repo_path)]
    return pull_actions + tuple(commit_actions) + tuple(push_actions)

def locate_module(submodules: Sequence[Path], root: Path, identifier: str) -> Optional[Path]:
    normalized_id = identifier.strip().rstrip("/")
    for path in submodules:
        rel_str = str(path.relative_to(root))
        if path.name == normalized_id or rel_str == normalized_id or rel_str.endswith(f"/{normalized_id}"):
            return path
    return None

def collect_ancestor_repos(root: Path, target: Path) -> Tuple[Path, ...]:
    ancestors = []
    current = target.parent
    while current != root and current != current.parent:
        if (current / ".git").exists():
            ancestors.append(current)
        current = current.parent
    ancestors.append(root)
    return tuple(ancestors)

def cascade_ancestors_push(ancestors: Sequence[Path], message: str) -> Tuple[subprocess.CompletedProcess, ...]:
    return tuple(
        action
        for repo in ancestors
        for action in process_repo_push(repo, message)
    )

def targeted_module_push(root: Path, target_id: str, message: str, files: Sequence[str]) -> Tuple[subprocess.CompletedProcess, ...]:
    submodules = query_submodules(root)
    target = locate_module(submodules, root, target_id)
    if not target:
        return (subprocess.CompletedProcess(args=(), returncode=1, stderr=f"Unknown module: {target_id}"),)
    target_results = process_repo_push(target, message, files)
    ancestors = collect_ancestor_repos(root, target)
    ancestor_results = cascade_ancestors_push(ancestors, message)
    return target_results + ancestor_results

def cascade_push(root: Path, message: str) -> Tuple[subprocess.CompletedProcess, ...]:
    submodules = sort_by_depth_descending(query_submodules(root))
    submodule_results = tuple(
        action
        for path in submodules
        for action in process_repo_push(path, message)
    )
    root_results = process_repo_push(root, message)
    return submodule_results + root_results

def sync_repo(root: Path) -> Tuple[subprocess.CompletedProcess, ...]:
    pull_root = safe_pull_repo(root)
    update_submodules = (
        execute_git(root, "submodule", "update", "--init", "--recursive", "--remote", "--merge"),
    )
    submodules = query_submodules(root)
    submodule_pulls = tuple(
        action
        for path in submodules
        for action in (execute_git(path, "checkout", "main"),) + safe_pull_repo(path)
    )
    return pull_root + update_submodules + submodule_pulls

def setup_repo(root: Path) -> Tuple[subprocess.CompletedProcess, ...]:
    init_update = execute_git(root, "submodule", "update", "--init", "--recursive")
    submodules = query_submodules(root)
    checkout_results = tuple(checkout_branch(path, "main") for path in submodules)
    return (init_update,) + checkout_results

def checkout_all(root: Path) -> Tuple[subprocess.CompletedProcess, ...]:
    submodules = query_submodules(root)
    return tuple(checkout_branch(path, "main") for path in submodules)

def handle_push_module(root: Path, args: Sequence[str]) -> Tuple[subprocess.CompletedProcess, ...]:
    if not args:
        return (subprocess.CompletedProcess(args=(), returncode=1, stderr="Module name required"),)
    target_id = args[0]
    message = args[1] if len(args) > 1 else f"chore({target_id}): update module"
    files = args[2:] if len(args) > 2 else ()
    return targeted_module_push(root, target_id, message, files)

def build_dispatcher() -> dict[str, Callable[[Path, Sequence[str]], Tuple[subprocess.CompletedProcess, ...]]]:
    return {
        "sync": lambda root, args: sync_repo(root),
        "pull": lambda root, args: sync_repo(root),
        "push": lambda root, args: cascade_push(root, args[0] if args else "chore: update submodules"),
        "push-module": lambda root, args: handle_push_module(root, args),
        "checkout": lambda root, args: checkout_all(root),
        "setup": lambda root, args: setup_repo(root),
    }

def run_action(command: str, root: Path, args: Sequence[str]) -> int:
    dispatcher = build_dispatcher()
    handler = dispatcher.get(command)
    if not handler:
        return 1
    results = handler(root, args)
    return 0 if all(r.returncode == 0 for r in results) else 1

def main() -> int:
    args = sys.argv[1:]
    command = args[0] if args else "sync"
    extra_args = args[1:]
    root = resolve_root()
    return run_action(command, root, extra_args)

if __name__ == "__main__":
    sys.exit(main())
