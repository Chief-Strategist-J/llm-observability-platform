import re

# We will define a dictionary containing the tailored when_to_use, how_to_use, critical_questions, and second_order_questions for each of the 22 caching strategies.
strategy_details = {
    "1": {
        "when": "Read-heavy workloads with dynamic/unpredictable query patterns where primary database load must be reduced.",
        "how": "Check the cache first. If a hit occurs, return the data. On a miss, fetch from the database, write back to the cache, and return.",
        "critical": [
            "What is the maximum acceptable latency drift before cache invalidation occurs?",
            "How do we handle concurrent writes trying to invalidate the same keys in Redis?",
            "Meta: How does Cache Aside affect our tracing topology's span structure on a miss?"
        ],
        "second": [
            "How does cache warm-up behave when restarting an instances cluster under high load?",
            "Does the double hop (Cache check + DB check) during a miss exhaust database connection pools?",
            "How do we mitigate the thunderous herd effect if a hot key expires unexpectedly?"
        ]
    },
    "2": {
        "when": "Systems requiring a clean application layer where caching logic is completely delegated to an integration proxy/gateway.",
        "how": "Configure the cache provider with a custom cache loader plugin that automatically queries the database on miss.",
        "critical": [
            "How do we monitor connection starvation between the cache loader and the primary database?",
            "What happens if the cache provider's database connection pool experiences a timeout?",
            "Meta: How do we aggregate latency metrics when database queries are hidden behind the cache proxy?"
        ],
        "second": [
            "How does the cache proxy serialize database schema upgrades without introducing downtime?",
            "How do we handle database failover when the cache loader is holding open persistent sockets?",
            "Does delegating read paths to the cache layer limit our ability to optimize complex database joins?"
        ]
    },
    "3": {
        "when": "Write-heavy systems requiring strict data consistency between the cache and the primary database.",
        "how": "Perform writes to the cache and the primary database simultaneously. Block the client's write acknowledgement until both writes complete.",
        "critical": [
            "What is the impact of synchronous dual-writes on write latency metrics under peak throughput?",
            "How do we handle partial failures if the database write succeeds but the cache write fails?",
            "Meta: How do we propagate parent trace context across synchronous dual-write system boundaries?"
        ],
        "second": [
            "Does writing to cache on every write evict active read-heavy keys, degrading read hit ratios?",
            "How does Write Through behave when operating across multi-region database replication topologies?",
            "Can we use distributed transactions (2PC) to guarantee consistency without causing severe lock contention?"
        ]
    },
    "4": {
        "when": "Ultra-high write throughput applications where database write overhead must be decoupled from client request paths.",
        "how": "Write directly to the cache, queue an asynchronous flush task to the database in-memory, and immediately return success to the client.",
        "critical": [
            "How do we handle data loss if the cache node crashes before the queue is flushed to the database?",
            "What backpressure mechanisms are active when the write queue reaches maximum memory capacity?",
            "Meta: How do we trace asynchronous background database updates back to the originating user span?"
        ],
        "second": [
            "How do database constraint violations (e.g., unique key conflicts) bubble up to the client asynchronously?",
            "Does batching writes from the queue to the database trigger lock escalation in the database engine?",
            "How do we maintain linearizability when a read request occurs for a key that is still queued for flush?"
        ]
    },
    "5": {
        "when": "Applications where written data is rarely read immediately, avoiding cache pollution with non-hot keys.",
        "how": "Perform writes directly to the primary database, skipping the cache layer, and invalidate any existing cache entry.",
        "critical": [
            "How do we prevent immediate cache misses if a client reads data shortly after writing it?",
            "What is the overhead of cache invalidation messages sent across the network on every database write?",
            "Meta: How do we track the latency footprint of cache eviction calls compared to direct database writes?"
        ],
        "second": [
            "Does skipping the cache during writes lead to stale reads on replica databases due to replication lag?",
            "How does Write Around behave under high concurrent updates to the same row in the primary database?",
            "Can we combine Write Around with a probabilistic pre-warm strategy for predicted hot records?"
        ]
    },
    "6": {
        "when": "Predictable read patterns where hot keys must be kept fresh in the cache to avoid any database lookup latency.",
        "how": "Monitor key access times. When a key is requested near its expiration threshold, asynchronously query the database to refresh the cache.",
        "critical": [
            "What threshold of the key's TTL should trigger the asynchronous background refresh?",
            "How do we prevent concurrent background threads from refreshing the same key simultaneously?",
            "Meta: How do we measure the CPU overhead of background revalidation threads on the host container?"
        ],
        "second": [
            "How does Refresh Ahead handle sudden shifts in user traffic patterns that make old hot keys stale?",
            "Does background query traffic saturate database connection pools during low-traffic periods?",
            "How do we prioritize key refreshes when the background task scheduler queue becomes full?"
        ]
    },
    "7": {
        "when": "Dynamic datasets with a predictable lifespan where stale data can be tolerated for a bounded duration.",
        "how": "Attach a fixed Time-To-Live (TTL) to each cache entry when writing. Evict the key automatically once the TTL expires.",
        "critical": [
            "How do we determine the optimal TTL duration that balances cache hit ratio against data staleness?",
            "What eviction policy (e.g., passive eviction vs active scanning) does the cache engine use?",
            "Meta: How do we track TTL expiration rates in our observability dashboard to detect abnormal data cycles?"
        ],
        "second": [
            "Does synchronized key expiry cause database stampedes when a large batch of keys expires at once?",
            "How does network latency affect TTL enforcement across distributed client nodes?",
            "Can we dynamically adjust key TTLs based on real-time database load and query performance?"
        ]
    },
    "8": {
        "when": "User sessions, active shopping carts, or stateful client connections where data must persist only while actively used.",
        "how": "Reset the key's expiration timer to its full TTL window on every read or write access.",
        "critical": [
            "How do we prevent extremely hot keys from living in the cache indefinitely and consuming memory?",
            "What is the network round-trip overhead of updating expiration timers on every read command?",
            "Meta: How does Sliding Expiration influence memory footprint forecasts in high-concurrency environments?"
        ],
        "second": [
            "Does sliding expiration cause memory fragmentation in the cache engine over long-running sessions?",
            "How do we coordinate sliding session expiries when requests are distributed across multiple edge locations?",
            "What happens if the cache engine fails to extend the TTL due to temporary connection glitches?"
        ]
    },
    "9": {
        "when": "Time-sensitive configurations, event promotions, or strict compliance data that must expire at an exact wall-clock time.",
        "how": "Set a hard timestamp for key deletion. Delete the key when the current system time exceeds this timestamp.",
        "critical": [
            "How do we ensure clock synchronization (NTP) across cluster nodes to prevent premature cache eviction?",
            "What is the impact of hard expiries on downstream database instances if thousands of keys expire exactly at midnight?",
            "Meta: How do we audit hard expiries for security and regulatory compliance reports?"
        ],
        "second": [
            "How do we handle timezone transitions or leap seconds when scheduling absolute expiries?",
            "Does absolute expiration create systemic latency spikes in batch processing applications?",
            "Can we pre-warm the cache before the absolute expiry threshold to avoid user-facing misses?"
        ]
    },
    "10": {
        "when": "Workloads with frequent queries for non-existent records, preventing database resource exhaustion.",
        "how": "When a database query returns null, cache a sentinel value (e.g., 'ABSENT') with a short TTL to block repeated queries.",
        "critical": [
            "What is the optimal TTL for sentinel values to prevent caching 'not found' results too long if data is created?",
            "How do we distinguish between a legitimate null result and a temporary database connection error?",
            "Meta: How do we identify malicious scan attacks by monitoring negative cache hit rates?"
        ],
        "second": [
            "Does negative caching consume excessive cache memory if an attacker generates infinite random keys?",
            "How do we synchronize negative cache eviction when a previously non-existent record is newly created?",
            "What is the impact of negative caching on search index synchronization in distributed systems?"
        ]
    },
    "11": {
        "when": "Highly concurrent API endpoints where serving slightly stale data is acceptable in exchange for zero-latency lookups.",
        "how": "Define a soft TTL and a hard TTL. On soft TTL expiry, serve the cached value immediately, and trigger a background refresh.",
        "critical": [
            "What is the maximum age of stale data that the application layer can safely expose to users?",
            "How do we prevent background revalidation tasks from backing up if the database experiences a slowdown?",
            "Meta: How do we segment metric dashboards to show stale hits vs clean cache hits?"
        ],
        "second": [
            "Does serving stale data hide database connection drops or outages from active client sessions?",
            "How does Stale-While-Revalidate behave under memory pressure when the cache engine evicts keys before soft TTL?",
            "Can we implement probabilistic background revalidation to smooth out peak refresh traffic?"
        ]
    },
    "12": {
        "when": "Extremely high-concurrency systems where hot key expiration threatens to trigger massive database stampedes.",
        "how": "Merge concurrent read requests for the same missing key into a single database query, returning the result to all callers.",
        "critical": [
            "How do we design the in-memory locking mechanism to prevent thread pool exhaustion while waiting for results?",
            "What happens if the single coalesced query to the primary database fails or times out?",
            "Meta: How do we capture trace propagation headers when merging multiple user requests into one DB span?"
        ],
        "second": [
            "Does request coalescing introduce a latency penalty for the first request while waiting for others to join?",
            "How does request coalescing scale across distributed nodes where local requests cannot be merged easily?",
            "Can we combine request coalescing with negative caching to prevent database overload during bulk key scans?"
        ]
    },
    "13": {
        "when": "Expensive query workloads where only a single thread should rebuild a missing cache key to protect database stability.",
        "how": "Acquire a distributed lock (e.g., Redlock) on cache miss. The lock owner fetches from DB and updates cache; others sleep and retry.",
        "critical": [
            "What is the lease duration of the distributed lock, and how do we prevent deadlock if the worker dies?",
            "How do we configure the retry backoff and sleep interval to minimize client latency without polling too fast?",
            "Meta: How do we track distributed lock contention metrics to identify hot key bottlenecks?"
        ],
        "second": [
            "Does lock acquisition latency exceed database query latency for relatively simple, lightweight queries?",
            "How do we handle split-brain scenarios in the lock manager when verifying lock ownership?",
            "What is the impact of lock contention on the thread safety and event loop cycles of our service nodes?"
        ]
    },
    "14": {
        "when": "High-throughput systems where database query distribution must be smoothed out, avoiding synchronized cache stampedes.",
        "how": "Calculate a refresh probability using a randomized exponential decay formula based on key expiration time and read frequency.",
        "critical": [
            "How do we configure the scaling factor beta to balance background traffic against the risk of cache miss?",
            "Does calculation of the random logarithmic formula on every read impact service CPU overhead?",
            "Meta: How do we validate probabilistic models in staging environments under non-homogeneous workloads?"
        ],
        "second": [
            "Does probabilistic refresh work effectively for cold keys that are accessed extremely infrequently?",
            "How does the randomized formula behave under sudden, vertical traffic spikes (e.g., flash sales)?",
            "Can we leverage machine learning to dynamically optimize the probability parameters per key class?"
        ]
    },
    "15": {
        "when": "Web services facing potential cache-penetration attacks or scanning workloads for keys that do not exist.",
        "how": "Maintain a space-efficient Bloom filter containing all valid keys. Intercept all read requests, rejecting queries for absent keys.",
        "critical": [
            "What is the acceptable false positive rate for the Bloom filter, and how does it scale with filter memory size?",
            "How do we synchronize the Bloom filter in real time when new records are added to the database?",
            "Meta: How do we monitor false positive matches to detect Bloom filter degradation over time?"
        ],
        "second": [
            "How do we handle false positives when the database query returns null despite passing the Bloom filter?",
            "Can we use a Scalable Bloom Filter or Cuckoo filter to support key deletions without full filter reconstruction?",
            "What is the latency overhead of hashing keys multiple times in the Bloom filter check path?"
        ]
    },
    "16": {
        "when": "Highly distributed systems requiring both microsecond-level local access and shared cache consistency across nodes.",
        "how": "Check in-process RAM (L1) first. On miss, query distributed Redis (L2). On L2 miss, query DB and populate both L1 and L2.",
        "critical": [
            "How do we broadcast cache invalidation events to L1 caches on other nodes when a key is updated?",
            "What eviction policy (e.g., LFU, LRU) should be applied to the L1 cache to prevent in-process OOM?",
            "Meta: How do we trace cache misses across L1 and L2 layers to calculate tiered latency offsets?"
        ],
        "second": [
            "Does the broadcast of invalidation messages create a network storm under write-heavy workloads?",
            "How do we handle temporary network partitions between the local application node and the L2 cluster?",
            "What is the impact of GC pauses on the latency profile of the in-memory L1 cache?"
        ]
    },
    "17": {
        "when": "Services running in cluster environments where remote cache round-trips to Redis introduce a bottleneck.",
        "how": "Wrap a local in-process cache around the remote distributed cache, serving reads locally and validating freshness periodically.",
        "critical": [
            "How long can the local near cache remain out of sync with the distributed cache before consistency breaks?",
            "How do we handle near cache invalidation messages when service instances are dynamically autoscaled?",
            "Meta: How does Near Cache implementation affect trace-linking of metrics aggregated at the process level?"
        ],
        "second": [
            "Does the memory overhead of the near cache restrict the host container's capacity for request processing?",
            "How does near cache interact with connection pooling and pipeline optimization in the Redis client?",
            "Can we configure different near cache sizes and TTLs depending on the relative business value of different keys?"
        ]
    },
    "18": {
        "when": "Static assets, images, media streaming, or API responses distributed globally to reduce latency at the network edge.",
        "how": "Deploy caching reverse proxies (e.g., Cloudflare, CloudFront) at regional PoPs. Route requests to edge caches, fallback to origin.",
        "critical": [
            "How do we configure Cache-Control headers to optimize edge retention while preserving immediate invalidation capability?",
            "What is the cache hit ratio at the edge, and how does it affect origin server bandwidth costs?",
            "Meta: How do we inject trace headers to correlate requests across edge and origin server spans?"
        ],
        "second": [
            "How does the CDN handle CORS headers and pre-flight requests when serving cached content?",
            "What happens to edge routing when a primary CDN PoP experiences a localized network outage?",
            "How do we manage edge cache eviction for personalized content without degrading performance?"
        ]
    },
    "19": {
        "when": "Stateful applications, user authorization flows, or multi-step transactional processes requiring user identity retention.",
        "how": "Store session state objects in a fast, in-memory cache keyed by an encrypted session ID token passed via HTTP headers.",
        "critical": [
            "How do we secure session data in transit and at rest to comply with user privacy regulations (e.g., GDPR)?",
            "What fallback mechanism exists if the session cache cluster becomes unavailable during active user sessions?",
            "Meta: How do we monitor session duration and active connection profiles inside the cache topology?"
        ],
        "second": [
            "Does session caching present a vector for session fixation or hijacking attacks if token validation is weak?",
            "How does session cache scale when user session objects grow large due to nested metadata accumulation?",
            "Can we use sticky sessions at the load balancer to reduce session cache lookup overhead on local RAM?"
        ]
    },
    "20": {
        "when": "Repetitive, expensive SQL queries or heavy analytical database computations with static parameters.",
        "how": "Generate an MD5 hash of the SQL query string and bind parameters. Cache the returned rowset keyed by this hash value.",
        "critical": [
            "How do we invalidate query result caches when underlying database tables are modified by write transactions?",
            "What is the memory footprint of storing large rowsets in the cache compared to database memory usage?",
            "Meta: How do we observe database query engine execution times vs query cache retrieval latencies?"
        ],
        "second": [
            "Does query cache hashing handle formatting differences (e.g., spaces, casing) in the SQL query string?",
            "How does query caching behave when transactions are rolled back in the primary database?",
            "Can query result caching lead to dirty reads when executing complex multi-user privilege queries?"
        ]
    },
    "21": {
        "when": "Domain models, database-mapped entities, or rich object graphs retrieved frequently by ID in application code.",
        "how": "Serialize objects into standard formats (e.g., JSON, Protocol Buffers) and cache. Deserialize on read hit.",
        "critical": [
            "What is the serialization and deserialization CPU overhead compared to database query execution time?",
            "How do we manage class schema version compatibility when deserializing older objects from the cache?",
            "Meta: How do we track object instantiation rates and heap allocation profiles when reading from the cache?"
        ],
        "second": [
            "Does object caching break entity references or deep object graph structures in ORM frameworks?",
            "How do we handle updates to nested child objects when the parent object is cached as a flat string?",
            "Can we use reference caching instead of serialization for in-memory object caches to achieve sub-microsecond retrieval?"
        ]
    },
    "22": {
        "when": "Web rendering engines, dashboard panels, or micro-frontend architectures generating modular HTML pieces.",
        "how": "Cache rendered HTML fragments (e.g., header, footer, widgets) separately. Concatenate them with dynamic data on page load.",
        "critical": [
            "How do we separate static HTML fragments from dynamic, user-specific elements inside the page template?",
            "What is the page assembly overhead when combining dozens of cached fragments in the rendering engine?",
            "Meta: How do we track Core Web Vitals (e.g., LCP, FID) when serving assembled page fragments?"
        ],
        "second": [
            "How does fragment caching interact with server-side rendering (SSR) frameworks and edge rendering?",
            "What happens if one critical fragment (e.g., payment checkout form) fails to load from the cache?",
            "Can we use Edge Side Includes (ESI) to delegate fragment concatenation directly to the CDN layer?"
        ]
    }
}

with open("proof.tex", "r") as f:
    content = f.read()

# Let's write a python parser to insert the details into each textbookalgo environment or after it.
# Wait, we want to insert them right before \end{textbookalgo} or right after it?
# Placing them right after \end{textbookalgo} as regular LaTeX sections/lists is very clean and readable.
# Let's inspect where \end{textbookalgo} is located.
# We will match:
# \begin{textbookalgo}{N.1}{Caption}
# \begin{algorithm}[H]
# ...
# \end{algorithm}
# \end{textbookalgo}

for num, details in strategy_details.items():
    algo_num = f"{num}.1"
    
    # We want to find the matching \begin{textbookalgo}{N.1}{...} ... \end{textbookalgo} block
    # Note that the caption is dynamic, so we will match \begin{textbookalgo}{N.1}{.*?}\n\begin{algorithm}[H]\n.*?\n\end{algorithm}\n\end{textbookalgo}
    pattern = re.compile(
        r"(\\begin\{textbookalgo\}\{" + re.escape(algo_num) + r"\}\{([^\}]+)\}\s*\n"
        r"\\begin\{algorithm\}\[H\]\s*\n"
        r"(.*?)\n"
        r"\\end\{algorithm\}\s*\n"
        r"\\end\{textbookalgo\})",
        re.DOTALL
    )
    
    match = pattern.search(content)
    if match:
        full_algo_block = match.group(1)
        caption = match.group(2)
        
        # Build the extra details block
        crit_list = "\n".join([f"  \\item {q}" for q in details["critical"]])
        sec_list = "\n".join([f"  \\item {q}" for q in details["second"]])
        
        details_latex = (
            f"\\noindent\n"
            f"\\textbf{{When to use:}} {details['when']}\\\\\n"
            f"\\textbf{{How to use:}} {details['how']}\n"
            f"\\begin{{itemize}}[leftmargin=*]\n"
            f"  \\item[] \\textbf{{Critical \\& Meta Questions:}}\n"
            f"  \\begin{{enumerate}}\n"
            f"{crit_list}\n"
            f"  \\end{{enumerate}}\n"
            f"  \\item[] \\textbf{{Second-Order Questions:}}\n"
            f"  \\begin{{enumerate}}\n"
            f"{sec_list}\n"
            f"  \\end{{enumerate}}\n"
            f"\\end{{itemize}}\n"
            f"\\medskip\n"
        )
        
        # Replace the algorithm block to append the details right after it
        new_algo_block = full_algo_block + "\n\n" + details_latex
        content = content.replace(full_algo_block, new_algo_block)
        print(f"Added details for Strategy {num}: {caption}")
    else:
        print(f"Could not find textbookalgo block for Algorithm {algo_num}")

with open("proof.tex", "w") as f:
    f.write(content)
