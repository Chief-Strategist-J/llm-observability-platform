Do not build your own P2P stack.
Use an existing P2P library as the transport layer.
Build your protocol on top.

Options:
  libp2p     ← used by Ethereum 2.0, Filecoin, Polkadot
               modular, language-agnostic, battle-tested
               Go, Rust, JavaScript implementations exist

  devp2p     ← Ethereum's original P2P protocol
               simpler but less modular than libp2p

  tendermint p2p ← used by Cosmos ecosystem
                   good if PoS/DPoS consensus direction chosen

Recommendation for multi-consensus modular chain:
  libp2p — it is runtime-agnostic and consensus-agnostic
  

Node Types — Define These Before Writing Code

Validator Node
  - participates in consensus
  - produces blocks
  - permissioned — requires registration
  - high availability requirement
  - never exposes RPC publicly

Full Node
  - stores complete chain state
  - validates all blocks
  - does NOT produce blocks
  - public read access
  - entry point for public participants

Archive Node
  - stores complete historical state
  - used by explorers, analytics
  - NOT in consensus path

Light Node / Client
  - stores block headers only
  - verifies proofs, not full blocks
  - used by end users, mobile clients

RPC Node
  - full node + public API exposure
  - rate limited
  - sits behind gateway
  - stateless from protocol perspective


Tradeoffs at P2P Layer

Gossip protocol (broadcast to all):
  + simple, resilient, no single point
  - bandwidth scales with node count
  - message duplication at scale

Structured overlay (DHT-based routing):
  + efficient, scales better
  - complex, more failure modes
  - slower propagation under network partition

For 10M users with hybrid participation:
  validators use structured overlay (known set, efficient)
  public nodes use gossip (unknown set, resilient)
  this is the hybrid P2P pattern