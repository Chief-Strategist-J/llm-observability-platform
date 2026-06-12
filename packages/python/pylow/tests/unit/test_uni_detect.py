from pytrace_features.uni.detect import lang_from_extension, lang_from_markers, parse_issues


def test_lang_from_extension_known():
    assert lang_from_extension("main.go") == "go"
    assert lang_from_extension("lib.rs") == "rust"
    assert lang_from_extension("App.java") == "java"
    assert lang_from_extension("app.ts") == "ts"
    assert lang_from_extension("comp.tsx") == "ts"
    assert lang_from_extension("index.js") == "js"
    assert lang_from_extension("svc.py") == "python"


def test_lang_from_extension_unknown():
    assert lang_from_extension("notes.txt") is None
    assert lang_from_extension("Makefile") is None


def test_lang_from_markers_priority():
    assert lang_from_markers(["go.mod", "README.md"]) == "go"
    assert lang_from_markers(["Cargo.toml"]) == "rust"
    assert lang_from_markers(["pom.xml"]) == "java"
    assert lang_from_markers(["build.gradle.kts"]) == "java"
    # tsconfig wins over package.json for TS projects
    assert lang_from_markers(["package.json", "tsconfig.json"]) == "ts"
    assert lang_from_markers(["package.json"]) == "js"
    assert lang_from_markers(["pyproject.toml"]) == "python"
    assert lang_from_markers(["README.md"]) is None


def test_parse_issues_go():
    out = "main.go:12:5: undefined: fmt.Printlnn"
    assert parse_issues(out) == ["main.go:12  undefined: fmt.Printlnn"]


def test_parse_issues_javac():
    out = "App.java:8: error: cannot find symbol\n        symbol: variable foo"
    assert parse_issues(out) == ["App.java:8  cannot find symbol"]


def test_parse_issues_tsc():
    out = "src/app.ts(4,7): error TS2322: Type 'string' is not assignable to type 'number'."
    issues = parse_issues(out)
    assert len(issues) == 1
    assert issues[0].startswith("src/app.ts:4  TS2322:")


def test_parse_issues_rust_uses_context_line():
    out = "error[E0425]: cannot find value `foo` in this scope\n --> src/main.rs:3:13\n  |\n3 |     let x = foo;"
    issues = parse_issues(out)
    assert issues == ["src/main.rs:3  error[E0425]: cannot find value `foo` in this scope"]


def test_parse_issues_python_traceback():
    out = 'Traceback (most recent call last):\n  File "svc.py", line 9, in <module>\n    boom()\nNameError: name \'boom\' is not defined'
    issues = parse_issues(out)
    assert len(issues) == 1
    assert issues[0].startswith("svc.py:9")


def test_parse_issues_dedupes_and_empty():
    assert parse_issues("") == []
    out = "main.go:1:1: bad\nmain.go:1:1: bad"
    assert parse_issues(out) == ["main.go:1  bad"]
