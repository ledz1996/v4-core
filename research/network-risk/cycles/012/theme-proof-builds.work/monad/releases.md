> ## Documentation Index
> Fetch the complete documentation index at: https://docs.monad.xyz/llms.txt
> Use this file to discover all available pages before exploring further.

# Releases

This page catalogues every notable release. Some releases target only specific networks.

> [!NOTE]
>
> We group changes into
>
> * protocol changes (generally requiring a new [Revision](https://docs.monad.xyz/developer-essentials/changelog#revisions))
>   * generally tagged with **\[EVM]**, **\[Consensus]**, or **\[Network params]**
> * RPC/SDK behavioral changes (generally tagged with **\[RPC]**)
> * performance changes
>   * tagged based on the nature of the change as **\[EVM]**, **\[Consensus]**, or **\[RPC]**
> * internal/node-ops changes (generally tagged as **\[Node ops]**)

## v0.16.7

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-11-19 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.7`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.7) (`670b8ce51`)
* `monad` (execution): [tag `v0.16.7`](https://github.com/category-labs/monad/releases/tag/v0.16.7) (`2690448ba`)

#### Highlights

* **Memory-bounded snapshot restore on page-encoded databases.** A new v2 binary-snapshot format groups storage by page so the loader can flush mid-shard, keeping peak memory bounded when restoring into a post–MIP-8 page-encoded database. This fixes out-of-memory kills seen when restoring on hosts with ≤48 GB RAM. Producing and restoring v2 snapshots both require v0.16.7 or newer; see the [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.7.md).
  * Ref: [monad (execution) PR #2464](https://github.com/category-labs/monad/pull/2464), [monad (execution) PR #2812](https://github.com/category-labs/monad/pull/2812)

#### Notable node-ops changes

* **\[Node ops]** `monad-cli --load-binary-snapshot` adds `--load-buffer-size` and lowers the default load flush threshold from 10 GiB to 5 GiB, bounding loader memory when restoring v2 snapshots.
  * Ref: [monad (execution) PR #2812](https://github.com/category-labs/monad/pull/2812)
* **\[Node ops]** `monad-cli --dump-binary-snapshot` now defaults to `--snapshot-format v1` (previously v0). Snapshot producers that need memory-bounded restores on low-RAM hosts should dump with `--snapshot-format v2`.
  * Ref: [monad (execution) PR #2464](https://github.com/category-labs/monad/pull/2464)

## v0.16.6

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.6`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.6) (`656435c15`)
* `monad` (execution): [tag `v0.16.6`](https://github.com/category-labs/monad/releases/tag/v0.16.6) (`4a0c81f54`)

#### Highlights

* **Debian packages for the node.** A native binary build script and a Debian package build were added, and packages now stamp the submodule commit and resolve the triedb driver via `ldd`.
  * Ref: [monad-bft PR #3277](https://github.com/category-labs/monad-bft/pull/3277)
* **Dual Prometheus/OTLP metrics export.** The node can now export metrics over both Prometheus and OTLP from a shared configuration.
  * Ref: [monad-bft PR #3275](https://github.com/category-labs/monad-bft/pull/3275)
* **State sync protocol v3 with page-encoded storage.** State sync now negotiates v3 and relays page-encoded storage records (protocol 1.3), with runloop\_monad and statesync assuming a page-encoded primary timeline.
  * Ref: [monad (execution) PR #2483](https://github.com/category-labs/monad/pull/2483), [monad (execution) PR #2551](https://github.com/category-labs/monad/pull/2551)
* **`monad-mpt --upgrade` and `--repair` removed.** The `--upgrade` flag together with the MONAD007 migration, and the `--repair` flag, have been dropped; operators who relied on them should follow the [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.6.md).
  * Ref: [monad (execution) PR #2709](https://github.com/category-labs/monad/pull/2709)

#### Notable RPC/SDK changes

* **\[RPC]** `eth_simulateV1` now returns simulation failures as error values carrying a bespoke simulation error type instead of throwing.
  * Ref: [monad (execution) PR #2556](https://github.com/category-labs/monad/pull/2556), [monad (execution) PR #2557](https://github.com/category-labs/monad/pull/2557)

#### Notable robustness changes

* **\[Consensus]** Legacy transaction signature `v` values outside the EIP-155 range are now rejected during RLP decoding.
  * Ref: [monad (execution) PR #2606](https://github.com/category-labs/monad/pull/2606)
* **\[Consensus]** High-S secp signatures are now rejected at deserialization, and the node commits to an encoding scheme rather than header bytes.
  * Ref: [monad-bft PR #3248](https://github.com/category-labs/monad-bft/pull/3248)
* **\[EVM]** An empty typed transaction is now rejected with an error instead of tripping an assertion.
  * Ref: [monad (execution) PR #2604](https://github.com/category-labs/monad/pull/2604)
* **\[EVM]** Memory bounds are now checked once per offset stack element.
  * Ref: [monad (execution) PR #2667](https://github.com/category-labs/monad/pull/2667)

#### Notable performance changes

* **\[EVM]** Reusing cached stack storage now establishes the involved lifetimes.
  * Ref: [monad (execution) PR #2603](https://github.com/category-labs/monad/pull/2603)
* **\[EVM]** Cached allocations are now given a concrete deleter.
  * Ref: [monad (execution) PR #2634](https://github.com/category-labs/monad/pull/2634)

#### Notable internal changes

* **\[Consensus]** Raptorcast now canonicalizes the depth and reserved fields.
  * Ref: [monad-bft PR #3247](https://github.com/category-labs/monad-bft/pull/3247)
* **\[Node ops]** The monad-wireauth per-session buffer limit is raised to 2 MiB.
  * Ref: [monad-bft PR #3294](https://github.com/category-labs/monad-bft/pull/3294)
* **\[Node ops]** monad-dataplane now applies global and per-peer UDP pacing.
  * Ref: [monad-bft PR #3175](https://github.com/category-labs/monad-bft/pull/3175)
* **\[Node ops]** statesync now aborts when a socket path is too long for `sun_path` instead of proceeding.
  * Ref: [monad (execution) PR #2598](https://github.com/category-labs/monad/pull/2598)
* **\[Node ops]** Backtrace storage is now aligned and frames are preserved on truncation.
  * Ref: [monad (execution) PR #2624](https://github.com/category-labs/monad/pull/2624)
* **\[EVM]** Literal-value shifts are emitted as two unaligned loads, and CLZ is emitted without branches or a stack spill and interpreted without branching on its input.
  * Ref: [monad (execution) PR #2631](https://github.com/category-labs/monad/pull/2631), [monad (execution) PR #2632](https://github.com/category-labs/monad/pull/2632), [monad (execution) PR #2633](https://github.com/category-labs/monad/pull/2633)
* **\[EVM]** Block-exit stack writes are now independent of heap addresses and avoid store forwarding stalls.
  * Ref: [monad (execution) PR #2644](https://github.com/category-labs/monad/pull/2644), [monad (execution) PR #2660](https://github.com/category-labs/monad/pull/2660)
* **\[EVM]** The zkvm gains a guest library with a two-mode CMake build, ZisK and SP1 backend crates, and an `execute_block_zkvm` runner with an x86 test runner.
  * Ref: [monad (execution) PR #2554](https://github.com/category-labs/monad/pull/2554), [monad (execution) PR #2288](https://github.com/category-labs/monad/pull/2288)

***

## v0.16.5

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-10-22 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-10-15 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.5`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.5) (`33d9d5c03`)
* `monad` (execution): [tag `v0.16.5`](https://github.com/category-labs/monad/releases/tag/v0.16.5) (`a3b16af1a`)

#### Highlights

* **`--triedb-path` must name the triedb device**, not a directory containing it. Packaged installs already pass `/dev/triedb` and need no change; custom deployments should check before upgrading. See the [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.5.md).
* **`monad-mpt --grow` uses the space added when the triedb device is extended in place**, so archive nodes running out of disk no longer need a full `--archive` and `--restore` onto a new device. See the [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.5.md) for the required order.
* **Triedb update and compaction counters are exported as Prometheus gauges** on packaged installs.
* **`eth_simulateV1` enforces a maximum response size**, and an empty full state override now matches Geth.

#### Notable RPC/SDK changes

* **\[RPC]** An empty full state override now zeroes the overridden account's storage, matching Geth.
  * Ref: [monad (execution) PR #2571](https://github.com/category-labs/monad/pull/2571)
* **\[RPC]** `eth_simulateV1` enforces the configured maximum response size.
  * Ref: [monad (execution) PR #2395](https://github.com/category-labs/monad/pull/2395), [monad-bft PR #3156](https://github.com/category-labs/monad-bft/pull/3156)
* **\[RPC]** `eth_simulateV1` and related paths exit gracefully when a block state merge fails, instead of terminating the request abnormally.
  * Ref: [monad (execution) PR #2565](https://github.com/category-labs/monad/pull/2565), [monad (execution) PR #2570](https://github.com/category-labs/monad/pull/2570)

#### Notable robustness changes

* **\[EVM]** Hardened RLP decoding of EIP-2718 transactions and EIP-4844 blob hash lists, and fixed list-prefix encoding writing past its size.
  * Ref: [monad (execution) PR #2555](https://github.com/category-labs/monad/pull/2555), [monad (execution) PR #2569](https://github.com/category-labs/monad/pull/2569)
* **\[EVM]** Hardened the offset trie decoder: the constructor validates that the data forms a tree, path length is bounded at `MAX_PATH_NIBBLES`, and an out-of-bounds read in `checked_end` is fixed. Not reachable in production: the offset trie is used only by execution-witness decoding, which has no caller in node execution today.
  * Ref: [monad (execution) PR #2496](https://github.com/category-labs/monad/pull/2496)
* **\[Node ops]** The execution event recorder no longer passes a null buffer to `mempcpy` when `--record-exec-events` is on.
  * Ref: [monad (execution) PR #2580](https://github.com/category-labs/monad/pull/2580)
* **\[RPC]** The triedb range query now validates its prefix key length, closing an over-read of the caller's buffer.
  * Ref: [monad (execution) PR #2599](https://github.com/category-labs/monad/pull/2599)
* **\[Node ops]** Fixed two shutdown races: fiber pool threads could free their scheduler while another thread was still waking them, and the VM compile thread's lock was released from the wrong thread.
  * Ref: [monad (execution) PR #2594](https://github.com/category-labs/monad/pull/2594), [monad (execution) PR #2593](https://github.com/category-labs/monad/pull/2593)

#### Notable performance changes

* **\[Node ops]** The triedb storage pool is a single device. Opening a 700 GiB pool uses roughly 29% less peak memory in `monad-mpt`. Existing pools open unchanged.
  * Ref: [monad (execution) PR #2562](https://github.com/category-labs/monad/pull/2562), [monad-bft PR #3270](https://github.com/category-labs/monad-bft/pull/3270)
* **\[EVM]** Widened the `JUMPDEST` scan index to 64-bit.
  * Ref: [monad (execution) PR #2553](https://github.com/category-labs/monad/pull/2553)

#### Notable internal changes

* **\[Node ops]** `monad-mpt --grow` takes up the space after the triedb device is extended in place with `lvextend` or a grown RAID array. It runs offline in seconds, moves no data, and can be re-run if interrupted. The node must run once on this release before the device is extended; a device extended earlier is refused.
  * Ref: [monad (execution) PR #2563](https://github.com/category-labs/monad/pull/2563)
* **\[Node ops]** `monad-node` exports seven triedb update/compaction gauges read from a statistics file written by execution. The packaged units set `--db-stats-file` and `--triedb-stats-path` to the same path; both are off by default.
  * Ref: [monad (execution) PR #2552](https://github.com/category-labs/monad/pull/2552), [monad-bft PR #3264](https://github.com/category-labs/monad-bft/pull/3264)
* **\[EVM]** The bn128 precompiles (`ecAdd`, `ecMul`, `ecPairing`) are vendored in-tree with unchanged semantics, and `ecrecover` shares one implementation with transaction sender recovery.
  * Ref: [monad (execution) PR #2522](https://github.com/category-labs/monad/pull/2522), [monad (execution) PR #2547](https://github.com/category-labs/monad/pull/2547)
* **\[EVM]** MIP-8 page-storage accounting is routed through the EVMC host interface. No behaviour change.
  * Ref: [monad (execution) PR #2548](https://github.com/category-labs/monad/pull/2548)
* Upgraded `h2`, `rustls` and related TLS dependencies.
  * Ref: [monad-bft PR #3268](https://github.com/category-labs/monad-bft/pull/3268)

***

## v0.16.4

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-09-28 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | N/A | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.4`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.4) (`2a2bcc046`)
* `monad` (execution): [tag `v0.16.4`](https://github.com/category-labs/monad/releases/tag/v0.16.4) (`f6a86a1a4`)

#### Notable internal changes

* **\[Node ops]** Added `--snapshot-format` flag to choose the layout a snapshot dump writes.
  * Ref: monad (execution) [PR #2566](https://github.com/category-labs/monad/pull/2566)
* **\[Node ops]** `monad-ledger-tail` now logs `gas_used` on each proposed block.
  * Ref: [monad-bft PR #3271](https://github.com/category-labs/monad-bft/pull/3271)

***

## v0.16.3

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-09-17 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.3`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.3) (`d12edcbc0`)
* `monad` (execution): [tag `v0.16.3`](https://github.com/category-labs/monad/releases/tag/v0.16.3) (`c1594ff80`)

#### Highlights

* **State Archive nodes no longer pay 2x write amplification past MIP-8** — historical nodes commit only the page-encoded timeline after the fork, and reads route per requested block version. Archive nodes that skipped the v0.16.1 hot-fix need a one-time `monad-mpt --storage <path> --promote-secondary` after installing; see the [upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.3.md).
* **Snapshot streams are versioned** — every stream carries an eight-byte header, so a format mismatch aborts loudly instead of misparsing.
* **Statesync protocol v0/v1 retired**, leaving a single implemented protocol version.

#### Notable RPC/SDK changes

* **\[RPC]** Storage encoding is routed by timeline past the MIP-8 cutoff. `TriedbEnv` tracks the migration phase and `primary_earliest`, so `get_storage_at` selects page or slot encoding according to the requested block version.
  * Ref: [monad-bft PR #3238](https://github.com/category-labs/monad-bft/pull/3238), [monad (execution) PR #2529](https://github.com/category-labs/monad/pull/2529)
* **\[RPC]** Filter methods return `InvalidParams` for a malformed `eth` filter rather than an internal error.
  * Ref: [monad-bft PR #3241](https://github.com/category-labs/monad-bft/pull/3241)

#### Notable robustness changes

* **\[Node ops]** Every snapshot stream (`eth_header`, `account`, `storage`, `code`) is opened with an eight-byte versioned header carrying a magic, version, kind and guard byte. An unrecognised version or a shard assembled from mismatched files aborts with a clear message instead of misparsing. Snapshots produced by this release cannot be read by earlier binaries.
  * Ref: [monad (execution) PR #2463](https://github.com/category-labs/monad/pull/2463)
* **\[EVM]** Fixed a 32-byte over-read of the EVM output buffer in `mce`.
  * Ref: [monad (execution) PR #2533](https://github.com/category-labs/monad/pull/2533)
* **\[EVM]** Fixed the leaf-on-branch hex-prefix in `VarLenMerkleCompute` and `RootVarLenMerkleCompute`, which diverged from the canonical Ethereum root for a branch node carrying both children and a value. Not reachable in production: every production variable-length trie is keyed by a prefix-free set, so no committed root was affected.
  * Ref: [monad (execution) PR #2442](https://github.com/category-labs/monad/pull/2442)
* **\[Consensus]** `proposal_basics` now finalizes in order.
  * Ref: [monad (execution) PR #2519](https://github.com/category-labs/monad/pull/2519)
* **\[EVM]** Bounded the push-immediate walk in `show_opcodes`.
  * Ref: [monad (execution) PR #2534](https://github.com/category-labs/monad/pull/2534)

#### Notable performance changes

* **\[EVM]** P-256 curve parameters are cached per thread in `p256_verify_impl`.
  * Ref: [monad (execution) PR #2525](https://github.com/category-labs/monad/pull/2525)
* **\[Node ops]** State Archive nodes commit only the page-encoded timeline past the MIP-8 fork, removing the 2x disk growth rate that dual-timeline committing caused in v0.16.1. The RODb secondary handle also shares the primary's service thread.
  * Ref: [monad (execution) PR #2529](https://github.com/category-labs/monad/pull/2529)

#### Notable internal changes

* **\[Consensus]** Statesync protocol v0 and v1 are retired and the version constants are derived from execution's `statesync_version.h` through a new `monad-statesync-version` crate. `STATESYNC_VERSION_MIN` rises to v2, the `StateSyncUpsertV0` encoding is removed, and a peer still speaking v0 or v1 is rejected with `BadVersion`.
  * Ref: [monad-bft PR #3211](https://github.com/category-labs/monad-bft/pull/3211), [monad (execution) PR #2487](https://github.com/category-labs/monad/pull/2487)
* **\[EVM]** EIP-7981 (increased access list cost) is implemented behind `eip_7981_active`, which is active only for EVM revisions at or above `MONAD_ETH_AMSTERDAM`. Not reachable on any current network.
  * Ref: [monad (execution) PR #2490](https://github.com/category-labs/monad/pull/2490)
* **\[EVM]** `ethash` is replaced with an in-house `hash256` type and keccak implementation. This also corrects a `SHA3_squeeze` arity mismatch that produced a wrong digest for every input on non-x86\_64 builds.
  * Ref: [monad (execution) PR #2507](https://github.com/category-labs/monad/pull/2507)
* **\[EVM]** `silkpre_recover_address` is replaced with `monad_recover_address`, and the vendored secp256k1 is linked directly.
  * Ref: [monad (execution) PR #2520](https://github.com/category-labs/monad/pull/2520), [monad (execution) PR #2488](https://github.com/category-labs/monad/pull/2488)
* **\[Node ops]** Trie update statistics are made monotonic via a snapshot API.
  * Ref: [monad (execution) PR #2502](https://github.com/category-labs/monad/pull/2502)
* **\[EVM]** The zkVM precompiles architecture is refactored.
  * Ref: [monad (execution) PR #2209](https://github.com/category-labs/monad/pull/2209)

## v0.16.2

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-09-10 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-09-03 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.2`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.2) (`4374d389e`)
* `monad` (execution): [tag `v0.16.2+1`](https://github.com/category-labs/monad/releases/tag/v0.16.2%2B1) (`aae93c535`)

#### Highlights

* **Raptorcast v1 publish** — nodes now publish proposals in the v1 raptorcast wire format on both the primary and secondary paths.
* **JSON-RPC error codes corrected** across `eth_call`, `eth_estimateGas`, `eth_simulateV1`, `debug_*` and `txpool_*`.
* Raptorcast throughput improved \~16.7% under multi-target load.

#### Notable protocol changes

* **\[Consensus]** Raptorcast advances to the `accept_both_publish_v1` stage; nodes publish proposals in the v1 wire format on both primary and secondary paths.
  * Ref: [monad-bft PR #3177](https://github.com/category-labs/monad-bft/pull/3177)
* **\[Consensus]** `AdvanceRound` is published to full nodes via broadcast rather than secondary raptorcast, avoiding a collision with the proposal commitment under v1.
  * Ref: [monad-bft PR #3176](https://github.com/category-labs/monad-bft/pull/3176)

#### Notable RPC/SDK changes

* **\[RPC]** Fix JSON-RPC error codes and messages returned by the call, simulate, debug, txpool and websocket handlers.
  * Ref: [monad-bft PR #3228](https://github.com/category-labs/monad-bft/pull/3228)
* **\[RPC]** Fix zero-fee `eth_call`s — a zero `maxFeePerGas` is no longer raised to the base fee, matching geth and reth.
  * Ref: [monad-bft PR #3164](https://github.com/category-labs/monad-bft/pull/3164)
* **\[RPC]** Fix EIP-1898 compatibility for `BlockTagOrHash`.
  * Ref: [monad-bft PR #3163](https://github.com/category-labs/monad-bft/pull/3163)
* **\[RPC]** `eth_createAccessList` now accepts state overrides.
  * Ref: [monad-bft PR #3179](https://github.com/category-labs/monad-bft/pull/3179)

#### Notable robustness changes

* **\[Consensus]** A validator publishes only the first accepted proposal to its full nodes, so an equivocated proposal is no longer forwarded.
  * Ref: [monad-bft PR #3180](https://github.com/category-labs/monad-bft/pull/3180)
* **\[RPC]** Concurrency limiter for `eth_feeHistory`, bounding memory on large block ranges.
  * Ref: [monad-bft PR #3212](https://github.com/category-labs/monad-bft/pull/3212)
* **\[EVM]** Runloop fix for when the node resets to the start block number.
  * Ref: [monad (execution) PR #2501](https://github.com/category-labs/monad/pull/2501)

#### Notable performance changes

* **\[Consensus]** Raptorcast avoids redundant wire-auth lookups in the authenticated send path — 15,796 to 18,427 chunks/s.
  * Ref: [monad-bft PR #3223](https://github.com/category-labs/monad-bft/pull/3223)

#### Notable internal changes

* **\[Node ops]** Nodes can opt out of serving statesync requests. Optional `node.toml` setting, default unchanged.
  * Ref: [monad-bft PR #3208](https://github.com/category-labs/monad-bft/pull/3208)
* **\[Node ops]** Update the `openssl` crate to 0.10.81, closing seven advisories. Reached only through `monad-rpc` with a MongoDB archive backend configured; `monad-node` does not link it.
  * Ref: [monad-bft PR #3191](https://github.com/category-labs/monad-bft/pull/3191)
* **\[EVM]** Seed `Address`, `bytes32` and `StorageKey` hashing per process, so colliding keys cannot be precomputed against node-local maps.
  * Ref: [monad (execution) PR #2462](https://github.com/category-labs/monad/pull/2462)
* **\[EVM]** Replace silkpre's ECRECOVER precompile with a vendored `monad_recover_address` on system libsecp256k1. Adds a `libsecp256k1-dev` build dependency outside the published Docker images.
  * Ref: [monad (execution) PR #2437](https://github.com/category-labs/monad/pull/2437)
* **\[EVM]** Allow dual-db commit in `runloop_monad_ethblocks` where `secondary_db` is optional.
  * Ref: cherry-pick from `staging-v0.16.1` (`df14e67bb`)
* **\[EVM]** Consolidate dual-db mirroring with `for_each_db`.
  * Ref: cherry-pick from `staging-v0.16.1` (`d836afc18`)

## v0.16.1

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | Required before MONAD\_TEN activation at 2026-09-02 14:30 UTC |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | N/A | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.1`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.1) (`12b7017d6`)
* `monad` (execution): [tag `v0.16.1`](https://github.com/category-labs/monad/releases/tag/v0.16.1) (`7279dfc7b`)

#### Highlights

* **MONAD\_TEN activation on mainnet** — MIP-8 (page-encoded storage) activates on mainnet at timestamp `1788359400` (2026-09-02 14:30 UTC). This is the mainnet counterpart to the testnet activation shipped in v0.16.0.
* **Page-encoded timeline now required on mainnet** — a mainnet node must present either a page-encoded primary (Phase C) or an active secondary timeline (Phase A/B dual-db), or it will fail to start.
* Dual-db commit support in the ethblocks runloop, allowing nodes still in Phase A/B to commit to both timelines.

#### Notable protocol changes

* **\[EVM]** Set the MONAD\_TEN activation timestamp for mainnet — `1788359400` (2026-09-02 14:30 UTC). MONAD\_NINE rules remain in effect below that timestamp.
  * Ref: [monad (execution) PR #2489](https://github.com/category-labs/monad/pull/2489)
* **\[EVM]** Enforce the page-encoded timeline assertion on mainnet — previously testnet-only. Nodes that have not completed Phase A (dual-db activation) will fail to start. See [MIP-8 Activation and Page Storage Migration](https://docs.monad.xyz/node-ops/upgrade-instructions/page-storage-mip-8-migration.md).
  * Ref: [monad (execution) PR #2489](https://github.com/category-labs/monad/pull/2489)

#### Notable robustness changes

* **\[Consensus]** monad-dataplane: fall back gracefully when io\_uring buffer ring setup fails, rather than failing node startup.
  * Ref: [monad-bft PR #3201](https://github.com/category-labs/monad-bft/pull/3201)
* **\[EVM]** Allow dual-db commit in `runloop_monad_ethblocks` where the secondary db is optional, so Phase A/B nodes commit to both timelines.

#### Notable internal changes

* **\[EVM]** Consolidate dual-db mirroring behind `for_each_db`, replacing duplicated commit paths in the runloop.
* **\[Consensus]** Fix the buffer-ring fallback build by removing a stale metrics argument.

## v0.16.0

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-08-06 | Adopted 2026-08-06 to 2026-08-08 |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.16.0`](https://github.com/category-labs/monad-bft/releases/tag/v0.16.0) (`c616743d1`)
* `monad` (execution): [tag `v0.16.0`](https://github.com/category-labs/monad/releases/tag/v0.16.0) (`e81ffe31c`)

#### Highlights

* **MONAD\_TEN activation** — MIP-8 (page-encoded storage) activates on testnet at timestamp `1786545000` (2026-08-12 14:30 UTC). Mainnet activation not yet set (staged rollout).
* Protocol-level change requiring a version bump from v0.15.x to v0.16.0.
* Robustness fixes, performance improvements, and internal refactors on top of v0.15.2.

#### Notable protocol changes

* **\[EVM]** Activate MONAD\_TEN — MIP-8 (page-encoded storage) activation on testnet (2026-08-12 14:30 UTC). Requires dual-db mode; nodes that have not completed Phase A will fail to start.
  * Ref: [monad (execution) PR #2459](https://github.com/category-labs/monad/pull/2459)

#### Notable robustness changes

* **\[EVM]** Enforce page-encoded timeline assertion on testnet — nodes that have not completed Phase A (dual-db activation) will fail to start. See [MIP-8 Activation and Page Storage Migration](https://docs.monad.xyz/node-ops/upgrade-instructions/page-storage-mip-8-migration.md). Ref: [monad (execution) PR #2475](https://github.com/category-labs/monad/pull/2475)
* **\[Consensus]** Reject storage keys over 32 bytes. Ref: [monad-bft PR #3160](https://github.com/category-labs/monad-bft/pull/3160)
* **\[Consensus]** Raptorcast: hardening secondary raptorcast client. Ref: [monad-bft PR #3157](https://github.com/category-labs/monad-bft/pull/3157)
* **\[EVM]** Throw on maximum code size exceeded; dispatch `MONAD_ASSERT_THROW` through `MONAD_THROW`. Ref: [monad (execution) PR #2415](https://github.com/category-labs/monad/pull/2415)
* **\[EVM]** mpt: bound promote target `primary_ring_idx` to a valid ring selector. Ref: [monad (execution) PR #2421](https://github.com/category-labs/monad/pull/2421)

#### Notable performance changes

* **\[EVM]** Tweak runtime `signextend` for better codegen. Ref: [monad (execution) PR #1527](https://github.com/category-labs/monad/pull/1527)

#### Notable internal changes

* **\[Node ops]** Enable metrics endpoint by default. Ref: [monad-bft PR #3167](https://github.com/category-labs/monad-bft/pull/3167)
* **\[EVM]** Refactor ECDSA signature recovery (incl. `EcdsaSignature` rename). Ref: [monad (execution) PR #2402](https://github.com/category-labs/monad/pull/2402)
* **\[EVM]** Dedup storage read path across `TrieDb` and `TrieRODb`. Ref: [monad (execution) PR #2436](https://github.com/category-labs/monad/pull/2436)
* **\[EVM]** Dedup page→slot fan-out behind `StoragePageSlots`. Ref: [monad (execution) PR #2434](https://github.com/category-labs/monad/pull/2434)
* **\[EVM]** Vendor blake2b compression, replacing silkpre's BLAKE2F precompile. Ref: [monad (execution) PR #2418](https://github.com/category-labs/monad/pull/2418)
* **\[EVM]** snapshot: raise fd limit, fail fast, report open errors on dump. Ref: [monad (execution) PR #2419](https://github.com/category-labs/monad/pull/2419)
* **\[EVM]** Add `is_code_tracer` to `StateTracer`. Ref: [monad (execution) PR #2448](https://github.com/category-labs/monad/pull/2448)
* **\[EVM]** Runloop as a C library. Ref: [monad (execution) PR #2021](https://github.com/category-labs/monad/pull/2021)

## v0.15.2

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-07-27 | Adopted 2026-07-27 to 2026-07-31 |

Tags or hashes:

* `monad-bft` (consensus): `staging-v0.15.2` (`6373056bf`)
* `monad` (execution): `staging-v0.15.2` (`2422a8592`)

#### Highlights

* **MIP-8 gas schedule** — adds page-based storage gas schedule; `eth_createAccessList` deduplicates storage keys by page (activation in a future release)
* **Follow-up to MIP-12: Block reward validation** — maximum block reward is now validated; blocks exceeding the cap are rejected
* **EIP-7843: Consensus round in tx context** — Monad consensus round number threaded into `evmc_tx_context` via `BlockHeader::slot_number`
* **Dual-timeline DB support** — MPT database supports a secondary page-encoded timeline; statesync works with both slot- and page-encoded databases

#### Notable consensus/protocol changes

* **\[Consensus]** Raptorcast: rollout deterministic stage 1 — enroll all nodes to "accept both publish v0". Ref: [monad-bft PR #3143](https://github.com/category-labs/monad-bft/pull/3143)
* **\[Execution]** MIP-8: Gas schedule for page-based storage — adds page-based gas schedule (activation in a future release). Ref: [monad (execution) PR #2268](https://github.com/category-labs/monad/pull/2268), [monad-bft PR #3150](https://github.com/category-labs/monad-bft/pull/3150)
* **\[Execution]** Follow-up to MIP-12: Validate maximum block reward — blocks exceeding the cap are now rejected. Ref: [monad (execution) PR #2365](https://github.com/category-labs/monad/pull/2365)
* **\[Execution]** EIP-7843: Thread Monad consensus round into `evmc_tx_context` via `BlockHeader::slot_number`. Ref: [monad (execution) PR #2324](https://github.com/category-labs/monad/pull/2324)
* **\[Execution]** AMSTERDAM EVM revision — new EVM revision targeting the Amsterdam hardfork. Ref: [monad (execution) PR #2368](https://github.com/category-labs/monad/pull/2368)

#### Notable RPC/SDK changes

* **\[RPC]** `eth_createAccessList` now deduplicates storage keys by page under MIP-8. Ref: [monad (execution) PR #2253](https://github.com/category-labs/monad/pull/2253)
* **\[RPC]** Fix `eth_getStorageAt` returning 0 on page-encoded nodes. Ref: [monad-bft PR #3153](https://github.com/category-labs/monad-bft/pull/3153), [monad (execution) PR #2393](https://github.com/category-labs/monad/pull/2393)
* **\[RPC]** `eth_call` execution revert error code changed from `-32603` to `3` — aligns with standard EVM behavior. Ref: [monad-bft PR #2683](https://github.com/category-labs/monad-bft/pull/2683)

#### Notable robustness changes

* **\[Consensus]** Raptorcast: reject group invites with unreasonable round span. Ref: [monad-bft PR #3145](https://github.com/category-labs/monad-bft/pull/3145)
* **\[Consensus]** Wireauth: remove unsafe mutation before responder key is verified. Ref: [monad-bft PR #3140](https://github.com/category-labs/monad-bft/pull/3140)
* **\[Consensus]** Raptorcast: bound memory usage on `RoundInfoCache`. Ref: [monad-bft PR #3132](https://github.com/category-labs/monad-bft/pull/3132)
* **\[Consensus]** `monad-state`: limit forwarded txs per message. Ref: [monad-bft PR #3015](https://github.com/category-labs/monad-bft/pull/3015)
* **\[Execution]** Memory-bounded LRU cache for execution state reads. Ref: [monad (execution) PR #2376](https://github.com/category-labs/monad/pull/2376)
* **\[Execution]** Statesync: reject messages with trailing bytes. Ref: [monad (execution) PR #2370](https://github.com/category-labs/monad/pull/2370)
* **\[Execution]** Trim both timelines in tandem in dynamic history length adjustment. Ref: [monad (execution) PR #2431](https://github.com/category-labs/monad/pull/2431)
* **\[Execution]** Expose dual-DB migration phase via FFI. Ref: [monad (execution) PR #2433](https://github.com/category-labs/monad/pull/2433)
* **\[Execution]** Fix `monad-mpt --activate-secondary` corrupting DB metadata on nodes that previously ran `--upgrade`; adds `monad-mpt --repair` to recover affected pools. Ref: [monad (execution) PR #2403](https://github.com/category-labs/monad/pull/2403)
* **\[Execution]** DbCache read-through caching — reads now cached on miss, reducing redundant disk reads during page-encoded commit. Ref: [monad (execution) PR #2414](https://github.com/category-labs/monad/pull/2414)

#### Notable internal changes

* **\[Consensus]** Prometheus config moved to `node.toml` — `prometheus_addr` and options now in `[prometheus]` section; CLI flags removed. Ref: [monad-bft PR #3141](https://github.com/category-labs/monad-bft/pull/3141)
* **\[Consensus]** Expose triedb migration-phase as a Prometheus metric. Ref: [monad-bft PR #3169](https://github.com/category-labs/monad-bft/pull/3169)
* **\[Execution]** Dual-timeline: MPT database supports a secondary timeline. Ref: [monad (execution) PR #2228](https://github.com/category-labs/monad/pull/2228), [PR #2302](https://github.com/category-labs/monad/pull/2302)
* **\[Execution]** Page storage: TrieDb and runloop are page-encoding-aware; statesync works with page-encoded databases. Ref: [monad (execution) PR #2354](https://github.com/category-labs/monad/pull/2354), [PR #2383](https://github.com/category-labs/monad/pull/2383), [PR #2385](https://github.com/category-labs/monad/pull/2385), [PR #2386](https://github.com/category-labs/monad/pull/2386)
* **\[Execution]** `monad-cli --version` now accepts `latest_finalized`. Ref: [monad (execution) PR #2364](https://github.com/category-labs/monad/pull/2364)
* **\[Execution]** Support binary snapshot dump/load on secondary timeline and page-encoded DB. Ref: [monad (execution) PR #2366](https://github.com/category-labs/monad/pull/2366)

## v0.15.1

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | Round 89758000 (\~2026-07-23 14:30UTC); hard fork |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | N/A | Received this in v0.15.0 |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.15.1`](https://github.com/category-labs/monad-bft/releases/tag/v0.15.1) (`fb3328c2e`)
* `monad` (execution): [tag `v0.15.1`](https://github.com/category-labs/monad/releases/tag/v0.15.1) (`817a09f64`) — unchanged from v0.15.0

v0.15.1 is a **consensus-only patch** on top of v0.15.0. The execution layer is unchanged.

#### Changes

* **\[Consensus] MIP-12: Populate mainnet block reward activation** — sets the mainnet activation round for the vote pace change and block reward update (25 → 18 MON) at Round 89,758,000. Ref: [monad-bft PR #3168](https://github.com/category-labs/monad-bft/pull/3168)

## v0.15.0

> [!NOTE]
>
> v0.14.6 and v0.14.7 were not deployed to external node operators. Their changes are included in this release.

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | Received this in v0.15.1 |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | N/A | Round 43821000 (\~2026-07-09 14:30UTC); hard fork |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.15.0`](https://github.com/category-labs/monad-bft/releases/tag/v0.15.0) (`8facc4fae`)
* `monad` (execution): [tag `v0.15.0`](https://github.com/category-labs/monad/releases/tag/v0.15.0) (`817a09f64`)

#### Highlights

* **MIP-12: Decrease Block Times** — block times reduced from 400 ms to 300 ms; rewards per block reduced proportionally
* **`eth_simulateV1`** — new RPC endpoint for simulating multiple transactions across multiple blocks with state and block overrides; node operators can enable by adding `--enable-eth-simulate-v1` (default: off)
* **Node operators: one-time DB metadata migration required** (`monad-mpt --upgrade`; see [v0.15.0 upgrade instructions](https://docs.monad.xyz/node-ops/upgrade-instructions/v0.15.0.md)) — bumps DB schema MONAD007 → MONAD008, initializing secondary timeline metadata for upcoming dual-timeline support
* **RPC batch concurrency limit** — new server-side cap on concurrent batch requests to defend against resource exhaustion
* **Raptorcast starvation fix** — defending against possible networking message starvation in raptorcast
* **Prometheus metrics migration** — node metrics now backed by the prometheus crate for better observability

#### Notable consensus/protocol changes

* **\[Consensus]** MIP-12: Revise vote pace from 400 ms to 300 ms; revise block rewards proportionally from 25 MON/block to 18 MON/block
  * Ref: [monad-bft PR #3120](https://github.com/category-labs/monad-bft/pull/3120)
* **\[Network params]** MIP-12: Reduce block gas limit from 200M to 150M, holding gas throughput at 500 Mgas/s as block time drops from 400 ms to 300 ms
  * The per-block transaction limit correspondingly drops from 5000 to 3750 (block gas limit ÷ 40k)
  * The per-transaction gas limit is unchanged at 30M
  * Ref: [monad-bft PR #3120](https://github.com/category-labs/monad-bft/pull/3120)

#### Notable RPC/SDK changes

* **\[RPC]** `eth_simulateV1` implementation — simulate multiple transactions across multiple blocks with state/block overrides, trace transfers, and call limits
  * Ref: [monad-bft PR #2779](https://github.com/category-labs/monad-bft/pull/2779), [monad (execution) PR #2060](https://github.com/category-labs/monad/pull/2060), [monad (execution) PR #2335](https://github.com/category-labs/monad/pull/2335) (graceful state override error handling), [monad (execution) PR #2355](https://github.com/category-labs/monad/pull/2355) (mixed TX envelope decoding)
* **\[RPC]** Gate `eth_simulateV1` behind `--enable-eth-simulate-v1` CLI flag (default: off) — returns "Method not supported" unless flag is set
  * Ref: [monad-bft PR #3149](https://github.com/category-labs/monad-bft/pull/3149)
* **\[RPC]** Add batch concurrent limit — server-side cap on concurrent RPC batch requests
  * Ref: [monad-bft PR #3128](https://github.com/category-labs/monad-bft/pull/3128)
* **\[RPC]** Remove decompression support from RPC — compressed request bodies no longer accepted
  * Ref: [monad-bft PR #3032](https://github.com/category-labs/monad-bft/pull/3032)
* **\[RPC]** Fix tx index ordering edge case in indexed log stream
  * Ref: [monad-bft PR #3118](https://github.com/category-labs/monad-bft/pull/3118)
* **\[RPC]** Fix `debug_traceCall` param requiredness
  * Ref: [monad-bft PR #3092](https://github.com/category-labs/monad-bft/pull/3092)

#### Notable robustness changes

* **\[Consensus]** Fix networking message starvation in raptorcast
  * Ref: [monad-bft PR #3137](https://github.com/category-labs/monad-bft/pull/3137)
* **\[Consensus]** Fix non-dedicated full node cold start
  * Ref: [monad-bft PR #3100](https://github.com/category-labs/monad-bft/pull/3100)
* **\[Consensus]** Drop future NoEndorsements
  * Ref: [monad-bft PR #3094](https://github.com/category-labs/monad-bft/pull/3094)
* **\[Consensus]** Emit UpdateCurrentRound on boot
  * Ref: [monad-bft PR #3091](https://github.com/category-labs/monad-bft/pull/3091)
* **\[Execution]** Convert user-facing `MONAD_ASSERT` to `MONAD_ASSERT_THROW` — prevents panics on malformed RPC input
  * Ref: [monad (execution) PR #2337](https://github.com/category-labs/monad/pull/2337)
* **\[Execution]** Throw on missing TX result — converts `MONAD_ASSERT` to `MONAD_ASSERT_THROW` in `execute_block_transactions` so RPC process fails gracefully instead of crashing
  * Ref: [monad (execution) PR #2356](https://github.com/category-labs/monad/pull/2356)
* **\[Execution]** Enforce staking syscall ordering — validation now rejects staking syscalls submitted out of order
  * Ref: [monad (execution) PR #2320](https://github.com/category-labs/monad/pull/2320)
* **\[Execution]** Fix event payload overflow check — rounds up size before alignment check to prevent assertion failure on large payloads
  * Ref: [monad (execution) PR #2194](https://github.com/category-labs/monad/pull/2194)
* **\[Execution]** Fix MONAD007→MONAD008 migration data corruption on nodes with ≥15.8 TB disk — prevents db\_offsets overrun and root-offsets ring bound violation during `monad-mpt --upgrade`
  * Ref: [monad (execution) PR #2387](https://github.com/category-labs/monad/pull/2387)
* **\[Execution]** Fix `monad-mpt --upgrade` crash on legacy databases — fixes integer underflow causing `Assertion 'r != MAP_FAILED'` on nodes with databases created before `num_cnv_chunks` was added to the storage pool footer
  * Ref: [monad (execution) PR #2353](https://github.com/category-labs/monad/pull/2353)

#### Notable internal changes

* **\[Consensus]** Switch to prometheus-backed metrics — all executor metrics migrated to prometheus registry
  * Ref: [monad-bft PR #2879](https://github.com/category-labs/monad-bft/pull/2879)
* **\[Consensus]** Raptorcast: Proposer validation per round — raptorcast now owns a `ProposerSchedule` type for per-round proposer validation, decoupled from MonadState
  * Ref: [monad-bft PR #3114](https://github.com/category-labs/monad-bft/pull/3114)
* **\[Consensus]** Decouple chunk assignment from partition
  * Ref: [monad-bft PR #3104](https://github.com/category-labs/monad-bft/pull/3104)
* **\[Consensus]** Stake partition algorithm in integer arithmetic
  * Ref: [monad-bft PR #3073](https://github.com/category-labs/monad-bft/pull/3073)
* **\[Consensus]** Allow auth-only name records in peer discovery
  * Ref: [monad-bft PR #3052](https://github.com/category-labs/monad-bft/pull/3052)
* **\[Consensus]** Separate bootstrap entrypoint address parts
  * Ref: [monad-bft PR #3051](https://github.com/category-labs/monad-bft/pull/3051)
* **\[Consensus]** Split peer entry ports
  * Ref: [monad-bft PR #3050](https://github.com/category-labs/monad-bft/pull/3050)
* **\[Node ops]** `monad-sign-name-record`: replace `--address ip:port` with separate `--ip`, `--tcp-port`, and `--udp-port` flags
  * Ref: [monad-bft PR #3103](https://github.com/category-labs/monad-bft/pull/3103)
* **\[Execution]** Dual-timeline: add secondary timeline metadata and `monad-mpt --upgrade` DB migration tool
  * Ref: [monad (execution) PR #2212](https://github.com/category-labs/monad/pull/2212)
* **\[Execution]** MPT memory-ordering fix: route `version_lower_bound_` reads through acquire accessor to fix data race on reader path
  * Ref: [monad (execution) PR #2310](https://github.com/category-labs/monad/pull/2310)
* **\[Execution]** Fix missing cast from `monad_eth_revision` to `evmc_revision`
  * Ref: [monad (execution) PR #2308](https://github.com/category-labs/monad/pull/2308)
* **\[Execution]** Add `--disable-sq-thread-cpu` flag to `cmd/monad`
  * Ref: [monad (execution) PR #2333](https://github.com/category-labs/monad/pull/2333)
* **\[Execution]** Remove support for Petersburg and Constantinople forks (Ethereum replay only)
  * Ref: [monad (execution) PR #2327](https://github.com/category-labs/monad/pull/2327), [monad (execution) PR #2325](https://github.com/category-labs/monad/pull/2325)
* **\[Execution]** Activate Prague on Ethereum mainnet replay
  * Ref: [monad (execution) PR #2301](https://github.com/category-labs/monad/pull/2301)
* **\[Execution]** Introduce in-tree `monad_eth_revision` type, replacing `evmc_revision`
  * Ref: [monad (execution) PR #2304](https://github.com/category-labs/monad/pull/2304)
* **\[Execution]** Restructure `intrinsic_gas` as additive feature gates (+ latent EIP-7702 gas bug fix)
  * Ref: [monad (execution) PR #2305](https://github.com/category-labs/monad/pull/2305)
* **\[Node ops]** `monad-mpt` status output format changed — the line previously showing `MPT database has N history, earliest is X latest is Y` now reads `MPT database has been configured to retain no more than Z versions.`, with block height on the `Latest finalized is <block>` line further down. `monad-status` has been updated to support the new format. Operators using custom scripts that parse `monad-mpt` output should update to read `Latest finalized is` instead of the old `latest is` pattern.
  * Ref: [monad (execution) PR #2228](https://github.com/category-labs/monad/pull/2228)
* **\[RPC]** Simplify calltree reassembly
  * Ref: [monad-bft PR #3112](https://github.com/category-labs/monad-bft/pull/3112)
* **\[RPC]** Cleanup debug handlers
  * Ref: [monad-bft PR #3111](https://github.com/category-labs/monad-bft/pull/3111)

***

## v0.14.5

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-06-11 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-06-04 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.14.5`](https://github.com/category-labs/monad-bft/releases/tag/v0.14.5) (`25672d619`)
* `monad` (execution): [tag `v0.14.5`](https://github.com/category-labs/monad/releases/tag/v0.14.5) (`ffefb81a0`)

#### Highlights

* **`eth_sendRawTransactionSync` now event-driven** — now subscribes to block updates from execution events, improving response time by up to 100ms. This method is now only supported with execution events enabled. Operators running RPC with websockets enabled will experience no changes; nodes without execution events will respond with "method not supported"
* **`createAccessList` revert fix** — `eth_createAccessList` now correctly returns the access list even when the call reverts
* **Historical block queries up to 2x faster** — `eth_getBlockByHash` and `eth_getBlockTransactionCountByHash` performance improved for historical blocks
* **WAL improvements** — bound WAL size with rotating chunks, persist events on dedicated thread, trace-only logging

#### Notable RPC/SDK changes

* **\[RPC]** Fix: return access list for `createAccessList` reverts
  * Ref: [monad-bft PR #3045](https://github.com/category-labs/monad-bft/pull/3045)
* **\[RPC]** Fix OpenRPC optional param flags
  * Ref: [monad-bft PR #3089](https://github.com/category-labs/monad-bft/pull/3089)
* **\[RPC]** Implement HistoricalDataSource for TriedbDataSource
  * Ref: [monad-bft PR #3085](https://github.com/category-labs/monad-bft/pull/3085)
* **\[RPC]** `eth_sendRawTransactionSync` now subscribes to block updates from execution events, improving response time by up to 100ms. This method is now only supported with execution events enabled. Operators running RPC with websockets enabled will experience no changes; nodes without execution events will respond with "method not supported"
  * Ref: [monad-bft PR #3105](https://github.com/category-labs/monad-bft/pull/3105)
* **\[RPC]** Separate RPC events buffer into write and view
  * Ref: [monad-bft PR #3102](https://github.com/category-labs/monad-bft/pull/3102)
* **\[RPC]** Use event aliases in RPC websocket impl
  * Ref: [monad-bft PR #3095](https://github.com/category-labs/monad-bft/pull/3095)

#### Notable performance changes

* **\[RPC]** Historical block queries up to 2x faster — `eth_getBlockByHash` and `eth_getBlockTransactionCountByHash` improved via HistoricalDataSource refactor
  * Ref: [monad-bft PR #3085](https://github.com/category-labs/monad-bft/pull/3085), [PR #3053](https://github.com/category-labs/monad-bft/pull/3053), [PR #3030](https://github.com/category-labs/monad-bft/pull/3030)

#### Notable robustness changes

* **\[Consensus]** Reject `fullnode_raptorcast.max_group_size` > 500 at boot — prevents misconfiguration
  * Ref: [monad-bft PR #3078](https://github.com/category-labs/monad-bft/pull/3078)
* **\[Execution]** Reject non-canonical RLP encoded strings/lists
  * Ref: [monad (execution) PR #2245](https://github.com/category-labs/monad/pull/2245)
* **\[Execution]** Prevent iterator overrun on odd input length
  * Ref: [monad (execution) PR #2257](https://github.com/category-labs/monad/pull/2257)
* **\[Execution]** Preserve access lists for reverted frames
  * Ref: [monad (execution) PR #2241](https://github.com/category-labs/monad/pull/2241)

#### Notable internal changes

* **\[Consensus]** Deterministic raptorcast: primary protocol rollout
  * Ref: [monad-bft PR #2811](https://github.com/category-labs/monad-bft/pull/2811) (4 commits: rollout, commitment, rebroadcast, packet parsing)
* **\[Consensus]** Deterministic raptorcast: secondary encoding and routing foundation
  * Ref: [monad-bft PR #2998](https://github.com/category-labs/monad-bft/pull/2998) (5 commits: encoder, routing, broadcast mode, receive gating)
* **\[Consensus]** MIP-9: Bump validator set max to 300 (consensus side only — execution side pending)
  * Ref: [monad-bft PR #3046](https://github.com/category-labs/monad-bft/pull/3046)
* **\[Consensus]** WAL: bound WAL size with rotating chunks
  * Ref: [monad-bft PR #2985](https://github.com/category-labs/monad-bft/pull/2985)
* **\[Consensus]** WAL: persist events on waltrace thread
  * Ref: [monad-bft PR #3022](https://github.com/category-labs/monad-bft/pull/3022)
* **\[Consensus]** WAL: trace only wal-logged events
  * Ref: [monad-bft PR #3024](https://github.com/category-labs/monad-bft/pull/3024)
* **\[Consensus]** Omit timeout.last\_rc verification when able
  * Ref: [monad-bft PR #3055](https://github.com/category-labs/monad-bft/pull/3055)
* **\[Consensus]** Clarify no fsync on forkpoint persistence
  * Ref: [monad-bft PR #3056](https://github.com/category-labs/monad-bft/pull/3056)
* **\[Execution]** Remove intx library, replace with custom uint128\_t/uint256\_t types
  * Ref: [monad (execution) PR #2143](https://github.com/category-labs/monad/pull/2143)
* **\[Execution]** Make DbCache a member of TrieDb
  * Ref: [monad (execution) PR #2255](https://github.com/category-labs/monad/pull/2255)

## v0.14.4

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-05-28 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-05-21 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.14.4`](https://github.com/category-labs/monad-bft/releases/tag/v0.14.4) (`06ed5828`)
* `monad` (execution): [tag `v0.14.4`](https://github.com/category-labs/monad/releases/tag/v0.14.4) (`6c75a8851`)

#### Highlights

* **`eth_fillTransaction` gas estimation fix** — aligns gas estimation behavior with `eth_estimateGas` so callers get consistent estimates across both endpoints

#### Notable RPC/SDK changes

* **\[RPC]** Fix gas estimation for `eth_fillTransaction`
  * Ref: [monad-bft PR #3006](https://github.com/category-labs/monad-bft/pull/3006)
  * Previously, calling an external contract only forwarded 63/64 gas, causing the inner frame to run out of gas and return `ExecutionError`. Now matches `eth_estimateGas` behavior.

#### Notable robustness changes

* **\[Consensus]** statesync: no panic on duplicate response index
  * Ref: [monad-bft PR #3033](https://github.com/category-labs/monad-bft/pull/3033)
* **\[RPC]** Use saturating arithmetic in `eth_gasPrice` to prevent overflow
  * Ref: [monad-bft PR #3026](https://github.com/category-labs/monad-bft/pull/3026)
* **\[Execution]** Clamp precompile input allocations to prevent slow block vector
  * Ref: [monad (execution) PR #2224](https://github.com/category-labs/monad/pull/2224)

#### Notable internal changes

* **\[Consensus]** Raptorcast chunk assignment cleanup: secondary raptorcast now uses Fisher-Yates shuffle + round-robin assignment (previously rotation); reduces latency and preps for deterministic raptorcast
  * Ref: [monad-bft PR #2978](https://github.com/category-labs/monad-bft/pull/2978)
* **\[Consensus]** Stricter round lookup for secondary raptorcast group — prevents future footgun ahead of deterministic raptorcast switch
  * Ref: [monad-bft PR #3021](https://github.com/category-labs/monad-bft/pull/3021)
* **\[Consensus]** Remove dynamic cap from fair queue / UDP layer
  * Ref: [monad-bft PR #3025](https://github.com/category-labs/monad-bft/pull/3025)
* **\[RPC]** Use TxHash and BlockHash type aliases in RPC (internal refactor, no behavior change)
  * Ref: [monad-bft PR #2997](https://github.com/category-labs/monad-bft/pull/2997)
* **\[Execution]** zkVM: add partial trie DB — new partial MPT implementation for the zkVM guest program (RISC-V), including RLP-encoded execution witness decoder
  * Ref: [monad (execution) PR #2170](https://github.com/category-labs/monad/pull/2170)

## v0.14.3

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-05-14 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-05-07 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.14.3`](https://github.com/category-labs/monad-bft/releases/tag/v0.14.3) (`f2a2092b`)
* `monad` (execution): [tag `v0.14.3`](https://github.com/category-labs/monad/releases/tag/v0.14.3) (`7fcd693f7`)

#### Highlights

* **Authenticated UDP enforcement** — Raptorcast now requires wire-authenticated UDP sockets; previously optional, now enforced for all nodes

#### Notable robustness changes

* **\[Consensus]** Raptorcast: require authenticated UDP socket
  * Ref: [monad-bft PR #2956](https://github.com/category-labs/monad-bft/pull/2956)
  * Enforces authenticated UDP socket setup; previously optional
* **\[Execution]** Fix `DbCache` assert-fail when reading finalized state older than latest finalized block
  * Ref: [monad (execution) PR #2190](https://github.com/category-labs/monad/pull/2190)
  * Replaces assertion with explicit checks; fixes incorrect `truncated` value propagation when walking the chain back past the latest finalized block
* **\[Execution]** Raise `MIN_HISTORY_LENGTH` floor from 257 to 300
  * Ref: [monad (execution) PR #2217](https://github.com/category-labs/monad/pull/2217)
  * Under disk pressure, history could shrink below the 256-block minimum required for the block hash buffer, forcing a full statesync after restart; new floor gives \~44 blocks of headroom
* **\[Execution]** Fix `evm-as` PushLabel encoding at offset zero for pre-Shanghai targets
  * Ref: [monad (execution) PR #2213](https://github.com/category-labs/monad/pull/2213)
  * Fixes incorrect `PUSH0` encoding in the EVM assembler for pre-Shanghai code paths

#### Notable performance changes

* **\[Execution]** Extend trie span optimization to fnext, child\_off, and SharedPtr arrays
  * Ref: [monad (execution) PR #2176](https://github.com/category-labs/monad/pull/2176)
* **\[Execution]** Remove inflight read coalescing from rwdb find path
  * Ref: [monad (execution) PR #2183](https://github.com/category-labs/monad/pull/2183)
* **\[Execution]** Elide DB fetch in `State::is_touched`
  * Ref: [monad (execution) PR #2198](https://github.com/category-labs/monad/pull/2198)
* **\[RPC]** Skip redundant receipt conversion on log retrieval path
  * Ref: [monad-bft PR #2839](https://github.com/category-labs/monad-bft/pull/2839)
  * Avoids building a full `TransactionReceipt` when serving log queries; goes directly from `(TxEnvelope, Receipt)` to `ReceiptEnvelope`, reducing overhead on `eth_getLogs` and related calls

#### Notable internal changes

* **\[Consensus]** Peer discovery: require authenticated UDP in name records
  * Ref: [monad-bft PR #2955](https://github.com/category-labs/monad-bft/pull/2955)
  * Enforces non-zero port policy for authenticated UDP; port 0 was used as an empty value in RLP-encoded peer entries and is now rejected
* **\[Consensus]** Add full nodes message type and handling logic for peer reputation scoring
  * Ref: [monad-bft PR #2914](https://github.com/category-labs/monad-bft/pull/2914), [PR #2915](https://github.com/category-labs/monad-bft/pull/2915)
  * Introduces a new message type for full nodes to send peer participation data to the publisher for reputation scoring
* **\[Consensus]** Peer discovery: drop V1 wire name records
  * Ref: [monad-bft PR #2952](https://github.com/category-labs/monad-bft/pull/2952)
  * Removes backward compatibility with V1 peer wire format; all peers must use V2 name records
* **\[Consensus]** Expose block number by hash retrieval in archive
  * Ref: [monad-bft PR #2980](https://github.com/category-labs/monad-bft/pull/2980)
  * Archive nodes now support block number lookup by block hash
* **\[Consensus]** Raptorcast: round-robin mode for stake-proportional chunk assigner
  * Ref: [monad-bft PR #2970](https://github.com/category-labs/monad-bft/pull/2970)
  * Adds round-robin assignment to the stake-proportional chunk assigner used in deterministic Raptorcast

## v0.14.2

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-04-30 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-04-23 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.14.2`](https://github.com/category-labs/monad-bft/releases/tag/v0.14.2) (`6307011c`)
* `monad` (execution): [tag `v0.14.2`](https://github.com/category-labs/monad/releases/tag/v0.14.2) (`169e5c45b`)

#### Highlights

* **`debug_*` improvements** — new `index` field on traced logs; `eth_call` returns explicit `reserve balance violation` error
* **8-9x speedup on compaction hot path** — trie node array optimization reduces redundant pointer recomputation
* **Fair queue forwarded ingress in txpool** — improves tx forwarding fairness between validators

#### Notable RPC/SDK changes

* **\[RPC]** Move callframe retrieval methods to ChainState
  * Ref: [monad-bft PR #2936](https://github.com/category-labs/monad-bft/pull/2936), [PR #2937](https://github.com/category-labs/monad-bft/pull/2937)
  * Covers block and transaction callframes; deduplicates call frame decoding in debug trace handlers
* **\[RPC]** Include log index in debug trace output; surface reserve balance error in `eth_call`
  * Ref: [monad-bft PR #2658](https://github.com/category-labs/monad-bft/pull/2658)
  * Adds `index` field to each traced log in the debug call tracer, reflecting the global log order within a transaction across all nested call frames; `eth_call` now returns an explicit `reserve balance violation` error instead of a generic failure when a transaction exceeds the sender's reserve balance
* **\[RPC]** Move eth call gas limit config to EthCallHandler
  * Ref: [monad-bft PR #2926](https://github.com/category-labs/monad-bft/pull/2926)
* **\[RPC]** `debug_*` methods now count toward eth call rate limiting
  * Ref: [monad-bft PR #2868](https://github.com/category-labs/monad-bft/pull/2868)
  * `debug_traceCall`, `debug_traceTransaction`, and related methods now update the eth call stats tracker; previously they bypassed it
* **\[RPC]** Enforce max response size earlier for debug RPC methods
  * Ref: [monad-bft PR #2959](https://github.com/category-labs/monad-bft/pull/2959)
* **\[RPC]** Lower RPC batch request limit to match Geth's default
  * Ref: [monad-bft PR #2934](https://github.com/category-labs/monad-bft/pull/2934)

#### Notable robustness changes

* **\[Consensus]** ConfirmGroup message fix
  * Ref: [monad-bft PR #2652](https://github.com/category-labs/monad-bft/pull/2652)
  * Prevents oversized ConfirmGroup messages being rejected by full nodes; introduces NoConfirm response when group reaches max size
* **\[Consensus]** Fix leak in leanudp identity usage map
  * Ref: [monad-bft PR #2930](https://github.com/category-labs/monad-bft/pull/2930)
* **\[Consensus]** Enforce stale message timeout in leanudp
  * Ref: [monad-bft PR #2873](https://github.com/category-labs/monad-bft/pull/2873)
* **\[RPC]** Fix eth call stats tracking memleak in RPC
  * Ref: [monad-bft PR #2910](https://github.com/category-labs/monad-bft/pull/2910)
* **\[Consensus]** Relax statesync assertion for stale DoneSync edge case
  * Ref: [monad-bft PR #2905](https://github.com/category-labs/monad-bft/pull/2905)
* **\[Execution]** Fix possible UB in unaligned read
  * Ref: [monad (execution) PR #2168](https://github.com/category-labs/monad/pull/2168)
* **\[Execution]** Fix incorrect auto\_expire\_version initialization after DB reset
  * Ref: [monad (execution) PR #2167](https://github.com/category-labs/monad/pull/2167)
* **\[Execution]** Fix compaction progress reset during statesync
  * Ref: [monad (execution) PR #2133](https://github.com/category-labs/monad/pull/2133)
  * Fixes compaction head being incorrectly reset to 0 during statesync, causing compaction to restart from the beginning
* **\[Consensus]** Decode exact forwarded transactions
  * Ref: [monad-bft PR #2810](https://github.com/category-labs/monad-bft/pull/2810)
  * Ensures forwarded transactions are decoded with no trailing bytes

#### Notable performance changes

* **\[Consensus]** Front-load cheap consensus validation checks
  * Ref: [monad-bft PR #2928](https://github.com/category-labs/monad-bft/pull/2928)
* **\[Consensus]** Fair queue forwarded ingress in txpool client
  * Ref: [monad-bft PR #2882](https://github.com/category-labs/monad-bft/pull/2882)
* **\[Consensus]** Move forwarded tx pacing into executor, simplify ingress batching
  * Ref: [monad-bft PR #2884](https://github.com/category-labs/monad-bft/pull/2884), [PR #2886](https://github.com/category-labs/monad-bft/pull/2886)
* **\[Consensus]** Drop already-obsolete consensus messages before certificate validation
  * Ref: [monad-bft PR #2927](https://github.com/category-labs/monad-bft/pull/2927)
* **\[Execution]** Optimize trie node array access (8-9x speedup on compaction hot path)
  * Ref: [monad (execution) PR #2163](https://github.com/category-labs/monad/pull/2163)
  * Hoists base pointers for packed node arrays; reduces redundant pointer recomputation in compaction, expiration, and version tracking loops

#### Notable internal changes

* **\[Consensus]** Raptorcast: direct UDP transport
  * Ref: [monad-bft PR #2898](https://github.com/category-labs/monad-bft/pull/2898), [PR #2900](https://github.com/category-labs/monad-bft/pull/2900)
  * Adds a dedicated direct UDP socket for point-to-point traffic, bypassing Raptorcast erasure coding. Eliminates the \~2.5x bandwidth amplification inherent in Raptorcast for unicast sends. Falls back to the Raptorcast path gracefully for peers that don't support it.
  * **Note:** Still in testing — not recommended for production use in this release.
* **\[Consensus]** Wireauth: lower per-instance defaults
  * Ref: [monad-bft PR #2906](https://github.com/category-labs/monad-bft/pull/2906)
* **\[Execution]** Replace system boost fiber with submodule (boost-1.83.0)
  * Ref: [monad (execution) PR #2157](https://github.com/category-labs/monad/pull/2157)
* **\[Execution]** Separate precompile gas cost calculation from runtime implementation
  * Ref: [monad (execution) PR #2099](https://github.com/category-labs/monad/pull/2099), [PR #2098](https://github.com/category-labs/monad/pull/2098)
  * Prep work for zkVM compilation
* **\[Execution]** Remove support for EVMC\_FRONTIER
  * Ref: [monad (execution) PR #2041](https://github.com/category-labs/monad/pull/2041)
* **\[Execution]** Add block-level event recording for Ethereum and Monad replay
  * Ref: [monad (execution) PR #2006](https://github.com/category-labs/monad/pull/2006)
  * Emits BLOCK\_START/BLOCK\_END events during replay, making replay event streams usable for tooling
* **\[Consensus]** Configure shared peer scoring for txpool and raptorcast
  * Ref: [monad-bft PR #2907](https://github.com/category-labs/monad-bft/pull/2907)
* **\[Consensus]** Raptorcast: enforce type-level safety for BroadcastGroup in build target
  * Ref: [monad-bft PR #2843](https://github.com/category-labs/monad-bft/pull/2843)
  * Restricts build target to established groups, eliminating packet builder epoch/round tracking desync risk

## v0.14.1

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-04-09 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-04-08 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.14.1`](https://github.com/category-labs/monad-bft/releases/tag/v0.14.1) (`4ed79392`)
* `monad` (execution): [tag `v0.14.1`](https://github.com/category-labs/monad/releases/tag/v0.14.1) (`54e132cfa`) — same commit as v0.14.0

> **Note:** Patch release on top of v0.14.0. Execution layer unchanged.

#### Notable RPC/SDK changes

* **\[RPC]** Fix `eth_fillTransaction` gas estimation and reserve balance handling
  * Ref: [monad-bft PR #2949](https://github.com/category-labs/monad-bft/pull/2949)
  * Maps reserve-balance failures to a dedicated result instead of collapsing into a generic error; makes omitted-gas fill estimation more permissive with an unbounded-balance state override during fill estimation
  * **Note:** `eth_fillTransaction` with insufficient balance now returns `reserve balance violation` (was: `insufficient balance`). Callers matching on exact error strings should update accordingly.

## v0.14.0

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-04-02 | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.14.0`](https://github.com/category-labs/monad-bft/releases/tag/v0.14.0) (`2d487de0`)
* `monad` (execution): [tag `v0.14.0`](https://github.com/category-labs/monad/releases/tag/v0.14.0) (`54e132cfa`)

#### Highlights

* **RPC: \~400ms faster receipt queries** — Receipts now tracked in chainstate buffer and available at Proposed time, eliminating trie lookups that added \~400ms on v0.13.0.
* **RPC: `eth_fillTransaction`** — New endpoint to get a fully populated transaction (gas, nonce, etc.) without signing. Useful for wallets and dapps preparing transactions.
* **RPC: Websocket notifications on proposed blocks** — `newHeads` and `logs` subscriptions now emit on proposed blocks instead of voted, reducing notification latency for real-time applications.

#### Notable RPC/SDK changes

* **\[RPC]** `eth_fillTransaction` RPC endpoint
  * Ref: [monad-bft PR #2662](https://github.com/category-labs/monad-bft/pull/2662), [PR #2932](https://github.com/category-labs/monad-bft/pull/2932)
  * PR #2932 fixes several inconsistencies: preserves user-provided `maxFeePerGas` when sufficient, treats `0x0` gas/fee as missing, allows gas fill for failed txs, rejects blob-style requests, handles EIP-2930 legacy-fee correctly
* **\[RPC]** Use proposed blocks in websocket notifications
  * Ref: [monad-bft PR #2817](https://github.com/category-labs/monad-bft/pull/2817)
* **\[RPC]** Transaction receipts in chainstate buffer (\~400ms faster receipt queries)
  * Ref: [monad-bft PR #2809](https://github.com/category-labs/monad-bft/pull/2809), [PR #2818](https://github.com/category-labs/monad-bft/pull/2818)
* **\[RPC]** Consolidate triedb usage to ChainState
  * Ref: [monad-bft PR #2876](https://github.com/category-labs/monad-bft/pull/2876)
* **\[RPC]** Use ChainStateBuffer for RPC logs
  * Ref: [monad-bft PR #2840](https://github.com/category-labs/monad-bft/pull/2840)
* **\[Execution]** Add execution events Rust SDK with path resolution and descriptor info
  * Ref: [monad (execution) PR #2123](https://github.com/category-labs/monad/pull/2123), [PR #2135](https://github.com/category-labs/monad/pull/2135), [PR #2136](https://github.com/category-labs/monad/pull/2136)

#### Notable robustness changes

* **\[Execution]** Remove ASSERT that relied on suboptimality of reserve balance accounting
  * Ref: [monad (execution) PR #2096](https://github.com/category-labs/monad/pull/2096)
* **\[Consensus]** RLP cleanup and stricter decoding enforcement
  * Ref: [monad-bft PR #2785](https://github.com/category-labs/monad-bft/pull/2785)
* **\[Consensus]** Fix zero-length allocation leak in triedb sync read FFI
  * Ref: [monad-bft PR #2816](https://github.com/category-labs/monad-bft/pull/2816)
* **\[Consensus]** Fix dataplane ban expiry TOCTOU underflow
  * Ref: [monad-bft PR #2851](https://github.com/category-labs/monad-bft/pull/2851)
* **\[Archive]** Fix S3 client stuck after sustained outage
  * Ref: [monad-bft PR #2823](https://github.com/category-labs/monad-bft/pull/2823)
* **\[Archive]** Relax checker replica matching for AWS args
  * Ref: [monad-bft PR #2943](https://github.com/category-labs/monad-bft/pull/2943)
  * Handles missing optional AWS fields in stored replica config; avoids dropping replicas from tracked state
* **\[Execution]** Fix runloop\_monad off-by-one when nblocks=1
  * Ref: [monad (execution) PR #2018](https://github.com/category-labs/monad/pull/2018)
* **\[Execution]** Fix RangedGetMachine skipping keys past min prefix
  * Ref: [monad (execution) PR #2110](https://github.com/category-labs/monad/pull/2110)
* **\[Execution]** Fix node writer reentrance causing non-contiguous writes
  * Ref: [monad (execution) PR #2082](https://github.com/category-labs/monad/pull/2082)
* **\[Execution]** Fix undefined behavior in RLP encoding with empty inputs
  * Ref: [monad (execution) PR #2152](https://github.com/category-labs/monad/pull/2152)
* **\[Consensus]** Fix unstable ordering of OpenRPC schemas
  * Ref: [monad-bft PR #2893](https://github.com/category-labs/monad-bft/pull/2893)
* **\[Consensus]** Fix ledger-tail: read author\_address from persisted peers
  * Ref: [monad-bft PR #2888](https://github.com/category-labs/monad-bft/pull/2888)

#### Notable performance changes

* **\[Consensus]** Cache all successful Raptorcast decoding outcomes
  * Ref: [monad-bft PR #2887](https://github.com/category-labs/monad-bft/pull/2887)
* **\[Consensus]** Weighted fair queue for transaction ingestion
  * Ref: [monad-bft PR #2828](https://github.com/category-labs/monad-bft/pull/2828)
* **\[Consensus]** Gas-based peer scoring
  * Ref: [monad-bft PR #2829](https://github.com/category-labs/monad-bft/pull/2829)
* **\[Consensus]** XOR decoder buffers in AVX2 chunks
  * Ref: [monad-bft PR #2863](https://github.com/category-labs/monad-bft/pull/2863)
* **\[Consensus]** Lazy decoder for BLS signature
  * Ref: [monad-bft PR #2861](https://github.com/category-labs/monad-bft/pull/2861)
* **\[Execution]** Improve fast list compaction offset calculation with hysteresis
  * Ref: [monad (execution) PR #2107](https://github.com/category-labs/monad/pull/2107)

#### Notable internal changes

* **\[Consensus]** ⚠️ Make auth UDP fields in `node.toml` required
  * Ref: [monad-bft PR #2891](https://github.com/category-labs/monad-bft/pull/2891)
* **\[Consensus]** Lower max `raptor10_fullnode_redundancy_factor` from 7 to 3
  * Ref: [monad-bft PR #2852](https://github.com/category-labs/monad-bft/pull/2852)
* **\[Node ops]** ⚠️ `monad-ledger-tail`: rename `--node-config-path` to `--peers-path`
  * Ref: [monad-bft PR #2916](https://github.com/category-labs/monad-bft/pull/2916)
  * If you run `monad-ledger-tail` manually or in a custom systemd unit, update the flag name
* **\[Node ops]** Change systemd services from `Restart=no` to `Restart=always`
  * Ref: [monad-bft PR #2860](https://github.com/category-labs/monad-bft/pull/2860)
* **\[Consensus]** Lightweight UDP framing protocol (leanudp)
  * Ref: [monad-bft PR #2827](https://github.com/category-labs/monad-bft/pull/2827)
* **\[Consensus]** Support direct UDP port in peer discovery
  * Ref: [monad-bft PR #2842](https://github.com/category-labs/monad-bft/pull/2842)
* **\[Consensus]** Auth socket with codec abstraction, direct point-to-point routing
  * Ref: [monad-bft PR #2897](https://github.com/category-labs/monad-bft/pull/2897), [PR #2896](https://github.com/category-labs/monad-bft/pull/2896)
* **\[Consensus]** Raptorcast: remove legacy packet parser
  * Ref: [monad-bft PR #2864](https://github.com/category-labs/monad-bft/pull/2864)
* **\[Archive]** Support per-source AWS profile with isolation (`--profile` flag for archiver source/sink/fallback, reads from `.aws/credentials` and `.aws/config`)
  * Ref: [monad-bft PR #2865](https://github.com/category-labs/monad-bft/pull/2865)
* **\[Execution]** Refactor chain: remove `static_validate_header` and `validate_transaction` virtual methods
  * Ref: [monad (execution) PR #2049](https://github.com/category-labs/monad/pull/2049)

## v0.13.1

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-03-16 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-03-16 | |
| `devnet` | N/A | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.13.1`](https://github.com/category-labs/monad-bft/releases/tag/v0.13.1) (`7db6cea2`)
* `monad` (execution): [tag `v0.13.1`](https://github.com/category-labs/monad/releases/tag/v0.13.1) (`722cbf5b5`)

> **Note:** This is a patch release based on v0.13.0 to fix State Archive node RPC issues. The monad (execution) tag points to the same commit as v0.13.0.

#### Notable robustness changes

* **\[RPC]** Use latest voted as fallback for last\_proposed
  * Ref: [monad-bft PR #2857](https://github.com/category-labs/monad-bft/pull/2857)
  * Fixes State Archive node RPC returning stale block data when `last_proposed` is unavailable

## v0.13.0 (MONAD\_NINE)

| Network | Date released | Hardfork timestamp | Comment |
| - | - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-03-12 | 1773930600(2026-03-19 14:30UTC) | `MONAD_NINE` hard fork |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-03-05 | 1773153000(2026-03-10 14:30UTC) | `MONAD_NINE` hard fork |
| `devnet` | N/A | N/A | |

Tags or hashes:

* `monad-bft` (consensus): [tag `v0.13.0`](https://github.com/category-labs/monad-bft/releases/tag/v0.13.0)
* `monad` (execution): [tag `v0.13.0+1`](https://github.com/category-labs/monad/releases/tag/v0.13.0+1)

> **Note:** The canonical release version is `v0.13.0`. The `+1` build metadata on the monad execution tag indicates a post-release rebuild that includes the reserve balance precompile fallback cost fix ([PR #2109](https://github.com/category-labs/monad/pull/2109)).

#### Highlights

* **RPC: `latest` block tag: `Finalized` -> `Proposed`** — queries with the `latest` block tag now return data from the latest proposed block, reducing query latency for `eth_getBalance`, `eth_call`, and other state queries.
* **RPC: `eth_sendRawTransactionSync`: `Voted` -> `Proposed`** — earlier receipts when using the `eth_sendRawTransactionSync` method.
* **Websocket: `newHeads/logs`: `Finalized` -> `Voted`** — earlier notifications for websocket subscribers to either `newHeads` or `logs`.

#### Notable protocol changes

All updates below are gated by the `MONAD_NINE` revision

* **\[EVM]** [MIP-3](https://github.com/monad-crypto/MIPs/blob/main/MIPs/MIP-3.md): Linear memory implementation
  * Ref: [monad PR #2032](https://github.com/category-labs/monad/pull/2032)
* **\[Execution]** [MIP-4](https://github.com/monad-crypto/MIPs/blob/main/MIPs/MIP-4.md): Reserve balance precompile
  * Ref: [monad PR #2040](https://github.com/category-labs/monad/pull/2040) (scaffolding)
  * Ref: [monad PR #2065](https://github.com/category-labs/monad/pull/2065) (cached/incremental checks)
  * Ref: [monad PR #2086](https://github.com/category-labs/monad/pull/2086) (add dippedIntoReserve)
  * Ref: [monad PR #2106](https://github.com/category-labs/monad/pull/2106) (dippedIntoReserve argument length error)
  * Ref: [monad PR #2109](https://github.com/category-labs/monad/pull/2109) (fallback cost fix for clean spec)
  * Ref: [monad PR #2037](https://github.com/category-labs/monad/pull/2037) (skip reserve checks for init-selfdestruct)
* **\[EVM]** [MIP-5](https://github.com/monad-crypto/MIPs/blob/main/MIPs/MIP-5.md): Activate Osaka fork EIPs
  * Modexp input bounds and gas increase (EIP-7823/EIP-7883)
  * `CLZ` opcode (EIP-7939)
  * Ref: [monad PR #2024](https://github.com/category-labs/monad/pull/2024)

> **Hard Fork:** This release activates MONAD\_NINE at timestamp `1773153000` (testnet) / `1773930600` (mainnet). Nodes must upgrade before activation.

#### Notable RPC/SDK changes

* **\[RPC]** Latest blocktag uses proposed blocks
  * Ref: [monad-bft PR #2675](https://github.com/category-labs/monad-bft/pull/2675)
* **\[RPC]** Use voted blocks in websocket notifications
  * Ref: [monad-bft PR #2799](https://github.com/category-labs/monad-bft/pull/2799)
* **\[RPC]** Add experimental flag to RPC doc macro
  * Ref: [monad-bft PR #2773](https://github.com/category-labs/monad-bft/pull/2773)
* **\[RPC]** Refactor RPC middleware for improved request handling
  * Ref: [monad-bft PR #2805](https://github.com/category-labs/monad-bft/pull/2805)
* **\[RPC]** Add decompression guard to RPC
  * Ref: [monad-bft PR #2793](https://github.com/category-labs/monad-bft/pull/2793)

#### Notable robustness changes

* **\[Consensus]** Add signature verifier for Raptorcast
  * Ref: [monad-bft PR #2747](https://github.com/category-labs/monad-bft/pull/2747)
* **\[Consensus]** Fix reactivate logic in r10 decoder
  * Ref: [monad-bft PR #2740](https://github.com/category-labs/monad-bft/pull/2740)
* **\[Execution]** Fix buffer overflow in C->Rust logging
  * Ref: [monad-bft PR #2769](https://github.com/category-labs/monad-bft/pull/2769)
* **\[Consensus]** Add global connect rate limit to wireauth
  * Ref: [monad-bft PR #2765](https://github.com/category-labs/monad-bft/pull/2765)
* **\[Consensus]** Validate ping/pong source address against name record in peer discovery
  * Ref: [monad-bft PR #2752](https://github.com/category-labs/monad-bft/pull/2752)
* **\[Consensus]** Persist voted\_head in ledger
  * Ref: [monad-bft PR #2744](https://github.com/category-labs/monad-bft/pull/2744)
* **\[Consensus]** Add dual UDP packet sender for dataplane
  * Ref: [monad-bft PR #2746](https://github.com/category-labs/monad-bft/pull/2746)
* **\[Execution]** Fix ThreadSanitizer race by joining bootstrap fiber before thread exit
  * Ref: [monad PR #2053](https://github.com/category-labs/monad/pull/2053)
* **\[Execution]** Include account balance in selfdestruct tracer frame
  * Ref: [monad PR #2039](https://github.com/category-labs/monad/pull/2039)
* **\[Consensus]** Ensure proposed head is on canonical chain
  * Ref: [monad-bft PR #2756](https://github.com/category-labs/monad-bft/pull/2756)
* **\[Execution]** Fix sentinel collision in compact virtual chunk offset
  * Ref: [monad PR #2083](https://github.com/category-labs/monad/pull/2083)
* **\[Execution]** Fix potential race condition in execute\_block\_transactions
  * Ref: [monad PR #2092](https://github.com/category-labs/monad/pull/2092)

#### Notable internal changes

* **\[Consensus]** Remove unneeded channels when secondary raptorcast is disabled
  * Ref: [monad-bft PR #2808](https://github.com/category-labs/monad-bft/pull/2808)
* **\[Consensus]** Upgrade alloy to stable release
  * Ref: [monad-bft PR #2792](https://github.com/category-labs/monad-bft/pull/2792)
* **\[Execution]** Add `evm-as` syntactic sugar for VM utilities
  * Ref: [monad PR #2097](https://github.com/category-labs/monad/pull/2097)
* **\[Consensus]** Parametrize wireauth metrics for better observability
  * Ref: [monad-bft PR #2692](https://github.com/category-labs/monad-bft/pull/2692)
* **\[Consensus]** Cleanup block persist implementation
  * Ref: [monad-bft PR #2767](https://github.com/category-labs/monad-bft/pull/2767)
* **\[Consensus]** Fix wip extension in block-persist
  * Ref: [monad-bft PR #2776](https://github.com/category-labs/monad-bft/pull/2776)
* **\[Consensus]** Remove legacy `do_local_insert`
  * Ref: [monad-bft PR #2728](https://github.com/category-labs/monad-bft/pull/2728)
* **\[Consensus]** Add metrics for raptorcast deserialize failures
  * Ref: [monad-bft PR #2789](https://github.com/category-labs/monad-bft/pull/2789)
* **\[RPC]** Reduce RPC event server broadcast channel size
  * Ref: [monad-bft PR #2815](https://github.com/category-labs/monad-bft/pull/2815)
* **\[Consensus]** Pre-TFM base fee cleanup
  * Ref: [monad-bft PR #2664](https://github.com/category-labs/monad-bft/pull/2664)
* **\[Consensus]** Remove pre-TFM reserve balance logic
  * Ref: [monad-bft PR #2622](https://github.com/category-labs/monad-bft/pull/2622)
* **\[RPC]** Simplify hex encoding/decoding in RPC
  * Ref: [monad-bft PR #2806](https://github.com/category-labs/monad-bft/pull/2806)
* **\[Archive]** Add exists(key) to kvstore
  * Ref: [monad-bft PR #2688](https://github.com/category-labs/monad-bft/pull/2688)

## v0.12.7

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-01-29 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-01-20 | |
| `devnet` | N/A | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.7`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.7)
* `monad`: [tag `v0.12.7`](https://github.com/category-labs/monad/releases/tag/v0.12.7)

#### Notable RPC/SDK changes

* **\[RPC]** Allow block hash as block identifier in `eth_estimateGas`
  * Ref: [monad-bft PR #2676](https://github.com/category-labs/monad-bft/pull/2676)
* **\[RPC]** Use `RawValue` for RPC id to preserve original JSON types
  * Reduces effectiveness of DoS attacks using large JSON arrays/dicts in request IDs
  * Ref: [monad-bft PR #2455](https://github.com/category-labs/monad-bft/pull/2455)

#### Notable robustness changes

* **\[EVM]** Fix undefined behavior in modexp precompile
  * Ref: [monad PR #2045](https://github.com/category-labs/monad/pull/2045)
* **\[Consensus]** Remove consecutive sequence number assertion
  * Ref: [monad-bft PR #2704](https://github.com/category-labs/monad-bft/pull/2704)
* **\[Consensus]** Improve liveness when advancing round using TC from timeout messages
  * Ref: [monad-bft PR #2701](https://github.com/category-labs/monad-bft/pull/2701)
* **\[Consensus]** Disallow creating an empty validator set
  * Ref: [monad-bft PR #2682](https://github.com/category-labs/monad-bft/pull/2682)

#### Notable internal changes

* **\[Consensus]** Add security tests for `secp256k1`
  * Adds Wycheproof tests, malleability tests, and security unit tests
  * Ref: [monad-bft PR #2706](https://github.com/category-labs/monad-bft/pull/2706)
* **\[Node ops]** Update `rkyv` and other dependencies
  * Ref: [monad-bft PR #2702](https://github.com/category-labs/monad-bft/pull/2702)
* **\[Consensus]** Return bound socket addresses synchronously in dataplane
  * Ref: [monad-bft PR #2653](https://github.com/category-labs/monad-bft/pull/2653)
* **\[Consensus]** Rename state backend cache for clarity
  * Ref: [monad-bft PR #2699](https://github.com/category-labs/monad-bft/pull/2699)

## v0.12.6

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2026-01-14 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2026-01-07 | |
| `devnet` | N/A | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.6`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.6)
* `monad`: [tag `v0.12.6`](https://github.com/category-labs/monad/releases/tag/v0.12.6)

#### Notable RPC/SDK changes

* **\[RPC]** Fix depth bug in selfdestructing call frames
  * Ref: [monad PR #1977](https://github.com/category-labs/monad/pull/1977)
* **\[RPC]** Prestate tracer conformance fixes
  * Ref: [monad PR #1946](https://github.com/category-labs/monad/pull/1946)

#### Notable robustness changes

* **\[Consensus]** Add signature verification rate limiting with authenticated peer bypass
  * Ref: [monad-bft PR #2601](https://github.com/category-labs/monad-bft/pull/2601)
* **\[Consensus]** Validate confirm group message before updating peers
  * Ref: [monad-bft PR #2680](https://github.com/category-labs/monad-bft/pull/2680)
* **\[Consensus]** Use Tai64N directly for wireauth timestamp comparison
  * Ref: [monad-bft PR #2678](https://github.com/category-labs/monad-bft/pull/2678)
* **\[Consensus]** Improve RaptorCast decoding cache eviction
  * Ref: [monad-bft PR #2651](https://github.com/category-labs/monad-bft/pull/2651)
* **\[Consensus]** Fix blocksync in-flight request tracking on cache hydration
  * Ref: [monad-bft PR #2635](https://github.com/category-labs/monad-bft/pull/2635)
* **\[Execution]** Update triedb voted metadata before executing proposal
  * Solves a race condition between Voted updates through websocket and corresponding JSON-RPC calls
  * Ref: [monad PR #1964](https://github.com/category-labs/monad/pull/1964)
* **\[Node ops]** Persist peers periodically for improved discovery resilience
  * Ref: [monad-bft PR #2633](https://github.com/category-labs/monad-bft/pull/2633)

#### Notable performance changes

* **\[Consensus]** Boost dataplane throughput with ring buffer implementation
  * Ref: [monad-bft PR #2596](https://github.com/category-labs/monad-bft/pull/2596)
* **\[Execution]** Native implementation for `MLOAD`, `MSTORE`, `MSTORE8`, `CALLDATALOAD` opcodes
  * Ref: [monad PR #1963](https://github.com/category-labs/monad/pull/1963)
* **\[Execution]** Improve snapshot write performance
  * Ref: [monad PR #1973](https://github.com/category-labs/monad/pull/1973), [monad PR #1960](https://github.com/category-labs/monad/pull/1960)
* **\[Execution]** Optimize database history length adjustment with binary search
  * Ref: [monad PR #1922](https://github.com/category-labs/monad/pull/1922)
* **\[Execution]** Unify single buffer and scatter read handling in AsyncIO
  * Ref: [monad PR #1944](https://github.com/category-labs/monad/pull/1944)

#### Notable internal changes

* **\[Node ops]** Docker single-node container updates for prebuilt images
  * Fixes to [Local Docker installation](https://github.com/category-labs/monad-bft/blob/master/README.md#using-pre-built-images)
  * Ref: [monad-bft PR #2674](https://github.com/category-labs/monad-bft/pull/2674)
* **\[Consensus]** Add support for generic txpool sidecars
  * Enables IPC transaction priority and forwarding controls
  * Ref: [monad-bft PR #2557](https://github.com/category-labs/monad-bft/pull/2557)
* **\[EVM]** Osaka fork preparation
  * Modexp gas changes and upper bound (EIP-7823/EIP-7883)
  * Implement `CLZ` opcode
    * Ref: [monad PR #1970](https://github.com/category-labs/monad/pull/1970), [monad PR #1981](https://github.com/category-labs/monad/pull/1981)
* **\[Node ops]** Accept `--hyphen-style` long options in CLI
  * Ref: [monad PR #2005](https://github.com/category-labs/monad/pull/2005)
* **\[Node ops / Archive]** Archive pipeline improvements
  * Add `WritePolicy` to `KVStore` for conditional write protection (`NoClobber`)
  * Add BFT-uploading stats logging
  * Ref: [monad-bft PR #2649](https://github.com/category-labs/monad-bft/pull/2649), [monad-bft PR #2661](https://github.com/category-labs/monad-bft/pull/2661)
* **\[Node ops]** Simplify RPC txpool status tracking
  * Ref: [monad-bft PR #2644](https://github.com/category-labs/monad-bft/pull/2644)
* **\[Node ops]** Snapshot tooling improvements in `monad_cli`
  * Add `--dump_concurrency_limit` parameter
  * Add sharding support for distributed snapshot creation
  * Ref: [monad PR #1967](https://github.com/category-labs/monad/pull/1967), [monad PR #1965](https://github.com/category-labs/monad/pull/1965)
* **\[Node ops]** Add RaptorCast decoding cache metrics
  * Ref: [monad-bft PR #2667](https://github.com/category-labs/monad-bft/pull/2667)
* **\[Execution]** Add `CommitBuilder` API to execution database
  * Ref: [monad PR #1968](https://github.com/category-labs/monad/pull/1968)
* **\[Execution]** Remove legacy `using_chunks_for_root_offsets` metadata field
  * Ref: [monad PR #1943](https://github.com/category-labs/monad/pull/1943)
* **\[Node ops / Txgen]** Add ERC-4337 + EIP-7702 generator (`erc4337_7702_bundled`)
  * Ref: [monad-bft PR #2628](https://github.com/category-labs/monad-bft/pull/2628)
* **\[Node ops]** Add systemd service scripts for `blockcapd` and execution events archivers
  * Ref: [monad-bft PR #2590](https://github.com/category-labs/monad-bft/pull/2590)
* **\[SDK]** Add `monad_event_resolve_ring_file` API
  * Ref: [monad PR #1741](https://github.com/category-labs/monad/pull/1741)
* **\[Execution]** Enable VM host exception handling outside VM
  * Ref: [monad PR #1990](https://github.com/category-labs/monad/pull/1990)

## v0.12.5

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | N/A | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-12-16 | reset from genesis |
| `devnet` | N/A | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.5`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.5)
* `monad`: [tag `v0.12.5`](https://github.com/category-labs/monad/releases/tag/v0.12.5)

#### Notable network changes

* **\[Network reset]** `testnet` **reset from genesis** starting from `MONAD_EIGHT`
  * Increases total supply to 100 B, consistent with `mainnet`
  * Clears a path to eliminate dead code (revisions required for early `testnet`)
  * Ref: [monad PR #1983](https://github.com/category-labs/monad/pull/1983), [monad-bft PR #2673](https://github.com/category-labs/monad-bft/pull/2673)

## v0.12.4

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2025-12-05 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-12-05 | |
| `devnet` | 2025-12-05 | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.4`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.4)
* `monad`: [tag `v0.12.4`](https://github.com/category-labs/monad/releases/tag/v0.12.4) *(unchanged from v0.12.3)*

#### Notable internal changes

* **\[Node ops]** Fix peer discovery port configuration when constructing self name record
  * Use port from peer discovery config instead of bound socket when constructing self name record.
    This bug affected node operators using a NAT.
  * Ref: [monad-bft PR #2655](https://github.com/category-labs/monad-bft/pull/2655)

## v0.12.3

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2025-12-05 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-12-04 | |
| `devnet` | 2025-12-04 | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.3`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.3)
* `monad`: [tag `v0.12.3`](https://github.com/category-labs/monad/releases/tag/v0.12.3)

#### Notable RPC/SDK changes

* **\[RPC]** [EIP-7966](https://eips.ethereum.org/EIPS/eip-7966) (`eth_sendRawTransactionSync`) support
  * Ref: [monad-bft PR #2542](https://github.com/category-labs/monad-bft/pull/2542)
* **\[RPC]** Populate `value` field on traces for staking precompile syscalls (added in `0.12.3-rpc-hotfix2`)
  * Ref: [monad PR #1938](https://github.com/category-labs/monad/pull/1938)

#### Notable robustness changes

* **\[Consensus]** Wire authentication protocol for UDP
  * Adds authenticated UDP communication to improve network security
  * Includes replay window adjustments for improved reliability
  * Ref: [monad-bft PR #2417](https://github.com/category-labs/monad-bft/pull/2417), [monad-bft PR #2544](https://github.com/category-labs/monad-bft/pull/2544), [monad-bft PR #2626](https://github.com/category-labs/monad-bft/pull/2626), [monad-bft PR #2091](https://github.com/category-labs/monad-bft/pull/2091)
* **\[Execution]** Improve `statesync` shutdown and fix protocol corruption
  * Modified `statesync_server_recv()` to guarantee complete reads
  * Ref: [monad PR #1930](https://github.com/category-labs/monad/pull/1930)
* **\[RPC]** Prevent reserve balance crash in RPC
  * Add reserve balance violation error messages in call frames
  * Ref: [monad PR #1932](https://github.com/category-labs/monad/pull/1932), [monad-bft PR #2629](https://github.com/category-labs/monad-bft/pull/2629)
  * This was already previously released in `v0.12.2-rpc-hotfix`
* **\[Consensus]** Add timeout to `txpool` IPC stream
  * Prevents hanging connections in transaction pool communication
  * Ref: [monad-bft PR #2619](https://github.com/category-labs/monad-bft/pull/2619)
* **\[Consensus]** Reject timeout certificates with empty signers
  * Adds validation to prevent malformed timeout certificates
  * Ref: [monad-bft PR #2630](https://github.com/category-labs/monad-bft/pull/2630)
* **\[Consensus]** Verify RaptorCast chunk length is non-zero
  * Adds validation to prevent malformed RaptorCast chunks
  * Ref: [monad-bft PR #2638](https://github.com/category-labs/monad-bft/pull/2638)
* **\[Execution]** Fix MPT restore bug that failed to preserve `version_lower_bound`
  * Ref: [monad PR #1955](https://github.com/category-labs/monad/pull/1955)
* **\[Execution]** Fix move trie version forward bug
  * Erase versions that fall out of history range before moving forward to newer versions
  * Ref: [monad PR #1957](https://github.com/category-labs/monad/pull/1957)
* **\[Execution]** Fix dangling pointers to intercode
  * Resolves memory safety issue with `get_code` and `read_code` functions
  * Ref: [monad PR #1941](https://github.com/category-labs/monad/pull/1941)
* **\[Execution]** Add retries to `runloop_monad_ethblocks`
  * Ref: [monad PR #1953](https://github.com/category-labs/monad/pull/1953)

#### Notable performance changes

* **\[RPC]** Improve `eth_getLogs` performance
  * Reduce memory copies and unify receipt-to-logs processing
  * Ref: [monad-bft PR #2588](https://github.com/category-labs/monad-bft/pull/2588), [monad-bft PR #2591](https://github.com/category-labs/monad-bft/pull/2591), [monad-bft PR #2631](https://github.com/category-labs/monad-bft/pull/2631)
* **\[Execution]** Fiber: add support for move-only functors
  * Improves execution efficiency by supporting move semantics
  * Ref: [monad PR #1936](https://github.com/category-labs/monad/pull/1936)

#### Notable internal changes

* **\[RPC / Node ops]** Allow RPC to run without `monad-bft`
  * Enables standalone RPC operation for improved deployment flexibility
  * Ref: [monad-bft PR #2613](https://github.com/category-labs/monad-bft/pull/2613)
* **\[Node ops]** Add `--root-offsets-chunk-count` flag to `monad-mpt` to configure the number of chunks allocated for root offsets
  * Each chunk holds approximately 16.5M blocks. Previously, all nodes were hardcoded to use 2 chunks (max TrieDB capacity of \~33M blocks)
  * New default: 16 **must be a power of 2**
  * Note that the default value of 16 translates to approximately 268M blocks \~ 1240 days. In most cases the limiting factor is disk capacity which will auto-compact when filled to 80%
  * Ref: [monad PR #1937](https://github.com/category-labs/monad/pull/1937)
* **\[Node ops]** Peer discovery improvements
  * Full nodes periodically pull validator name records for dynamic validator discovery
  * Add authenticated UDP port to name record
  * Ref: [monad-bft PR #2607](https://github.com/category-labs/monad-bft/pull/2607), [monad-bft PR #2538](https://github.com/category-labs/monad-bft/pull/2538)
* **\[Node ops / Archive]** Archive infrastructure improvements
  * Refactor `monad-block-writer` for improved reliability with `--max-blocks-per-iter` configuration
  * Async backfill with traces-only archive support
  * Add `require-traces` archiver flag and indexer fallback source
  * Support for historical execution event archiving with generic directory archiving
  * **Potentially breaking: Remove `--start-block` from `monad-archiver` systemd service; operators must use imperative CLI to set start block**
    * Example: `monad-archiver set-start-block --block 1000000 --archive-sink s3://bucket-name/path`
    * Use `--async-backfill` flag to set the async-backfill marker instead of primary marker
  * Ref: [monad-bft PR #2610](https://github.com/category-labs/monad-bft/pull/2610), [monad-bft PR #2606](https://github.com/category-labs/monad-bft/pull/2606), [monad-bft PR #2598](https://github.com/category-labs/monad-bft/pull/2598), [monad-bft PR #2514](https://github.com/category-labs/monad-bft/pull/2514), [monad-bft PR #2612](https://github.com/category-labs/monad-bft/pull/2612), [monad-bft PR #2569](https://github.com/category-labs/monad-bft/pull/2569), [monad-bft PR #2623](https://github.com/category-labs/monad-bft/pull/2623)
* **\[Node ops]** Networking configuration updates
  * Use default MTU 1500
  * Add HDR histogram for broadcast latency tracking in `monad-executor` and `monad-raptorcast`
  * Ref: [monad-bft PR #2576](https://github.com/category-labs/monad-bft/pull/2576), [monad-bft PR #2602](https://github.com/category-labs/monad-bft/pull/2602)
* **\[Consensus]** RaptorCast improvements
  * Clear histogram every 30s and keep only p99 for better latency tracking
  * Fix timer update after receiving control messages to ensure proper keepalives
  * Ref: [monad-bft PR #2627](https://github.com/category-labs/monad-bft/pull/2627), [monad-bft PR #2637](https://github.com/category-labs/monad-bft/pull/2637)
* **\[Consensus]** Dataplane: refactor to use socket handles
  * Prepares dataplane for future extension with authenticated sockets
  * Ref: [monad-bft PR #2458](https://github.com/category-labs/monad-bft/pull/2458)
* **\[Execution]** Replay monad: always execute first block off latest finalized state
  * Ref: [monad PR #1927](https://github.com/category-labs/monad/pull/1927)
* **\[Node ops]** Txgen improvements: README and guide, nonce gaps and legacy tx options, ERC20 pools, Uniswap v3 mode, NFT sale mode, websocket and RPC request generation
  * Ref: [monad-bft PR #2568](https://github.com/category-labs/monad-bft/pull/2568), [monad-bft PR #2567](https://github.com/category-labs/monad-bft/pull/2567), [monad-bft PR #2577](https://github.com/category-labs/monad-bft/pull/2577), [monad-bft PR #2600](https://github.com/category-labs/monad-bft/pull/2600), [monad-bft PR #2527](https://github.com/category-labs/monad-bft/pull/2527), [monad-bft PR #2394](https://github.com/category-labs/monad-bft/pull/2394), [monad-bft PR #2608](https://github.com/category-labs/monad-bft/pull/2608)

## v0.12.2

| Network | Date released | Comment |
| - | - | - |
| [`mainnet`](https://docs.monad.xyz/developer-essentials/network-information) | 2025-11-19 | |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-11-18 | |
| `devnet` | 2025-11-18 | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.2-rc`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.2-rc)
* `monad`: [tag `v0.12.2-rc`](https://github.com/category-labs/monad/releases/tag/v0.12.2-rc)

#### Notable protocol changes

All updates below are gated by the `MONAD_EIGHT` revision

* **\[Execution]** Reserve balance checks now use the final state code hash. This makes checks
  slightly more liberal (less likely to revert transactions during execution), and also makes the
  implementation closer to the
  [Coq model](https://category-labs.github.io/category-research/formalverif/reserve-balance/monad.proofs.reservebal.html)
  that was proven correct under some assumptions.
  * This changes the behavior of the following corner case:
    * In transaction 1, account X is sent a small amount of MON (e.g. 5 MON)
    * Then (much later) in transaction 2, someone both deploys a smart contract wallet at account
      X and sends MON out of that smart contract.
    * Previously, transaction 2's execution would treat account X as an EOA and apply reserve
      balance checks on it, thus reverting the transaction because it would be a dipping
      transaction that was not pre-authorized by consensus.
    * After this change, account X will be treated as a smart contract account and
      will be omitted from reserve balance checks.
    * Note that smart contract addresses are deterministic, making it effectively impossible for
      an address that receives a code deployment to also be an EOA (i.e. to correspond to a
      private key).
  * Ref: [monad PR #1916](https://github.com/category-labs/monad/pull/1916),
    [monad PR #1917](https://github.com/category-labs/monad/pull/1917)
* **\[EVM]** Reduce pagination on staking precompile inverse mappings from 100 to 50
  * Applies to `precompile_get_delegations()` and `precompile_get_delegators()`
  * Ref: [monad PR #1920](https://github.com/category-labs/monad/pull/1920)

#### Notable deployment changes

* **\[SDK]** Execution events no longer require a special "preview" release to enable all EVM notifications (there are no more `--exec-events` special versions)
* **\[SDK]** Fix race condition in event ring create
  * Ref: [monad PR #1914](https://github.com/category-labs/monad/pull/1914)

#### Notable robustness changes

* **\[RPC]** Fix `eth_feeHistory`
  * Ref: [monad-bft PR #2366](https://github.com/category-labs/monad-bft/pull/2366)
* **\[Consensus]** Update transaction classification logic to apply emptying before delegation
  * Improves delegation ordering in `try_apply_block_fees`
  * Ref: [monad-bft PR #2561](https://github.com/category-labs/monad-bft/pull/2561)
* **\[Execution]** Failsafe sanity checks for reward system transactions
  * Ref: [monad PR #1921](https://github.com/category-labs/monad/pull/1921)
* **\[RPC]** Check reserve balance in `eth_call`
  * Prevent simulated transactions from violating reserve balance
  * Call `revert_transaction` in `eth_call` implementation
  * Ref: [monad PR #1912](https://github.com/category-labs/monad/pull/1912)
* **\[Node ops]** Fix remotely fetched `forkpoint.toml` write format
  * Ensures forkpoint files are written in the correct format when fetched from remote sources
  * Ref: [monad-bft PR #2554](https://github.com/category-labs/monad-bft/pull/2554)
* **\[Node ops]** Fix `monad-keystore` key corruption issue
  * `to_bls` and `to_secp` now consume secret to prevent corrupted keystore files
  * Add tests for command line keystore app to verify all flags combinations work correctly
  * Ref: [monad-bft PR #2553](https://github.com/category-labs/monad-bft/pull/2553)
* **\[Execution]** Fix bad write offset in `storage_pool` `try_trim_contents()` when bytes to start TRIM is not a multiple of disk page size
  * Ref: [monad PR #1908](https://github.com/category-labs/monad/pull/1908)
* **\[RPC]** Use txpool bridge channel size for ratelimiting
  * Prevents `try_send` method from failing by using channel capacity for `eth_sendRawTransaction` ratelimiting
  * Ref: [monad-bft PR #2506](https://github.com/category-labs/monad-bft/pull/2506)
* **\[Consensus]** Improve RaptorCast message validation
  * Add sanity check for `chunk_id` range in message parsing
  * Reject overflowing `merkle_leaf_idx` in merkle proof construction
  * Update calculation of `encoded_symbol_capacity` in decoder
  * Ref: [monad-bft PR #2541](https://github.com/category-labs/monad-bft/pull/2541)
* **\[Consensus]** Improve RaptorCast group invite response checks
  * Add sanity check to prevent processing group invite accept after reject from same full node
  * Ref: [monad-bft PR #2574](https://github.com/category-labs/monad-bft/pull/2574)
* **\[Consensus]** Update txpool insertion policy - make balance check stricter
  * Ref: [monad-bft PR #2575](https://github.com/category-labs/monad-bft/pull/2575)

#### Notable performance changes

* **\[Consensus]** Add dataplane warnings when priority queues are overrun
  * Sets total priority queue capacity to 100MB per priority queue (200MB total max)
  * Messages will be dropped with warnings logged if capacity is exceeded
  * Ref: [monad-bft PR #2559](https://github.com/category-labs/monad-bft/pull/2559)
* **\[Execution / Node ops]** Remove read-only database `io_uring` SQ poll thread
  * **IMPORTANT**: Operators with `monad-execution` systemctl overrides should make the appropriate changes to eliminate the `--ro_sq_thread_cpu` parameter as demonstrated in [monad-bft PR #2558](https://github.com/category-labs/monad-bft/pull/2558). Overrides are commonly set when running an RPC or archive node with `--trace_calls` enabled.
  * Reduces thread contention during statesync, improving block execution performance
  * Make `ro_sq_thread_cpu` argument optional, remove from default configuration
  * Ref: [monad PR #1911](https://github.com/category-labs/monad/pull/1911), [monad-bft PR #2558](https://github.com/category-labs/monad-bft/pull/2558)
* **\[RPC]** Move recover authority logic inside submitted lambda for `eth_call`
  * Avoid blocking on fiber promises when called from rust thread, preventing performance issues
  * Replace parallelization with single call to `recover_authority()` since `eth_call` transactions have single authority
  * Ref: [monad PR #1827](https://github.com/category-labs/monad/pull/1827)
* **\[Execution]** Remove `iopoll` support
  * Ref: [monad PR #1910](https://github.com/category-labs/monad/pull/1910)

#### Notable internal changes

* **\[Node ops]** Add `monad-version` crate for git version info in binaries
  * Ref: [monad-bft PR #2572](https://github.com/category-labs/monad-bft/pull/2572)
* **\[Node ops]** Add CLI argument for number of fibers in trace transaction execution pool (default: 100)
  * Ref: [monad-bft PR #2584](https://github.com/category-labs/monad-bft/pull/2584)
* **\[Node ops]** Update block reward for mainnet
  * Ref: [monad-bft PR #2582](https://github.com/category-labs/monad-bft/pull/2582)
* **\[Node ops]** Add block writer binary for testing and debugging
  * Ref: [monad-bft PR #2546](https://github.com/category-labs/monad-bft/pull/2546)
* **\[Node ops]** Make cruft timer retention configurable
  * Add environment variable support for artifact retention times (override in `/home/monad/.env`)
  * Ref: [monad-bft PR #2548](https://github.com/category-labs/monad-bft/pull/2548)
* **\[Node ops]** Add warning when restoring from snapshot (hard reset) is required
  * Prompt node operator when local tip is behind by `STATESYNC_BLOCK_THRESHOLD`
  * Ref: [monad-bft PR #2581](https://github.com/category-labs/monad-bft/pull/2581)
* **\[Node ops]** Update `monad-cruft` permissions to monad user
  * Ref: [monad-bft PR #2556](https://github.com/category-labs/monad-bft/pull/2556)
* **\[Node ops]** Fix txpool metrics recording for transaction replacements
  * Ref: [monad-bft PR #2564](https://github.com/category-labs/monad-bft/pull/2564)
* **\[RPC]** Operator can configure RPC worker threads
  * Ref: [monad-bft PR #2562](https://github.com/category-labs/monad-bft/pull/2562)
* **\[Archive]** Add TOML config file support instead of CLI-only configuration
  * Enables `monad-archiver` binary to use `--config` flag for configuration
  * CLI arguments continue to work and take precedence over config file values
  * Ref: [monad-bft PR #2570](https://github.com/category-labs/monad-bft/pull/2570)
* **\[Node ops]** Add random mutations to `txgen` for improved testing
  * Ref: [monad-bft PR #2543](https://github.com/category-labs/monad-bft/pull/2543)
* **\[Node ops]** Add reserve balance coherency tests
  * Ref: [monad-bft PR #2573](https://github.com/category-labs/monad-bft/pull/2573)
* **\[SDK]** Record execution events
  * Includes state access and system transactions
  * Ref: [monad PR #1906](https://github.com/category-labs/monad/pull/1906), [monad PR #1907](https://github.com/category-labs/monad/pull/1907), [monad PR #1913](https://github.com/category-labs/monad/pull/1913)
* **\[SDK]** Explicitly clear flow info that doesn't apply to certain event types
  * Prevents poorly written event clients from reading invalid data
  * Ref: [monad PR #1919](https://github.com/category-labs/monad/pull/1919)
* **\[Execution]** Improve assertion messages with `MONAD_ASSERT_PRINTF`
  * Ref: [monad PR #1918](https://github.com/category-labs/monad/pull/1918)
* **\[Node ops]** Add statesync server metrics
  * Add `SyncDone` metric to track successes and failures
  * Add request timing metric for statesync server
  * Ref: [monad-bft PR #2555](https://github.com/category-labs/monad-bft/pull/2555)
* **\[Node ops]** Disambiguate triedb error logs
  * Improve error message clarity by making each log call unique
  * Ref: [monad-bft PR #2579](https://github.com/category-labs/monad-bft/pull/2579)
* **\[Node ops]** Update devnet chain configs
  * Shorten default devnet epoch length from 50,000 blocks to 10,000 blocks and epoch start delay from 5,000 rounds to 1,000 rounds
  * Ref: [monad-bft PR #2578](https://github.com/category-labs/monad-bft/pull/2578)
* **\[Node ops]** Update test infrastructure
  * Switch `test_state` and `precompiles_test` tests to `TraitsTest`
  * Add `runloop_monad_ethblocks` to CLI for Monad EVM block replay
  * Ref: [monad PR #1905](https://github.com/category-labs/monad/pull/1905), [monad PR #1894](https://github.com/category-labs/monad/pull/1894)
* **\[Execution]** Remove unused cross-thread pipe messaging infrastructure
  * Ref: [monad PR #1915](https://github.com/category-labs/monad/pull/1915)
* **\[Node ops]** Keep manytrace agent alive in node state
  * Ref: [monad-bft PR #2583](https://github.com/category-labs/monad-bft/pull/2583)
* **\[Node ops]** Update keystore documentation
  * Ref: [monad-bft PR #2380](https://github.com/category-labs/monad-bft/pull/2380)
* **\[Node ops]** Add more logging for block validation errors
  * Ref: [monad-bft PR #2550](https://github.com/category-labs/monad-bft/pull/2550)
* **\[Node ops]** Log round leader when processing certificates
  * Ref: [monad-bft PR #2580](https://github.com/category-labs/monad-bft/pull/2580)

## v0.12.1

| Network | Date released | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-11-12 | |
| `devnet` | 2025-11-12 | |

Tags or hashes:

* `monad-bft`: [tag `v0.12.1`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.1)
* `monad`: [tag `v0.12.1`](https://github.com/category-labs/monad/releases/tag/v0.12.1)

#### Notable RPC/SDK changes

* **\[RPC]** Support for prestate and statediff tracing for the following RPC endpoints:
  * `debug_traceTransaction`
  * `debug_traceBlockByNumber`
  * `debug_traceBlockByHash`
  * Ref: [monad PR #1753](https://github.com/category-labs/monad/pull/1753), [monad-bft PR #2403](https://github.com/category-labs/monad-bft/pull/2403)
* **\[RPC]** New endpoint `eth_createAccessList`
  * Ref: [monad PR #1748](https://github.com/category-labs/monad/pull/1748), [monad-bft PR #2519](https://github.com/category-labs/monad-bft/pull/2519)
* **\[RPC]** Fix serialization for `to` address in historical traces
  * Follow on to [monad-bft PR #2516](https://github.com/category-labs/monad-bft/pull/2516) implemented in `v0.12.0` (in a historical context)
  * Ref: [monad-bft PR #2523](https://github.com/category-labs/monad-bft/pull/2523), [monad PR #1861](https://github.com/category-labs/monad/pull/1861)
* **\[RPC]** Remove artificial block height floor for `eth_call` and RPC queries
  * Previously limited queries using `latest` and `safe` block tags to `finalized + 1`, now uses actual latest voted block
  * Ref: [monad-bft PR #2148](https://github.com/category-labs/monad-bft/pull/2148)
* **\[RPC]** Fix RPC errors when requesting traces for call frames that include a self-destructing transaction
  * Ref: [monad PR #1887](https://github.com/category-labs/monad/pull/1887)
* **\[RPC]** Fix inconsistent results being reported when using state overrides in RPC calls
  * Ref: [monad PR #1812](https://github.com/category-labs/monad/pull/1812)
* **\[RPC]** Fix for a possible denial-of-service attack on RPC nodes by overriding balances in the staking contract
  * Ref: [monad PR #1903](https://github.com/category-labs/monad/pull/1903)

#### Notable robustness changes

* **\[Node ops/Consensus]** Validators limit statesync service to validators and whitelisted full nodes
  * Full nodes service all requests
  * Ref: [monad-bft PR #2524](https://github.com/category-labs/monad-bft/pull/2524)
* **\[Consensus]** More intelligent txpool eviction logic
  * Ref: [monad-bft PR #2525](https://github.com/category-labs/monad-bft/pull/2525)
* **\[Consensus]** Start vote pacing timer on startup
  * Ref: [monad-bft PR #2528](https://github.com/category-labs/monad-bft/pull/2528)
* **\[Consensus]** Fix historical logs `selfdestruct` issue
  * Ref: [monad-bft PR #2531](https://github.com/category-labs/monad-bft/pull/2531)
* **\[Consensus]** Graceful handling of gas limit check
  * Ref: [monad-bft PR #2518](https://github.com/category-labs/monad-bft/pull/2518)
* **\[Consensus]** Remove 0-stake validator support
  * Support for 0-stake validators in the validator set was used as a workaround for lack of full-node support in the past and should no longer be supported
  * Ref: [monad-bft PR #2545](https://github.com/category-labs/monad-bft/pull/2545)

#### Notable performance changes

* **\[Consensus]** Bias statesync requests to responsive peers
  * Support dynamic peer expansion/contraction
  * Nodes no longer panic if all peers are pruned (e.g., not whitelisted by any init peers)
  * Ref: [monad-bft PR #2536](https://github.com/category-labs/monad-bft/pull/2536)
* **\[Consensus]** Drop blocksync requests that hit disk after cache hydration (\~7min after startup)
  * Ref: [monad-bft PR #2533](https://github.com/category-labs/monad-bft/pull/2533)
* **\[Consensus]** Dataplane: replace interval with sleep
  * Ref: [monad-bft PR #2517](https://github.com/category-labs/monad-bft/pull/2517)
* **\[Execution]** Replace data structures in `VersionStack` code to improve performance when pushing and popping EVM call frames.
  * Ref: [monad PR #1802](https://github.com/category-labs/monad/pull/1802), [monad PR #1877](https://github.com/category-labs/monad/pull/1877)

#### Notable internal changes

* **\[Node ops]** Try fetching remote `forkpoint.toml` and `validators.toml` on startup
  * **IMPORTANT**: Nodes now automatically attempt to download configuration files from remote locations on startup, no "Soft Reset" required. This remote fetch is subject to a configurable remote threshold
  * The following env variables must be set to enable this behavior:
    * `REMOTE_FORKPOINT_URL`
    * `REMOTE_VALIDATORS_URL`
  * Ref: [monad-bft PR #2484](https://github.com/category-labs/monad-bft/pull/2484), [monad-bft PR #2534](https://github.com/category-labs/monad-bft/pull/2534)
* **\[Node ops]** Serialize forkpoints in both TOML and RLP formats, with RLP as source of truth; cleanup `get_latest_config` branches
  * Ref: [monad-bft PR #2521](https://github.com/category-labs/monad-bft/pull/2521)
* **\[Node ops/Consensus]** Dynamically expand statesync upstream peers
  * Always initializes to `statesync.init_peers` (no longer defaults to bootstrap peers)
  * If `expand_to_group` is enabled, expands to validator set (for validators) and/or secondary raptorcast peers (for public / prioritized full nodes)
  * Ref: [monad-bft PR #2535](https://github.com/category-labs/monad-bft/pull/2535)
* **\[Node ops/Consensus]** Full nodes no longer default to blocksync from validator set
  * Dedicated full nodes must specify upstream as blocksync override
  * **IMPORTANT**: prioritized/public full nodes can only blocksync *after* joining secondary raptorcast group. `refresh_period` and `invite_lookahead` recommended to be lowered to 20 seconds
  * Ref: [monad-bft PR #2532](https://github.com/category-labs/monad-bft/pull/2532)
* **\[Consensus]** Use epoch field to encode round number for secondary raptorcast
  * Fixes issue where syncing full nodes receive unsolicited chunks from expired groups
  * Ref: [monad-bft PR #2442](https://github.com/category-labs/monad-bft/pull/2442)
* **\[Consensus]** Add statesync server pending requests metric (better load visibility)
  * Ref: [monad-bft PR #2530](https://github.com/category-labs/monad-bft/pull/2530)
* **\[Node ops]** Import `monad-execution` API changes
  * Ref: [monad-bft PR #2522](https://github.com/category-labs/monad-bft/pull/2522)

## v0.12.0

| Network | Date released | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-11-05 | Revision is set to [`MONAD_SEVEN`](https://docs.monad.xyz/developer-essentials/changelog#revisions) at 2025-11-05 14:30 GMT |
| `devnet` | 2025-11-03 | Devnet was reset with this new release, with revision set to [`MONAD_SEVEN`](https://docs.monad.xyz/developer-essentials/changelog#revisions) |

Tags or hashes:

* `monad-bft`: [tag `v0.12.0`](https://github.com/category-labs/monad-bft/releases/tag/v0.12.0)
* `monad`: [tag `v0.12.0`](https://github.com/category-labs/monad/releases/tag/v0.12.0)

#### Notable protocol changes

* **\[EVM/Network params]** [Opcode/precompile repricing](https://docs.monad.xyz/developer-essentials/opcode-pricing.md)
  * Opcode pricing: increase cost of cold storage access
  * Precompile pricing: better align a few underpriced precompile gas costs with the associated hardware / latency costs
  * Ref: [monad PR #1600](https://github.com/category-labs/monad/pull/1600) (for most of the repricings) and [monad PR #1700](https://github.com/category-labs/monad/pull/1700) (for `CREATE`/`CREATE2` repricing), [monad PR #1830](https://github.com/category-labs/monad/pull/1830) (for reduced v2 scope), [monad PR #1871](https://github.com/category-labs/monad/pull/1871) (activation for `MONAD_SEVEN`)
  * Gated by `MONAD_SEVEN` revision
* **\[Consensus/Network params]** \[Staking] Increase `BLOCK_REWARD_MON` from 1 MON to 25 MON
  * Note that this is not gated by `MONAD_SEVEN` (execution hard fork) but by a specific epoch start for `testnet`
  * Ref: [monad-bft PR #2511](https://github.com/category-labs/monad-bft/pull/2511)

#### Notable robustness changes

* **\[Consensus]** Consensus message prioritization in dataplane
  * Priority queues for UDP traffic ensure consensus messages are delivered before other traffic
  * All consensus messages to validators are published and rebroadcast with high priority
  * Ref: [monad-bft PR #2352](https://github.com/category-labs/monad-bft/pull/2352),
    [monad-bft PR #2354](https://github.com/category-labs/monad-bft/pull/2354)
* **\[Consensus]** DoS protection: Reject repeated invalid consensus messages
  * Prevents malicious validators from consuming CPU time by repeatedly sending invalid BLS signatures
  * Ref: [monad-bft PR #2445](https://github.com/category-labs/monad-bft/pull/2445)
* **\[Consensus]** Leader synchronization improvements
  * Forward AdvanceRound messages to current leader to prevent stale views due to message censorship
  * Ref: [monad-bft PR #2485](https://github.com/category-labs/monad-bft/pull/2485)
* **\[Consensus]** Validate group message sender authenticity
  * Ref: [monad-bft PR #2457](https://github.com/category-labs/monad-bft/pull/2457)

#### Notable RPC/SDK changes

* **\[RPC]** Fix `eth_syncing` serialization
  * Ref: [monad-bft PR #2476](https://github.com/category-labs/monad-bft/pull/2476)
* **\[RPC]** Update `debug_getRawReceipts` RLP encoding
  * Ref: [monad-bft PR #2490](https://github.com/category-labs/monad-bft/pull/2490)
* **\[RPC]** Failed contract creation should return null to address
  * Ref: [monad PR #1861](https://github.com/category-labs/monad/pull/1861),
    [monad-bft PR #2516](https://github.com/category-labs/monad-bft/pull/2516)

#### Notable performance changes

* **\[Consensus]** Dataplane: io\_uring batching for UDP sends
  * Replace GSO with io\_uring batching to preserve 64KB burst size while splitting payload
  * Batches multiple UDP sends into single io\_uring submission
  * Ref: [monad-bft PR #2317](https://github.com/category-labs/monad-bft/pull/2317)
* **\[Consensus]** Dataplane: Restore full 1500 byte MTU
  * Ref: [monad-bft PR #2438](https://github.com/category-labs/monad-bft/pull/2438)
* **\[Consensus]** RaptorCast: Modular packet assembly and round-robin ordering
  * Ref: [monad-bft PR #2377](https://github.com/category-labs/monad-bft/pull/2377),
    [monad-bft PR #2469](https://github.com/category-labs/monad-bft/pull/2469),
    [monad-bft PR #2318](https://github.com/category-labs/monad-bft/pull/2318)
* **\[Consensus]** Txpool optimizations
  * Add configurable limits, remove pending pool, refactor last commit state tracking
  * Ref: [monad-bft PR #2487](https://github.com/category-labs/monad-bft/pull/2487),
    [monad-bft PR #2363](https://github.com/category-labs/monad-bft/pull/2363),
    [monad-bft PR #2475](https://github.com/category-labs/monad-bft/pull/2475)
* **\[Archive]** Move indexer read-back to async task
  * Ref: [monad-bft PR #2486](https://github.com/category-labs/monad-bft/pull/2486)
* **\[RPC]** Remove unnecessary lock in request submission path
  * Ref: [monad-bft PR #2416](https://github.com/category-labs/monad-bft/pull/2416)

#### Notable internal changes

* **\[Node ops]** Docker support for local Monad installation
  * Optional `--use-prebuilt` flag to avoid compilation
  * Ref: [monad-bft PR #2456](https://github.com/category-labs/monad-bft/pull/2456),
    [monad-bft PR #2489](https://github.com/category-labs/monad-bft/pull/2489)
* **\[Node ops]** ledger-tail: New CLI configuration options
  * Supports custom paths for ledger, forkpoint, node config, and validators files
  * Fixes default `validators.toml` path
  * Ref: [monad-bft PR #2439](https://github.com/category-labs/monad-bft/pull/2439)
* **\[Node ops]** wal2json: Multi-file support with timestamp filtering
  * Fast timestamp seeking/filtering across multiple files (e.g., `wal2json -a"3:30pm EDT" -b"4:00pm EDT" wal*`)
  * Improved performance with parallel processing and reduced locking
  * Ref: [monad-bft PR #2496](https://github.com/category-labs/monad-bft/pull/2496),
    [monad-bft PR #2493](https://github.com/category-labs/monad-bft/pull/2493)

## v0.11.6-tn1

Revisions [`MONAD_FIVE`](https://docs.monad.xyz/developer-essentials/changelog#revisions) and
[`MONAD_SIX`](https://docs.monad.xyz/developer-essentials/changelog#revisions) introduced.
Revision [`MONAD_NEXT`](https://docs.monad.xyz/developer-essentials/changelog#revisions) re-defined.

| Network | Date released | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-10-31 | Revision is set to `MONAD_SIX` at 2025-10-31 13:30 GMT |
| `devnet` | 2025-10-30 | Devnet was reset with this new release, with revision set to `MONAD_NEXT` |

Tags or hashes for `testnet` deployment (no protocol differences):

* `monad-bft`: [tag `v0.11.6-tn1`](https://github.com/category-labs/monad-bft/releases/tag/v0.11.6-tn1)
* `monad`: [tag `v0.11.6-tn1`](https://github.com/category-labs/monad/releases/tag/v0.11.6-tn1)

#### Notable protocol changes - `MONAD_NEXT`

* **\[EVM/Network params]** [Opcode Repricing](https://docs.monad.xyz/developer-essentials/opcode-pricing.md)
  * Ref: [monad PR #1600](https://github.com/category-labs/monad/pull/1600) (for most of the
    repricings) and  [monad PR #1700](https://github.com/category-labs/monad/pull/1700) (for
    on storage slot deletion via `SSTORE`
  * Raise the cost of `CREATE` and `CREATE2`
  * Note that this reduces the set of opcode pricings on `MONAD_NEXT` relative to `v0.11.3`.

#### Notable protocol changes - `MONAD_SIX`

* **\[EVM]** EIP-2935 bugfix
  * Ref: [monad PR #1846](https://github.com/category-labs/monad/pull/1846)

#### Notable protocol changes - `MONAD_FIVE`

* **\[Consensus/EVM]** \[Staking] Lower `ACTIVE_VALIDATOR_STAKE` from 25,000,000 MON to **10,000,000 MON**
  * Ref: [monad PR #1810](https://github.com/category-labs/monad/pull/1810)
* **\[EVM]** \[Staking] Add `getProposerValId()` method to return the `val_id` of the most recent block proposer
  * Ref: [monad PR #1815](https://github.com/category-labs/monad/pull/1815)

#### Notable RPC/SDK changes

* **\[RPC]** Fix race condition in block number queries
  * Return triedb block number in ChainState to prevent errors when `eth_getBlockNumber` returns blocks not yet available in triedb
  * Fixes common wallet workflow issue with sequential `eth_getBlockNumber` and `eth_getBalance` calls
  * Ref: [monad-bft PR #2393](https://github.com/category-labs/monad-bft/pull/2393)
* **\[SDK]** Add call frame recording to execution events
  * Ref: [monad PR #1541](https://github.com/category-labs/monad/pull/1541)
  * These will not be recorded unless the `--trace_calls` command line argument is passed to execution
* **\[RPC]** Add `monad_eth_call_executor_get_state()` API for better visibility into `eth_call` requests
  * Ref: [monad PR #1764](https://github.com/category-labs/monad/pull/1764)
  * Returns counts of currently executing/queued requests and error counts

#### Notable robustness changes

* **\[Consensus]** Deterministic timeout certificate tiebreaking
  * When TC contains multiple tips with the same round, tiebreak by tip.qc for consistency
  * Ref: [monad-bft PR #2460](https://github.com/category-labs/monad-bft/pull/2460)
* **\[Consensus]** Transaction nonce overflow validation
  * Ref: [monad-bft PR #2388](https://github.com/category-labs/monad-bft/pull/2388)
* **\[Consensus]** More consistent checks on `EpochChange` between block proposer and validator
  * This addresses an observed chain halt in `testnet-2`
  * Ref: [monad-bft PR #2494](https://github.com/category-labs/monad-bft/pull/2494)

#### Notable performance changes

* **\[EVM]** Use komihash in StateDelta maps
  * Ref: [monad PR #1786](https://github.com/category-labs/monad/pull/1786)
* **\[EVM]** JIT compiler: only emit jump table for contracts with indirect jumps
  * Ref: [monad PR #1749](https://github.com/category-labs/monad/pull/1749)
* **\[RPC]** Improve eth call concurrency with atomic sequence numbers
  * Ref: [monad PR #1759](https://github.com/category-labs/monad/pull/1759)

#### Notable internal changes

* **\[Node ops]** Fuzzer refactor (`--focus` flag addition)
  * Ref: [monad PR #1744](https://github.com/category-labs/monad/pull/1744)
* **\[Node ops]** Build images with debug symbols
  * Ref: [monad-bft PR #2459](https://github.com/category-labs/monad-bft/pull/2459)

## v0.11.3-tn1

Revisions [`MONAD_FOUR`](https://docs.monad.xyz/developer-essentials/changelog#revisions) and
[`MONAD_NEXT`](https://docs.monad.xyz/developer-essentials/changelog#revisions) introduced.

| Network | Date released | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-10-13 | Revision is set to `MONAD_FOUR` at 2025-10-14 13:30 GMT |
| `devnet` | 2025-10-08 | Revision is set to `MONAD_NEXT` upon upgrade |

Tags or hashes for `testnet` deployment (no protocol differences):

* `monad-bft`: [tag `v0.11.3-tn1`](https://github.com/category-labs/monad-bft/releases/tag/v0.11.3-tn1)
* `monad`: [hash `3e17265`](https://github.com/category-labs/monad/tree/3e17265fae80710229c657d725d821053cec940b)

#### Notable protocol changes - `MONAD_NEXT`

* **\[EVM/Network params]** [Opcode Repricing](https://docs.monad.xyz/developer-essentials/opcode-pricing.md))
  * Ref: [monad PR #1600](https://github.com/category-labs/monad/pull/1600) (for most of the
    repricings) and  [monad PR #1700](https://github.com/category-labs/monad/pull/1700) (for
    `CREATE`/`CREATE2` repricing)
  * Opcodes are repriced as discussed in the
    [Monad Initial Spec Proposal](https://forum.monad.xyz/t/monad-initial-specification-proposal/195)
  * Increase cost of cold storage access
  * Precompiles: better align a few underpriced precompile gas costs with the associated
    hardware / latency costs
  * Note: this release also includes a few opcode repricings in MISP v1.0.2 which were later removed:
  * Increase cost of storage slot creation via `SSTORE`, and increase the percent of gas refunded
    on storage slot deletion via `SSTORE`
  * Raise the cost of `CREATE` and `CREATE2`
* **\[EVM]** Disable CREATE and CREATE2 when executing delegated code
  * Ref: [monad PR #1601](https://github.com/category-labs/monad/pull/1601)

#### Notable protocol changes - `MONAD_FOUR`

* **\[Consensus/EVM]** [Staking](https://docs.monad.xyz/monad-arch/consensus/staking.md) is live
  * (many PRs; see
    [staking](https://github.com/category-labs/monad/tree/main/category/execution/monad/staking))
  * Active validator set is now determined by on-chain state of the staking precompile
  * This takes effect starting from a designated `staking_activation` epoch
  * Note: staking rewards do not activate until `staking_rewards_activation` epoch
    (future point in time)
  * External rewards - enable external (non-block-reward) deposits to the validator pool, see
    [monad PR #1625](https://github.com/category-labs/monad/pull/1625)
  * Also added additional events to staking precompile in [monad PR #1742](https://github.com/category-labs/monad/pull/1742)
  * Adds `ValidatorRewarded`, `EpochChanged`, `ClaimRewards` events
* **\[Consensus/EVM]** [Reserve balance](https://docs.monad.xyz/developer-essentials/reserve-balance.md) logic is live
  * Ref: [monad-bft PR #2160](https://github.com/category-labs/monad-bft/pull/2160) and
    [monad PR #1537](https://github.com/category-labs/monad/pull/1537)
  * Due to async execution, consensus does not have the latest state available for transaction
    inclusion logic. Reserve balance is a buffer that enables simpler accounting for a given
    account to mitigate the possibility of overspending in that delay window.
  * Per-EOA reserve balance is set to `10 MON`
* **\[Consensus/EVM]** [EIP-7702](https://docs.monad.xyz/developer-essentials/eip-7702.md) is live
  * Ref: [monad-bft PR #2160](https://github.com/category-labs/monad-bft/pull/2160), [monad-bft PR #2218](https://github.com/category-labs/monad-bft/pull/2218) and
    [monad PR #1362](https://github.com/category-labs/monad/pull/1362)
* **\[Network params]** Set per-transaction gas limit of 30M gas
  * Ref: [monad-bft PR #2246](https://github.com/category-labs/monad-bft/pull/2246)
  * As discussed in the
    [Monad Initial Spec Proposal](https://forum.monad.xyz/t/monad-initial-specification-proposal/195)
* **\[Network params]** Increase block gas limit from 150M gas (375 Mgas/s) to **200M** gas
  (500 Mgas/s)
  * Ref: [monad-bft PR #2266](https://github.com/category-labs/monad-bft/pull/2266)
* **\[Network params]** Implement [dynamic base fee](https://docs.monad.xyz/developer-essentials/gas-pricing.md)
  * Ref: [monad-bft PR #2207](https://github.com/category-labs/monad-bft/pull/2207)
  * As specified in the
    [Monad Initial Spec Proposal](https://forum.monad.xyz/t/monad-initial-specification-proposal/195)
  * Target gas is 80% of a block
  * Raise minimum base fee from 50 MON-gwei to **100 MON-gwei**
* **\[EVM]** Enable [EIP-2935](https://eips.ethereum.org/EIPS/eip-2935) + blockhash
  buffer
  * Ref: [monad PR #1520](https://github.com/category-labs/monad/pull/1520)
* **\[EVM]** Enable [EIP-7951](https://eips.ethereum.org/EIPS/eip-7951) (P256VERIFY
  precompile support)
  * Ref: [monad PR #1518](https://github.com/category-labs/monad/pull/1518)
* **\[EVM]** Enable [EIP-2537](https://eips.ethereum.org/EIPS/eip-2537) (BLS12-381 precompiles)
  * Ref: [monad-bft PR #1342](https://github.com/category-labs/monad/pull/1342) and [monad-bft PR #1350](https://github.com/category-labs/monad/pull/1350)
* **\[EVM]** Raise max contract size for `CREATE`/`CREATE2` to 128 kb
  * Ref: [monad PR #1440](https://github.com/category-labs/monad/pull/1440)
  * This brings `CREATE`/`CREATE2` to parity with toplevel contract creation transactions, which
    had their limit raised in `MONAD_TWO`.
  * Previously, they were unintentionally limited to Ethereum's max initcode size (49.152 kb)
    due to a bug

#### Notable RPC/SDK changes

* **\[SDK]** Added support for [Execution Events](https://docs.monad.xyz/execution-events.md)
* **\[RPC]** Extend `eth_call` support for preStateTracer and stateDiffTracer with `debug_traceCall`
  * Ref: [monad-bft PR #2275](https://github.com/category-labs/monad-bft/pull/2275) and
    [monad PR #1471](https://github.com/category-labs/monad/pull/1471)
* **\[RPC]** Support the `withLog` parameter with `callTracer`
  * Ref: [monad-bft PR #2400](https://github.com/category-labs/monad-bft/pull/2400)
  * If `withLog` is set to true, `callTracer` includes event logs in the trace output

#### Notable performance changes

* **\[EVM]** Kernel caching of db reads and writes
  * Ref: [monad PR #1559](https://github.com/category-labs/monad/pull/1559)
  * Utilize available host memory to cache recent DB operations - this cache
    should increase performance of execution and RPC
* **\[RPC]** Improve RPC Db Node Cache and make it memory bounded
  * Ref: [monad PR #1581](https://github.com/category-labs/monad/pull/1581)
  * Note a rename of RPC cli flags: `--eth-call-executor-node-lru-size` to
    `--eth-call-executor-node-lru-max-mem` and a new flag `--triedb-node-lru-max-mem` with
    both default to 100MB.

#### Notable internal changes

* **\[Node ops]** Remove `bft-fullnode` binary; only `bft` binary now
  * Ref: [monad-bft PR #2072](https://github.com/category-labs/monad-bft/pull/2072)
  * `bft-fullnode` removed from `deb` pkg for `v0.11`
* **\[Node ops]** PeerDiscovery: Introduce precheck for peer self name address
* **\[Consensus]** Blocksync: only select blocksync peers from connected nodes
  * Ref: [monad-bft PR #2401](https://github.com/category-labs/monad-bft/pull/2401)
* **\[Consensus]** Raptorcast: DOS protection on decoding state cache
  * Ref: [monad-bft PR #2092](https://github.com/category-labs/monad-bft/pull/2092)
* **\[Node ops]** Secondary raptorcast config change
  * Ref: [monad-bft PR #2378](https://github.com/category-labs/monad-bft/pull/2378)
  * Replace ambiguous secondary raptorcast  `mode` parameter with `enable_publisher` and `enable_client`
* **\[Node ops]** Dynamically reload prioritized full-nodes
  * Ref: [monad-bft PR #2364](https://github.com/category-labs/monad-bft/pull/2364)
* **\[Node ops]** Fix wal2json
  * Ref: [monad-bft PR #2404](https://github.com/category-labs/monad-bft/pull/2404)
* **\[Node ops/RPC]** Support the RPC CLI param `ws-sub-per-conn-limit`
  * Ref: [monad-bft PR #2161](https://github.com/category-labs/monad-bft/pull/2161)
  * Sets the maximum number of websocket subscriptions per connection (default to 100)
* **\[Node ops/RPC]** Add configuration options for high eth-call pool
  * Ref: [monad-bft PR #2387](https://github.com/category-labs/monad-bft/pull/2387)

## v0.11.1

Note: `v0.11.1` was a version that was deployed only on `testnet-2` (a temporary network deprecated
on 2025-10-27) from roughly 2025-09-16 until 2025-10-08; however, it maps some features differently
to revision `MONAD_FOUR` which are no longer memorialized in the codebase. `testnet-2` was reset
before deploying `v0.11.3`.

For all intents and purposes, this version can be ignored. This changelog will compare `v0.11.3`
with `v0.10.4`.

Tags or hashes:

* `monad-bft`: [tag `v0.11.1`](https://github.com/category-labs/monad-bft/releases/tag/v0.11.1)
* `monad`: [hash `7746980`](https://github.com/category-labs/monad/tree/7746980c45b82f812bd8c4d39f4b0a1232ae16de)

## v0.10.4

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-08-18 | Revision is still `MONAD_THREE` |

Tags or hashes:

* `monad-bft`: [tag `v0.10.4`](https://github.com/category-labs/monad-bft/releases/tag/v0.10.4)
* `monad`: hash `39c42e6`

#### Notable RPC/SDK changes

* **\[RPC]** EIP-4844 related fields in RPC responses are removed.
  * Block headers returned from RPC will no longer have `blobGasUsed` , `excessBlobGas`, and
    `parentBeaconBlockRoot`.

#### Notable performance changes

* **\[Consensus]** Votes are now sent to current round leader. This is a consensus optimization that
  reduces the effective delay due to a round timeout
  * Ref: [monad-bft PR #2093](https://github.com/category-labs/monad-bft/pull/2093)
* **\[Consensus]** Caching of recently-verified quorum certificates
  * Ref: [monad-bft PR #2167](https://github.com/category-labs/monad-bft/pull/2167)
* **\[Node ops]** Enablement of trace calls is now controlled via `monad` (execution) command line
  arg `--trace_calls`.
  * To preserve legacy behavior, `--trace_calls` is currently enabled in the debian package. In the
    future we recommend disabling for validators and enabling it for RPC and archive nodes.
  * This allows voting validators to opt out of computing traces since they're only need for
    RPC nodes.

#### Notable internal changes

* **\[Consensus]** TC forwarding to prioritized and public (non-dedicated) full nodes
  * Ref: [monad-bft PR #2149](https://github.com/category-labs/monad-bft/pull/2149)
  * Prior to `v0.10.4`, all full nodes were subject to lagging behind validators in the event of a
    timeout because round advancement due to TC was not forwarded (and still isn’t to dedicated full
    nodes).
  * As a result, after timeouts, full nodes would frequently forward transactions to the
    next three leaders relative to a stale state. This results in those transactions often missing
    and the ensuing blocks being comparatively empty.
* **\[Node ops]** Bugfix for secondary raptorcast (round gap crash) that affected validators in
  Publisher mode
  * Ref: [monad-bft PR #2090](https://github.com/category-labs/monad-bft/pull/2090)
* **\[Node ops]** `ledger-tail` improvements
  * Ref: [monad-bft PR #2144](https://github.com/category-labs/monad-bft/pull/2144)
  - Reduced memory usage on startup
  - `author_dns` field changed to `author_address` to reflect change in v10 addresses
  - Timeouts and finalizations are tracked and logged
* **\[Consensus]** Txpool account preloading bugfix
  * Ref: [monad-bft PR #2108](https://github.com/category-labs/monad-bft/pull/2108)

## v0.10.3

[`MONAD_THREE`](https://docs.monad.xyz/developer-essentials/changelog#revisions) revision introduced.

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-08-12 | Revision is set to `MONAD_THREE` when upgraded |

#### Notable protocol changes - `MONAD_THREE`

* **\[Consensus]** Consensus mechanism upgraded from [Fast-HotStuff](https://arxiv.org/abs/2010.11454)
  to [MonadBFT](https://docs.monad.xyz/monad-arch/consensus/monad-bft.md)
  * This is a major upgrade that adds
    *(i)* [resilience to tail forking](https://docs.monad.xyz/monad-arch/consensus/monad-bft.md#no-tail-forking) and
    *(ii)* [1-slot speculative finality](https://docs.monad.xyz/monad-arch/consensus/monad-bft.md#speculative-finality)
* **\[Network params]** Block time reduced from 500 ms to **400 ms**

#### Notable RPC/SDK changes

* **\[RPC]** Add support for [real-time data](https://docs.monad.xyz/monad-arch/realtime-data) via
  [WebSocket](https://docs.monad.xyz/reference/websockets.md) and shared memory queue access (docs coming soon):
  * Geth real-time events (via WebSocket)
  * Geth real-time events with Monad extensions (via WebSocket)
  * Real-time data via shared memory queue, for programs on a full node host using the execution event SDK

#### Notable performance changes

* **\[Execution]** Switch to JIT EVM. The bytecode of expensive or frequently-executed contracts is
  compiled directly to native code for faster execution
* **\[Execution]** Switch to using file pointer-based IPC to execute blocks. Previously, the client
  was using a write-ahead log (WAL), which did not take advantage of available consensus
  information and could result in avoidable execution

#### Notable internal changes

* **\[Node ops]** Adds peer discovery
* **\[Node ops]** Adds full node [RaptorCast](https://docs.monad.xyz/monad-arch/consensus/raptorcast.md), making the full
  node network scalable

## v0.9.3

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-05-29 | Revision is still `MONAD_TWO` |

#### Notable RPC/SDK changes

* **\[RPC]** `eth_call` and `eth_estimateGas` limits
  * RPC providers can now set individual per-transaction limits on maximum gas for `eth_call` and
    `eth_estimateGas`
    * Previously the limit would always be the block gas limit (150M), now the RPC provider may
      choose (default: 30M)
    * Controlled with `--eth-call-provider-gas-limit` and `--eth-estimate-gas-provider-gas-limit`
  * Add a maximum timeout for queueing when executing `eth_call` and `eth_estimateGas`
    * Controlled with `--eth_call_executor_queuing_timeout`

#### Notable performance changes

* **\[RPC]** Improve overall `eth_call` performance by maintaining separate queues for cheap and
  expensive `eth_call` operations, so that cheap `eth_call` operations will not be queued behind expensive ones.
  * This adds two new RPC error strings:
    * `failure to submit eth_call to thread pool: queue size exceeded`
    * `failure to execute eth_call: queuing time exceeded timeout threshold`
* **\[RPC]**  Added an archive index for `eth_getLogs` to support queries with address and/or topic
  filters
  * This enables larger block ranges to be queried efficiently, with work proportional to number
    of matching logs instead of number of blocks in range
* **\[Execution]** Better bounding of TrieDB traversals

#### Notable internal changes

* **\[Node ops]**  Performance improvements for slow statesync client upsert
* **\[Node ops]**  Bugfix for execution delay and abrupt history length drops caused by premature
  soft reset
* **\[Node ops]**  `keystore` QOL improvements
  * Support for importing from a private key in hex string format (previously required conversion
    to json file)
  * More helpful documentation via `--help` command

## testnet-1 active set expansion

On 2025-05-02, `testnet-1` experienced an active set expansion

#### Notable internal changes

* **\[Network params]** Testnet validator set expanded from 72 to **99** nodes

## v0.9.2

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-04-05 | Revision is still `MONAD_TWO` |

#### Notable performance changes

* **\[RPC]** Update to the `eth_call` execution implementation - uses fewer threads to achieve the
  same concurrency as in `v0.9.1`

#### Notable internal changes

* **\[Node ops]** Support for a faster [statesync](https://docs.monad.xyz/monad-arch/consensus/statesync.md) mechanism
* **\[RPC]** RPC no longer accepts requests while node is statesyncing
* **\[Node ops]** Some reliability and efficiency improvements to how statesync traffic is carried
  between nodes
* **\[Node ops]** Bugfixes for execution crashes (`monad::mpt::deserialize_node_from_buffer`,
  `'Resource temporarily unavailable`)

- **\[Node ops]** Bug fix for unbounded blocksync requests that result in node OOM failures
- **\[Node ops]** Removal of DNS resolution panic on start up

## v0.9.1

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-03-24 | Revision is set to `MONAD_TWO` |

#### Notable internal changes

* **\[Node ops]** Bugfix for blocksync errors
* **\[Node ops]** Reliability and efficiency improvements to statesync

## v0.9.0

Revision [`MONAD_TWO`](https://docs.monad.xyz/developer-essentials/changelog#revisions) introduced.

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-03-14 | Revision is set to `MONAD_TWO` at 2025-03-14 19:00 GMT |

#### Notable protocol changes - `MONAD_TWO`

* **\[EVM]** Max contract size increased from 24kb to **128kb**

#### Notable RPC/SDK changes

* **\[RPC]** `debug_traceTransaction` fixes
  * Fixed a bug where, within one transaction, only the first 100 calls were being traced
  * Added `error` and `revertReason` fields to response data

#### Notable performance changes

* **\[Consensus]** Dataplane v2 - simpler and more efficient implementation; small performance
  improvement in broadcast time
* **\[RPC]** Improvements to RPC performance for `eth_call`

- **\[RPC]** Removed redundant sender\_recovery operation on raw transactions received via RPC

#### Notable internal changes

* **\[Node ops]** Statesync improvements to mitigate negative performance effects on upstream
  validator nodes

- **\[RPC]** EIP-2 signature validation added to RPC transaction validation
- **\[Node ops]** Miscellaneous tracing, logging and metrics additions
- **\[Consensus]** RaptorCast performance improvement when dealing with invalid symbols

## v0.8.1

Revision [`MONAD_ONE`](https://docs.monad.xyz/developer-essentials/changelog#revisions) introduced.

| Network | Date deployed | Comment |
| - | - | - |
| [`testnet`](https://docs.monad.xyz/developer-essentials/testnet) | 2025-02-14 | Revision is set to `MONAD_ONE` at 2025-02-14 19:00 GMT |

#### Notable protocol changes - `MONAD_ONE`

* **\[Network params]** Block time reduced from 1s to **500 ms**

* **\[Network params]** Block gas limit reduced from 300M to **150M** (to keep gas limit consistent)

* **\[EVM]** Transactions are [charged](https://docs.monad.xyz/developer-essentials/gas-pricing.md) based on gas limit,
  not gas consumed

#### Notable RPC/SDK changes

* **\[RPC]** UX improvements for [transaction status](https://docs.monad.xyz/monad-arch/transaction-lifecycle.md). RPC
  nodes track status of transactions submitted to them in order to provide updates to users.


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.