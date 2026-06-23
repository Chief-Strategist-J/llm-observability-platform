Pattern: Modular Consensus with Pluggable Engines
This is the most critical architectural decision. Getting it wrong means rebuilding the entire chain.

Modular consensus means:
  consensus logic is behind an interface
  you can swap PoA → PoS → DPoS
  without changing the execution layer above it

Interface contract (language-agnostic):
  ProposeBlock(validator, transactions) → Block
  ValidateBlock(block) → bool
  FinalizeBlock(block) → FinalizedBlock
  GetValidatorSet() → []Validator
  UpdateValidatorSet(changes) → ValidatorSet

Every consensus engine implements this interface.
The execution layer calls this interface.
The execution layer never knows which engine is running.

PoA — Proof of Authority

Use when:
  - early network, known validators
  - enterprise/permissioned context
  - speed is priority over decentralization

Properties:
  finality:     immediate (1 block)
  throughput:   very high (no mining/staking overhead)
  security:     depends entirely on validator honesty
  decentralization: low — validators are known and trusted

Critical tradeoff:
  PoA is NOT Byzantine fault tolerant by default
  if f validators are malicious out of n total,
  you need n > 3f for BFT-PoA (PBFT-based)
  most PoA implementations ignore this — that is a security hole

Validator set management:
  on-chain governance contract
  adds/removes validators by existing validator vote
  minimum validator count: 4 (tolerates 1 malicious)
  recommended: 7+ (tolerates 2 malicious)


PoS — Proof of Stake
Use when:
  - decentralization matters
  - economic security model needed
  - Sybil resistance via stake

Properties:
  finality:     probabilistic (N blocks) or deterministic (Casper FFG style)
  throughput:   high (no PoW) but lower than PoA
  security:     economic — attacking costs stake
  decentralization: medium-high

Critical tradeoffs:
  Nothing-at-stake problem:
    validators can vote on multiple forks at no cost
    solution: slashing conditions (penalize equivocation)
    you MUST implement slashing before PoS is secure

  Long-range attack:
    attacker buys old keys, rewrites history
    solution: weak subjectivity checkpoints
    you MUST implement this

  Stake centralization:
    large stakers dominate
    solution: quadratic voting, delegation limits

DPoS — Delegated Proof of Stake

Use when:
  - high throughput is critical
  - community governance model
  - token holders want participation without running nodes

Properties:
  finality:     fast (small elected validator set)
  throughput:   highest of the three
  security:     depends on delegate honesty + token holder vigilance
  decentralization: medium (delegation concentrates power)

Critical tradeoff:
  Cartel formation:
    top delegates collude, dominate block production
    solution: vote decay, delegate rotation limits
    this is the most common DPoS failure mode

  Voter apathy:
    most token holders don't vote
    small engaged group controls validator set
    solution: voting incentives, default delegation

For Your System — Modular Consensus Decision
Since you chose "all consensus mechanisms":

Build in this order:
  1. PoA first — simplest, fastest to implement, use for testnet
  2. PoS second — add slashing + weak subjectivity
  3. DPoS third — add delegation layer on top of PoS

Each builds on the previous.
The modular interface means L1 execution never changes.
Only the consensus engine swaps.

Governance decides which engine is active.
Migration between engines is a governance vote, not a code deploy.