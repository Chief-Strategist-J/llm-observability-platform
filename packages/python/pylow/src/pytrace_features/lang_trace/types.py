from dataclasses import dataclass

SUPPORTED_LANGS = ("go", "rust", "java", "ts")

LANG_ALIASES = {
    "golang": "go",
    "typescript": "ts",
    "node": "ts",
    "js": "ts",
    "javascript": "ts",
}


@dataclass
class LangTraceRequest:
    """Input DTO for a multi-language trace run."""
    lang: str
    pid: int = 0
    duration: float = 10.0
    func_regex: str | None = None
    cmd: str | None = None  # launch this command under a tracer instead of attaching

    def normalized_lang(self) -> str:
        lang = self.lang.lower()
        return LANG_ALIASES.get(lang, lang)
