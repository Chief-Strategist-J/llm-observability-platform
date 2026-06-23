The L1 execution layer is a deterministic state machine.

State(n+1) = Transition(State(n), Block(n))

Every node runs the same transition function.
Every node must arrive at the same State(n+1).
Any non-determinism is a consensus failure.

Non-determinism sources to eliminate:
  - floating point arithmetic (use integer math only)
  - system time calls (use block timestamp)
  - random number generation (use VRF or commit-reveal)
  - map iteration order (use sorted deterministic structures)
  - external API calls (never in execution layer)

Transaction Lifecycle

User signs transaction
    │
    ▼
RPC Node receives + validates signature
    │
    ▼
Mempool (pending transaction pool)
    │  ordered by: fee, nonce, timestamp
    ▼
Validator selects transactions for block
    │  applies: gas limit, block size limit
    ▼
Block proposed to consensus layer
    │
    ▼
Consensus validates + finalizes block
    │
    ▼
Execution layer applies state transition
    │
    ▼
State root updated + stored
    │
    ▼
Block propagated to all nodes via P2P


State Storage — Critical Decision

Options:
  Merkle Patricia Trie (Ethereum model)
    + cryptographic proof of any state value
    + light client friendly
    - write amplification — one state change updates many nodes
    - complex implementation

  Sparse Merkle Tree
    + simpler than MPT
    + efficient proofs
    - less battle-tested

  Database with separate proof layer
    + simple, fast writes
    - proof generation is separate concern
    - not light-client native

For L1+L2 with rollup capability:
  Merkle Patricia Trie or Sparse Merkle Tree
  You NEED cryptographic state proofs for L2 fraud/validity proofs
  A database-only approach makes L2 impossible or insecure