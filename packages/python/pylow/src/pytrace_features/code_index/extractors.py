"""Pure symbol extraction for the code index (no IO — unit-testable).

Built-in fallback used when universal-ctags is not installed. One regex set
per language, all producing the same Symbol shape.
"""
import re
from dataclasses import dataclass

LANG_FOR_EXT = {
    ".py": "python", ".go": "go", ".rs": "rust", ".java": "java",
    ".ts": "ts", ".tsx": "ts", ".js": "js", ".jsx": "js", ".mjs": "js",
}

SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", "__pycache__",
             ".venv", "venv", "vendor", ".idea", ".pylow", ".egg-info"}


@dataclass
class Symbol:
    name: str
    kind: str
    line: int
    signature: str


_PATTERNS: dict[str, list[tuple[re.Pattern, str]]] = {
    "python": [
        (re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\("), "function"),
        (re.compile(r"^\s*class\s+(\w+)"), "class"),
    ],
    "go": [
        (re.compile(r"^func\s+\([^)]*\)\s*(\w+)\s*\("), "method"),
        (re.compile(r"^func\s+(\w+)\s*\("), "function"),
        (re.compile(r"^type\s+(\w+)\s+struct\b"), "struct"),
        (re.compile(r"^type\s+(\w+)\s+interface\b"), "interface"),
        (re.compile(r"^type\s+(\w+)\s+"), "type"),
    ],
    "rust": [
        (re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)"), "function"),
        (re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?struct\s+(\w+)"), "struct"),
        (re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?enum\s+(\w+)"), "enum"),
        (re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?trait\s+(\w+)"), "trait"),
        (re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:const|static)\s+(\w+)\s*:"), "const"),
    ],
    "java": [
        (re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*"
                    r"(?:class|interface|enum|record)\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:public|private|protected)[\w\s<>\[\],.?]*?\s(\w+)\s*\([^;]*\)\s*(?:throws[\w\s,.]+)?\{"), "method"),
    ],
    "ts": [
        (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)"), "function"),
        (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:export\s+)?interface\s+(\w+)"), "interface"),
        (re.compile(r"^\s*(?:export\s+)?type\s+(\w+)\s*="), "type"),
        (re.compile(r"^\s*(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(?[\w\s,{}:\[\]]*\)?\s*(?::[^=]+)?=>"), "function"),
        (re.compile(r"^\s*(?:export\s+)?enum\s+(\w+)"), "enum"),
    ],
}
_PATTERNS["js"] = _PATTERNS["ts"]


def lang_for_file(path: str) -> str | None:
    for ext, lang in LANG_FOR_EXT.items():
        if path.endswith(ext):
            return lang
    return None


def extract_symbols(source: str, lang: str) -> list[Symbol]:
    patterns = _PATTERNS.get(lang)
    if not patterns:
        return []
    symbols: list[Symbol] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        for pattern, kind in patterns:
            m = pattern.match(line)
            if m:
                symbols.append(Symbol(m.group(1), kind, lineno, line.strip()[:120]))
                break
    return symbols


def rank_matches(query: str, names: list[str]) -> list[int]:
    """Return indexes of names ordered: exact match > prefix > substring."""
    q = query.lower()
    scored = []
    for i, name in enumerate(names):
        n = name.lower()
        if n == q:
            scored.append((0, i))
        elif n.startswith(q):
            scored.append((1, i))
        elif q in n:
            scored.append((2, i))
    return [i for _, i in sorted(scored)]
