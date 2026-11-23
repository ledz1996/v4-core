> ## Documentation Index
> Fetch the complete documentation index at: https://docs.base.org/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> For the current source of truth, read https://docs.base.org/llms.txt and connect the Base docs MCP server at https://docs.base.org/mcp.

# Transaction Ordering

> How transactions are ordered on Base, including block building with 200ms blocks and validity transactions.

## Overview

This section describes how transactions are ordered on the Base networks.

## Block Building

Base builds a complete canonical block every 200ms. Each block has its own hash, state root, and receipts. Blocks are built by `base-reth-node`, and transactions within each block are ordered by priority fee. See [200ms Native Blocks](https://docs.base.org/upgrades/denim/200ms-blocks.md) for the protocol design.

When a block starts building, the builder takes a snapshot of the transaction pool, and it builds the block only from transactions in that snapshot. This applies to standard transactions and validity transactions alike. A transaction that reaches the sequencer after a block has started building waits for the next block: it becomes eligible for the first block that starts building after it arrives, where it is ordered by priority fee. A transaction can't join the block that is already being built, whatever priority fee it pays.

As soon as a block is built, the sequencer seals it and broadcasts it to the network. It doesn't wait for a fixed deadline, so other nodes receive each block sooner and have more time to react before the next block starts building. If the sequencer doesn't get the signal that a block is ready, it seals the block at the 150ms deadline instead. Early broadcasting doesn't change block contents or timestamps.

## Validity Transactions

A [validity transaction](https://docs.base.org/specifications/build-transaction/validity-transactions.md) competes for inclusion only after every predicate matches. A matching predicate does not reserve block space.

## Mempool Visibility

Base has no public peer-to-peer mempool. Base nodes do not gossip pending transactions to their peers. A node that is not the sequencer forwards the transactions it receives to the sequencer instead of sharing them with other nodes. This stops peer-to-peer propagation, but the node you submit to still sees your transaction.

This limits who can see a pending transaction. It does not guarantee protection from front-running or back-running:

* **Your submission path can see it.** The RPC provider, wallet, or relayer you submit through receives your transaction before the sequencer does. Some share or sell that order flow to searchers.
* **Node transaction-pool methods can list it.** A Base node that serves the `txpool` RPC methods, such as `txpool_content`, returns the pending transactions it holds to anyone who can call it. The public endpoints `https://mainnet.base.org` and `https://sepolia.base.org` do not serve the `txpool` namespace (see [Connect to Base](https://docs.base.org/get-started/connect-to-base.md)), but other RPC providers and self-run nodes can enable it.
* **Ordering is by priority fee.** Anyone who sees your transaction before it is included can set the priority fee on their own transaction to try to place it ahead of or behind yours.
* **Transactions are not encrypted.** The sequencer sees every transaction in plaintext and orders it using the rules on this page.

To limit who sees your pending transactions, submit them through an RPC endpoint you trust.

## Source Code

The components that implement these ordering rules, including the block builder and the transaction pool, are open source. See [Open-Source Sequencer Components](https://docs.base.org/specifications/security/reliability-and-liveness.md#open-source-sequencer-components).
