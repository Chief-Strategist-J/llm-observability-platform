Phase 1 — P2P Network + Basic Node   (foundation)
Phase 2 — Consensus Layer            (correctness before anything else)
Phase 3 — L1 Execution Layer         (state machine on top of consensus)
Phase 4 — Multi-VM Execution         (EVM first, WASM second, custom last)
Phase 5 — L2 Rollup Layer            (only after L1 is battle-tested)
Phase 6 — Developer Tooling + APIs   (usable surface on top of protocol)
Phase 7 — Application Layer          (last — built by ecosystem, not you)

Skipping Phase 2 stability before Phase 3 means your state machine has no correctness guarantee. Skipping Phase 3 stability before Phase 5 means your rollup settles to an unstable chain. The order is the architecture.
