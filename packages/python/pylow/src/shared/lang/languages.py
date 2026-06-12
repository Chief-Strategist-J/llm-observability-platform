"""All supported languages declared as data — THE single place to add one.

To support a new language, add one LanguageRegistry.register(LanguageSpec(...))
block here. No engine (uni, lang_trace, call_tree, step_debug) needs editing:
they interpret these specs through registries, never through if/elif chains.

Registration order = marker-detection priority (e.g. tsconfig.json beats
package.json because ts is registered before js).
"""
from shared.lang.registry import LanguageRegistry
from shared.lang.specs import (
    CallTreeBackend, DebuggerSpec, LanguageSpec, StageRule, TracerBackend,
)

LanguageRegistry.register(LanguageSpec(
    name="go",
    aliases=("golang",),
    extensions=(".go",),
    markers=("go.mod",),
    stages=(
        ("build", (
            StageRule(when=("is_dir",), argv=("go", "build", "{extra}", "./..."), cwd_is_target=True),
            StageRule(argv=("go", "build", "{extra}", "{target}")),
        )),
        ("run", (
            StageRule(when=("is_dir",), argv=("go", "run", "./...", "{args}"), cwd_is_target=True),
            StageRule(argv=("go", "run", "{target}", "{args}")),
        )),
        ("debug", (
            StageRule(when=("is_dir",), argv=("dlv", "debug"), cwd_is_target=True),
            StageRule(argv=("dlv", "debug", "{target}")),
        )),
    ),
    tracers=(
        TracerBackend("dlv", "dlv_trace_attach"),
        TracerBackend("perf", "perf_profile"),
        TracerBackend("strace", "strace_summary"),
        TracerBackend("", "simulated"),
    ),
    calltree=(
        CallTreeBackend("dlv", "dlv_calltree", mode="both"),
        CallTreeBackend("uftrace", "uftrace_tree", mode="launch"),
        CallTreeBackend("perf", "perf_tree", mode="both"),
        CallTreeBackend("", "unavailable"),
    ),
    debugger=DebuggerSpec(
        tools=("dlv",),
        argv=("{tool}", "debug", "{target}"),
        break_line="break {file}:{line}",
        break_func="break {func}",
        run="continue",
        locals_cmds=("args", "locals"),
        watch_cmd="print {expr}",
        cont="continue",
        quit="exit",
        hit_marker=r"> .*\.go:\d+",
        end_marker="has exited with status",
        interactive_style="init_file:--init",
    ),
    launch_cmd="go run {target}",
    error_patterns=(r"^(?P<file>[^\s:]+\.go):(?P<line>\d+)(?::\d+)?:\s*(?P<msg>.+)$",),
))

LanguageRegistry.register(LanguageSpec(
    name="rust",
    extensions=(".rs",),
    markers=("Cargo.toml",),
    stages=(
        ("build", (
            StageRule(when=("is_dir",), argv=("cargo", "build", "{extra}"), cwd_is_target=True),
            StageRule(when=("has:Cargo.toml",), argv=("cargo", "build", "{extra}")),
            StageRule(argv=("rustc", "{extra}", "{target}")),
        )),
        ("run", (
            StageRule(when=("is_dir",), argv=("cargo", "run", "--", "{args}"), cwd_is_target=True),
            StageRule(when=("has:Cargo.toml",), argv=("cargo", "run", "--", "{args}")),
            StageRule(strategy="rustc_then_exec"),
        )),
        ("debug", (
            StageRule(when=("tool:rust-gdb",), argv=("rust-gdb", "{target}")),
            StageRule(when=("tool:gdb",), argv=("gdb", "{target}")),
            StageRule(argv=("lldb", "{target}")),
        )),
    ),
    tracers=(
        TracerBackend("perf", "perf_profile"),
        TracerBackend("strace", "strace_summary"),
        TracerBackend("", "simulated"),
    ),
    calltree=(
        CallTreeBackend("uftrace", "uftrace_tree", mode="launch"),
        CallTreeBackend("perf", "perf_tree", mode="both"),
        CallTreeBackend("", "unavailable"),
    ),
    debugger=DebuggerSpec(
        tools=("rust-gdb", "gdb"),
        argv=("{tool}", "--nx", "-q", "{target}"),
        prelude=("set confirm off", "set pagination off"),
        break_line="break {file}:{line}",
        break_func="break {func}",
        run="run",
        locals_cmds=("info args", "info locals"),
        watch_cmd="print {expr}",
        cont="continue",
        quit="quit",
        hit_marker=r"Breakpoint \d+, ",
        end_marker="[Inferior 1 (process",
        interactive_style="flag:-ex",
        note="target must be a binary built with debug info (cargo build, not --release)",
    ),
    launch_cmd="cargo run",
    error_patterns=(r"^\s*-->\s*(?P<file>[^\s:]+\.rs):(?P<line>\d+):\d+",),
))

LanguageRegistry.register(LanguageSpec(
    name="java",
    aliases=("jvm",),
    extensions=(".java",),
    markers=("pom.xml", "build.gradle", "build.gradle.kts"),
    stages=(
        ("build", (
            StageRule(when=("is_dir", "has:pom.xml"), argv=("mvn", "-q", "compile", "{extra}"), cwd_is_target=True),
            StageRule(when=("is_dir", "has:build.gradle"), argv=("gradle", "compileJava", "{extra}"), cwd_is_target=True),
            StageRule(when=("is_dir", "has:build.gradle.kts"), argv=("gradle", "compileJava", "{extra}"), cwd_is_target=True),
            StageRule(argv=("javac", "{extra}", "{target}")),
        )),
        ("run", (
            StageRule(when=("is_dir",), argv=("java", "{target}", "{args}"), cwd_is_target=True),
            StageRule(argv=("java", "{target}", "{args}")),   # JEP 330 single-file launch
        )),
        ("debug", (
            StageRule(argv=("jdb", "{target_stem}")),
        )),
    ),
    tracers=(
        TracerBackend("jcmd", "jcmd_jfr"),
        TracerBackend("jstack", "jstack_dump"),
        TracerBackend("", "simulated"),
    ),
    calltree=(
        CallTreeBackend("jdb", "jdb_method_trace", mode="launch"),
        CallTreeBackend("jcmd", "jfr_delegate", mode="attach"),
        CallTreeBackend("", "unavailable"),
    ),
    debugger=DebuggerSpec(
        tools=("jdb",),
        argv=("{tool}", "{target_stem}"),
        break_line="stop at {file}:{line}",       # {file} = fully-qualified class name
        break_func="stop in {func}",
        run="run",
        locals_cmds=("locals",),
        watch_cmd="print {expr}",
        cont="cont",
        quit="quit",
        hit_marker=r"Breakpoint hit:",
        end_marker="The application exited",
        prepare=(StageRule(when=("ext:.java",), argv=("javac", "-g", "{target}")),),
        interactive_style="manual",
        note="breakpoints use class names (stop at Demo:12); compiled with javac -g automatically",
    ),
    launch_cmd="java {target}",
    error_patterns=(r"^(?P<file>[^\s:]+\.java):(?P<line>\d+):\s*error:\s*(?P<msg>.+)$",),
))

LanguageRegistry.register(LanguageSpec(
    name="ts",
    aliases=("typescript", "node"),
    extensions=(".ts", ".tsx"),
    markers=("tsconfig.json",),
    stages=(
        ("build", (
            StageRule(when=("is_dir",), argv=("tsc", "{extra}"), cwd_is_target=True),
            StageRule(argv=("tsc", "--noEmit", "{extra}", "{target}")),
        )),
        ("run", (
            StageRule(when=("tool:tsx",), argv=("tsx", "{target}", "{args}")),
            StageRule(when=("tool:ts-node",), argv=("ts-node", "{target}", "{args}")),
            StageRule(strategy="tsc_then_node", note="tsx/ts-node not found — compiling with tsc then running node"),
        )),
        ("debug", (
            StageRule(when=("tool:ts-node",), argv=("node", "inspect", "--require", "ts-node/register", "{target}")),
            StageRule(argv=("node", "inspect", "{target}")),
        )),
    ),
    tracers=(
        TracerBackend("", "node_attach"),
    ),
    calltree=(
        CallTreeBackend("node", "node_cpuprofile", mode="launch"),
        CallTreeBackend("", "unavailable"),
    ),
    debugger=DebuggerSpec(
        tools=("node",),
        argv=("{tool}", "inspect", "{target}"),
        break_line="setBreakpoint('{file}', {line})",
        run="cont",
        locals_cmds=("list(2)",),
        watch_cmd="exec('{expr}')",
        cont="cont",
        quit=".exit",
        hit_marker=r"break in ",
        end_marker="Waiting for the debugger to disconnect",
        skip_initial_stop=True,
        interactive_style="manual",
        note="node inspect cannot dump all locals — pass --watch expressions to capture values",
    ),
    launch_cmd="node {target}",
    error_patterns=(r"^(?P<file>[^\s(]+\.[cm]?tsx?)\((?P<line>\d+),\d+\):\s*error\s*(?P<msg>TS\d+:.+)$",),
))

LanguageRegistry.register(LanguageSpec(
    name="js",
    aliases=("javascript",),
    extensions=(".js", ".jsx", ".mjs"),
    markers=("package.json",),
    stages=(
        ("build", (
            StageRule(when=("is_file",), argv=("node", "--check", "{target}"),
                      note="(no compile step for JavaScript — running a syntax check)"),
            StageRule(strategy="noop"),
        )),
        ("run", (
            StageRule(argv=("node", "{target}", "{args}")),
        )),
        ("debug", (
            StageRule(argv=("node", "inspect", "{target}")),
        )),
    ),
    trace_as="ts",
    launch_cmd="node {target}",
    error_patterns=(r"^(?P<file>[^\s:]+\.[cm]?jsx?):(?P<line>\d+)$",),
))

LanguageRegistry.register(LanguageSpec(
    name="python",
    aliases=("py",),
    extensions=(".py",),
    markers=("pyproject.toml", "setup.py"),
    stages=(
        ("build", (
            StageRule(when=("is_dir",), argv=("python3", "-m", "compileall", "-q", "{target}")),
            StageRule(argv=("python3", "-m", "py_compile", "{target}")),
        )),
        ("run", (
            StageRule(argv=("python3", "{target}", "{args}")),
        )),
        ("debug", (
            StageRule(argv=("python3", "-m", "pdb", "{target}")),
        )),
    ),
    calltree=(
        CallTreeBackend("python3", "python_settrace", mode="launch"),
        CallTreeBackend("", "unavailable"),
    ),
    debugger=DebuggerSpec(
        tools=("python3",),
        argv=("{tool}", "-m", "pdb", "{target}"),
        break_line="break {file}:{line}",
        break_func="break {func}",
        run="continue",
        locals_cmds=("args", "p {k: v for k, v in list(locals().items()) if not k.startswith('_')}"),
        watch_cmd="p {expr}",
        cont="continue",
        quit="quit",
        hit_marker=r"> [^\s(]+\(\d+\)\S*\(\)",
        end_marker="The program finished and will be restarted",
        skip_initial_stop=True,
        interactive_style="flag:-c",
    ),
    launch_cmd="python3 {target}",
    error_patterns=(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+)',),
))
