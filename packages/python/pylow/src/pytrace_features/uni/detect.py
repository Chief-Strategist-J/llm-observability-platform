"""Pure detection + error-normalization logic for uni (no IO — unit-testable).

Detection data and error formats live in the shared LanguageRegistry
(shared/lang/languages.py); this module only exposes pure lookups over it.
"""
import re

from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import LanguageRegistry

MARKERS = tuple(
    (marker, spec.name)
    for spec in (LanguageRegistry.get(n) for n in LanguageRegistry.names())
    for marker in spec.markers
)

ERROR_PATTERNS = tuple(
    re.compile(pattern)
    for spec in (LanguageRegistry.get(n) for n in LanguageRegistry.names())
    for pattern in spec.error_patterns
)


def lang_from_extension(path: str) -> str | None:
    return LanguageRegistry.lang_for_extension(path)


def lang_from_markers(present_files: list) -> str | None:
    return LanguageRegistry.lang_for_markers(present_files)


def _context_message(lines: list, idx: int) -> str:
    # rustc/python point at file:line on one line with the message on a neighbour
    for ctx in (lines[idx - 1] if idx else "", lines[idx + 1] if idx + 1 < len(lines) else ""):
        stripped = ctx.strip()
        if stripped and "-->" not in stripped and not stripped.startswith("|"):
            return stripped
    return ""


def parse_issues(output: str) -> list:
    """Collapse any compiler/runtime output into a unified file:line issue list."""
    issues: list = []
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
