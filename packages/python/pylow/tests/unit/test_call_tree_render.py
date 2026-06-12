from pytrace_features.call_tree.render import indent_jdb_trace, parse_cpuprofile

CPUPROFILE = {
    "nodes": [
        {"id": 1, "callFrame": {"functionName": "(root)", "url": ""}, "children": [2]},
        {"id": 2, "callFrame": {"functionName": "main", "url": "file:///app/src/main.ts",
                                "lineNumber": 9}, "hitCount": 3, "children": [3, 4]},
        {"id": 3, "callFrame": {"functionName": "internalNoise", "url": "node:internal/timers",
                                "lineNumber": 1}, "children": [5]},
        {"id": 4, "callFrame": {"functionName": "vendored", "url": "file:///app/node_modules/lib/x.js",
                                "lineNumber": 5}, "children": []},
        {"id": 5, "callFrame": {"functionName": "processOrder", "url": "file:///app/src/orders.ts",
                                "lineNumber": 41}, "hitCount": 7, "children": []},
    ]
}


def test_parse_cpuprofile_filters_noise_and_keeps_file_line():
    lines = parse_cpuprofile(CPUPROFILE)
    assert lines == [
        "└─ main  /app/src/main.ts:10  [3 samples]",
        "  └─ processOrder  /app/src/orders.ts:42  [7 samples]",
    ]


def test_parse_cpuprofile_promotes_children_of_dropped_frames():
    # processOrder is a child of dropped node:internal frame yet appears one level under main
    lines = parse_cpuprofile(CPUPROFILE)
    assert lines[1].startswith("  └─ processOrder")


def test_parse_cpuprofile_keep_filter():
    lines = parse_cpuprofile(CPUPROFILE, keep="orders")
    assert len(lines) == 1 and "processOrder" in lines[0]


def test_parse_cpuprofile_empty_profile():
    assert parse_cpuprofile({}) == []


JDB_OUTPUT = """\
Set deferred breakpoint Demo.main
Method entered: "thread=main", Demo.main(), line=10 bci=0
Method entered: "thread=main", Demo.greet(), line=4 bci=0
Method exited: return value = <void value>, "thread=main", Demo.greet(), line=6 bci=10
Method entered: "thread=main", Demo.farewell(), line=8 bci=0
Method exited: return value = <void value>, "thread=main", Demo.farewell(), line=8 bci=5
Method exited: return value = <void value>, "thread=main", Demo.main(), line=12 bci=20
The application exited
"""


def test_indent_jdb_trace_builds_depth_tree():
    lines = indent_jdb_trace(JDB_OUTPUT)
    assert lines[0].startswith("└─") and "Demo.main()" in lines[0]
    assert lines[1].startswith("  └─") and "Demo.greet()" in lines[1]
    assert lines[2].startswith("  └─") and "Demo.farewell()" in lines[2]


def test_indent_jdb_trace_package_filter():
    lines = indent_jdb_trace(JDB_OUTPUT, pkg_filter="greet")
    assert len(lines) == 1 and "Demo.greet()" in lines[0]


def test_indent_jdb_trace_ignores_non_trace_lines():
    assert indent_jdb_trace("random output\nno trace here") == []
