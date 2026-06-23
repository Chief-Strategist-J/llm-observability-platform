Pattern: VM Abstraction Layer
Same pattern as modular consensus.
VM execution is behind an interface.
The execution layer calls the interface.
The execution layer never knows which VM is running.

Interface contract:
  Execute(bytecode, input, state, gasLimit) → (output, newState, gasUsed, error)
  Validate(bytecode) → bool
  EstimateGas(bytecode, input) → gasEstimate

EVM — Build First

Why first:
  largest existing developer ecosystem
  most tooling exists (Hardhat, Foundry, Remix)
  most audited smart contract patterns exist
  immediate developer adoption

Tradeoffs:
  + massive existing contract ecosystem
  + tooling, audits, developers
  - Solidity limitations (no native async, limited types)
  - EVM opcode set is fixed — adding opcodes is a hard fork
  - 256-bit word size is inefficient for most operations

Implementation approach:
  do not build EVM from scratch
  use existing EVM implementation as reference or embed:
    evmone (C++) — fastest EVM implementation
    go-ethereum EVM — most reference-compatible
    revm (Rust) — modern, audited

  wrap it behind your VM interface
  do not expose EVM internals to your execution layer

WASM — Build Second

Why second:
  multi-language smart contracts (Rust, Go, C, AssemblyScript)
  near-native performance
  sandboxed execution model
  growing ecosystem (CosmWasm, ink!)

Tradeoffs:
  + language flexibility
  + performance
  + growing tooling
  - WASM determinism requires careful host function design
  - gas metering in WASM is non-trivial
  - smaller existing contract ecosystem than EVM

Critical WASM-specific requirements:
  deterministic execution:
    disable floating point (use integer math)
    no WASM threads (non-deterministic memory)
    controlled host functions only

  gas metering:
    instrument WASM bytecode at deployment time
    inject gas check before each basic block
    not at each instruction (too slow)

Custom VM — Build Last

Why last:
  only build if EVM + WASM cannot support your use case
  custom VM = custom security audit surface
  custom VM = zero existing tooling
  custom VM = developers must learn new environment

When it makes sense:
  domain-specific operations (e.g. ZK proof verification, ML inference)
  performance-critical operations that EVM/WASM cannot optimize
  privacy-preserving computation model

Tradeoffs:
  + maximum flexibility
  + optimized for your specific use case
  - everything must be built from scratch
  - security audit is entirely your responsibility
  - developer adoption is near zero initially