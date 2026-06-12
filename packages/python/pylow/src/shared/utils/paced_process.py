"""Marker-paced process driver — interactive tools driven reliably.

Blind piping breaks debuggers that read stdin while the program runs (jdb
consumes every queued command the moment the VM starts). This driver sends
command batches only when the tool's output proves it is stopped:

    setup batch  → sent immediately (prelude, breakpoints, run)
    per-stop     → sent each time hit_marker appears in the output
    quit         → sent at end_marker, max_steps, or timeout

Pure orchestration — what to send and which markers to watch comes from the
declarative DebuggerSpec, so this driver works for every language unchanged.
"""
import queue
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PacedPlan:
    setup: tuple = ()            # commands sent as soon as the tool starts
    per_stop: tuple = ()         # commands sent after every hit_marker match
    hit_marker: str = ""         # regex: "the tool is stopped at a breakpoint"
    end_marker: str = ""         # literal: "the program has finished"
    quit_cmd: str = ""
    continue_cmd: str = ""
    skip_initial_stop: bool = False
    max_steps: int = 50
    timeout: float = 300.0
    cwd: str | None = None
    interactive: bool = True


def _format_line(line: str) -> str:
    line_stripped = line.strip()
    
    # Hide JDB ParseException and format as out-of-scope
    if "ParseException: Name unknown" in line_stripped:
        var_name = line_stripped.split("unknown:")[-1].strip()
        return f"\033[31mWatched '{var_name}'\033[0m: \033[90m<not in current scope>\033[0m\n"
    if line.startswith(" ") and line_stripped.endswith(" = null"):
        return ""

    if "--- CALL STACK ---" in line_stripped or "--- SOURCE CODE ---" in line_stripped:
        header = line_stripped.split('"')[1]
        return f"\n\033[90m{'─' * 30}\033[0m\n\033[1;36m{header}\033[0m\n"

    # Filter out massive framework call stacks to keep the console clean
    if line_stripped.startswith("[") and "] " in line_stripped:
        content = line_stripped.split("] ", 1)[-1]
        noise_prefixes = ("java.", "javax.", "jdk.", "sun.", "org.springframework.", "org.apache.", "org.eclipse.", "io.netty.")
        if content.startswith(noise_prefixes):
            return "" # Skip printing this line to console

    if "=>" in line_stripped:
        return f"\033[1;33m{line}\033[0m"  # Yellow for current execution line

    if line_stripped.endswith(":"):
        return f"\n\033[90m{'─' * 30}\033[0m\n\033[1;36m{line}\033[0m"  # Cyan for headers with separator
        
    if "=" in line_stripped and not line_stripped.startswith("Breakpoint"):
        key, sep, val = line.partition("=")
        return f"\033[32m{key}\033[0m{sep}\033[33m{val}\033[0m"  # Green key, Yellow val
        
    if "Breakpoint hit" in line_stripped or "break in" in line_stripped:
        separator = "\033[90m" + "─" * 60 + "\033[0m"
        if "), line=" in line_stripped:
            func_part = line_stripped.split(",")[1].strip()
            return f"\n{separator}\n\033[1;45;37m 🛑 STOPPED IN: {func_part} \033[0m\n\033[90m{line_stripped}\033[0m\n"
        return f"\n{separator}\n\033[1;35m{line}\033[0m"  # Magenta for breakpoints
        
    return line

def run_paced(argv: list, plan: PacedPlan) -> str:
    """Run argv, pace stdin batches on output markers, return full transcript."""
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=plan.cwd)
    lines: queue.Queue = queue.Queue()
    threading.Thread(target=_pump, args=(proc, lines), daemon=True).start()

    transcript: list = []
    # Wait for the debugger process to initialize before sending setup commands
    time.sleep(1.5)
    _send(proc, plan.setup)
    hit = re.compile(plan.hit_marker) if plan.hit_marker else None
    stops_seen = 0
    deadline = time.time() + plan.timeout

    while time.time() < deadline:
        line = _next_line(lines, proc)
        if line is _EOF:
            break
        if line is _IDLE:
            continue
        transcript.append(line)
        if plan.interactive:
            print(_format_line(line), end="", flush=True)
        if plan.end_marker and plan.end_marker in line:
            _send(proc, (plan.quit_cmd,))
            break
        if hit and hit.search(line):
            stops_seen += 1
            if plan.skip_initial_stop and stops_seen == 1:
                continue
            if stops_seen - int(plan.skip_initial_stop) > plan.max_steps:
                _send(proc, (plan.quit_cmd,))
                break
            
            # 1. Ask the debugger to print variables for this stop
            _send(proc, plan.per_stop)
            
            # 2. Wait for user to read it (if interactive)
            if plan.interactive:
                # Sleep to let the debugger compute and flush the variable printouts
                time.sleep(0.5)
                # Drain the queue and buffer the step output
                step_buffer = []
                while not lines.empty():
                    try:
                        q_line = lines.get_nowait()
                        if q_line is not None:
                            transcript.append(q_line)
                            step_buffer.append(q_line)
                    except queue.Empty:
                        break
                
                if step_buffer:
                    from .ai_formatter import format_debugger_state_with_ai
                    ai_output = format_debugger_state_with_ai("".join(step_buffer))
                    print("\n" + ai_output + "\n", flush=True)
                        
                try:
                    input(f"\n[pylow] Stopped at breakpoint {stops_seen}. Press Enter to continue...")
                except (KeyboardInterrupt, EOFError):
                    _send(proc, (plan.quit_cmd,))
                    break
            
            # 3. Proceed to the next step
            if plan.continue_cmd:
                _send(proc, (plan.continue_cmd,))

    _send(proc, (plan.quit_cmd,))
    _shutdown(proc, lines, transcript)
    return "".join(transcript)


_EOF = object()
_IDLE = object()


def _pump(proc, lines: queue.Queue) -> None:
    for line in proc.stdout:
        lines.put(line)
    lines.put(None)


def _next_line(lines: queue.Queue, proc):
    try:
        line = lines.get(timeout=2.0)
    except queue.Empty:
        return _EOF if proc.poll() is not None else _IDLE
    return _EOF if line is None else line


def _send(proc, commands: tuple) -> None:
    payload = "\n".join(c for c in commands if c)
    if not payload or proc.stdin is None or proc.poll() is not None:
        return
    try:
        proc.stdin.write(payload + "\n")
        proc.stdin.flush()
    except (BrokenPipeError, ValueError, OSError):
        pass


def _shutdown(proc, lines: queue.Queue, transcript: list) -> None:
    try:
        proc.stdin.close()
    except (BrokenPipeError, ValueError, OSError):
        pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    # drain whatever the reader thread pushed after we stopped looping
    deadline = time.time() + 3
    while time.time() < deadline:
        try:
            line = lines.get(timeout=0.5)
        except queue.Empty:
            break
        if line is None:
            break
        transcript.append(line)
