"""Tracer strategy registry — each backend behavior is a registered function.

Engines select a TracerBackend from the LanguageSpec (priority order, first
installed tool wins) and dispatch here by name. Adding a backend = one new
registered function + one TracerBackend entry in shared/lang/languages.py.
"""


class TracerStrategies:
    _strategies: dict = {}

    @classmethod
    def register(cls, name):
        def decorator(fn):
            cls._strategies[name] = fn
            return fn
        return decorator

    @classmethod
    def run(cls, name, service, request):
        strategy = cls._strategies.get(name, cls._strategies["simulated"])
        return strategy(service, request)


@TracerStrategies.register("dlv_trace_attach")
def _(service, request):
    regex = request.func_regex or "main\\..*"
    print(f"Using delve function tracing (pattern: {regex})")
    service._exec(["dlv", "trace", "-p", str(request.pid), regex], timeout=request.duration)


@TracerStrategies.register("perf_profile")
def _(service, request):
    print("Using perf on-CPU sampling")
    service._perf_profile(request.pid, request.duration)


@TracerStrategies.register("strace_summary")
def _(service, request):
    print("Using strace syscall summary")
    service._strace_summary(request.pid, request.duration)


@TracerStrategies.register("jcmd_jfr")
def _(service, request):
    service._java_thread_snapshot(request.pid)
    service._java_flight_recording(request.pid, request.duration)


@TracerStrategies.register("jstack_dump")
def _(service, request):
    _, out = service._exec_capture(["jstack", str(request.pid)], timeout=10)
    print(out[:4000])


@TracerStrategies.register("node_attach")
def _(service, request):
    inspector_opened = service._open_node_inspector(request.pid)
    if inspector_opened is None:
        return
    fallback = service._pick(["perf", "strace"])
    runner = {
        "perf": lambda: service._perf_profile(request.pid, request.duration),
        "strace": lambda: service._strace_summary(request.pid, request.duration),
    }.get(fallback)
    if runner:
        runner()
    elif not inspector_opened:
        service._simulated("ts")


@TracerStrategies.register("simulated")
def _(service, request):
    service._simulated(request.lang)
