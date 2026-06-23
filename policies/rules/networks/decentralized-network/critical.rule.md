Traditional system thinking:
  packages = services that serve requests
  network = how services find each other
  database = where state lives
  gateway = how users reach services

Blockchain system thinking:
  packages = either protocol participants OR protocol clients
  network = trustless message passing with Byzantine assumptions
  database = replicated state machine that nobody owns
  gateway = RPC layer — READ ONLY for most packages

This is not a migration of technology.
This is a migration of trust model.

Traditional: you trust your infrastructure
Blockchain:  infrastructure is designed to be untrusted
             correctness is guaranteed by protocol, not by ops

====================================================================             
They build the execution layer before the consensus layer is stable.
Then they find a consensus bug after the execution layer is built on top.
Fixing the consensus bug breaks the execution layer assumptions.
Everything gets rebuilt.

The rule: consensus correctness is a prerequisite, not a parallel track.
          do not write a single line of execution layer code
          until consensus has passed Byzantine fault tolerance testing
          under network partition, validator failure, and equivocation scenarios.

This is not a process recommendation.
It is the difference between a chain that survives its first attack
and one that does not.
========
Step 0 — Classify Every Package
infra-migration/
└── classification/
    └── registry.yaml

Classification A — BECOMES A NODE
  Definition: package participates in the protocol itself
  Examples:
    - transaction validator
    - block producer
    - state indexer
    - bridge relayer
    - sequencer (L2)
  Result: package is rewritten as a chain node type
  Migration complexity: HIGH — fundamental rewrite
  Timeline: months per package

Classification B — BECOMES A CLIENT
  Definition: package reads/writes to chain via RPC
  Examples:
    - user-facing API
    - payment processor
    - notification service
    - analytics service
    - CRM (your Angular app)
  Result: package gets a chain SDK, talks to RPC node
  Migration complexity: MEDIUM — API layer change
  Timeline: weeks per package

Classification C — BECOMES A CONTRACT
  Definition: package's core logic moves on-chain
  Examples:
    - settlement logic
    - access control
    - token management
    - governance voting
  Result: package logic is rewritten as smart contract
  Migration complexity: VERY HIGH — formal verification needed
  Timeline: months per contract + audit time

Classification D — STAYS TRADITIONAL
  Definition: package has no reason to touch the chain
  Examples:
    - email service
    - file storage
    - internal tooling
    - observability stack
  Result: no migration needed
  Migration complexity: NONE
  Timeline: zero

# infra-migration/classification/registry.yaml
# Fill this before any migration work begins

packages:
  <package-1>:
    classification: B          # CLIENT
    reason: "user-facing API, reads chain state, submits transactions"
    current-state: TRADITIONAL
    target-state: CHAIN-CLIENT
    priority: 2
    owner: chief

  <package-2>:
    classification: A          # NODE
    reason: "validates transactions, participates in consensus"
    current-state: TRADITIONAL
    target-state: VALIDATOR-NODE
    priority: 1                # nodes migrate before clients
    owner: chief

  <package-3>:
    classification: C          # CONTRACT
    reason: "settlement logic must be trustless, on-chain"
    current-state: TRADITIONAL
    target-state: SMART-CONTRACT
    priority: 3                # contracts deploy after nodes are stable
    owner: chief

  <package-n>:
    classification: D          # STAYS TRADITIONAL
    reason: "email delivery, no chain interaction needed"
    current-state: TRADITIONAL
    target-state: TRADITIONAL
    priority: null
    owner: chief

The Mapping — Existing Layers to Chain Layers

EXISTING SYSTEM                    BLOCKCHAIN EQUIVALENT
───────────────────────────────────────────────────────────

Docker network / k8s namespace  →  P2P network segment
  isolated per service              isolated per node type
  controlled ingress/egress         controlled peer connections
  bridge policies for migration     bootstrap peers for discovery

Gateway (nginx/traefik/envoy)   →  RPC Gateway
  routes external traffic           routes external RPC calls
  rate limits per tier              rate limits per API key / IP
  TLS termination                   TLS termination
  auth token validation             API key / JWT validation
  BUT: does NOT touch consensus     CRITICAL: gateway is read-only path
                                    it never touches validator network

Service-to-service calls        →  Contract calls or RPC calls
  package-A calls package-B         client calls contract function
  direct HTTP/gRPC                  via signed transaction or eth_call
  synchronous                       asynchronous (tx confirmation)
  rollback on error                 no rollback — chain is append-only

Shared database                 →  Chain state (replicated)
  one DB, multiple writers          all nodes hold identical state
  you control schema changes        schema changes = hard fork
  migrations are internal           migrations are governance votes
  rollback possible                 rollback IMPOSSIBLE after finality

Per-service database            →  Contract storage
  isolated, owned by service        isolated, owned by contract address
  SQL/NoSQL queries                 key-value storage with Merkle proof
  no external verification          any node can verify any value

Message queue                   →  Transaction mempool
  async job processing              pending transaction pool
  guaranteed delivery               probabilistic inclusion (fee-based)
  you control ordering              validator controls ordering (MEV risk)

CI/CD pipeline                  →  Chain upgrade governance
  deploy new version                propose hard fork
  instant rollout                   requires validator vote + activation block
  rollback in minutes               NO ROLLBACK after activation block

Config management               →  On-chain governance parameters
  environment variables             governance contract parameters
  changed by ops team               changed by validator vote
  instant effect                    effect at next epoch or block height

Migration Order — Derived from Dependencies

The rule is the same as traditional migration:
  migrate what has no dependencies first
  migrate what everything depends on last

BUT blockchain adds a new constraint:
  nodes must exist and be stable
  before clients can migrate to use them
  before contracts can deploy on them

Forced order:

STAGE 1 — Infrastructure (no chain dependency)
  Deploy chain node infrastructure
  P2P network up
  Genesis block created
  Testnet stable (minimum 30 days)

STAGE 2 — Node packages (Classification A)
  Packages that become nodes migrate here
  They join the testnet first
  Mainnet only after testnet validation

STAGE 3 — Contract packages (Classification C)
  Packages that become contracts deploy here
  Contracts need stable node network to deploy on
  Audits must complete before mainnet deployment

STAGE 4 — Client packages (Classification B)
  Packages that become clients migrate here
  They need contracts to exist to call
  They need RPC nodes to connect to

STAGE 5 — Traditional packages (Classification D)
  No migration needed
  May need config updates to call new client packages
  Not a chain migration concern

How Each Classification Migrates

Classification A — Package Becomes a Node

CURRENT STATE:
  packages/<package-name>/
    docker-compose.yml
    src/
    Dockerfile

PROBLEM:
  this package's logic needs to participate in consensus
  or validate transactions
  or sequence L2 batches
  it cannot do this as a traditional service

MIGRATION PATH:

Step 1 — Identify what protocol role it plays
  Is it a validator? → consensus/engines/<chosen-engine>/
  Is it a sequencer? → l2/sequencer/
  Is it an indexer?  → rpc/indexer/
  Each role has different network requirements

Step 2 — Extract the domain logic
  The business logic inside this package
  that is NOT protocol-specific
  moves to a library
  The protocol wrapper is built around it

Step 3 — Build the node wrapper
  P2P connectivity (libp2p or chosen library)
  Chain protocol messages (block gossip, tx gossip)
  Consensus participation (if validator)
  State sync on startup

Step 4 — Key management
  Validator keys are NOT environment variables
  They live in HSM or secure key management
  NEVER in docker-compose.yml or k8s secrets
  This is a hard requirement — not optional

Step 5 — Dual-run period
  Old package still handles traditional workload
  New node runs on testnet in parallel
  Only when node is validated on testnet
  does old package get decommissioned

TARGET STATE:
  chain/
    p2p/                    ← package's networking rewritten here
    consensus/engines/      ← package's validation logic lives here
  infra/
    nodes/<node-type>/      ← deployment config for this node

=========
Classification B — Package Becomes a Client
CURRENT STATE:
  packages/<package-name>/
    src/
      service.ts            ← calls other internal services directly
      database.ts           ← reads/writes to internal DB

PROBLEM:
  this package's data will move to chain state
  its calls to other services will become contract calls
  its database reads will become RPC calls

MIGRATION PATH:

Step 1 — Identify every data dependency
  What data does this package read?
  What data does this package write?
  Which of that data will live on-chain?
  Which stays traditional?

Step 2 — Add chain SDK as a dependency
  package gets an SDK for your chain
  sdk/
    <language>/
      client.ts             ← connects to RPC node
      contracts/            ← typed contract interfaces
      transactions/         ← transaction building + signing

Step 3 — Dual data layer (CRITICAL — this is your zero-downtime mechanism)
  package reads from BOTH traditional DB and chain
  package writes to BOTH traditional DB and chain
  reads: traditional DB is primary, chain is secondary (verification)
  writes: traditional DB first, chain second (async)

  This is not permanent.
  It is the migration bridge for data.
  Duration: until chain data is verified complete and consistent

Step 4 — Flip the read primary
  chain becomes primary for reads
  traditional DB becomes secondary (fallback)
  monitor: any fallback hit = data gap on chain
  fix gaps before proceeding

Step 5 — Remove traditional write path
  writes go to chain only
  traditional DB becomes read-only archive
  monitor: no writes hitting traditional DB

Step 6 — Decommission traditional DB
  only after step 5 is stable for minimum 30 days
  archive data to cold storage before deletion
  deletion is irreversible — treat as decommission, not cleanup

TARGET STATE:
  packages/<package-name>/
    src/
      service.ts            ← calls contracts via SDK
      chain-client.ts       ← RPC connection, query, tx submission
    chain/
      contracts/            ← contract ABIs this package uses
      queries/              ← read patterns (eth_call, getLogs)
      transactions/         ← write patterns (signed tx submission)

============================
Classification C — Package Becomes a Contract
CURRENT STATE:
  packages/<package-name>/
    src/
      settlement.ts         ← business logic that determines who gets paid
      access-control.ts     ← who can do what

PROBLEM:
  this logic needs to be trustless
  nobody — including you — should be able to manipulate it
  it needs to be verifiable by any participant
  it needs to be immutable after deployment

THIS IS THE HARDEST MIGRATION.
Not because the code is complex.
Because the mindset is completely different.

MIGRATION PATH:

Step 1 — Formal specification first
  write the logic in plain language
  every rule, every edge case, every exception
  this becomes the specification the contract is tested against
  DO NOT write contract code before this is complete

Step 2 — Rewrite in contract language
  EVM path: Solidity or Vyper
  WASM path: Rust (ink!) or AssemblyScript
  the rewrite is not a translation
  it is a reimplementation against the specification

Step 3 — Test coverage requirement
  100% branch coverage is the minimum, not the goal
  property-based testing (fuzzing) is required
  invariant testing: what must ALWAYS be true regardless of input
  DO NOT deploy without this

Step 4 — Audit
  internal audit: your team reviews against specification
  external audit: third-party security firm
  timeline: 6-12 weeks for a thorough audit
  cost: significant — budget for this

Step 5 — Testnet deployment + monitoring
  deploy on testnet
  run old package and new contract in parallel
  compare outputs for every operation
  minimum 30 days of parallel running

Step 6 — Mainnet deployment with time-lock
  upgrade mechanism: proxy pattern with time-lock
  any upgrade requires 48-72h delay
  delay gives users time to exit if they disagree
  NO UPGRADES without time-lock — this is a security requirement

Step 7 — Gradual volume migration
  route 5% of operations through contract
  compare results with old package
  increase percentage as confidence grows
  same pattern as traffic migration — just for operations

TARGET STATE:
  chain/
    contracts/
      core/
        <contract-name>/
          spec.md           ← formal specification
          contract.*        ← implementation
          tests/
          audits/
  packages/<package-name>/
    src/                    ← now just a thin client calling the contract

============
Why This Is Critical — The Real Reasons

Traditional system at 10M users:
  users trust YOU to not manipulate their data
  users trust YOUR database to be accurate
  users trust YOUR settlement logic to be fair
  if you make a mistake or act maliciously — they have no recourse

Blockchain system at 10M users:
  settlement logic is on-chain — you cannot change it arbitrarily
  state is replicated — you cannot secretly modify it
  every operation is auditable — manipulation is visible
  users verify, they do not trust

For any package handling:
  - financial transactions
  - access control
  - ownership records
  - voting / governance
  - identity

the blockchain model removes YOU as a trust requirement
this is not a technical benefit — it is a product benefit
it changes what users are willing to do on your platform

Reason 2 — State Integrity at Scale

Traditional system:
  10M users → database under load → replication lag
  replication lag → different services see different state
  different state → consistency bugs
  consistency bugs at 10M users = large-scale data integrity issues

Blockchain system:
  10M users → transactions in mempool
  consensus decides order → all nodes process same order
  all nodes arrive at identical state
  no replication lag — state is only final after consensus

The tradeoff:
  traditional: low latency, potential inconsistency
  blockchain: higher latency, guaranteed consistency

For packages where consistency matters more than latency:
  blockchain model is strictly better
  for packages where latency matters more than consistency:
  stay traditional (Classification D)

Reason 3 — Upgrade Safety

Traditional system:
  deploy new version → instant effect
  rollback: re-deploy old version
  users experience change immediately
  you control the upgrade

Blockchain system:
  propose upgrade → governance vote → activation block
  no rollback after activation block
  users see upgrade coming, can exit if they disagree
  protocol controls the upgrade

This sounds slower. It is.
But at 10M users with financial logic:
  a bad upgrade to traditional system = you discover the bug after damage
  a bad upgrade to blockchain = governance catches it before activation
  the slow process IS the safety mechanism

======
The Data Migration — Most Critical Part
Data migration in traditional systems:
  pause writes → export → transform → import → verify → resume writes
  if it fails: restore from backup
  window: hours

Data migration to blockchain:
  you cannot pause a blockchain
  you cannot "restore from backup" — chain is append-only
  migration IS a series of transactions
  each transaction is permanent

This is why data migration to blockchain is irreversible.
==========
Data Migration Pattern — Per Package
For every package with Classification B or C:

Phase 1 — Shadow writes (no reads from chain yet)
  every write to traditional DB also submits a chain transaction
  chain state builds up in parallel
  no user impact — they still read traditional DB

Phase 2 — Verify parity
  compare traditional DB state vs chain state
  every record, every value
  automated: run verification script continuously
  human: spot check random samples daily
  duration: minimum 14 days before proceeding

Phase 3 — Flip reads (chain becomes primary)
  reads now go to chain first
  traditional DB is fallback
  any fallback hit = gap in chain data = stop and investigate

Phase 4 — Remove traditional write path
  writes go to chain only
  traditional DB freezes (read-only)
  monitor for 30 days

Phase 5 — Archive traditional DB
  export to cold storage
  verify archive is complete
  delete live DB

NEVER skip Phase 2 verification.
NEVER compress Phase 4 duration below 30 days.
These two rules prevent irreversible data loss.

=======
Folder Structure — Combined System

root/
│
├── packages/                          ← your existing 30+ packages
│   └── <package-name>/
│       ├── src/
│       ├── chain/                     ← added during migration
│       │   ├── client/                ← RPC connection (Classification B)
│       │   ├── contracts/             ← contract interfaces used
│       │   └── transactions/          ← tx building patterns
│       ├── CONTRACT.md                ← existing network contract
│       ├── CHAIN-CONTRACT.md          ← new: chain interaction contract
│       │                                declares: which contracts called
│       │                                         which RPC methods used
│       │                                         read vs write operations
│       └── classification.yaml        ← A/B/C/D + migration state
│
├── chain/                             ← new — the blockchain itself
│   ├── p2p/
│   ├── consensus/
│   ├── execution/
│   ├── vm/
│   ├── l2/
│   ├── rpc/
│   ├── contracts/
│   │   └── core/
│   │       └── <contract-name>/
│   │           ├── spec.md
│   │           ├── src/
│   │           ├── tests/
│   │           └── audits/
│   └── sdk/
│       └── <language>/
│
├── infra/
│   ├── network/                       ← existing — updated for chain nodes
│   │   ├── topology/
│   │   │   └── segments.md            ← add: validator-segment, rpc-segment
│   │   └── isolation/
│   │       └── per-segment/
│   │           ├── validator/         ← STRICT: never public-facing
│   │           ├── rpc-node/          ← public read, rate limited
│   │           └── <existing>/        ← unchanged
│   │
│   ├── gateway/                       ← existing — add RPC routing
│   │   └── routing/
│   │       └── rules/
│   │           ├── <existing>/
│   │           └── rpc/               ← new: routes to RPC nodes
│   │
│   ├── nodes/                         ← new
│   │   ├── validator/
│   │   │   ├── key-management/
│   │   │   └── deployment/
│   │   ├── full/
│   │   └── rpc/
│   │
│   └── migration/                     ← existing — extended
│       ├── state.yaml                 ← add chain migration states
│       ├── classification/
│       │   └── registry.yaml          ← A/B/C/D per package
│       ├── data/
│       │   └── per-package/
│       │       └── <package-name>/
│       │           ├── shadow-write-config
│       │           ├── parity-verify
│       │           └── flip-procedure
│       └── chain/
│           ├── testnet-checklist
│           ├── mainnet-checklist
│           └── contract-deploy-procedure

============
The Single Most Important Thing
Every package you migrate to blockchain
removes a trust assumption from your users.

Every package you migrate incorrectly
creates an irreversible error at 10M user scale.

The classification step — A, B, C, or D —
is the most important decision in this entire process.

Get the classification wrong:
  put Classification D logic on-chain
  → you paid audit costs, complexity costs, latency costs
  → for zero user benefit

  put Classification C logic in traditional service
  → users must trust you for settlement, access control, ownership
  → the entire point of blockchain is lost

The question for every package is not:
  "can this go on-chain?"

The question is:
  "does removing the trust requirement here
   create enough value for users
   to justify the irreversibility, complexity, and cost?"

If yes → migrate.
If no  → Classification D. Stay traditional.