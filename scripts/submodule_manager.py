import os
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Callable, Sequence, Tuple

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

def checkout_branch(repo_path: Path, branch: str = "main") -> subprocess.CompletedProcess:
    execute_git(repo_path, "checkout", branch)
    return execute_git(repo_path, "pull", "--ff-only", "origin", branch)

def stage_and_commit(repo_path: Path, message: str) -> subprocess.CompletedProcess:
    execute_git(repo_path, "add", "-A")
    return execute_git(repo_path, "commit", "-m", message)

def push_repo(repo_path: Path) -> subprocess.CompletedProcess:
    branch = read_branch(repo_path)
    return execute_git(repo_path, "push", "origin", f"HEAD:{branch}")

def process_repo_push(repo_path: Path, message: str) -> Tuple[subprocess.CompletedProcess, ...]:
    actions = []
    if is_dirty(repo_path):
        actions.append(stage_and_commit(repo_path, message))
    actions.append(push_repo(repo_path))
    return tuple(actions)

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
    pull_root = execute_git(root, "pull", "--ff-only", "origin", "main")
    update_submodules = execute_git(
        root, "submodule", "update", "--init", "--recursive", "--remote", "--merge"
    )
    submodules = query_submodules(root)
    checkout_results = tuple(checkout_branch(path, "main") for path in submodules)
    return (pull_root, update_submodules) + checkout_results

def setup_repo(root: Path) -> Tuple[subprocess.CompletedProcess, ...]:
    init_update = execute_git(root, "submodule", "update", "--init", "--recursive")
    submodules = query_submodules(root)
    checkout_results = tuple(checkout_branch(path, "main") for path in submodules)
    return (init_update,) + checkout_results

def checkout_all(root: Path) -> Tuple[subprocess.CompletedProcess, ...]:
    submodules = query_submodules(root)
    return tuple(checkout_branch(path, "main") for path in submodules)

def build_dispatcher() -> dict[str, Callable[[Path, Sequence[str]], Tuple[subprocess.CompletedProcess, ...]]]:
    return {
        "sync": lambda root, args: sync_repo(root),
        "pull": lambda root, args: sync_repo(root),
        "push": lambda root, args: cascade_push(root, args[0] if args else "chore: update submodules"),
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
