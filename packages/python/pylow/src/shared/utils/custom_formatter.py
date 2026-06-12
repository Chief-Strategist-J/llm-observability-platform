import re
from datetime import datetime

# Global state to track changes across steps
_last_vars = {}
_stop_count = 0

def format_custom_ui(transcript_buffer: list) -> str:
    global _last_vars, _stop_count
    _stop_count += 1
    
    raw = "".join(transcript_buffer)
    
    # Defaults
    thread_name = "Main"
    location = "Unknown"
    file_line = "Unknown"
    
    # Parse Breakpoint Info
    bp_match = re.search(r'Breakpoint hit: "thread=([^"]+)", (.*?)\(\), line=(\d+)', raw)
    if bp_match:
        thread_name = bp_match.group(1)
        location = bp_match.group(2) + "()"
        file_line = location.split('.')[-1].replace("()", "") + ".java:" + bp_match.group(3)

    out = []
    # Header
    out.append("╔" + "═" * 68 + "╗")
    out.append(f"║ BREAKPOINT #{_stop_count:<55}║")
    out.append("╠" + "═" * 68 + "╣")
    out.append(f"║ Location : {location:<55} ║")
    out.append(f"║ File     : {file_line:<55} ║")
    out.append(f"║ Thread   : {thread_name:<55} ║")
    out.append(f"║ Time     : {datetime.now().strftime('%H:%M:%S.%f')[:-3]:<55} ║")
    out.append("╚" + "═" * 68 + "╝\n")

    # Parse Source Code & Current Statement
    source_lines = []
    current_statement = ""
    in_source = False
    for line in raw.splitlines():
        if "--- SOURCE CODE ---" in line:
            in_source = True
            continue
        if in_source and line.strip():
            if line.startswith("=>"):
                current_statement = line.replace("=>", "").strip()
                source_lines.append(line.replace("=>", "▶ ").replace("  ", " │ ", 1))
            else:
                parts = line.split(" ", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    source_lines.append(f"{parts[0]:<2} │ {parts[1].strip()}")

    if current_statement:
        out.append("▶ Current Statement\n" + "─" * 68)
        parts = current_statement.split(" ", 1)
        if len(parts) == 2:
            out.append(f"{parts[0]:<2} │ {parts[1].strip()}\n")

    # Parse Parameters and Locals
    params = []
    locals_ = []
    current_section = None
    
    current_vars = {}
    
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("Method arguments:"):
            current_section = "params"
            continue
        elif line.startswith("Local variables:"):
            current_section = "locals"
            continue
        elif line.startswith("--- CALL STACK ---") or line.startswith("--- SOURCE CODE ---"):
            current_section = None
            
        if current_section and "=" in line and "instance of" not in line:
            key, val = [x.strip() for x in line.split("=", 1)]
            current_vars[key] = val
            if current_section == "params":
                params.append(f"{key:<4} = {val}")
            elif current_section == "locals":
                locals_.append(f"{key:<4} = {val}")

    if params:
        out.append("▶ Parameters\n" + "─" * 68)
        out.extend(params)
        out.append("")

    if locals_:
        out.append("▶ Locals\n" + "─" * 68)
        out.extend(locals_)
        out.append("")
        
    # State Changes
    changes = []
    for k, v in current_vars.items():
        if k in _last_vars and _last_vars[k] != v:
            changes.append(f"{k}: {_last_vars[k]} → {v}")
    _last_vars = current_vars.copy()
    
    # Call Stack
    stack = []
    in_stack = False
    for line in raw.splitlines():
        if "--- CALL STACK ---" in line:
            in_stack = True
            continue
        if "--- SOURCE CODE ---" in line:
            in_stack = False
        if in_stack and line.strip().startswith("["):
            # Clean it up to match format
            match = re.search(r'\[\d+\]\s+(.*?)\s+\((.*?)\)', line)
            if match:
                func = match.group(1).split('.')[-1]
                file = match.group(2)
                stack.append(f"#{len(stack)+1:<2} {func:<20} {file}")
                
    if stack:
        out.append("▶ Call Path\n" + "─" * 68)
        out.extend(stack)
        out.append("")

    if source_lines:
        out.append("▶ Source Context\n" + "─" * 68)
        out.extend(source_lines)
        out.append("")
        
    if changes:
        out.append("▶ State Changes Since Last Stop\n" + "─" * 68)
        out.extend(changes)
        out.append("")

    return "\n".join(out)
