import re

with open("proof.tex", "r") as f:
    content = f.read()

# 1. Insert the textbookalgo environment into the preamble.
# We will locate the line `%% ── Title Format` and insert our environment just before it.
preamble_insertion = """
%% ── Textbook Algorithm Environment ───────────────────────────────────────────
\\newenvironment{textbookalgo}[2]{%
  \\par\\addvspace{1.2em}\\noindent
  \\hrule height 1.2pt
  \\vspace{1.5pt}
  \\hrule height 0.4pt
  \\vspace{5pt}
  {\\noindent\\large\\bfseries\\sffamily ALGORITHM #1 \\quad #2}
  \\par\\vspace{5pt}
  \\RestyleAlgo{plain}
}{%
  \\par\\vspace{4pt}
  \\hrule height 0.4pt
  \\vspace{1.5pt}
  \\hrule height 1.2pt
  \\par\\addvspace{1.2em}
}
"""

if "%% ── Textbook Algorithm Environment ───────────────────────────────────────────" not in content:
    content = content.replace("%% ── Title Format ─────────────────────────────────────────────", 
                              preamble_insertion + "\n%% ── Title Format ─────────────────────────────────────────────")

# 2. Refactor all mathbox blocks that contain the side-by-side layout
mathbox_pattern = re.compile(r"(\\begin\{mathbox\}\{(\d+)\.\s+([^\}]+)\}.*?\\end\{mathbox\})", re.DOTALL)
matches = list(mathbox_pattern.finditer(content))
print(f"Found {len(matches)} mathbox blocks.")

new_content = content
refactored_count = 0

for m in matches:
    block_text = m.group(0)
    num = m.group(2)
    name = m.group(3)
    
    if "\\begin{minipage}{0.45\\textwidth}" in block_text:
        inner_pat = re.compile(
            r"\\begin\{mathbox\}\{\d+\.\s+[^\}]+\}\s*\n"
            r"\\textbf\{Complexity:\}\s*(.*?)\s*\n\s*\n"
            r"\\begin\{minipage\}\{0\.45\\textwidth\}\s*\n"
            r"\\begin\{verbatim\}\s*\n"
            r"(.*?)\n"
            r"\\end\{verbatim\}\s*\n"
            r"\\end\{minipage\}\s*\n"
            r"\\hfill\s*\n"
            r"\\begin\{minipage\}\{0\.5\\textwidth\}\s*\n"
            r"\\begin\{algorithm\}\[H\]\s*\n"
            r"\\caption\{([^\}]+)\}\s*\n"
            r"(.*?)\n"
            r"\\end\{algorithm\}\s*\n"
            r"\\end\{minipage\}\s*\n"
            r"\\end\{mathbox\}",
            re.DOTALL
        )
        
        inner_match = inner_pat.match(block_text)
        if inner_match:
            complexity = inner_match.group(1)
            ascii_tree = inner_match.group(2)
            caption = inner_match.group(3)
            algo_body = inner_match.group(4)
            
            algo_num = f"{num}.1"
            
            new_block = (
                f"\\begin{{mathbox}}{{{num}. {name}}}\n"
                f"\\textbf{{Complexity:}} {complexity}\n\n"
                f"\\begin{{verbatim}}\n"
                f"{ascii_tree}\n"
                f"\\end{{verbatim}}\n"
                f"\\end{{mathbox}}\n\n"
                f"\\begin{{textbookalgo}}{{{algo_num}}}{{{caption}}}\n"
                f"\\begin{{algorithm}}[H]\n"
                f"{algo_body}\n"
                f"\\end{{algorithm}}\n"
                f"\\end{{textbookalgo}}"
            )
            
            new_content = new_content.replace(block_text, new_block)
            print(f"Successfully refactored Strategy {num}: {name} -> Algorithm {algo_num} {caption}")
            refactored_count += 1
        else:
            print(f"Failed to parse inner contents of Strategy {num}: {name}")

print(f"Total strategies refactored: {refactored_count}")

with open("proof.tex", "w") as f:
    f.write(new_content)
