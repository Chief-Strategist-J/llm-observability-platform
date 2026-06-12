"""Pure detection + error-normalization logic for uni (no IO — unit-testable)."""
import os
import re

EXT_LANG = {
    ".py": "python", ".go": "go", ".rs": "rust", ".java": "java",
    ".ts": "ts", ".tsx": "ts", ".js": "js", ".jsx": "js", ".mjs": "js",
}

# project marker file → language, first match wins
MARKERS = [
    ("go.mod", "go"), ("Cargo.toml", "rust"), ("pom.xml", "java"),
    ("build.gradle", "java"), ("build.gradle.kts", "java"),
    ("tsconfig.json", "ts"), ("package.json", "js"),
    ("pyproject.toml", "python"), ("setup.py", "python"),
]

# one regex per compiler/runtime error format → unified (file, line, message)
ERROR_PATTERNS = [
    re.compile(r"^(?P<file>[^\s:]+\.go):(?P<line>\d+)(?::\d+)?:\s*(?P<msg>.+)$"),          # go build
    re.compile(r"^\s*-->\s*(?P<file>[^\s:]+\.rs):(?P<line>\d+):\d+"),                       # rustc/cargo
    re.compile(r"^(?P<file>[^\s:]+\.java):(?P<line>\d+):\s*error:\s*(?P<msg>.+)$"),         # javac
    re.compile(r"^(?P<file>[^\s(]+\.[cm]?tsx?)\((?P<line>\d+),\d+\):\s*error\s*(?P<msg>TS\d+:.+)$"),  # tsc
    re.compile(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+)'),                          # python traceback
]


def lang_from_extension(path: str) -> str | None:
    return EXT_LANG.get(os.path.splitext(path)[1].lower())


def lang_from_markers(present_files: list[str]) -> str | None:
    names = set(present_files)
    for marker, lang in MARKERS:
        if marker in names:
            return lang
    return None


def _context_message(lines: list[str], idx: int) -> str:
    # rustc/python point at file:line on one line with the message on a neighbour
    for ctx in (lines[idx - 1] if idx else "", lines[idx + 1] if idx + 1 < len(lines) else ""):
        stripped = ctx.strip()
        if stripped and "-->" not in stripped and not stripped.startswith("|"):
            return stripped
    return ""


def parse_issues(output: str) -> list[str]:
    """Collapse any compiler/runtime output into a unified file:line issue list."""
    issues: list[str] = []
    lines = output.splitlines()
    for i, line in enumerate(lines):
        for pat in ERROR_PATTERNS:
            m = pat.match(line)
            if not m:
                continue
            msg = (m.groupdict().get("msg") or "").strip() or _context_message(lines, i)
            issues.append(f"{m.group('file')}:{m.group('line')}  {msg}")
            break
    return list(dict.fromkeys(issues))
