import re

with open("proof.tex", "r") as f:
    content = f.read()

# Let's match each strategy block:
# \clearpage
# \begin{mathbox}{N. Strategy Name}
# \textbf{Complexity:} <Complexity>
# \begin{verbatim}
# <ASCIITree>
# \end{verbatim}
# \end{mathbox}
# 
# \begin{textbookalgo}{N.1}{<Caption>}
# \begin{algorithm}[H]
# <AlgoBody>
# \end{algorithm}
# \end{textbookalgo}
# 
# \noindent
# \textbf{When to use:} <When>\\
# \textbf{How to use:} <How>
# \begin{itemize}[leftmargin=*]
# ...
# \end{itemize}
# \medskip

# We can match this using a regular expression that captures all the components.
# Let's write a parser that parses strategy-by-strategy.
# Since we know there are 22 strategies, we can loop over N from 1 to 22.

for num in range(1, 23):
    algo_num = f"{num}.1"
    
    # We will match the entire block starting from \clearpage\n\begin{mathbox}{N. Strategy Name}
    # all the way to the end of the \end{itemize}\n\medskip
    pattern = re.compile(
        r"\\clearpage\s*\n"
        r"\\begin\{mathbox\}\{" + str(num) + r"\.\s+([^\}]+)\}\s*\n"
        r"\\textbf\{Complexity:\}\s*(.*?)\s*\n\s*\n"
        r"\\begin\{verbatim\}\s*\n"
        r"(.*?)\n"
        r"\\end\{verbatim\}\s*\n"
        r"\\end\{mathbox\}\s*\n\s*\n"
        r"(\\begin\{textbookalgo\}\{" + re.escape(algo_num) + r"\}\{[^\}]+\}\s*\n"
        r"\\begin\{algorithm\}\[H\]\s*\n"
        r".*?\n"
        r"\\end\{algorithm\}\s*\n"
        r"\\end\{textbookalgo\})\s*\n\s*\n"
        r"(.*?\\end\{itemize\}\s*\n\s*\\medskip\s*\n?)",
        re.DOTALL
    )
    
    match = pattern.search(content)
    if match:
        full_match = match.group(0)
        strategy_name = match.group(1)
        complexity = match.group(2)
        ascii_tree = match.group(3)
        algo_block = match.group(4)
        questions_block = match.group(5)
        
        # Construct the reordered block
        reordered_block = (
            f"\\clearpage\n"
            f"\\subsection{{{num}. {strategy_name}}}\n\n"
            f"{algo_block}\n\n"
            f"{questions_block.strip()}\n\n"
            f"\\begin{{mathbox}}{{Complexity \\& Operational Diagram}}\n"
            f"\\textbf{{Complexity:}} {complexity}\n\n"
            f"\\begin{{verbatim}}\n"
            f"{ascii_tree}\n"
            f"\\end{{verbatim}}\n"
            f"\\end{{mathbox}}\n"
        )
        
        content = content.replace(full_match, reordered_block)
        print(f"Reordered Strategy {num}: {strategy_name}")
    else:
        print(f"COULD NOT MATCH Strategy {num}")

with open("proof.tex", "w") as f:
    f.write(content)
