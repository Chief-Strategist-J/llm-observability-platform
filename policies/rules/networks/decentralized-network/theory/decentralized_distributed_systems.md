The Foundation — What Makes a System Truly Decentralized

Most systems called "distributed" are not decentralized.

Distributed = workload split across multiple machines
              but a central authority controls those machines
              AWS, Google Cloud, your own k8s cluster
              these are distributed, not decentralized

Decentralized = no single entity controls the system
                any node can join or leave
                no node is trusted more than another
                the system continues if any node disappears
                including the node that built it

The difference is not technical — it is about control.
A system is only as decentralized as its most central component.

Common centralization points people miss:
  DNS         → you depend on ICANN / your registrar
  Bootstrap   → new nodes need to find existing nodes somehow
  Upgrade     → who decides when software updates?
  Key PKI     → who issues certificates?
  Governance  → who decides protocol rules?

A fully decentralized system has answers to all of these
that do not depend on any single party.

Part 1 — Theoretical Foundations

Formally:
  In a distributed system, during a network partition,
  you can guarantee either Consistency OR Availability.
  Never both simultaneously.

C — Consistency
  every read receives the most recent write
  or an error
  all nodes see the same data at the same time

A — Availability
  every request receives a response
  not guaranteed to be the most recent data
  system never refuses a request

P — Partition Tolerance
  system continues operating
  when network messages are dropped or delayed
  between nodes

Why P is not optional:
  network partitions always happen eventually
  cables fail, routers drop packets, data centers split
  a system that stops working on partition is not production-ready
  therefore P is mandatory
  therefore the real choice is always C vs A during partition

The tradeoff visualized:

PARTITION OCCURS
      │
      ▼
Node A ─────✗───── Node B
(has new write)    (has old data)

Request arrives at Node B:

CP system (choose consistency):
  Node B: "I cannot reach Node A to verify latest state"
  Node B: returns ERROR
  user gets error, but never stale data
  example: traditional RDBMS with synchronous replication
           ZooKeeper, etcd, HBase

AP system (choose availability):
  Node B: "I cannot reach Node A but I will respond"
  Node B: returns its current (potentially stale) data
  user gets response, but may be stale
  example: Cassandra, CouchDB, DynamoDB
           most blockchain systems (eventual consistency)

Neither is wrong. The choice depends on what failure mode
is less catastrophic for your specific use case.

Financial settlement:  CP — wrong balance is worse than no response
User feed:             AP — slightly stale feed is fine, error is not
AI trace storage:      AP — slightly stale trace is fine
AI model registry:     CP — wrong model version is catastrophic

PACELC — CAP Extended for Real Systems

CAP only describes behavior during partition.
Most of the time there is no partition.
PACELC extends CAP to normal operation:

If Partition → choose between A and C (CAP)
Else (normal) → choose between L (Latency) and C (Consistency)

Even without partition:
  strong consistency requires coordination between nodes
  coordination adds latency
  low latency means accepting some inconsistency

PACELC choices for each component of a decentralized system:

Component               Partition behavior    Normal behavior
─────────────────────────────────────────────────────────────
P2P gossip layer        PA (favor available)  EL (favor latency)
Consensus layer         PC (favor consistent) EC (favor consistent)
State storage           PC (favor consistent) EC (favor consistent)
Cache layer             PA (favor available)  EL (favor latency)
User-facing API         PA (favor available)  EL (favor latency)

Consistency Models — The Spectrum

Strongest → Weakest

Linearizability (strongest)
  operations appear instantaneous
  all nodes agree on a single timeline
  reading after write always returns that write
  cost: highest latency, requires coordination
  use: financial balances, leader election

Sequential Consistency
  all nodes see operations in same order
  but not necessarily real-time order
  cost: high latency
  use: distributed locks, consensus protocols

Causal Consistency
  causally related operations seen in order
  concurrent operations may be seen differently
  cost: medium latency
  use: collaborative editing, social feeds

Eventual Consistency (weakest practical)
  all nodes will eventually agree
  no guarantee on when
  reads may return stale data
  cost: lowest latency
  use: DNS, most blockchain state, caches

The blockchain consistency model:
  between blocks:     eventual consistency
  after finality:     linearizable (for finalized blocks)
  this is why finality matters —
  it is the transition from eventual to linearizable

Consensus Algorithms — Deep Comparison
The consensus problem:
  N nodes must agree on a single value
  even when some nodes are faulty or malicious
  even when the network drops messages

Two failure models:

Crash Fault Tolerance (CFT):
  nodes can crash and stop responding
  they do not send malicious messages
  assumption: failed nodes are honest but dead
  algorithms: Paxos, Raft, Multi-Paxos

Byzantine Fault Tolerance (BFT):
  nodes can behave arbitrarily
  send conflicting messages to different peers
  lie about their state
  coordinate with other malicious nodes
  assumption: f nodes out of n are actively malicious
  requirement: n > 3f (need 2/3+ honest nodes)
  algorithms: PBFT, Tendermint, HotStuff, Casper

Why BFT matters for decentralized systems:
  in a permissioned system you control all nodes → CFT sufficient
  in a decentralized system any node could be malicious → BFT required
  this is a hard requirement, not a nice-to-have

RAFT (CFT — understand this first, it's the foundation)

Roles: Leader, Follower, Candidate
Term: monotonically increasing election period

Leader election:
  follower times out waiting for heartbeat
  becomes candidate, increments term
  requests votes from all nodes
  first to get majority becomes leader

Log replication:
  client sends command to leader
  leader appends to its log
  leader sends AppendEntries to all followers
  followers append, respond success
  leader commits when majority responds
  leader notifies followers of commit

Safety guarantee:
  only one leader per term
  leader has all committed entries
  committed entries never lost

Liveness guarantee:
  system makes progress if majority of nodes alive
  n nodes tolerates (n-1)/2 failures

Weakness:
  not BFT — a malicious leader corrupts the system
  not suitable for untrusted participant sets


PBFT (BFT — Byzantine fault tolerant, higher cost)

Phases for each consensus round:
  1. Pre-prepare: leader broadcasts request with sequence number
  2. Prepare:     each node broadcasts prepare message
                  waits for 2f+1 prepare messages
  3. Commit:      each node broadcasts commit message
                  waits for 2f+1 commit messages
  4. Reply:       node executes request, replies to client

Safety: requires 3f+1 total nodes to tolerate f Byzantine nodes
Liveness: requires 2f+1 honest nodes online

Cost:
  O(n²) message complexity — every node talks to every node
  does not scale beyond ~100 nodes
  fine for permissioned validator sets
  not suitable for thousands of nodes

Where PBFT is used:
  Hyperledger Fabric (permissioned blockchain)
  early Tendermint versions
  enterprise blockchain systems

TENDERMINT (BFT — practical, production-grade)

Improvement over PBFT:
  same BFT safety guarantees
  better liveness properties
  explicit round structure
  deterministic leader rotation

Rounds:
  Propose:   designated proposer broadcasts block
  Prevote:   validators broadcast prevote for block or nil
  Precommit: if 2/3+ prevotes → broadcast precommit
  Commit:    if 2/3+ precommits → commit block, move to next height

Key property — instant finality:
  once a block is committed, it is final
  no probabilistic finality like PoW
  no reorgs after commit
  this is critical for financial applications

Validator rotation:
  round-robin by default
  weighted by stake for PoS variant
  if proposer is offline → timeout → next proposer

Safety guarantee:
  two conflicting blocks can never both be committed
  requires 1/3+ validators to equivocate (detectable, slashable)

Liveness guarantee:
  progress as long as 2/3+ validators online and honest
  if network partitions → may stall → recovers when partition heals

Used by:
  Cosmos ecosystem (Tendermint Core)
  Binance Chain
  Many PoS chains as consensus engine

HOTSTUFF (BFT — state of the art, linear message complexity)

Why it matters:
  PBFT: O(n²) messages per consensus round
  HotStuff: O(n) messages per round (linear)
  this makes BFT feasible at larger validator sets

Key innovation — threshold signatures:
  instead of every node sending to every node
  nodes send to leader who aggregates signatures
  one aggregated proof instead of n² individual messages

Phases (chained variant):
  each block vote is also a vote for the previous block
  three-chain rule: block is committed after three descendants
  pipelined — new block every round without waiting

Safety: same as Tendermint (2/3+ honest)
Liveness: same as Tendermint

Used by:
  Facebook's Diem (Libra)
  Aptos (DiemBFT variant)
  Flow blockchain
  Many modern PoS chains

For your custom chain:
  HotStuff or a variant is the right choice for permissioned validators
  it gives you BFT safety at manageable message complexity
  scales to hundreds of validators without O(n²) bottleneck

====================
Part 2 — P2P Network Design
Node Discovery — The Bootstrap Problem
The fundamental problem:
  new node wants to join network
  does not know any existing nodes
  needs at least one peer to bootstrap

Solutions ranked by decentralization:

1. Hardcoded bootstrap peers (least decentralized)
   list of known stable nodes in client config
   weakness: if those nodes go down → new nodes cannot join
   weakness: bootstrap node operators have power over network entry
   used by: Bitcoin (DNS seeds), Ethereum (hardcoded bootnodes)
   acceptable for: permissioned networks where you control validators

2. DNS-based discovery
   DNS record contains list of active peers
   new node queries DNS → gets peer list
   weakness: DNS is centralized (ICANN, registrar)
   strength: easy to update peer list without client changes
   used by: Bitcoin DNS seeds, Ethereum ENR records

3. DHT-based discovery (most decentralized)
   Distributed Hash Table — nodes collectively store peer info
   new node contacts any known peer → gets routed to relevant peers
   no central authority for peer discovery
   weakness: DHT poisoning attacks (malicious nodes insert bad data)
   strength: fully decentralized, scales to millions of nodes
   used by: BitTorrent, IPFS, Ethereum devp2p

4. Peer exchange (PEX)
   nodes share peer lists with each other
   new node → bootstrap peer → gets list of other peers
   → contacts those peers → gets more peers
   weakness: still needs initial bootstrap peer
   strength: very fast peer discovery after initial contact
   used by: most production P2P systems as complement to DHT

============
Kademlia DHT — The Standard
Structure:
  every node has a 160-bit node ID (SHA1 of public key)
  nodes are organized in a logical space by XOR distance
  XOR(nodeA_id, nodeB_id) = logical distance between A and B
  closer nodes in XOR space are responsible for similar data

K-buckets:
  each node maintains k-buckets for different distance ranges
  k-bucket = list of k closest known nodes at that distance
  when bucket is full → ping oldest node
  if alive → keep oldest, discard new (favors long-lived nodes)
  if dead → replace with new node
  this makes Kademlia naturally resistant to churn

Lookup algorithm:
  find node with ID x
  start with k closest known nodes to x
  iteratively query those nodes: "who is closest to x you know?"
  converges to the target node in O(log n) steps
  n = total nodes in network

Properties:
  O(log n) lookup time — scales to millions of nodes
  self-organizing — no central directory
  resilient to node failure — multiple paths to any destination
  resistant to some Sybil attacks (XOR routing limits manipulation)

===
Gossip Protocol — How Information Spreads
Problem: need to propagate a message to all nodes
         without knowing all nodes
         without a central broadcast server

Gossip (epidemic) protocol:
  node receives message
  randomly selects k peers from known peer list
  forwards message to those k peers
  each recipient does the same
  message spreads exponentially

Convergence time:
  O(log n) rounds to reach all nodes
  n = network size, k = fan-out

Variants:

Push gossip:
  node pushes message to k random peers immediately
  fast propagation
  high bandwidth (duplicates common)

Pull gossip:
  nodes periodically pull from k random peers
  lower bandwidth
  slower propagation
  good for state synchronization

Push-pull gossip (best for most cases):
  nodes push new messages immediately
  nodes periodically pull to catch missed messages
  fast initial propagation + eventual completeness

Anti-entropy (for state sync):
  nodes periodically compare state with peers
  exchange missing pieces
  convergence guaranteed
  used for: blockchain state sync, CRDT replication

For block propagation specifically:
  compact block relay (Bitcoin): send header + short txids
    receiver has most transactions already (from mempool)
    only requests missing transactions
    reduces bandwidth by 90%+

  IBLT (Invertible Bloom Lookup Tables):
    even more efficient — probabilistic set reconciliation
    sender and receiver sync only differences
    used by: Bitcoin Erlay proposal, some newer chains
===
Eclipse Attack — The Critical P2P Vulnerability

Attack:
  attacker controls enough nodes to surround target node
  all of target's peers are attacker-controlled
  target sees only attacker's view of the network
  attacker can: hide blocks, double-spend, censor transactions

Why it is critical:
  does not require breaking cryptography
  requires only enough nodes and network connections
  very practical attack against isolated validators

Mitigations:

1. Diverse peer connections
   maintain peers in multiple /16 IP subnets
   attacker must control IPs across many subnets
   Bitcoin uses this: max 1 peer per /16 subnet

2. Peer rotation
   periodically replace some peers with random new ones
   prevents long-term isolation
   balance: stability vs security

3. Authenticated peer connections
   peers sign their messages with known keys
   validator-to-validator: only connect to known validator IDs
   makes Sybil attacks much harder

4. Multiple independent peer discovery methods
   DHT + DNS seeds + hardcoded peers + peer exchange
   attacker must control all discovery channels simultaneously

5. Anomaly detection
   monitor: "am I seeing fewer blocks than expected?"
   monitor: "are all my peers in the same ASN?"
   alert: possible eclipse if suspicious patterns

==================
Part 3 — Fault Tolerance

Crash failure:
  node stops responding
  does not send any more messages
  cleanest failure — others detect via timeout
  CFT algorithms handle this

Omission failure:
  node selectively drops messages
  may receive but not respond
  or respond to some but not others
  harder to detect than crash

Byzantine failure:
  node behaves arbitrarily
  sends conflicting messages to different peers
  lies about state
  coordinates with other malicious nodes
  worst case — requires BFT algorithms

Network partition:
  subset of nodes cannot communicate with other subset
  both subsets may continue operating
  creates split-brain risk

Timing failure:
  messages arrive outside expected time window
  partially synchronous systems must handle this
  pure asynchronous systems assume no timing guarantees

==
The FLP Impossibility

Fischer, Lynch, Paterson (1985):
  In a fully asynchronous system with even one crash failure,
  it is impossible to guarantee consensus termination.

What this means practically:
  you cannot build a consensus algorithm that is:
  - safe (never returns wrong answer)
  - live (always eventually returns answer)
  - tolerant of even one crash
  simultaneously in a purely asynchronous network

How real systems get around it:
  partial synchrony assumption:
    network is asynchronous most of the time
    but there exist periods of synchrony (GST — Global Stabilization Time)
    after GST, messages arrive within known bound Δ
    Tendermint, HotStuff use this assumption

  randomization:
    random leader selection breaks the deterministic impossibility
    Ben-Or consensus uses randomization
    gives probabilistic liveness (almost certain to terminate)

This is why "blockchain solves consensus" is wrong.
Blockchains work around FLP, they do not solve it.
They make the same tradeoffs every distributed system makes.

Failure Detection

The fundamental problem:
  how do you know if a node has crashed vs. is slow vs. is malicious?
  you cannot distinguish these with certainty in async networks

Approaches:

Heartbeat timeout:
  nodes send periodic heartbeat messages
  if no heartbeat within timeout → assumed failed
  timeout too short: false positives (slow node looks crashed)
  timeout too long: slow failure detection
  production: adaptive timeouts that adjust to network conditions

Phi accrual failure detector (Cassandra):
  instead of binary failed/alive
  outputs a suspicion level φ
  φ increases as heartbeats are missed
  application decides threshold: "treat as failed when φ > 8"
  adapts to network jitter automatically

Gossip-based failure detection:
  nodes gossip their heartbeat counters
  if node X's counter stops increasing in gossip
  → X is suspected failed
  multiple nodes must agree before X is declared failed
  more robust than single-point detection

For validator sets specifically:
  validator performance is on-chain
  missed block proposals are recorded
  consistent missing → automatic slashing or removal
  no separate failure detector needed for consensus participation
  the consensus protocol itself is the failure detector
===
Split-Brain — The Most Dangerous Failure

Scenario:
  network partition splits validators into two groups
  Group A (3 validators) and Group B (3 validators)
  total = 6 validators, both groups have 50%

BFT requirement: need 2/3+ to commit
  Group A: 3/6 = 50% — cannot commit (below 2/3)
  Group B: 3/6 = 50% — cannot commit (below 2/3)
  system stalls — neither partition can make progress
  THIS IS CORRECT BEHAVIOR

Why stalling is correct:
  if both groups could commit independently
  they would commit different blocks
  you would have two incompatible chain histories
  this is worse than stalling
  BFT consensus chooses safety over liveness during partition

Recovery:
  partition heals
  nodes reconnect
  one chain history is correct (the one with 2/3+ validators)
  minority chain is discarded
  validators on minority chain may be slashed
  (they signed blocks that got orphaned)

The danger point:
  if you build a system that prioritizes availability during partition
  and two partitions both commit
  you have a real split-brain
  reconciliation is the hardest problem in distributed systems
  blockchain systems avoid this by choosing CP over AP at consensus layer

======
Part 4 — Decentralized Data

CRDT — Conflict-Free Replicated Data Types
Problem: multiple nodes update the same data concurrently
         without coordination
         how do you merge conflicting updates?

CRDT solution:
  data types designed so concurrent updates always merge correctly
  no coordination needed
  no conflicts possible — by mathematical design

Types:

G-Counter (grow-only counter):
  each node has its own counter slot
  increment: node increments its own slot only
  read: sum all slots
  merge: take max of each slot
  concurrent increments from different nodes: always merge correctly
  cannot decrement (grow-only)

PN-Counter (positive-negative counter):
  two G-Counters: P (increments) and N (decrements)
  value = sum(P) - sum(N)
  supports both increment and decrement
  concurrent updates always merge

LWW-Register (Last Write Wins):
  each write has a timestamp
  merge: keep the write with higher timestamp
  simple but: requires synchronized clocks
              concurrent writes lose one update

OR-Set (Observed-Remove Set):
  add elements with unique tags
  remove element: mark all observed tags as removed
  concurrent add + remove: add wins (observed-remove)
  merge: union of adds, remove only what was observed

Vector Clock:
  not a CRDT but enables CRDT reasoning
  tracks causality between events
  [nodeA: 3, nodeB: 2, nodeC: 5]
  if event X has clock [3,2,5] and event Y has [3,3,5]
  then Y happened after X (nodeB incremented between them)
  if [3,2,5] and [4,2,4] → concurrent (neither dominates)

Where CRDTs apply in decentralized systems:
  peer scores in P2P network (PN-Counter)
  validator uptime tracking (G-Counter per validator)
  feature flags across nodes (OR-Set)
  collaborative editing (text CRDTs like YATA, RGA)
  NOT for financial balances (need linearizability)

====
Merkle Trees — Data Integrity at Scale

Structure:
  leaf nodes: hash of data block
  internal nodes: hash of children's hashes
  root: single hash representing entire dataset

Properties:
  tamper-evident: change any data → root hash changes
  efficient proof: prove one leaf belongs to tree
                   with O(log n) hashes (not full tree)
  efficient sync: two nodes compare root hashes
                  if equal → identical data
                  if different → binary search to find differences

Merkle proof (inclusion proof):
  prove that transaction T is in block B
  provide: T, path of sibling hashes from T to root
  verifier: recompute hashes up the path
  if computed root = published root → T is in B
  proof size: O(log n) where n = number of transactions
  verification time: O(log n) hash computations

Merkle Patricia Trie (Ethereum state):
  combines Merkle tree (integrity) with Patricia trie (efficient lookup)
  key-value store where any value can be proven by key
  state root = single hash representing all account balances + storage
  used to prove: "account X has balance Y at block Z"
  without downloading entire state

Verkle Trees (next generation):
  replace Merkle Patricia Trie in Ethereum's roadmap
  smaller proofs: O(1) proof size vs O(log n)
  uses vector commitments instead of hash trees
  critical for: stateless clients (verify without full state)

Content-Addressed Storage

Traditional storage:
  data stored at location (URL, path)
  you trust the location to return correct data
  location can change, be deleted, return different data

Content-addressed storage:
  data is addressed by its hash
  hash(data) = address
  requesting hash X → guaranteed to receive data with hash X
  or nothing
  cannot receive wrong data for a given address
  location is irrelevant — any node with the data can serve it

IPFS (InterPlanetary File System):
  content-addressed, P2P file storage
  add file → get CID (Content Identifier = hash of content)
  retrieve CID → get file from any node that has it
  data is immutable by address
  updating = new CID (old data still accessible)

Why it matters for decentralized systems:
  smart contract code: stored by hash → cannot be silently changed
  off-chain data referenced on-chain: hash on chain, content on IPFS
  anyone can verify on-chain hash matches off-chain content
  no central storage server that can be taken down

Pinning problem:
  IPFS only keeps data if someone is "pinning" it
  nobody pinning → data disappears (garbage collected)
  solution: pinning services (Pinata, Infura) — introduces centralization
  better solution: Filecoin (pay nodes to store data permanently)
  or: run your own pinning infrastructure

===
Part 5 — The Full Structure

decentralized-system/
│
├── theory/                            ← not code — documented decisions
│   ├── cap-choices.md                 ← per component: CP or AP, why
│   ├── consistency-model.md           ← what consistency each layer provides
│   ├── failure-assumptions.md         ← CFT or BFT, why, what f value
│   └── trust-model.md                 ← who trusts whom, what is assumed honest
│
├── p2p/
│   ├── identity/
│   │   ├── node-id/                   ← how node IDs are generated
│   │   │                                 public key → hash → node ID
│   │   ├── key-management/            ← node key generation, rotation
│   │   └── peer-verification/         ← how peers prove their identity
│   │
│   ├── discovery/
│   │   ├── bootstrap/                 ← initial peer list, DNS seeds
│   │   ├── dht/                       ← Kademlia implementation
│   │   │   ├── routing-table/         ← k-bucket management
│   │   │   ├── lookup/                ← iterative node lookup
│   │   │   └── storage/               ← what DHT stores (peer records)
│   │   └── peer-exchange/             ← PEX protocol
│   │
│   ├── transport/
│   │   ├── protocols/                 ← TCP, QUIC, WebRTC adapters
│   │   │                                 each behind transport interface
│   │   ├── multiplexing/              ← multiple streams per connection
│   │   ├── encryption/                ← Noise protocol or TLS 1.3
│   │   └── nat-traversal/             ← hole punching for NAT peers
│   │
│   ├── gossip/
│   │   ├── protocol/                  ← push-pull gossip implementation
│   │   ├── message-types/             ← what gets gossiped (blocks, txs, etc)
│   │   ├── deduplication/             ← seen-message cache
│   │   └── fan-out/                   ← how many peers per gossip round
│   │
│   └── security/
│       ├── eclipse-prevention/        ← subnet diversity, peer rotation
│       ├── sybil-resistance/          ← proof of work / stake for peer IDs
│       └── rate-limiting/             ← per-peer message rate limits
│
├── consensus/
│   ├── interface/                     ← language-agnostic consensus API
│   │
│   ├── failure-detector/
│   │   ├── heartbeat/                 ← basic timeout-based detection
│   │   ├── phi-accrual/               ← adaptive suspicion level
│   │   └── gossip-based/              ← distributed failure detection
│   │
│   ├── leader-election/
│   │   ├── round-robin/               ← deterministic rotation
│   │   ├── vrf-based/                 ← verifiable random function
│   │   └── stake-weighted/            ← weighted by validator stake
│   │
│   ├── engines/
│   │   ├── raft/                      ← CFT, understand fundamentals
│   │   ├── pbft/                      ← BFT, O(n²) — small validator sets
│   │   ├── tendermint/                ← BFT, instant finality
│   │   └── hotstuff/                  ← BFT, O(n) — large validator sets
│   │
│   ├── safety/
│   │   ├── equivocation-detection/    ← detect double-signing
│   │   ├── slashing/                  ← penalize Byzantine validators
│   │   └── fork-choice/               ← how to pick canonical chain
│   │
│   └── liveness/
│       ├── timeout-management/        ← adaptive timeouts
│       ├── view-change/               ← replace failed leader
│       └── recovery/                  ← rejoin after crash
│
├── data/
│   ├── state/
│   │   ├── model/                     ← what state the system maintains
│   │   ├── trie/                      ← Merkle Patricia Trie or Verkle
│   │   ├── snapshots/                 ← periodic state snapshots
│   │   └── pruning/                   ← remove old state to save space
│   │
│   ├── replication/
│   │   ├── sync-protocol/             ← how new nodes sync chain state
│   │   │   ├── fast-sync/             ← download state snapshot
│   │   │   ├── full-sync/             ← replay all blocks from genesis
│   │   │   └── light-sync/            ← headers only + proofs on demand
│   │   └── anti-entropy/              ← background state reconciliation
│   │
│   ├── crdt/
│   │   └── types/                     ← per use case: counter, set, register
│   │
│   ├── content-addressed/
│   │   ├── storage/                   ← IPFS or equivalent integration
│   │   └── pinning/                   ← ensure data persistence
│   │
│   └── integrity/
│       ├── merkle-proofs/             ← inclusion proof generation
│       └── verification/              ← proof verification
│
├── fault-tolerance/
│   ├── chaos/
│   │   ├── scenarios/                 ← documented failure scenarios
│   │   │   ├── single-node-crash/
│   │   │   ├── network-partition/
│   │   │   ├── byzantine-validator/
│   │   │   ├── eclipse-attack/
│   │   │   └── split-brain/
│   │   └── tests/                     ← automated fault injection tests
│   │
│   ├── recovery/
│   │   ├── node-rejoin/               ← how crashed node rejoins
│   │   ├── partition-recovery/        ← what happens when partition heals
│   │   └── state-repair/              ← fix corrupted state
│   │
│   └── monitoring/
│       ├── liveness-checks/           ← is consensus making progress?
│       ├── safety-invariants/         ← are safety properties holding?
│       └── network-health/            ← P2P network metrics
│
└── security/
    ├── threat-model/                  ← documented attacker capabilities
    │                                     what attacker can do, what they cannot
    ├── attack-vectors/
    │   ├── sybil/                     ← fake identity attacks
    │   ├── eclipse/                   ← network isolation attacks
    │   ├── long-range/                ← history rewrite attacks (PoS)
    │   ├── nothing-at-stake/          ← PoS specific
    │   └── 51-percent/                ← majority control attacks
    └── mitigations/
        └── per-attack/                ← one folder per attack vector

==============
The Three Laws That Govern All of This
Law 1 — You cannot eliminate the CAP tradeoff
  you can only choose which failure mode is less catastrophic
  choose based on your use case, not on what sounds better

Law 2 — Decentralization has a cost
  every degree of decentralization adds:
    latency (coordination takes time)
    complexity (more failure modes)
    cost (more infrastructure)
  the benefit must justify the cost for each component
  not everything should be decentralized

Law 3 — Security assumptions compound
  if your P2P layer assumes honest majority
  and your consensus layer assumes honest supermajority
  and your data layer assumes correct replication
  your system is only as secure as the weakest assumption
  document every assumption explicitly
  a system with undocumented assumptions
  is a system with unknown security properties