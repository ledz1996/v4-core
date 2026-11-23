> ## Documentation Index
> Fetch the complete documentation index at: https://docs.base.org/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> For the current source of truth, read https://docs.base.org/llms.txt and connect the Base docs MCP server at https://docs.base.org/mcp.

# Changelog

> Per-hardfork, per-feature migration notes for the B20 token standard, newest first, including new methods, deprecations, and activation dates.

Per-hardfork, per-feature migration notes for the [B20 token standard](https://docs.base.org/specifications/b20.md). Each Cobalt and Denim entry is a focused, code-forward changelog for one scoped feature change that crosses a hardfork boundary. Newest first.

> [!NOTE]
>
> B20 method and event signatures are part of the chain's consensus surface. Existing selectors do not change, and new functionality ships by addition. Behavior can change at a hardfork boundary: two Denim entries below are breaking for some integrations.

## Hardfork Ordinals

| Ordinal | Hardfork | Status |
| - | - | - |
| `01` | Beryl | Live |
| `02` | Cobalt | Live |
| `03` | Denim | Live |

## [Denim](https://docs.base.org/upgrades/denim/overview.md), Ordinal 03

| Network | Activated |
| - | - |
| Base Mainnet | 2026-11-05 |
| Base Sepolia | 2026-10-21 |

| Product(s) | Change | Affected interfaces | Entry |
| - | - | - | - |
| B20 Asset, B20 Stablecoin | (Breaking) Reject the token itself as a credit recipient | `IB20` (shared surface), `IB20Asset` (`batchMint`) | [Token receiver](https://docs.base.org/base-chain/specs/reference/b20/changelog/03-denim-b20-token-receiver.md) |
| B20 Asset, B20 Stablecoin | (Breaking) Transfer executor policy on every transfer path | `IB20` (shared surface) | [Transfer executor enforcement](https://docs.base.org/base-chain/specs/reference/b20/changelog/03-denim-b20-transfer-executor-enforcement.md) |
| PolicyRegistry | NOT / invert policies | `IPolicyRegistry` | [NOT policies](https://docs.base.org/base-chain/specs/reference/b20/changelog/03-denim-policyregistry-not-policy.md) |

## [Cobalt](https://docs.base.org/upgrades/cobalt/overview.md), Ordinal 02

| Network | Activated |
| - | - |
| Base mainnet | 2026-09-30 |
| Base Sepolia | 2026-09-23 |

| Product(s) | Change | Affected interfaces | Entry |
| - | - | - | - |
| B20 Asset | Schedule Multiplier Updates (ERC-8056) | `IB20Asset` | [Multiplier / ERC-8056](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-b20asset-multiplier.md) |
| B20 Asset, B20 Stablecoin | Seize surface + `burnBlocked` deprecation | `IB20` (shared surface) | [Seize surface](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-b20-seize.md) |
| PolicyRegistry | Composite Policies (UNION / INTERSECT) | `IPolicyRegistry` | [Composite policies](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-policyregistry-composite-policy.md) |

## [Beryl](https://docs.base.org/upgrades/beryl/overview.md): Initial Release

| Network | Activated |
| - | - |
| Base mainnet | 2026-06-25 |
| Base Sepolia | 2026-06-18 |

Shipped with the [Beryl upgrade](https://docs.base.org/upgrades/beryl/overview.md).

**Added**

* The B20 standard as a native precompile: a superset of ERC-20 with full selector and behavior parity for `transfer`, `transferFrom`, `approve`, `allowance`, `balanceOf`, `totalSupply`, `name`, `symbol`, `decimals`, `Transfer`, and `Approval`
* [Role-based access control](https://docs.base.org/specifications/b20/concepts/roles-and-pause.md#2-roles) with built-in roles, user-defined roles in the role graph, and `renounceLastAdmin` for permanent admin-less operation
* [PolicyRegistry](https://docs.base.org/specifications/b20/concepts/policies.md#21-the-registry-and-the-token) singleton precompile with `BLOCKLIST` and `ALLOWLIST` policy types, two-step admin transfer, and the `ALWAYS_ALLOW` and `ALWAYS_BLOCK` built-ins
* [Four policy scopes](https://docs.base.org/specifications/b20/concepts/policies.md#32-policy-scopes) on every token, covering transfer sender, receiver, and executor, and mint receiver
* [Memo variants](https://docs.base.org/specifications/b20/reference/interfaces/ib20) of transfer, transferFrom, mint, and burn, emitting `Memo` immediately after the primary event
* [Granular pausing](https://docs.base.org/specifications/b20/concepts/roles-and-pause.md#3-pause) by `PausableFeature`: `TRANSFER`, `MINT`, and `BURN`
* `burnBlocked` and `BURN_BLOCKED_ROLE` for administrative removal of a blocked holder's balance
* [Optional supply caps](https://docs.base.org/specifications/b20/reference/interfaces/ib20/supply-cap), with `type(uint128).max` as the uncapped sentinel and maximum supply
* [ERC-2612 `permit`](https://docs.base.org/specifications/b20) with an EIP-712 domain at version `"1"`
* [ERC-7572 `contractURI`](https://docs.base.org/specifications/b20/reference/interfaces/ib20/contract-uri) and `METADATA_ROLE`-gated name, symbol, and URI updates
* [B20Factory](https://docs.base.org/specifications/b20/reference/interfaces/ib20-factory/create-b20) singleton precompile with deterministic, variant-encoding addresses and `initCalls` bootstrap semantics
* ActivationRegistry gating for state-changing PolicyRegistry calls
* The [`ASSET` variant](https://docs.base.org/specifications/b20/concepts/token-types#4-asset): `OPERATOR_ROLE`, WAD-precision UI multipliers with scheduled and instant updates, announcements, `batchMint`, and issuer-defined extra metadata
* The [`STABLECOIN` variant](https://docs.base.org/specifications/b20/concepts/token-types#5-stablecoin): fixed 6 decimals and a `currency()` code set once at creation

`seizeWithMemo`, the `SEIZE` pause feature, the two seize policy scopes, and the deprecation of `burnBlocked` shipped later with Cobalt. See the [seize changelog entry](https://docs.base.org/base-chain/specs/reference/b20/changelog/02-cobalt-b20-seize.md).
