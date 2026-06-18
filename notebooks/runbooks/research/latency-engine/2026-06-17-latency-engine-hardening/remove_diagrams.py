import re

with open("proof.tex", "r") as f:
    content = f.read()

# 1. Remove the TikZ system architecture diagram from Section 2.
# Let's find: \begin{vizbox}{System Architecture | Ingestion Pipeline and Redis Outage Buffering} ... \end{vizbox}
# We can replace the whole box with just a brief text or remove it.
vizbox_pattern = re.compile(r"\\begin\{vizbox\}\{System Architecture \| Ingestion Pipeline and Redis Outage Buffering\}.*?\\end\{vizbox\}", re.DOTALL)
content, count_viz = vizbox_pattern.subn("", content)
print(f"Removed system architecture vizbox: {count_viz}")

# 2. Remove the PGFPlots chart from Section 4.
# Let's find: \begin{figure}[H]\n\centering\n\begin{tikzpicture} ... \end{tikzpicture}\n\caption{...}\n\label{...}\n\end{figure}
fig_pattern = re.compile(r"\\begin\{figure\}\[H\]\s*\n\\centering\s*\n\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}\s*\n\\caption\{DDSketch Quantile Approximations vs Exact Latency\.\}\s*\n\\label\{fig:ddsketch-accuracy\}\s*\n\\end\{figure\}", re.DOTALL)
content, count_fig = fig_pattern.subn("", content)
print(f"Removed DDSketch plot figure: {count_fig}")

# 3. Remove the Caching Decision Tree Flowchart from the end.
# Let's find: \begin{figure}[H]\n\centering\n\begin{minipage}{\textwidth}\n\begin{verbatim}\n                           Is the operations pattern? ... \end{verbatim}\n\end{minipage}\n\caption{ASCII Caching strategy selection flowchart.}\n\end{figure}
tree_pattern = re.compile(r"\\begin\{figure\}\[H\]\s*\n\\centering\s*\n\\begin\{minipage\}\{\\textwidth\}\s*\n\\begin\{verbatim\}\s*\n\s*Is the operations pattern\?.*?\\end\{verbatim\}\s*\n\\end\{minipage\}\s*\n\\caption\{ASCII Caching strategy selection flowchart\.\}\s*\n\\end\{figure\}", re.DOTALL)
content, count_tree = tree_pattern.subn("", content)
print(f"Removed Caching Decision Tree Flowchart figure: {count_tree}")

# 4. Remove all mathbox blocks at the bottom of all 41 strategies, and move Complexity under the subsection title.
# For each strategy N (from 1 to 41), the structure is:
# \clearpage
# \subsection{N. Strategy Name}
#
# \begin{textbookalgo}{N.1}{Caption}
# ...
# \end{textbookalgo}
#
# \noindent
# \textbf{When to use:} ...
# ...
# \end{itemize}
# \medskip
#
# \begin{mathbox}{Complexity & Operational Diagram} (or Complexity & Execution Flowchart)
# \textbf{Complexity:} ComplexityText
# \begin{verbatim}
# ASCII Tree
# \end{verbatim}
# \end{mathbox}

for num in range(1, 42):
    # Match the block for the strategy N
    # We match from \subsection{N. Name} all the way to \end{mathbox}
    # To be extremely precise, let's find the mathbox block for each strategy:
    # \begin{mathbox}{Complexity & Operational/Execution...}
    # \textbf{Complexity:} <Complexity>
    # \begin{verbatim}
    # <Tree>
    # \end{verbatim}
    # \end{mathbox}
    
    # We can search for the mathbox right after the subsection
    pattern = re.compile(
        r"(\\clearpage\s*\n\\subsection\{" + str(num) + r"\.\s+([^\}]+)\}\s*\n\s*\n)"
        r"(.*?)\s*\n\s*\n"
        r"\\begin\{mathbox\}\{Complexity\s+\\\&\s+(?:Operational\s+Diagram|Execution\s+Flowchart)\}\s*\n"
        r"\\textbf\{Complexity:\}\s*(.*?)\s*\n\s*\n"
        r"\\begin\{verbatim\}\s*\n"
        r".*?\n"
        r"\\end\{verbatim\}\s*\n"
        r"\\end\{mathbox\}",
        re.DOTALL
    )
    
    match = pattern.search(content)
    if match:
        full_match = match.group(0)
        sub_header = match.group(1)
        name = match.group(2)
        inner_content = match.group(3)
        complexity = match.group(4)
        
        # We reorder by putting Complexity right after the subsection header, then inner_content, and no mathbox!
        new_block = (
            f"{sub_header}"
            f"\\noindent\n"
            f"\\textbf{{Complexity:}} {complexity}\n\\smallskip\n\n"
            f"{inner_content}\n"
        )
        content = content.replace(full_match, new_block)
        print(f"Removed diagram and kept complexity for Strategy {num}: {name}")
    else:
        # Check if it has the old title name like {N. Strategy Name} in mathbox (e.g. from any missed ones)
        print(f"Could not find diagram block for Strategy {num}")

with open("proof.tex", "w") as f:
    f.write(content)
