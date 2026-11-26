> ## Documentation Index
> Fetch the complete documentation index at: https://docs.base.org/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> For the current source of truth, read https://docs.base.org/llms.txt and connect the Base docs MCP server at https://docs.base.org/mcp.

# Upgrades

> Track Base network upgrades, activation dates, and the protocol changes included in each release.

Base evolves through named network upgrades. Each release introduces protocol changes, new features, or parameter updates that activate across Base Sepolia and Base Mainnet.

A month without a confirmed activation timestamp is a planning target and may change.

**TBD**

## Everest

Everest introduces Base Transactions (EIP-8430), a new transaction type that allows for batching, sponsorship, token gas payments, and high throughput natively.

* **Base Sepolia:** TBD
* **Base Mainnet:** TBD

[View Features](https://docs.base.org/upgrades/everest/overview.md)

**November 5, 2026**

## Denim

Denim introduces native blocks at a 200ms cadence, replacing Flashblocks with canonical block and RPC streams.

* **Base Sepolia:** Activated October 21, 2026
* **Base Mainnet:** Activated November 5, 2026

[View Features](https://docs.base.org/upgrades/denim/overview.md)

**September 30, 2026**

## Cobalt

Cobalt improves the B20 token standard, adds validity transactions, introduces dynamic node upgrades (metrics-only on Mainnet), and migrates TEE signer registration to onchain attestation verification.

* **Base Sepolia:** Activated September 23, 2026
* **Base Mainnet:** Activated September 30, 2026

[View Features](https://docs.base.org/upgrades/cobalt/overview.md)

**June 25, 2026**

## Beryl

Beryl makes Base a first-class issuance platform with B20 tokens, reduces withdrawal delays, and adopts Reth V2 as the reference execution client.

* **Base Sepolia:** Activated June 18, 2026
* **Base Mainnet:** Activated June 25, 2026

[View Features](https://docs.base.org/upgrades/beryl/overview.md)

**May 28, 2026**

## Azul

Azul is Base's first independent network upgrade. It strengthens security and decentralization, advances the path to 1 gigagas per second, and improves the developer experience.

* **Base Sepolia:** Activated April 20, 2026
* **Base Mainnet:** Activated May 28, 2026

[View Features](https://docs.base.org/upgrades/azul/overview.md)

## Upstream OP Stack Hardforks

Base adopted the following upstream OP Stack hardforks. Entries are ordered by Base Mainnet activation date.

**December 2, 2025**

## Jovian

Jovian introduces a configurable minimum base fee and a data availability footprint gas scalar for improved fee-market stability.

* **Base Sepolia:** Activated November 19, 2025
* **Base Mainnet:** Activated December 2, 2025

[View Features](https://docs.base.org/upgrades/jovian/overview.md)

**May 9, 2025**

## Isthmus

Isthmus incorporates Ethereum Pectra EIPs and introduces the operator fee mechanism for sequencer revenue.

* **Base Sepolia:** Activated April 17, 2025
* **Base Mainnet:** Activated May 9, 2025

[View Features](https://docs.base.org/upgrades/isthmus/overview.md)

**January 9, 2025**

## Holocene

Holocene introduces dynamic EIP-1559 parameters configurable through `SystemConfig` and stricter block derivation rules.

* **Base Sepolia:** Activated November 26, 2024
* **Base Mainnet:** Activated January 9, 2025

[View Features](https://docs.base.org/upgrades/holocene/overview.md)

**September 11, 2024**

## Granite

Granite adds `bn256Pairing` precompile input-size restrictions and updates the channel timeout parameter.

* **Base Sepolia:** Activated August 12, 2024
* **Base Mainnet:** Activated September 11, 2024

[View Features](https://docs.base.org/upgrades/granite/overview.md)

**July 10, 2024**

## Fjord

Fjord introduces FastLZ-based L1 fee estimation, the RIP-7212 `secp256r1` precompile, and Brotli channel compression.

* **Base Sepolia:** Activated May 29, 2024
* **Base Mainnet:** Activated July 10, 2024

[View Features](https://docs.base.org/upgrades/fjord/overview.md)

**March 14, 2024**

## Ecotone

Ecotone integrates Ethereum Dencun changes, including EIP-4844 blob transactions and EIP-4788 beacon block roots.

* **Base Sepolia:** Activated February 21, 2024
* **Base Mainnet:** Activated March 14, 2024

[View Features](https://docs.base.org/upgrades/ecotone/overview.md)

**February 22, 2024**

## Delta

Delta introduces span batches to reduce L1 data costs by compressing multiple L2 blocks into a single batcher transaction.

* **Base Sepolia:** Activated December 22, 2023
* **Base Mainnet:** Activated February 22, 2024

[View Features](https://docs.base.org/upgrades/delta/overview.md)

**January 11, 2024**

## Canyon

Canyon brings Ethereum Shanghai EIPs, including EIP-3651, EIP-3855, and EIP-3860, to the Base execution layer.

* **Base Sepolia:** Activated November 14, 2023
* **Base Mainnet:** Activated January 11, 2024

[View Features](https://docs.base.org/upgrades/canyon/overview.md)

## Other Changes

The [configuration changelog](https://docs.base.org/base-chain/network-information/configuration-changelog.md) tracks network parameter changes that do not belong to a specific upgrade.
