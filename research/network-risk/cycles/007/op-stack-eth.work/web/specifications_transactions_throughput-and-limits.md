> ## Documentation Index
> Fetch the complete documentation index at: https://docs.base.org/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> For the current source of truth, read https://docs.base.org/llms.txt and connect the Base docs MCP server at https://docs.base.org/mcp.

# Throughput and Limits

> Gas limits and throughput-related network parameters on Base.

Base throughput is constrained by gas limits, data availability throughput, fee market parameters, and endpoint limits. There is no single transactions-per-second value that applies to every workload, because transactions consume different amounts of gas and data.

Base has sustained multiple bursts of over 5,000 TPS, and throughput continues to increase as the chain scales. For more context, see [Introducing Base Azul](https://www.base.org/blog/introducing-base-azul?utm_source=docs).

## Current Limits

| Limit | Value |
| - | - |
| Per-transaction gas maximum | 16,777,216 gas (2^24) |
| Deposit transaction limit | Maximum gas includable in an L1 block (20,000,000 gas) |

### Block Gas Limit

Base produces 5 blocks per second, so the per-second gas capacity is five times the per-block gas limit.

| Network | Gas limit per block | Gas per second at the limit |
| - | - | - |
| Base Mainnet | 40,000,000 gas | 200,000,000 gas |
| Base Sepolia | 120,000,000 gas | 600,000,000 gas |

These values come from the onchain `SystemConfig` gas limit and can change without a protocol upgrade. To read the current per-block gas limit, query a recent block with [`eth_getBlockByNumber`](https://docs.base.org/base-chain/api-reference/ethereum-json-rpc-api/eth_getBlockByNumber) and check its `gasLimit` field:

```bash Terminal theme={null}
curl -s https://mainnet.base.org \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest",false],"id":1}' \
  | jq -r '.result.gasLimit' | xargs printf "%d\n"
```

## Block Production

Base produces a canonical block every 200ms. Each block has its own hash, state root, receipts, and unsafe, safe, and finalized lifecycle.

| Metric | Value |
| - | - |
| Block time | 200ms |
| Blocks per second | 5 |

See [200ms Native Blocks](https://docs.base.org/upgrades/denim/200ms-blocks.md) for the protocol design.

## Per-Transaction Gas Maximum

As of the [Azul hardfork](https://docs.base.org/upgrades/azul/exec-engine.md#transaction-gas-limit-cap), Base enforces a protocol-level per-transaction gas maximum of **16,777,216 gas (2^24)** via [EIP-7825](https://eips.ethereum.org/EIPS/eip-7825). Transactions that specify a gas limit above this value are **rejected during block validation**. `eth_sendTransaction` or `eth_sendRawTransaction` will return a JSON-RPC error (for example: `exceeds maximum per-transaction gas limit`).

> [!NOTE]
>
> Deposit transactions are exempt from this cap. They are limited by the maximum gas includable in an L1 block (20,000,000 gas).

Bundler operators for smart contract wallets must configure their systems to limit the bundle size to fit within this cap.

## Fee Parameters

Fees affect practical throughput because they determine whether transactions can be included when demand approaches available capacity.

For current fee parameters, see [Minimum Base Fee](https://docs.base.org/specifications/transactions/network-fees.md#minimum-base-fee) and [EIP-1559 Fee Parameters](https://docs.base.org/specifications/transactions/network-fees.md#eip-1559-fee-parameters) on the Network Fees page.

## Data Availability Throughput

Base transaction data is posted to Ethereum for data availability. If data availability throughput becomes constrained, the sequencer can limit L2 transaction throughput while the batcher catches up.

During DA throttling, even transactions with high priority fees may be delayed. There is no RPC endpoint that calculates priority fee estimates with throttling in mind. See [Troubleshooting Transactions](https://docs.base.org/specifications/transactions/troubleshooting-transactions.md#priority-fee-too-low) for the transaction-submission implications.

## Endpoint Limits

Public endpoints are rate-limited and are not suitable for production traffic. Hosted RPC providers can also apply request-per-second limits, compute-unit limits, method restrictions, archive-data limits, or WebSocket subscription limits.

Endpoint limits do not change Base protocol capacity, but they can become the practical bottleneck for apps, wallets, indexers, and monitoring systems. For production use, choose an RPC provider from the [Builder Stack](https://docs.base.org/get-started/builder-stack.md) or [run a Base node](https://docs.base.org/specifications/node-operators/run-a-node.md).
