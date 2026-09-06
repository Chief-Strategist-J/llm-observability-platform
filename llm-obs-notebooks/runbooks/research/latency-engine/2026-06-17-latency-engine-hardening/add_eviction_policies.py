import re

# Define the new LaTeX section for eviction policies containing 23. LRU to 29. TinyLFU
eviction_latex = """
%% =============================================================================
\\section{Cache Eviction Policies \\& Architectural Mechanics}\\label{sec:eviction-policies}
%% =============================================================================
Caching systems require robust eviction policies to free up memory when capacities are reached. This section details the internal algorithms, complexity, and operational trade-offs of the 7 core eviction policies.

\\clearpage
\\subsection{23. LRU (Least Recently Used)}

\\begin{textbookalgo}{23.1}{AccessLRU(key, val, op)}
\\begin{algorithm}[H]
\\If{$\\text{map.contains}(key)$}{
  $node \\leftarrow \\text{map.get}(key)$\\;
  \\If{$op == \\text{"write"}$}{
    $node.val \\leftarrow val$\\;
  }
  $\\text{dll.move\\_to\\_head}(node)$\\;
  \\Return $node.val$\\;
}
\\If{$\\text{dll.size} == \\text{capacity}$}{
  $tail \\leftarrow \\text{dll.pop\\_tail()}$\\;
  $\\text{map.delete}(tail.key)$\\;
}
$new\\_node \\leftarrow \\text{create\\_node}(key, val)$\\;
$\\text{dll.add\\_to\\_head}(new\\_node)$\\;
$\\text{map.set}(key, new\\_node)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} General-purpose caching where items accessed recently are likely to be accessed again soon.\\\\
\\textbf{How to use:} Implement a hash map mapped to nodes of a doubly linked list to achieve $O(1)$ operations.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How does LRU perform under a sequential scan of a dataset larger than the cache size?
    \\item What is the impact of lock contention on the doubly linked list head pointer in multi-threaded environments?
    \\item Meta: How do we monitor cache churn rates (eviction count per second) in an LRU setup?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item How does memory alignment of node pointers affect cache-miss rates at the CPU level?
    \\item Can we use a segmented LRU (SLRU) to protect the cache from single-access scans?
    \\item How does virtual memory paging interact with large in-memory LRU structures?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ lookup and update | Space: $O(\\text{capacity})$

\\begin{verbatim}
Read/Write Key
 |
 +- Key in Map?
     +- Yes -> Move Node to Head of DLL -> Return/Update
     +- No -> DLL Size == Capacity?
               +- Yes -> Evict Tail Node from DLL & Map
               +- No -> Insert Node at Head of DLL & Map
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{24. LFU (Least Frequently Used)}

\\begin{textbookalgo}{24.1}{AccessLFU(key, val, op)}
\\begin{algorithm}[H]
\\If{$\\text{map.contains}(key)$}{
  $node \\leftarrow \\text{map.get}(key)$\\;
  $freq \\leftarrow node.freq$\\;
  $node.freq \\leftarrow freq + 1$\\;
  $\\text{freq\\_map.get}(freq).\\text{remove}(node)$\\;
  \\If{$\\text{freq\\_map.get}(freq).\\text{is\\_empty}() \\land freq == \\text{min\\_freq}$}{
    $\\text{min\\_freq} \\leftarrow \\text{min\\_freq} + 1$\\;
  }
  $\\text{freq\\_map.get}(freq+1).\\text{add}(node)$\\;
  \\Return $node.val$\\;
}
\\If{$\\text{map.size} == \\text{capacity}$}{
  $evict\\_node \\leftarrow \\text{freq\\_map.get}(\\text{min\\_freq}).\\text{pop\\_tail()}$\\;
  $\\text{map.delete}(evict\\_node.key)$\\;
}
$new\\_node \\leftarrow \\text{create\\_node}(key, val, \\text{freq}=1)$\\;
$\\text{freq\\_map.get}(1).\\text{add}(new\\_node)$\\;
$\\text{map.set}(key, new\\_node)$\\;
$\\text{min\\_freq} \\leftarrow 1$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Long-running, stable workloads with distinct and static hot-sets (e.g. static configuration registries).\\\\
\\textbf{How to use:} Use a frequency map pointing to doubly-linked lists of nodes sharing the same frequency to maintain $O(1)$ runtime.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we prevent newly inserted keys from being evicted immediately due to their low frequency?
    \\item What is the memory footprint of maintaining frequency node headers for each frequency count?
    \\item Meta: How do we observe frequency inflation when cache keys are active over months?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Can we implement logarithmic frequency aging to decay old hot keys?
    \\item How does LFU behave when key access counts exceed integer storage bounds?
    \\item Does LFU trigger high lock contention on the global minimum frequency tracker under load?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ lookup and update | Space: $O(\\text{capacity})$

\\begin{verbatim}
Access Key
 |
 +- Key in Map?
     +- Yes -> Increment Count -> Move to New Freq Bucket Node
     +- No -> Cache Full?
               +- Yes -> Evict Node with Min Freq from List
               +- No -> Insert Node with Freq = 1
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{25. FIFO (First In, First Out)}

\\begin{textbookalgo}{25.1}{AccessFIFO(key, val)}
\\begin{algorithm}[H]
\\If{$\\text{map.contains}(key)$}{
  \\Return $\\text{map.get}(key)$\\;
}
\\If{$\\text{queue.size} == \\text{capacity}$}{
  $old\\_key \\leftarrow \\text{queue.dequeue()}$\\;
  $\\text{map.delete}(old\\_key)$\\;
}
$\\text{queue.enqueue}(key)$\\;
$\\text{map.set}(key, val)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Simple queues, stream buffering, or low-overhead applications where temporal order of insertion dominates.\\\\
\\textbf{How to use:} Implement a standard ring buffer or FIFO queue linked to a hash map.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How does FIFO compare to LRU when keys are repeatedly accessed shortly after insertion?
    \\item What is the impact of Belady's anomaly on page faults inside a FIFO cache?
    \\item Meta: How does FIFO queue latency behave under sustained queue saturation?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item How do we prevent FIFO cache thrashing when processing bulk periodic imports?
    \\item Does FIFO simplify GC memory recycling compared to pointer-heavy LRU implementations?
    \\item Can we implement a FIFO variant with a Second Chance (clock algorithm) to improve accuracy?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{capacity})$

\\begin{verbatim}
Insert Key
 |
 +- Cache Full?
     +- Yes -> Pop Head of Queue -> Remove from Map
     +- No -> Push Key to Queue Tail -> Add to Map
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{26. MRU (Most Recently Used)}

\\begin{textbookalgo}{26.1}{AccessMRU(key, val)}
\\begin{algorithm}[H]
\\If{$\\text{map.contains}(key)$}{
  $node \\leftarrow \\text{map.get}(key)$\\;
  $\\text{dll.move\\_to\\_head}(node)$\\;
  \\Return $node.val$\\;
}
\\If{$\\text{dll.size} == \\text{capacity}$}{
  $head \\leftarrow \\text{dll.pop\\_head()}$\\;
  $\\text{map.delete}(head.key)$\\;
}
$new\\_node \\leftarrow \\text{create\\_node}(key, val)$\\;
$\\text{dll.add\\_to\\_head}(new\\_node)$\\;
$\\text{map.set}(key, new\\_node)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Specialized patterns where older data is more likely to be requested again than recently fetched data (e.g. scanning loops).\\\\
\\textbf{How to use:} Use a doubly-linked list where eviction targets the head node instead of the tail.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item What real-world database access patterns (e.g. nested loop joins) benefit most from MRU?
    \\item How do we recover MRU hit ratios when a scan finishes and normal random reads resume?
    \\item Meta: How do we track MRU usage trends to distinguish loop scans from standard query pipelines?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item How does MRU behave when multiple concurrent loops run at different speeds?
    \\item Can we dynamically switch between LRU and MRU based on the measured access stride?
    \\item What is the thread safety overhead of evicting from the head of the DLL?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{capacity})$

\\begin{verbatim}
Access Key
 |
 +- Key in Map?
     +- Yes -> Move Node to Head -> Return
     +- No -> Cache Full?
               +- Yes -> Evict Head Node (MRU) from Map
               +- No -> Insert Node at Head of Map
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{27. Random (Random Eviction)}

\\begin{textbookalgo}{27.1}{AccessRandom(key, val)}
\\begin{algorithm}[H]
\\If{$\\text{map.contains}(key)$}{
  \\Return $\\text{map.get}(key)$\\;
}
\\If{$\\text{map.size} == \\text{capacity}$}{
  $rand\\_key \\leftarrow \\text{map.get\\_random\\_key()}$\\;
  $\\text{map.delete}(rand\\_key)$\\;
}
$\\text{map.set}(key, val)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Ultra-low overhead constraints, resource-limited microcontrollers, or as a fallback eviction policy in heavy Redis clusters.\\\\
\\textbf{How to use:} Store keys in a map and a flat array, swapping and popping elements in $O(1)$ time to evict a random index.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How much lower is the CPU utilization of Random eviction compared to pointer-heavy LRU?
    \\item What is the variance in cache hit ratio when comparing Random to LRU under zipfian distributions?
    \\item Meta: How do we inject synthetic seeds to test cache predictability under Random eviction?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item How does random number generator (RNG) quality affect cache coverage and cluster parity?
    \\item Does Random eviction prevent malicious cache-timing attacks by introducing non-determinism?
    \\item Can we run a two-candidate random selection policy (2-random choice) to approximate LRU?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{capacity})$

\\begin{verbatim}
Insert Key
 |
 +- Cache Full?
     +- Yes -> Pick Random Key -> Evict Node
     +- No -> Write Cache Node
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{28. ARC (Adaptive Replacement Cache)}

\\begin{textbookalgo}{28.1}{AccessARC(key, val)}
\\begin{algorithm}[H]
\\If{$key \\in T1 \\cup T2$}{
  $\\text{move}(key, T2)$\\;
  \\Return $\\text{get}(key)$\\;
}
\\If{$key \\in B1$}{
  $p \\leftarrow \\min(p + \\max(1, |B2|/|B1|), c)$\\;
  $\\text{replace}(key, \\text{false})$\\;
  $\\text{move}(key, T2)$\\;
  \\Return $\\text{fetch\\_and\\_set}(key)$\\;
}
\\If{$key \\in B2$}{
  $p \\leftarrow \\max(p - \\max(1, |B1|/|B2|), 0)$\\;
  $\\text{replace}(key, \\text{true})$\\;
  $\\text{move}(key, T2)$\\;
  \\Return $\\text{fetch\\_and\\_set}(key)$\\;
}
\\If{$|T1| + |B1| == c$}{
  \\If{$|T1| < c$}{
    $\\text{delete\\_last}(B1)$; $\\text{replace}(key, \\text{false})$\\;
  }\\Else{
    $del\\_key \\leftarrow \\text{pop\\_last}(T1)$; $\\text{delete}(del\\_key)$\\;
  }
}\\ElseIf{$|T1| + |T2| + |B1| + |B2| \\ge c$}{
  \\If{$|T1| + |T2| + |B1| + |B2| == 2c$}{
    $\\text{delete\\_last}(B2)$\\;
  }
  $\\text{replace}(key, \\text{false})$\\;
}
$\\text{insert}(key, T1)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} High-performance storage servers, databases, or cache managers that must dynamically adapt to changing recency vs frequency ratios.\\\\
\\textbf{How to use:} Maintain four doubly linked lists (T1: recency, T2: frequency, B1: recency ghost cache, B2: frequency ghost cache) with a tuning parameter $p$.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How does ghost cache tracking prevent cache pollution during heavy analytical scans?
    \\item What is the patent/licensing status of the ARC algorithm for production commercial software?
    \\item Meta: How do we plot parameter $p$ trends to observe real-time transitions in access behavior?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does ARC outperform LIRS (Low Inter-reference Recency Set) under typical OLTP databases?
    \\item How do we parallelize ARC list movements without using coarse-grained locks?
    \\item What is the effect of ghost cache scale limits on the adaptation convergence speed?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{capacity})$

\\begin{verbatim}
Access Key
 |
 +- Case 1: In T1 or T2 -> Move to T2
 +- Case 2: In B1 -> Increase Recency Target -> Pull to T2
 +- Case 3: In B2 -> Increase Frequency Target -> Pull to T2
 +- Case 4: Cache Miss -> Evict from T1/T2 based on size -> T1
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{29. TinyLFU (W-TinyLFU)}

\\begin{textbookalgo}{29.1}{AccessTinyLFU(key, val)}
\\begin{algorithm}[H]
$sketch.increment(key)$\\;
\\If{$\\text{window.contains}(key)$}{
  $\\text{window.access}(key)$\\;
  \\Return $\\text{get}(key)$\\;
}
\\If{$\\text{main.contains}(key)$}{
  $\\text{main.access}(key)$\\;
  \\Return $\\text{get}(key)$\\;
}
\\If{$\\text{window.size} == \\text{window\\_capacity}$}{
  $cand \\leftarrow \\text{window.get\\_eviction\\_candidate()}$\\;
  \\If{$\\text{main.size} == \\text{main\\_capacity}$}{
    $victim \\leftarrow \\text{main.get\\_eviction\\_candidate()}$\\;
    \\If{$sketch.estimate(cand) > sketch.estimate(victim)$}{
      $\\text{main.evict}(victim)$\\;
      $\\text{main.insert}(cand)$\\;
    }\\Else{
      $\\text{drop}(cand)$\\;
    }
  }
}
$\\text{window.insert}(key, val)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} In-memory application caches (e.g., Caffeine, Spring Boot caches) requiring near-optimal hit ratios with high concurrency.\\\\
\\textbf{How to use:} Combine a small LRU window cache (for burst tolerance) with a main cache guarded by a Count-Min Sketch filter.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How does the Count-Min Sketch reset/decay frequency counts to prevent historical data bias?
    \\item What is the hash collision rate impact on the admission filter's accuracy?
    \\item Meta: How do we trace query paths through the window and main segment splits?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Can we dynamically resize the LRU window size based on real-time hit ratios?
    \\item How does W-TinyLFU behave when cache memory footprint restrictions force tiny sketch sizes?
    \\item What is the impact of multi-threading on the Count-Min Sketch's atomic increment steps?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{capacity} + \\text{sketch\\_size})$

\\begin{verbatim}
New Key Candidate
 |
 +- Window Cache (LRU) full?
     +- Yes -> Eviction candidate vs Main Cache eviction candidate
                 +- Check Count-Min Sketch frequency
                 +- Win -> Insert Main Cache
                 +- Fail -> Evict Candidate
\\end{verbatim}
\\end{mathbox}
"""

with open("proof.tex", "r") as f:
    content = f.read()

# Let's locate the Redis Outage section and insert the new section just before it.
target_str = "%% =============================================================================\n\\section{Redis Outage"

if "Cache Eviction Policies" not in content:
    content = content.replace(target_str, eviction_latex + "\n" + target_str)
    print("Successfully added Eviction Policies section to proof.tex")
else:
    print("Eviction Policies already present in proof.tex")

with open("proof.tex", "w") as f:
    f.write(content)
