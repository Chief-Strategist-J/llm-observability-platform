from unittest.mock import patch

from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import (
    LanguageRegistry, PredicateRegistry, StageContext, format_argv,
)
from shared.lang.specs import LanguageSpec, StageRule


def test_every_supported_language_is_registered():
    assert {"go", "rust", "java", "ts", "js", "python"} <= set(LanguageRegistry.names())


def test_alias_resolution():
    assert LanguageRegistry.get("golang").name == "go"
    assert LanguageRegistry.get("typescript").name == "ts"
    assert LanguageRegistry.get("PYTHON").name == "python"
    assert LanguageRegistry.get("cobol") is None


def test_extension_detection():
    assert LanguageRegistry.lang_for_extension("a/b/main.go") == "go"
    assert LanguageRegistry.lang_for_extension("x.tsx") == "ts"
    assert LanguageRegistry.lang_for_extension("notes.txt") is None


def test_marker_detection_priority():
    # ts (tsconfig) beats js (package.json) because ts registers first
    assert LanguageRegistry.lang_for_markers(["package.json", "tsconfig.json"]) == "ts"
    assert LanguageRegistry.lang_for_markers(["package.json"]) == "js"
    assert LanguageRegistry.lang_for_markers(["go.mod", "README.md"]) == "go"
    assert LanguageRegistry.lang_for_markers(["README.md"]) is None


def test_stage_rule_resolution_first_passing_rule_wins():
    spec = LanguageRegistry.get("go")
    dir_rule = LanguageRegistry.resolve_stage(spec, "build", StageContext("proj", is_dir=True))
    file_rule = LanguageRegistry.resolve_stage(spec, "build", StageContext("main.go", is_dir=False))
    assert dir_rule.cwd_is_target and "./..." in dir_rule.argv
    assert "{target}" in file_rule.argv


def test_tool_predicate():
    with patch("shared.lang.registry.shutil.which", side_effect=lambda t: t == "tsx" or None):
        assert PredicateRegistry.passes(("tool:tsx",), StageContext()) is True
        assert PredicateRegistry.passes(("tool:ts-node",), StageContext()) is False


def test_ext_predicate():
    assert PredicateRegistry.passes(("ext:.java",), StageContext(target="Demo.java"))
    assert not PredicateRegistry.passes(("ext:.java",), StageContext(target="Demo"))


def test_unknown_predicate_never_passes():
    assert PredicateRegistry.passes(("no-such-predicate",), StageContext()) is False


def test_format_argv_substitutes_and_splices():
    argv = format_argv(("go", "build", "{extra}", "{target}"),
                       {"extra": ["-v"], "target": "main.go"})
    assert argv == ["go", "build", "-v", "main.go"]
    # empty expansions drop out entirely
    assert format_argv(("go", "build", "{extra}", "{target}"),
                       {"extra": [], "target": "main.go"}) == ["go", "build", "main.go"]


def test_new_language_needs_only_a_registry_entry():
    spec = LanguageSpec(
        name="zig-test", extensions=(".zigtest",),
        stages=(("build", (StageRule(argv=("zig", "build-exe", "{target}")),)),),
    )
    LanguageRegistry.register(spec)
    try:
        assert LanguageRegistry.lang_for_extension("m.zigtest") == "zig-test"
        rule = LanguageRegistry.resolve_stage(spec, "build", StageContext("m.zigtest"))
        assert format_argv(rule.argv, {"target": "m.zigtest"}) == ["zig", "build-exe", "m.zigtest"]
    finally:
        LanguageRegistry._specs.pop("zig-test", None)
        LanguageRegistry._extensions.pop(".zigtest", None)


def test_every_language_declares_debug_essentials():
    for name in ("python", "go", "rust", "java", "ts"):
        debugger = LanguageRegistry.get(name).debugger
        assert debugger is not None, name
        assert debugger.tools and debugger.argv and debugger.hit_marker, name
        assert debugger.cont and debugger.quit, name
