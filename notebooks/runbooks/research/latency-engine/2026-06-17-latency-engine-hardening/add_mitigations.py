import re

mitigations_latex = """
%% =============================================================================
\\section{Advanced Caching Mitigation Patterns}\\label{sec:caching-mitigations}
%% =============================================================================
To prevent catastrophic cache failures, stampedes, and data synchronization issues under high throughput, applications employ specific architectural mitigation patterns. This section details 12 advanced caching mitigation patterns.

\\begin{infobox}{Caching Mitigation Patterns Matrix}
\\small
\\centering
\\begin{tabularx}{\\textwidth}{lXX}
\\toprule
\\textbf{Pattern} & \\textbf{What problem it solves} & \\textbf{When to use it} \\\\
\\midrule
TTL + Jitter & Prevents synchronized expiry & Most caches \\\\
\\addlinespace
Versioned Keys & Avoids stale overwrite and simplifies invalidation & Deploys, schema changes \\\\
\\addlinespace
Singleflight & Stops duplicate concurrent queries for same key & Hot keys \\\\
\\addlinespace
Mutex on Miss & Ensures only one writer rebuilds expensive cache & Expensive cache fills \\\\
\\addlinespace
Stale-While-Revalidate & Serves stale data while refresh happens & UX-sensitive APIs \\\\
\\addlinespace
Negative Cache & Caches "not found" results briefly & Miss-heavy lookup paths \\\\
\\addlinespace
Bloom Filter Guard & Blocks repeated invalid-key DB hits & Large keyspaces \\\\
\\addlinespace
Two-Level Cache & L1 local + L2 Redis & Low latency plus shared cache \\\\
\\addlinespace
Hot-Key Replication & Spreads load for one popular key & Skewed traffic \\\\
\\addlinespace
Cache Warming & Preloads expected data & Deploys and traffic spikes \\\\
\\addlinespace
Read Repair & Fixes stale entries when detected & Eventually consistent systems \\\\
\\addlinespace
Soft TTL / Hard TTL & Allows controlled staleness with fallback & Production APIs \\\\
\\bottomrule
\\end{tabularx}
\\end{infobox}

\\clearpage
\\subsection{30. TTL + Jitter}

\\begin{textbookalgo}{30.1}{SetWithJitter(key, val, base\\_ttl)}
\\begin{algorithm}[H]
$jitter \\leftarrow \\text{random\\_uniform}(-0.1, 0.1) \\times base\\_ttl$\\;
$final\\_ttl \\leftarrow base\\_ttl + jitter$\\;
$\\text{cache.write}(key, val, final\\_ttl)$\\;
\\Return $\\text{success}$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Preventing synchronized cache stampedes where multiple keys expire at the exact same moment.\\\\
\\textbf{How to use:} Add a randomized time offset (jitter) to the base TTL when storing items in the cache.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item What is the optimal jitter ratio (e.g., 10\\%) to balance cache freshness against alignment?
    \\item How does jitter impact cache eviction metrics in high-turnover key namespaces?
    \\item Meta: How do we measure the variance in cache invalidation times under jitter?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does jitter affect replication sync times in master-replica cache topologies?
    \\item How does jitter interact with memory reclamation schedules in LFU systems?
    \\item Can we dynamically scale jitter based on real-time database query latency?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(1)$

\\begin{verbatim}
Calculate Expiry Time
 |
 +- Generate Random Jitter Interval
 +- Set Expiry = Base TTL + Jitter
 +- Save Key to Cache
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{31. Versioned Keys}

\\begin{textbookalgo}{31.1}{GetVersionedKey(base\\_key)}
\\begin{algorithm}[H]
$ver \\leftarrow \\text{cache.read}(\\text{"version:"} + base\\_key)$\\;
\\If{$ver == \\text{null}$}{
  $ver \\leftarrow \\text{db.read\\_version}(base\\_key)$\\;
  $\\text{cache.write}(\\text{"version:"} + base\\_key, ver)$\\;
}
$versioned\\_key \\leftarrow base\\_key + \\text{":"} + ver$\\;
\\Return $\\text{cache.read}(versioned\\_key)$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Avoiding stale overwrite issues and simplifying bulk cache invalidation during deployments or schema updates.\\\\
\\textbf{How to use:} Prefix or suffix your cache keys with a version number retrieved from a central location or configuration.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we prevent version lookup from becoming a single-point-of-failure database bottleneck?
    \\item What is the overhead of storing version metadata keys alongside actual data keys?
    \\item Meta: How do we trace trace context across version validation boundaries?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does versioned key generation increase memory fragmentation in key dictionaries?
    \\item How do we clean up orphaned historical key versions to prevent memory leaks?
    \\item Can we use logical timestamps instead of sequential numbers for versioning?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(1)$

\\begin{verbatim}
Read Versioned Key
 |
 +- Fetch Current Active Version
 +- Construct Key = BaseKey + ":" + Version
 +- Read Cache (VersionedKey)
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{32. Singleflight / Request Coalescing}

\\begin{textbookalgo}{32.1}{GetSingleflight(key)}
\\begin{algorithm}[H]
$val \\leftarrow \\text{cache.read}(key)$\\;
\\If{$val \\neq \\text{null}$}{\\Return $val$\\;}
\\If{$\\text{flight\\_table.contains}(key)$}{
  $listener \\leftarrow \\text{register\\_listener}(key)$\\;
  \\Return $\\text{await}(listener)$\\;
}
$\\text{flight\\_table.register}(key)$\\;
$val \\leftarrow \\text{db.read}(key)$\\;
$\\text{cache.write}(key, val)$\\;
$\\text{flight\\_table.broadcast\\_and\\_clear}(key, val)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Mitigating database overloading under heavy read concurrency during cache misses for hot keys.\\\\
\\textbf{How to use:} Maintain a flight registry of in-progress queries; merge duplicate keys into a single database transaction.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item What happens if the single query in flight fails or experiences a timeout?
    \\item How do we limit thread blocking times in the request merger queue?
    \\item Meta: How do we correlate multiple user trace IDs into the single database query span?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item How does request coalescing perform in distributed microservice architectures?
    \\item Does request coalescing affect downstream load balancer routing decisions?
    \\item Can we implement speculative execution where a second query is spawned if the first is slow?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(\\text{db\\_read})$ | Space: $O(\\text{flight\\_table})$

\\begin{verbatim}
Query Key
 |
 +- Key in Flight?
     +- Yes -> Register Listener -> Await Signal -> Return
     +- No -> Register Key in Flight -> Query DB -> Populate Cache -> Signal Listeners
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{33. Mutex on Miss}

\\begin{textbookalgo}{33.1}{GetMutexOnMiss(key)}
\\begin{algorithm}[H]
$val \\leftarrow \\text{cache.read}(key)$\\;
\\If{$val \\neq \\text{null}$}{\\Return $val$\\;}
\\If{$\\text{mutex.acquire}(key, \\text{timeout}=5)$}{
  $val \\leftarrow \\text{db.read}(key)$\\;
  $\\text{cache.write}(key, val)$\\;
  $\\text{mutex.release}(key)$\\;
  \\Return $val$\\;
}
$\\text{sleep}(100)$\\;
\\Return $\\text{GetMutexOnMiss}(key)$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Ensuring that exactly one writer rebuilds expensive cache blocks, protecting backend databases.\\\\
\\textbf{How to use:} Acquire a short-lived local or distributed lock on cache miss before fetching from the primary database.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we prevent deadlocks if the instance holding the mutex crashes?
    \\item What is the impact of lock contention on request timeouts under peak traffic?
    \\item Meta: How do we track mutex acquire times in our performance metrics?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does using distributed mutex locks add more latency than the database query itself?
    \\item How does lock leasing interact with database connection pools?
    \\item Can we implement adaptive sleep times based on historical lock duration?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(\\text{lock\\_acquire} + \\text{db\\_read})$ | Space: $O(1)$

\\begin{verbatim}
Cache Miss
 |
 +- Acquire Mutex Lock (Key)
     +- Success -> Query DB -> Update Cache -> Release Mutex
     +- Failure -> Sleep/Retry Cache Read
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{34. Stale-While-Revalidate}

\\begin{textbookalgo}{34.1}{GetStaleWhileRevalidateMitigation(key)}
\\begin{algorithm}[H]
$entry \\leftarrow \\text{cache.read\\_entry}(key)$\\;
\\If{$entry == \\text{null}$}{
  $val \\leftarrow \\text{db.read}(key)$\\;
  $\\text{cache.write\\_entry}(key, val)$\\;
  \\Return $val$\\;
}
\\If{$\\text{current\\_time()} > entry.soft\\_expiry \\land \\neg \\text{is\\_revalidating}(key)$}{
  $\\text{spawn\\_async\\_revalidation}(key)$\\;
}
\\Return $entry.val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} UX-sensitive APIs where zero-latency is preferred, and stale values are acceptable during background refresh.\\\\
\\textbf{How to use:} Write keys with both a soft and hard TTL, spawning background update threads when soft TTL is breached.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we manage background task queues when database responses slow down?
    \\item What is the maximum acceptable staleness window for our business domain?
    \\item Meta: How do we identify the proportion of requests served with stale data?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item How does stale serving affect API cache headers sent to downstream clients?
    \\item Does background revalidation increase overall write IOPS on the cache cluster?
    \\item Can we coordinate background refreshes to prevent redundant tasks across replicas?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ serve | Space: $O(1)$

\\begin{verbatim}
Query Key
 |
 +- Key in Cache?
     +- Yes -> Check Soft Expiration
                 +- Active -> Return
                 +- Expired -> Serve Stale -> Spawn Async DB Fetch
     +- No -> Sync DB Fetch -> Update Cache -> Return
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{35. Negative Cache}

\\begin{textbookalgo}{35.1}{GetNegativeCacheMitigation(key)}
\\begin{algorithm}[H]
$val \\leftarrow \\text{cache.read}(key)$\\;
\\If{$val == \\text{"SENTINEL\\_NULL"}$}{\\Return $\\text{null}$\\;
}
\\If{$val \\neq \\text{null}$}{\\Return $val$\\;}
$val \\leftarrow \\text{db.read}(key)$\\;
\\If{$val == \\text{null}$}{
  $\\text{cache.write}(key, \\text{"SENTINEL\\_NULL"}, \\text{ttl}=30)$\\;
}
\\Else{
  $\\text{cache.write}(key, val)$\\;
}
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Protecting databases from repetitive queries targeting non-existent identifiers (e.g. invalid user scans).\\\\
\\textbf{How to use:} Cache a temporary empty/null sentinel value for identifiers not found in the database.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we balance sentinel TTL duration with immediate availability when keys are created?
    \\item What is the impact of negative caching on lookup latency for newly signed up users?
    \\item Meta: How do we monitor malicious probing requests through negative cache hit spikes?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does negative cache size inflation threaten memory limits during automated attacks?
    \\item Can we use dynamic TTLs for negative caches depending on the request source?
    \\item How does negative caching interact with search index updates?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{sentinel\\_count})$

\\begin{verbatim}
Query Key
 |
 +- Sentinel Found? -> Return Null
 +- Cache Miss -> Query DB
                    +- Null -> Store Sentinel Value with short TTL
                    +- Result -> Store Result
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{36. Bloom Filter Guard}

\\begin{textbookalgo}{36.1}{GetBloomFilterGuard(key)}
\\begin{algorithm}[H]
\\If{$\\neg \\text{bloom\\_filter.contains}(key)$}{
  \\Return $\\text{null}$\\;
}
$val \\leftarrow \\text{cache.read}(key)$\\;
\\If{$val \\neq \\text{null}$}{\\Return $val$\\;}
$val \\leftarrow \\text{db.read}(key)$\\;
$\\text{cache.write}(key, val)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Large keyspaces where database query capacity is limited and a massive percentage of lookups targets non-existent keys.\\\\
\\textbf{How to use:} Evaluate key existence in a local in-memory Bloom filter before invoking cache or database lookups.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we handle deletions when items are removed from the primary database?
    \\item What is the false positive rate, and how does it scale with active key density?
    \\item Meta: How do we track Bloom filter memory allocation across our microservices?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does Bloom filter checking increase CPU latency inside critical event loop threads?
    \\item How do we replicate Bloom filter updates across distributed server processes?
    \\item Can we combine Bloom filters with Cuckoo filters to allow key deletion?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ check | Space: $O(\\text{filter\\_memory})$

\\begin{verbatim}
Query Key
 |
 +- Check Bloom Filter
     +- Absent -> Reject immediately (Return Null)
     +- Present -> Query Cache / Database
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{37. Two-Level Cache}

\\begin{textbookalgo}{37.1}{GetTwoLevelCacheMitigation(key)}
\\begin{algorithm}[H]
$val \\leftarrow \\text{l1\\_cache.read}(key)$\\;
\\If{$val \\neq \\text{null}$}{\\Return $val$\\;}
$val \\leftarrow \\text{l2\\_cache.read}(key)$\\;
\\If{$val \\neq \\text{null}$}{
  $\\text{l1\\_cache.write}(key, val)$\\;
  \\Return $val$\\;
}
$val \\leftarrow \\text{db.read}(key)$\\;
$\\text{l2\\_cache.write}(key, val)$\\;
$\\text{l1\\_cache.write}(key, val)$\\;
\\Return $val$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Optimizing retrieval latency in highly distributed architectures that require process-local performance plus shared state.\\\\
\\textbf{How to use:} Chain a process-local RAM cache (L1) with a shared distributed Redis/Memcached cluster (L2).
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we propagate cache invalidation messages to L1 caches on other nodes?
    \\item What is the eviction policy on L1 to prevent process out-of-memory crashes?
    \\item Meta: How do we observe the hit ratios of L1 vs L2 in our telemetry?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does L1-L2 cache inconsistency lead to race conditions in client UI states?
    \\item What is the GC pressure overhead of keeping thousands of objects in L1 memory?
    \\item How does network partition between L1 and L2 affect node stability?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ L1, $O(1)$ L2 | Space: $O(\\text{L1\\_cap} + \\text{L2\\_cap})$

\\begin{verbatim}
Query Key
 |
 +- Check L1 (In-Memory RAM)
     +- Hit -> Return
     +- Miss -> Check L2 (Distributed Redis)
                 +- Hit -> Write L1 -> Return
                 +- Miss -> Query DB -> Write L2 & L1 -> Return
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{38. Hot-Key Replication}

\\begin{textbookalgo}{38.1}{GetHotKeyReplica(key)}
\\begin{algorithm}[H]
\\If{$\\text{is\\_registered\\_hot\\_key}(key)$}{
  $idx \\leftarrow \\text{random\\_integer}(1, R)$\\;
  \\Return $\\text{cache.read}(key + \\text{":"} + idx)$\\;
}
\\Return $\\text{cache.read}(key)$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Spreading read load across multiple Redis nodes for a single, extremely popular cache key (skewed traffic).\\\\
\\textbf{How to use:} Write the hot key to multiple replica keys (e.g. key:1, key:2) and read from a random replica.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we identify which keys are hot enough to trigger replication dynamically?
    \\item What is the write overhead of updating all replicas when the hot key value changes?
    \\item Meta: How do we map hot-key replicas in our dashboard visualizations?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does hot-key replication increase overall memory footprint inside clustered environments?
    \\item How do we handle partial failures when writing to replica keys?
    \\item Can we implement consistent hashing to locate replicas instead of random selection?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(\\text{replicas} \\times \\text{size})$

\\begin{verbatim}
Read Hot Key
 |
 +- Generate Random Replica Index: 1 to R
 +- Query Key + ":" + Index
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{39. Cache Warming}

\\begin{textbookalgo}{39.1}{PrewarmCache(hot\\_keys\\_list)}
\\begin{algorithm}[H]
\\For{$key \\in hot\\_keys\\_list$}{
  $val \\leftarrow \\text{db.read}(key)$\\;
  $\\text{cache.write}(key, val)$\\;
}
\\Return $\\text{success}$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Preventing database outages or latency spikes immediately following deployments or planned traffic surges.\\\\
\\textbf{How to use:} Run script tasks during initialization to load predicted hot data into the cache before routing users.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we accurately determine which keys to pre-warm without caching dead data?
    \\item What is the impact of pre-warming on deployment duration and startup times?
    \\item Meta: How do we track cache hit ratios immediately post-deployment to verify warming?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does cache warming saturate database connections before the app starts accepting traffic?
    \\item How do we handle data updates that occur while the pre-warming script is running?
    \\item Can we use production access logs to dynamically generate the pre-warm key list?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(\\text{preload\\_count})$ | Space: $O(\\text{preload\\_count})$

\\begin{verbatim}
System Init / Deploy
 |
 +- Query Hot Datasets from DB
 +- Write Keys to Cache
 +- Start Traffic Ingress
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{40. Read Repair}

\\begin{textbookalgo}{40.1}{GetReadRepair(key)}
\\begin{algorithm}[H]
$values \\leftarrow \\text{parallel\\_read\\_nodes}(key)$\\;
$fresh\\_val \\leftarrow \\text{get\\_most\\_recent}(values)$\\;
\\For{$v \\in values$}{
  \\If{$v.timestamp < fresh\\_val.timestamp$}{
    $\\text{spawn\\_async\\_write}(v.node, key, fresh\\_val)$\\;
  }
}
\\Return $fresh\\_val.data$\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Fixing stale or corrupted cache entries upon detection in eventually consistent storage topologies.\\\\
\\textbf{How to use:} Verify consistency or version checksums during read paths and trigger background repairs on mismatch.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item What is the overhead of validating versions/checksums on every read query?
    \\item How do we resolve conflicts if timestamps from two replica nodes are identical?
    \\item Meta: How do we monitor read repair frequencies in our logging dashboard?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does read repair trigger write amplification on replica nodes under read-heavy loads?
    \\item How does read repair interact with distributed database transactional boundaries?
    \\item Can we use vector clocks to make version reconciliation more precise?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ read, $O(1)$ async write | Space: $O(1)$

\\begin{verbatim}
Read Key
 |
 +- Fetch from multiple nodes (or read-with-checksum)
 +- Detect stale/out-of-sync value
     +- Yes -> Serve fresh -> Spawn async update to stale node
     +- No -> Serve value
\\end{verbatim}
\\end{mathbox}

\\clearpage
\\subsection{41. Soft TTL / Hard TTL}

\\begin{textbookalgo}{41.1}{GetSoftHardTTL(key)}
\\begin{algorithm}[H]
$entry \\leftarrow \\text{cache.read}(key)$\\;
\\If{$entry == \\text{null}$}{\\Return $\\text{null}$\\;
}
\\If{$\\text{current\\_time()} < entry.soft\\_expiry$}{
  \\Return $entry.val$\\;
}
\\If{$\\text{current\\_time()} < entry.hard\\_expiry$}{
  \\If{$\\neg \\text{is\\_revalidating}(key)$}{
    $\\text{spawn\\_async\\_refresh}(key)$\\;
  }
  \\Return $entry.val$ (Stale served)\\;
}
$\\text{cache.delete}(key)$\\;
\\Return $\\text{null}$ (Hard expired)\\;
\\end{algorithm}
\\end{textbookalgo}

\\noindent
\\textbf{When to use:} Achieving controlled staleness fallbacks in production APIs without blocking user requests.\\\\
\\textbf{How to use:} Store a metadata wrapper containing soft and hard expiration markers on every write.
\\begin{itemize}[leftmargin=*]
  \\item[] \\textbf{Critical \\& Meta Questions:}
  \\begin{enumerate}
    \\item How do we dynamically configure the delta between soft and hard TTL?
    \\item What is the impact of hard expiry locks on high-throughput database writes?
    \\item Meta: How do we categorize metrics by soft-hit, soft-stale-hit, and hard-miss?
  \\end{enumerate}
  \\item[] \\textbf{Second-Order Questions:}
  \\begin{enumerate}
    \\item Does soft/hard TTL configuration degrade memory efficiency in Redis databases?
    \\item How does this strategy handle downstream API dependency failures during soft expiration?
    \\item Can we implement adaptive soft/hard TTL scaling depending on service health index?
  \\end{enumerate}
\\end{itemize}
\\medskip

\\begin{mathbox}{Complexity \\& Operational Diagram}
\\textbf{Complexity:} Time: $O(1)$ | Space: $O(1)$

\\begin{verbatim}
Read Key
 |
 +- Time < Soft TTL -> Serve Fresh
 +- Soft TTL <= Time < Hard TTL -> Serve Stale -> Trigger Async Refresh
 +- Time >= Hard TTL -> Purge Key -> Return Miss
\\end{verbatim}
\\end{mathbox}
"""

with open("proof.tex", "r") as f:
    content = f.read()

target_str = "%% =============================================================================\n\\section{Redis Outage"

if "Advanced Caching Mitigation Patterns" not in content:
    content = content.replace(target_str, mitigations_latex + "\n" + target_str)
    print("Successfully added Mitigations section to proof.tex")
else:
    print("Mitigations already present in proof.tex")

with open("proof.tex", "w") as f:
    f.write(content)
