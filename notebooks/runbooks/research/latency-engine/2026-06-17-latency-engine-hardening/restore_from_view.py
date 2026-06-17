import json
import re

with open("/home/btpl-lap-22/.gemini/antigravity-cli/brain/a1997a83-c2e5-4501-8242-9f30fb351e58/.system_generated/logs/transcript_full.jsonl", "r") as f:
    steps = [json.loads(line) for line in f]

# Find the view_file tool outputs
view_contents = {}
for step in steps:
    content = step.get("content", "")
    if "Total Lines: 983" in content:
        print(f"Found view_file output in step {step.get('step_index')}")
        # Let's extract the lines
        for line in content.split("\n"):
            m = re.match(r"^\s*(\d+):\s(.*)$", line)
            if m:
                view_contents[int(m.group(1))] = m.group(2)

# Let's double check if we got all 983 lines
print(f"Extracted {len(view_contents)} lines.")
if len(view_contents) > 0:
    max_line = max(view_contents.keys())
    full_text = []
    for i in range(1, max_line + 1):
        full_text.append(view_contents.get(i, ""))
    
    with open("proof.tex.restored", "w") as out:
        out.write("\n".join(full_text) + "\n")
    print("Successfully wrote proof.tex.restored")
