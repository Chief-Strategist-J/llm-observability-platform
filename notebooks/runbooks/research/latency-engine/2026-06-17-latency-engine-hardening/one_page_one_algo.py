import re

with open("proof.tex", "r") as f:
    content = f.read()

# We will match `\begin{mathbox}{N. ` and insert `\clearpage` right before it.
# We do this for all strategies 1 to 22.
for num in range(1, 23):
    pattern = re.compile(r"(\\begin\{mathbox\}\{" + str(num) + r"\.\s+)")
    
    # Check if \clearpage is already before it to avoid duplication
    # Let's search for the pattern
    match = pattern.search(content)
    if match:
        matched_str = match.group(1)
        # We replace the matched_str with `\clearpage\n` + matched_str
        # But let's check if there's already a \clearpage before it
        start_idx = match.start()
        prefix = content[max(0, start_idx - 20):start_idx]
        if "\\clearpage" not in prefix:
            content = content[:start_idx] + "\\clearpage\n" + content[start_idx:]
            print(f"Added \\clearpage before Strategy {num}")
        else:
            print(f"\\clearpage already present before Strategy {num}")

with open("proof.tex", "w") as f:
    f.write(content)
