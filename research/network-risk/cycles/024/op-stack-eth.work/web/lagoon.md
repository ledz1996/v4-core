> ## Documentation Index
> Fetch the complete documentation index at: https://docs.optimism.io/llms.txt
> Use this file to discover all available pages before exploring further.

# Lagoon

> Hardfork registry entry for the Lagoon network upgrade, which activates Superchain interop.

> [!NOTE]
>
> **Normative spec:** This upgrade is normatively defined in the
> [Lagoon specification](https://specs.optimism.io/protocol/lagoon/overview.html). This page records activation data and operational pointers; it does not restate the spec. The Lagoon spec is not yet finalized.

Lagoon (Upgrade 22) is the upcoming hardfork that activates Superchain
[interop](https://docs.optimism.io/op-stack/interop/explainer.md).
It has no superchain-wide activation default in the superchain-registry.
Instead, each chain that takes Lagoon sets its own activation time in its chain
config.

| Network | Chains | Interop | Activation |
| - | - | - | - |
| Sepolia | OP Sepolia, Unichain Sepolia | Yes | Thu, 10 Dec 2026 16:00:01 UTC (`1796918401`) |
| Sepolia | Ink Sepolia, Soneium Minato | No | Thu, 10 Dec 2026 16:00:01 UTC (`1796918401`) |
| Mainnet | OP Mainnet, Unichain | Yes | Mon, 11 Jan 2027 16:00:01 UTC (`1799683201`) |
| Mainnet | Ink, Soneium | No | Mon, 11 Jan 2027 16:00:01 UTC (`1799683201`) |

The mainnet activation is subject to governance approval.
See the [Upgrade 22 notice](https://docs.optimism.io/notices/upgrade-22.md) for the full schedule,
required actions, and the L1 contract upgrade that comes with Lagoon, and the
[interop activation prep notice](https://docs.optimism.io/notices/interop-prep.md) for the node topology
interop chains need.

| | |
| - | - |
| Status | In development |
| Governing spec | [specs.optimism.io](https://specs.optimism.io/protocol/lagoon/overview.html) |
| Operator notice | [Upgrade 22 notice](https://docs.optimism.io/notices/upgrade-22.md) |
| Mainnet activation (superchain default) | Not scheduled |
| Sepolia activation (superchain default) | Not scheduled |

## What's included

Per the [spec overview](https://specs.optimism.io/protocol/lagoon/overview.html)
(subject to change while the spec is in development):

* Execution layer: reduced BLS12-381 precompile input sizes,
  post-execution transactions, and
  [sequencer defined metering](https://docs.optimism.io/op-stack/features/sdm.md).
* Consensus layer: Lagoon derivation changes, plus the interop dependency
  set, derivation, sequencer and verifier behavior, and super roots.
* Smart contracts: interop messaging, predeploys, token bridging, ETH
  liquidity, ETH bridging, and the interop changes to `OptimismPortal` and
  `ETHLockbox`.

The Super Fault Dispute Game is not part of this hardfork.
