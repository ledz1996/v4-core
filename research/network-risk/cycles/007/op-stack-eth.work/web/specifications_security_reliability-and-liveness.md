> ## Documentation Index
> Fetch the complete documentation index at: https://docs.base.org/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> For the current source of truth, read https://docs.base.org/llms.txt and connect the Base docs MCP server at https://docs.base.org/mcp.

# Reliability and Liveness

> Where to find Base network status, uptime, and incident history, third-party audits, bug bounties, censorship-resistance guarantees, proposal liveness, and the open-source sequencer components.

## Network Status and Incident History

[status.base.org](https://status.base.org) reports the live status of Base Mainnet and Base Sepolia components, including block production, batch submission, the transaction pool, deposits, withdrawals, and the public RPC API.

* **Uptime:** [status.base.org/uptime](https://status.base.org/uptime) shows the uptime percentage for each month, for Base Mainnet as a whole and for each component, such as [Mainnet block production](https://status.base.org/uptime/j4ln68pbzsmg). The page shows three months at a time; page back to see earlier months. Each percentage is based on the time the component was marked as in a major or partial outage on the status page, with partial outage time weighted at 30%. The status page doesn't publish a 12-month or annual uptime figure: the [main page](https://status.base.org) shows uptime over the past 90 days, and the uptime page shows each month separately.
* **Incident history:** [status.base.org/history](https://status.base.org/history) lists past incidents with their timelines and resolutions.
* **Notifications:** subscribe on [status.base.org](https://status.base.org) to receive incident updates.
* **Postmortems:** Base publishes detailed postmortems for major incidents on the [Base Engineering Blog](https://www.base.org/blog?utm_source=docs), for example the [June 25th block production outage postmortem](https://www.base.org/blog/postmortem-june-25th-block-production-outage?utm_source=docs).

## Audits

Third-party audit reports for the Base Stack are published in the open-source repositories they cover. Each report lists its scope, the reviewed commit, the findings, and how each finding was resolved.

* **Smart contracts:** [base/contracts audits](https://github.com/base/contracts/tree/main/audits), including the multiproof, proof, Cobalt, and dynamic upgrade contract reviews.
* **Node and precompiles:** [base/base audits](https://github.com/base/base/tree/main/audits), including the B20 precompile and dynamic upgrade node reviews.
* **Audit competitions:** [Immunefi reports](https://reports.immunefi.com/base), including the Azul hardfork competition.

The following table lists the reports published in these locations. It covers only those reports, so check the linked repositories for newly added reviews. Each Cantina report summarizes how many issues it found and marks each one as fixed or acknowledged.

| Date | Auditor or program | Scope | Report |
| - | - | - | - |
| March 17, 2026 | Cantina | AggregateVerifier multiproof contracts | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_multiproof_mar2026.pdf) |
| March 19, 2026 | Cantina | TEE multiproof contracts | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_nitro_enclave_mar2026.pdf) |
| April 10, 2026 | Cantina | TEE multiproof contracts (second review) | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_nitro_enclave_apr2026.pdf) |
| April 10, 2026 | Cantina | AggregateVerifier multiproof contracts (second review) | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_aggregateverifier_apr2026.pdf) |
| April 21 to May 4, 2026 | Immunefi audit competition | Azul hardfork | [Immunefi](https://reports.immunefi.com/base) |
| June 4, 2026 | Cantina | Proof contracts update | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_proof_contracts_update_jun2026.pdf) |
| August 14, 2026 | Cantina | Precompiles, including B20 (Beryl) | [base/base](https://github.com/base/base/blob/main/audits/beryl/beryl-b20.pdf) |
| August 14, 2026 | Cantina | Precompile macros and storage (Beryl) | [base/base](https://github.com/base/base/blob/main/audits/beryl/beryl-precompiles-storage.pdf) |
| September 2, 2026 | Cantina | Cobalt contracts (v8.3.0, excluding dynamic upgrades) | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_cobalt_sep2026.pdf) |
| September 10, 2026 | Cantina | Precompile changes, including B20 (Cobalt) | [base/base](https://github.com/base/base/blob/main/audits/cobalt/cobalt-b20.pdf) |
| September 19, 2026 | Cantina | Dynamic upgrades contracts | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_dynamic_upgrades_sep2026.pdf) |
| September 19, 2026 | Cantina | Dynamic upgrades node implementation (Cobalt) | [base/base](https://github.com/base/base/blob/main/audits/cobalt/cobalt-dynamic-upgrades.pdf) |
| October 1, 2026 | Cantina | 200ms blocks node and contracts, including BaseTime and AggregateVerifier (Denim) | [base/contracts](https://github.com/base/contracts/blob/main/audits/cantina_coinbase_200ms_blocks_oct2026.pdf), [base/base](https://github.com/base/base/blob/main/audits/denim/denim-200ms-blocks.pdf) |
| October 2, 2026 | Cantina | B20 precompile v3 (Denim) | [base/base](https://github.com/base/base/blob/main/audits/denim/denim-b20-v3.pdf) |

Dates for base/contracts reports come from the [base/contracts audit index](https://github.com/base/contracts/blob/main/audits/README.md), which also lists the reviewed commit for each report. Dates for base/base reports are the report dates on each cover page.

Audits of the OP Stack components that Base used through OP Stack Upgrade 18, including the bridge and `OptimismPortal` contracts, are in [Optimism's security reviews](https://github.com/ethereum-optimism/optimism/tree/develop/docs/security-reviews).

## Bug Bounties and Audit Competitions

Base runs bug bounty programs on HackerOne (offchain components and infrastructure) and Cantina (deployed smart contracts), and ran a public Immunefi audit competition for the Azul upgrade. See [Report a Vulnerability](https://docs.base.org/specifications/security/report-a-vulnerability.md) for award limits, scope, and how to submit a report.

## Censorship Resistance and Sequencer Liveness

Base currently operates a single active sequencer. The sequencer runs as a high-availability cluster in which leadership transfers to a follower if the current leader stops producing blocks. See [Open-Source Sequencer Components](#open-source-sequencer-components) for the software involved.

If the sequencer censors your transactions or stops producing blocks, you can still get a transaction onto Base by sending it as a [deposit](https://docs.base.org/specifications/base-protocol/bridging/deposits.md) through the `OptimismPortal` contract on Ethereum:

* **Deposits must be included.** Each L1 block defines the deposits that must be included in the first L2 block of its [sequencing epoch](https://docs.base.org/specifications/reference/glossary.md#sequencing-epoch). A block that omits them is invalid under the [derivation rules](https://docs.base.org/specifications/base-protocol/consensus/derivation.md).
* **Maximum delay.** If the sequencer does not post batches to Ethereum, nodes wait one [sequencing window](https://docs.base.org/specifications/reference/glossary.md#sequencing-window) and then derive the missing L2 blocks themselves, including the pending deposits. On Base the sequencing window is 3,600 L1 blocks, about 12 hours at a 12-second L1 block time (see [Configuration](https://docs.base.org/specifications/reference/configuration.md#consensus-parameters)).

Halts and degraded transaction inclusion are reported on [status.base.org](https://status.base.org).

## Proposal Liveness

The [proposer](https://docs.base.org/specifications/base-protocol/proofs/proposer.md) posts Base state to Ethereum by creating dispute games through the `DisputeGameFactory` contract. If it stops creating games, Base keeps producing blocks and processing transactions and deposits, but canonical withdrawals to Ethereum are delayed: a withdrawal can be proven only against a dispute game that covers the Base block it was initiated in (see [Withdrawals](https://docs.base.org/specifications/base-protocol/bridging/withdrawals.md#withdrawal-verification-and-finalization)). Once proposals resume, delayed withdrawals can be proven against the new games.

To check when the last game was created on Base Mainnet, read the newest entry from the [`DisputeGameFactoryProxy`](https://docs.base.org/specifications/reference/base-contracts) on Ethereum. `gameAtIndex` returns the game type, the creation timestamp, and the game address. You can also watch the factory's `DisputeGameCreated` events.

```bash Check the Latest Dispute Game theme={null}
FACTORY=0x43edB88C4B80fDD2AdFF2412A7BebF9dF42cB40e
COUNT=$(cast call $FACTORY "gameCount()(uint256)" --rpc-url $ETH_RPC_URL | awk '{print $1}')
cast call $FACTORY "gameAtIndex(uint256)(uint32,uint64,address)" $((COUNT - 1)) --rpc-url $ETH_RPC_URL
```

Base state is usually proposed within about 20 to 60 minutes, so a gap of several hours since the last game points to a proposal stall. Proposal stalls may be reported as incidents on [status.base.org](https://status.base.org), where you can subscribe to updates.

## Open-Source Sequencer Components

The software that orders and sequences Base transactions is open source:

| Component | Role | Source |
| - | - | - |
| base-consensus | Consensus layer client, run by the sequencer and by node operators | [base/base](https://github.com/base/base/tree/main/crates/consensus) |
| base-reth-node | Execution layer client, including the transaction pool | [base/base](https://github.com/base/base/tree/main/crates/execution) |
| base-builder | Block builder that orders transactions into blocks | [base/base](https://github.com/base/base/tree/main/crates/builder) |
| op-conductor | High-availability controller that elects the sequencer leader | [ethereum-optimism/optimism](https://github.com/ethereum-optimism/optimism/tree/develop/op-conductor) |

The ordering rules these components implement are described in [Transaction Ordering](https://docs.base.org/specifications/transactions/transaction-ordering.md). Node operators independently derive and verify the canonical chain from batches and deposit data published on Ethereum.

## Planned Upgrades

Planned network upgrades and their target activation months are listed on the [Upgrades](https://docs.base.org/upgrades/overview.md) page.
