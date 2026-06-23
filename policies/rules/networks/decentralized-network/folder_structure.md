Folder Structure — Full Stack
chain/
│
├── p2p/                               ← Phase 1
│   ├── transport/                     ← libp2p or chosen library adapter
│   ├── discovery/                     ← node discovery protocol
│   ├── gossip/                        ← transaction + block propagation
│   ├── peer-scoring/                  ← reputation, ban lists
│   └── node-types/
│       ├── validator/
│       ├── full/
│       ├── archive/
│       ├── light/
│       └── rpc/
│
├── consensus/                         ← Phase 2
│   ├── interface/                     ← THE interface all engines implement
│   ├── engines/
│   │   ├── poa/                       ← build first
│   │   │   ├── validator-set/
│   │   │   ├── block-proposal/
│   │   │   └── finality/
│   │   ├── pos/                       ← build second
│   │   │   ├── staking/
│   │   │   ├── slashing/              ← REQUIRED before PoS is safe
│   │   │   ├── weak-subjectivity/     ← REQUIRED before PoS is safe
│   │   │   └── finality/
│   │   └── dpos/                      ← build third
│   │       ├── delegation/
│   │       ├── validator-election/
│   │       └── vote-decay/
│   ├── validator-registry/            ← on-chain validator management
│   └── governance/                    ← consensus engine switching
│
├── execution/                         ← Phase 3
│   ├── state/
│   │   ├── trie/                      ← Merkle Patricia Trie or SMT
│   │   ├── accounts/
│   │   └── storage/
│   ├── mempool/
│   │   ├── ordering/
│   │   ├── validation/
│   │   └── eviction/
│   ├── block/
│   │   ├── builder/
│   │   ├── validator/
│   │   └── processor/
│   └── transaction/
│       ├── types/
│       ├── signing/
│       └── receipt/
│
├── vm/                                ← Phase 4
│   ├── interface/                     ← THE interface all VMs implement
│   ├── evm/                           ← build first
│   │   ├── interpreter/
│   │   ├── opcodes/
│   │   ├── precompiles/
│   │   └── gas/
│   ├── wasm/                          ← build second
│   │   ├── runtime/
│   │   ├── host-functions/            ← determinism-controlled
│   │   ├── gas-metering/
│   │   └── validation/
│   └── custom/                        ← build last, only if needed
│       ├── instruction-set/
│       ├── runtime/
│       └── gas/
│
├── l2/                                ← Phase 5
│   ├── sequencer/
│   │   ├── mempool/
│   │   ├── ordering/
│   │   └── batch-builder/
│   ├── rollup/
│   │   ├── optimistic/
│   │   │   ├── fraud-proof/
│   │   │   ├── challenger/
│   │   │   └── dispute-resolution/
│   │   └── zk/
│   │       ├── circuit/
│   │       ├── prover/
│   │       └── verifier/
│   ├── bridge/
│   │   ├── l1-contract/               ← most security-critical code
│   │   ├── deposit/
│   │   └── withdrawal/
│   └── state-publisher/
│
├── rpc/                               ← Phase 6
│   ├── api/
│   │   ├── eth-compatible/            ← EVM JSON-RPC compatibility layer
│   │   ├── native/                    ← your chain's own API
│   │   └── ws/                        ← WebSocket subscriptions
│   ├── gateway/
│   │   ├── rate-limiting/
│   │   ├── auth/
│   │   └── load-balancing/
│   └── indexer/                       ← event indexing for queries
│
├── contracts/                         ← Phase 6
│   ├── core/
│   │   ├── validator-registry/
│   │   ├── staking/
│   │   ├── governance/
│   │   └── bridge/                    ← L1 bridge contract
│   ├── standards/                     ← token standards, NFT standards
│   └── audits/                        ← audit reports, findings, fixes
│
├── sdk/                               ← Phase 6
│   ├── <language-A>/
│   └── <language-B>/
│
└── infra/                             ← runs across all phases
    ├── nodes/
    │   ├── validator/
    │   ├── full/
    │   └── rpc/
    ├── network/
    │   ├── p2p-ports/                 ← P2P port config per node type
    │   ├── rpc-gateway/               ← public RPC entry point
    │   └── validator-isolation/       ← validators never public-facing
    ├── keys/
    │   ├── validator-key-management/  ← HSM policy, key rotation
    │   └── signing/
    ├── monitoring/
    │   ├── chain-health/              ← block time, finality, fork detection
    │   ├── validator-performance/
    │   └── p2p-health/
    └── migration/                     ← chain upgrades, hard fork management
        ├── hard-fork-procedure/
        ├── state-migration/
        └── rollback-procedure/