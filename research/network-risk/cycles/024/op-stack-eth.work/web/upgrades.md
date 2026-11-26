> ## Documentation Index
> Fetch the complete documentation index at: https://docs.optimism.io/llms.txt
> Use this file to discover all available pages before exploring further.

# Network upgrades

> The hardfork registry — activation times, governing specs, and minimum component versions for every OP Stack network upgrade.

> [!NOTE]
>
> **Normative spec:** Network upgrade activation is normatively defined in the
> [Superchain upgrades specification](https://specs.optimism.io/protocol/superchain-upgrades.html#activation-rules). This registry records activation data and operational pointers; each upgrade's own specification, linked from its registry page, defines what it changes.

This page is the index of the **hardfork registry**: every OP Stack hardfork
has one permanent page recording its activation timestamps, governing
specification, governance approval, and minimum component versions.
Governance-approved [contract upgrades](#contract-upgrades) that carry no
hardfork are listed separately below. Network upgrade names after Bedrock
follow a geology theme based on the next letter of the English alphabet.

The table below is generated from the registry pages' structured frontmatter
and validated against the
[superchain-registry](https://github.com/ethereum-optimism/superchain-registry) —
it is never hand-edited. See
[How this registry is maintained](#how-this-registry-is-maintained).

## Activations

Network upgrades activate by L2 block timestamp. Failing to upgrade your OP
Stack software before the activation timestamp causes a chain divergence, and
you will need to resync the chain. Operator action items for each upgrade are
published in [Notices](https://docs.optimism.io/notices.md).

| Hardfork | Status | [Mainnet activation](https://github.com/ethereum-optimism/superchain-registry/blob/main/superchain/configs/mainnet/superchain.toml) | [Sepolia activation](https://github.com/ethereum-optimism/superchain-registry/blob/main/superchain/configs/sepolia/superchain.toml) |
| - | - | - | - |
| [Lagoon](https://docs.optimism.io/op-stack/protocol/hardforks/lagoon.md) | In development | Not scheduled | Not scheduled |
| [Karst](https://docs.optimism.io/op-stack/protocol/hardforks/karst.md) | Active | Wed, 08 Jul 2026 16:00:01 UTC (`1783526401`) | Wed, 17 Jun 2026 16:00:01 UTC (`1781712001`) |
| [Jovian](https://docs.optimism.io/op-stack/protocol/hardforks/jovian.md) | Active | Tue, 02 Dec 2025 16:00:01 UTC (`1764691201`) | Wed, 19 Nov 2025 16:00:01 UTC (`1763568001`) |
| [Isthmus](https://docs.optimism.io/op-stack/protocol/hardforks/isthmus.md) | Active | Fri, 09 May 2025 16:00:01 UTC (`1746806401`) | Thu, 17 Apr 2025 16:00:00 UTC (`1744905600`) |
| [Holocene](https://docs.optimism.io/op-stack/protocol/hardforks/holocene.md) | Active | Thu, 09 Jan 2025 18:00:01 UTC (`1736445601`) | Tue, 26 Nov 2024 15:00:00 UTC (`1732633200`) |
| [Granite](https://docs.optimism.io/op-stack/protocol/hardforks/granite.md) | Active | Wed, 11 Sep 2024 16:00:01 UTC (`1726070401`) | Mon, 12 Aug 2024 16:00:00 UTC (`1723478400`) |
| [Fjord](https://docs.optimism.io/op-stack/protocol/hardforks/fjord.md) | Active | Wed, 10 Jul 2024 16:00:01 UTC (`1720627201`) | Wed, 29 May 2024 16:00:00 UTC (`1716998400`) |
| [Ecotone](https://docs.optimism.io/op-stack/protocol/hardforks/ecotone.md) | Active | Thu, 14 Mar 2024 00:00:01 UTC (`1710374401`) | Wed, 21 Feb 2024 17:00:00 UTC (`1708534800`) |
| [Delta](https://docs.optimism.io/op-stack/protocol/hardforks/delta.md) | Active | Thu, 22 Feb 2024 00:00:00 UTC (`1708560000`) | Fri, 22 Dec 2023 00:00:00 UTC (`1703203200`) |
| [Canyon](https://docs.optimism.io/op-stack/protocol/hardforks/canyon.md) | Active | Thu, 11 Jan 2024 17:00:01 UTC (`1704992401`) | Tue, 14 Nov 2023 17:00:00 UTC (`1699981200`) |
| [Regolith](https://docs.optimism.io/op-stack/protocol/hardforks/regolith.md) | Active | Genesis / at Bedrock | Genesis / at Bedrock |

Activation timestamps are the superchain-wide defaults from the [superchain-registry](https://github.com/ethereum-optimism/superchain-registry). Timestamps are the canonical activation mechanism — block heights differ per chain, so no block numbers are listed. Individual chains outside those defaults set their own activation times in their chain config.

All of the above build on **Bedrock**, the
[governance-approved](https://gov.optimism.io/t/final-upgrade-1-bedrock-protocol-upgrade-v2/5548)
2023 re-genesis of OP Mainnet at block `105235063` (L2 timestamp `1686068903`)
that the hardfork series starts from. Sepolia OP Stack chains launched on
Bedrock directly.

### One upgrade per activation timestamp

Two network upgrades must never be configured to activate at the same L2 block
timestamp after genesis. Every upgrade's activation-block behavior — the
upgrade transactions it deposits, the state it changes, the block attributes it
derives — is only defined against a chain on which every earlier upgrade is
already active, so two upgrades sharing an activation block is an unsupported
configuration whose combined behavior no specification covers. Activation
timestamps must be strictly increasing in upgrade order, and `op-node` rejects
a rollup config that schedules two upgrades to activate together. See the
[activation rules](https://specs.optimism.io/protocol/superchain-upgrades.html?utm_source=op-docs\&utm_medium=docs#activation-rules)
in the superchain upgrades specification.

Chains that launch after an upgrade already exists activate that upgrade in
their genesis block instead, conventionally by setting its activation timestamp
to `0` — so upgrades that are active from genesis do share a timestamp, and
that is the one case the rule allows. This restriction covers OP Stack upgrades
only: it does not constrain an OP Stack upgrade timestamp against an L1 fork
timestamp on the same chain, which may coincide.

## Contract upgrades

Not every governance-approved upgrade is a hardfork: hardforks activate by L2
block timestamp on every chain, while contract upgrades ship as
[op-contracts releases](https://docs.optimism.io/releases/op-contracts.md) and are executed on each
chain's L1 contracts after governance approval. Contract-only upgrades have no
activation timestamp, so they do not get hardfork registry pages — their
permanent record is the op-contracts release history and the operator notice.

| Upgrade | What it shipped | Operator notice | op-contracts release |
| - | - | - | - |
| Upgrade 21 | `ETHLockbox` as the custody and pause identifier for every chain, and the L1 contract changes for interop | [Notice](https://docs.optimism.io/notices/archive/upgrade-21) | [`v9.0.0`](https://docs.optimism.io/releases/op-contracts) |
| Upgrade 20 | Super Root Dispute Games (`SUPER_PERMISSIONED`, `SUPER_CANNON_KONA`) and `SystemConfig` interface cleanup | [Notice](https://docs.optimism.io/notices/archive/upgrade-20) | [`v8.0.0`](https://docs.optimism.io/releases/op-contracts) |
| Upgrade 18 | Cannon + Kona game type, Custom Gas Token v2, creator-pattern dispute game refactor | [Notice](https://docs.optimism.io/notices/archive/upgrade-18) | [`v6.0.0`](https://docs.optimism.io/releases/op-contracts) |
| Upgrade 16a | Maintenance release superseding Upgrade 16 (removes unused interop withdrawal-proving code, adds feature toggles) | [Notice](https://docs.optimism.io/notices/archive/upgrade-16a) | [`v4.1.0`](https://docs.optimism.io/releases/op-contracts) |
| Upgrade 16 | Interop-ready `OptimismPortal`, Stage 1 updates, Go 1.23 support in Cannon | [Notice](https://docs.optimism.io/notices/archive/upgrade-16) | [`v4.0.0`](https://docs.optimism.io/releases/op-contracts) |
| Upgrade 14 | Multithreaded 64-bit Cannon (MT-Cannon) and Isthmus L1 contracts | [Notice](https://docs.optimism.io/notices/archive/upgrade-14) | [`v3.0.0`](https://docs.optimism.io/releases/op-contracts) |
| Upgrade 13 | OP Contracts Manager (OPCM) and incident response improvements | [Notice](https://docs.optimism.io/notices/archive/upgrade-13) | [`v2.0.0`](https://docs.optimism.io/releases/op-contracts) |

Hardfork-carrying upgrades (for example Upgrade 15 / Isthmus, Upgrade 17 /
Jovian, Upgrade 19 / Karst) are listed in the
[activations table](#activations) above and link to their notices from their
registry pages.

## Upgrade process

Network upgrades follow this general process in which the features included in
the upgrade are put into a release version cut from the `develop` branch and
then the software is deployed on production networks.

> [!NOTE]
>
> "Baking" on a network means the node software has been deployed and is live.
> Engineers take this time to observe the behavior of the software on
> production networks.

Node Software Release Timeline

**1. Devnet**

* `Devnet Upgrade Notice Period` is for core developers to upgrade the
  node software on an internal devnet prior to the activation timestamp.
* `Upgrade Activates on Devnet`
* `Baking on Devnet`

**2. Testnet**

* `Testnet Upgrade Notice Period` is to allow testnet node operators to
  upgrade the node software on testnet prior to the activation timestamp.
* `Upgrade Activates on Testnet`
* `Baking on Testnet`

**3. Mainnet**

* `Governance Voting Review Period` is when Optimism governance
  reviews proposals, including network upgrade proposals.
* `Governance Voting Period` is when Optimism governance
  votes on proposals.
* `Veto Period` is when the Citizens' House of the governance system can
  veto a protocol upgrade that has been approved by the Token House.
* `Cut Mainnet Release`
* `Mainnet Upgrade Notice Period` is to allow mainnet node operators to
  upgrade the node software on mainnet prior to the activation timestamp.
* `Upgrade Activated`

## How this registry is maintained

Each hardfork page keeps its machine-readable facts (lifecycle, activation
timestamps, spec link, minimum component versions) in structured frontmatter.
`scripts/generate-hardforks.ts` validates that data against the
superchain-registry and renders the activation tables — a frontmatter edit
followed by regeneration is the only way to change an activation row. The
schema is documented in
[`scripts/hardfork-registry.md`](https://github.com/ethereum-optimism/optimism/blob/develop/docs/public-docs/scripts/hardfork-registry.md).
