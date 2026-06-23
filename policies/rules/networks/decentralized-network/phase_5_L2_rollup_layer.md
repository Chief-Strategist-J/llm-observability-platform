Two Rollup Patterns — Both Have Fundamental Tradeoffs
Optimistic Rollup:
  assumption: transactions are valid unless challenged
  fraud proof window: 7 days (standard)
  finality: 7 days (slow)
  throughput: high
  complexity: lower than ZK

  build this first — simpler, faster to implement
  Ethereum's Optimism and Arbitrum use this model

ZK Rollup:
  validity proof: cryptographic proof of correct execution
  finality: as fast as proof generation
  finality time: minutes to hours (proof generation cost)
  throughput: high
  complexity: very high (ZK circuit design)

  build this second — requires ZK expertise
  Ethereum's zkSync, StarkNet use this model

L2 Architecture — How It Connects to L1

L2 Components:
  Sequencer
    - receives L2 transactions
    - orders and batches them
    - single sequencer = centralization risk
    - decentralized sequencer = complex coordination

  Batch Submitter
    - compresses L2 transaction batches
    - submits to L1 as calldata or blob
    - pays L1 gas fees

  State Root Publisher
    - publishes L2 state root to L1 contract
    - this is the trust anchor

  L1 Bridge Contract
    - accepts deposits from L1 → L2
    - processes withdrawals L2 → L1
    - verifies fraud proofs (optimistic) or validity proofs (ZK)
    - THIS IS THE MOST SECURITY-CRITICAL CONTRACT YOU WILL WRITE

  Challenger (optimistic only)
    - monitors L2 state roots published to L1
    - submits fraud proofs if invalid state root detected
    - must be run by multiple independent parties

Critical L2 Tradeoff — Sequencer Centralization

Single sequencer:
  + simple, fast, high throughput
  - single point of failure
  - sequencer can censor transactions
  - sequencer can front-run transactions (MEV)

Decentralized sequencer set:
  + censorship resistant
  + no single point of failure
  - requires consensus among sequencers
  - adds latency
  - complex to implement correctly

For your hybrid model (permissioned validators, public read):
  permissioned sequencer set — known, accountable operators
  public read of sequencer mempool — transparency without permissionless write
  this is the pragmatic middle ground at your stage