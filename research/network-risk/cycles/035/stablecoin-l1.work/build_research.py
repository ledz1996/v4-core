"""Writes cycles/035/stablecoin-l1.research.json from the outputs in this work directory."""
import json, os

W = 'research/network-risk/cycles/035/stablecoin-l1.work'
TEMPO = 'https://rpc.mainnet.tempo.xyz'
ARC = 'https://rpc.mainnet.arc.io'
PN = 'https://arc-rpc.publicnode.com'
DRPC = 'https://arc.drpc.org'
BIN = 'https://download.tempo.xyz/binaries/v1.19.2/'
RAWT = 'https://raw.githubusercontent.com/tempoxyz/tempo'
RAWA = 'https://raw.githubusercontent.com/circlefin/arc-node'
CS = 'https://docker.cloudsmith.io/v2/circle/arc-network/arc-execution'
UPG = 'https://tempo.com/developers/docs/guide/node/network-upgrades.md'
T15 = 'https://tempo.com/developers/docs/protocol/upgrades/t15.md'

profiles = [
 {"chainId": 4217, "lens": "L1",
  "summary": "The v1.19.2 release binaries that mainnet runs are now published. In the x86_64 binary every arithmetic, comparison, shift, BYTE, SIGNEXTEND, EXP, KECCAK256, calldata, return data, memory, MCOPY, JUMP, JUMPI, TLOAD, TSTORE, PUSH, DUP and SWAP handler tree, and the four jump destination analysis routines, are instruction for instruction those of the v1.19.1 binary that cycles 28 to 31 lifted, so those lifts now speak for the running build. All six tool reruns match the specification on the live endpoint.",
  "deltas": [
   {"delta": "download.tempo.xyz/binaries now lists v1.19.2 (files dated 27 November 2026 13:52). x86_64 archive sha256 7722426b5f7a5bc27a17f3db3ba0d4f19a713d2747fe96a447babcd54631eae3 equals its .sha256 file; the binary (114,241,840 bytes, sha256 27a42f86b4f3c1d3c5e8623d597c80ea6299920ec9c70f3a303b4083bc023ddd, GNU build id 87e7d8bbfcef729698cca974dd1b6a434b152de5, rustc 1.100.0, LLD 23.1.5) embeds commit c0c937211e0d48dff569c0855931b1645207ddd8, which the endpoint reports as tempo/v1.19.2-c0c9372, names ruint-1.21.1 and holds no evm2-jit code.",
    "source": f"{BIN} ; web3_clientVersion on {TEMPO} (2026-11-27) ; {W}/dl/x_x86_64 (readelf -n, readelf -p .comment, strings)", "relevance": "low"},
   {"delta": "Handler comparison against v1.19.1 (scripts/bincmp.py, scripts/coldcmp.py): the three dispatch tables moved to 0x6c468d0, 0x6c29b18 and 0x6c460d0 and were matched by handler entry offset and FDE size (256, 151 and 256 of 256, 151 and 256 entries). From 351 handler roots, 729 functions and 64,139 instructions were compared up to eight call levels with absolute addresses replaced, branch targets mapped and jump tables decoded. Only the CALL family frame code and the SSTORE gas check differ: three context fields sit 12 bytes later (0x600 to 0x60c, 0x604 to 0x610, 0x605 to 0x611) and the frame entry routine grew from 1,448 to 1,787 bytes, saving the execution flag and taking a reference count, which is the nested transaction guard cycle 33 read in the evm2 7c9f3b6d source. The remaining 28 unmatched targets are both _Unwind_Resume@plt.",
    "source": f"{W}/results/bincmp_d8.json ; {W}/results/coldcmp_d8.json ; {W}/results/f_old.s ; {W}/results/f_new.s ; research/network-risk/cycles/028/theme-tempo-release-binary-read.work/results/x64_arith_funcs.json", "relevance": "low"},
   {"delta": "The jump destination analysis routines of v1.19.1 (0x1e29620, 0x1e29770, 0x1e29cf0, 0x1e29fa0: dispatcher and the SSE4.1, AVX2 and AVX-512 kernels) are byte for byte equal after address normalisation to v1.19.2 at 0x1e2d3b0, 0x1e2d500, 0x1e2da80 and 0x1e2dd30.",
    "source": f"{W}/dl/x_x86_64 ; research/network-risk/cycles/028/theme-tempo-release-binary-read.work/results/x64_jd_funcs.json", "relevance": "low"},
   {"delta": "The main branch still says version 1.19.2 and pins evm2 7c9f3b6deb23005fc84596ba1b13a6492d942014 and ruint 1.21.1; its Cargo.lock differs from c0c9372 only by two fuzz crates.",
    "source": f"{RAWT}/main/Cargo.toml ; {RAWT}/main/Cargo.lock ; {W}/dl/tempo-main-Cargo.lock", "relevance": "none"},
   {"delta": "Reruns on tempo/v1.19.2-c0c9372: 99,985 battery and 85,544 targeted vectors with no mismatch, call semantics 50 of 50, 1,034 mined swaps exact. pmdiff differs on scripts 9, 14, 29, 67, 79, 81, 86, 147, 175 and 233 as cycle 33's rerun did; with 20 times the gas 8 become identical and 67 and 86 still end at the gas-limited open-limit swap. pmdiff2 differs on the same six scripts as cycle 33.",
    "source": f"eth_call on {TEMPO} (2026-11-27) ; {W}/battery.log ; {W}/targeted.log ; {W}/callsem.log ; {W}/pmdiff.log ; {W}/pmdiff_explain.log ; {W}/pmdiff2.log ; {W}/swaps.log", "relevance": "none"}]},
 {"chainId": 4217, "lens": "L2",
  "summary": "On the main branch, which is still version 1.19.2, no production code starts a transaction inside a running one on the Tempo chain's own EVM. The speculative replay builder and its candidate test are unchanged, and a PoolManager call still cannot be a replay candidate under the T15 payment rules.",
  "deltas": [
   {"delta": "callers.py over 529 Rust files of tempoxyz/tempo main (crawled from 17 crate roots including payload/builder and the zone crates) lists 17 production lines. 11 equal the Tempo-owned lines of cycle 33's v1.19.2 list. crates/payload/builder/src/prewarming.rs:193 runs transact on a pooled worker EVM created by evm_for_ctx and exists at c0c9372 as well; cycle 33 did not crawl that crate. The other 5 are in crates/zones (zone node, payload, executor, fuzz harness), which run a zone chain, not the Tempo chain that holds the PoolManager.",
    "source": f"{RAWT}/main/crates/payload/builder/src/prewarming.rs ; {RAWT}/c0c937211e0d48dff569c0855931b1645207ddd8/crates/payload/builder/src/prewarming.rs ; {W}/results/callers_main.txt ; research/network-risk/cycles/033/theme-tempo-v1192-nested-dispatch.work/out/callers_new.txt", "relevance": "low"},
   {"delta": "is_parallel_candidate (prewarming.rs:494-503 on main) still admits only is_payment_v2 transactions with a nonzero nonce key, and --builder.parallel is still hidden with default false (crates/node/src/node.rs:137-139). is_payment_v3, the T15 rule the TODO names, still requires every call to be a TIP-1045 call to a TIP-20 token or the channel reserve (crates/primitives/src/transaction/envelope.rs:286-330).",
    "source": f"{RAWT}/main/crates/payload/builder/src/prewarming.rs ; {RAWT}/main/crates/node/src/node.rs ; {RAWT}/main/crates/primitives/src/transaction/envelope.rs", "relevance": "low"}]},
 {"chainId": 4217, "lens": "L4",
  "summary": "On main, from T15, a TIP-20 transfer to a zone deposit address credits the zone's portal and then calls the portal's depositVirtual synchronously, and any revert of the portal reverts the whole transfer. Mints and other payouts refuse such addresses.",
  "deltas": [
   {"delta": "crates/precompiles/src/tip20/mod.rs on main: resolve_transfer (lines 1674-1695) maps a registered zone deposit address to portal_address(zone_id) from T15 and rejects version 0 and unregistered zones; deposit_virtual (lines 1070-1115) refuses the routing when the transfer runs inside another precompile's frame, refuses a zero amount, and returns the portal's revert as the transfer's revert; resolve (lines 1653-1661) makes such an address an invalid recipient for mints and other payouts.",
    "source": f"{RAWT}/main/crates/precompiles/src/tip20/mod.rs", "relevance": "low"}]},
 {"chainId": 4217, "lens": "L6",
  "summary": "T14 is still set for 8 December 2026 15:00 UTC (1,796,742,000) and runs on v1.19.2. T15 has no release and no activation time, and its published scope is configurable voucher signers for the channel reserve only. The endpoint serves latest at the finalized height today.",
  "deltas": [
   {"delta": "The network upgrades page lists tempo/v1.19.0 as the T14 release and T15 with release 'Not yet published', targets 8 December (testnet) and 15 December 2026 (mainnet). The T15 page covers TIP-1166 only. crates/hardfork/src/lib.rs on main returns None for every T15 timestamp, and constants.rs keeps MAINNET_T14_TIMESTAMP = 1_796_742_000.",
    "source": f"{UPG} ; {T15} ; {RAWT}/main/crates/hardfork/src/lib.rs ; {RAWT}/main/crates/hardfork/src/constants.rs", "relevance": "low"},
   {"delta": "eth_getBlockByNumber at 18:20 UTC: latest 51,109,480, safe and finalized 51,109,481. Whether latest runs ahead of finalized after T14 remains to be seen on 8 December.",
    "source": f"eth_getBlockByNumber on {TEMPO} (2026-11-27) ; {W}/tempo_heads.log", "relevance": "none"}]},
 {"chainId": 5042, "lens": "L1",
  "summary": "Circle publishes arc-execution images only for v0.8.5 (602eed3b) and v0.8.6 (b11795567992a7bf51e7f538ae37e7f19d076e13). Neither the official endpoint's 37812c61, drpc's v0.8.6 at 8e8edb7a, nor Blockdaemon's db2d22c1 has a public image, so three of the four builds that answer are unpublished. Both images embed reth 508cbdf, which is circlefin/arc-reth tag v2.2.0-arc.2. All six tool reruns match on the official endpoint and on PublicNode.",
  "deltas": [
   {"delta": "docker.cloudsmith.io/circle/arc-network/arc-execution and arc-consensus list tags 0.6.0 to 0.8.6 with commit-suffixed tags 0.8.5-602eed3b and 0.8.6-b1179556 and no other 0.8.5 or 0.8.6 suffix. The amd64 binary of 0.8.6 (sha256 97ad5a38e197e33a6ab820f6161c199beb022316840ec1957e4f84e89eb0b84f, image created 2026-11-19) reports 'v0.8.6 (b1179556)' and git_commit b11795567992a7bf51e7f538ae37e7f19d076e13; the 0.8.5 binary reports 602eed3b702728cabb16be716a8fd5eb8e99a027. Both carry the string reth/v2.2.0-508cbdf and the full hash 508cbdf7d6ba49b4ce735d678863897067fa381a. The image configs carry no labels, so no org.opencontainers revision annotation exists to read.",
    "source": f"{CS}/tags/list ; {CS}/manifests/0.8.6 ; {CS}/manifests/0.8.5 ; {W}/ghcr/", "relevance": "low"},
   {"delta": "crates/evm/src/evm.rs and Cargo.lock at b11795567992a7bf51e7f538ae37e7f19d076e13 are byte equal to the v0.8.6 tag and to cycle 33's copy. Cargo.lock at 602eed3b and at v0.8.6 takes 103 reth crates from git+https://github.com/circlefin/arc-reth?tag=v2.2.0-arc.2#508cbdf7d6ba49b4ce735d678863897067fa381a, with revm 38.0.0, revm-interpreter 35.0.1 and ruint 1.20.0 from crates.io.",
    "source": f"{RAWA}/b11795567992a7bf51e7f538ae37e7f19d076e13/crates/evm/src/evm.rs ; {RAWA}/v0.8.6/Cargo.lock ; {RAWA}/602eed3b702728cabb16be716a8fd5eb8e99a027/Cargo.lock", "relevance": "low"},
   {"delta": "arc_getVersion, two samples each on 2026-11-27: rpc.mainnet.arc.io v0.8.6-rc1 (37812c61), arc.drpc.org v0.8.6 (8e8edb7a), rpc.blockdaemon.mainnet.arc.io v0.8.5 (db2d22c1), arc-rpc.publicnode.com v0.8.5 (602eed3b). drpc's v0.8.6 is a different commit from the published v0.8.6.",
    "source": f"arc_getVersion on {ARC}, {DRPC}, https://rpc.blockdaemon.mainnet.arc.io, {PN} ; {W}/pn/arc_version.log", "relevance": "low"},
   {"delta": "Reruns: official endpoint 99,985 battery and 85,544 targeted vectors with no mismatch, call semantics 50 of 50, pmdiff 250 of 250, pmdiff2 300 of 300, 6,525 mined swaps exact and 25 multi-step swaps replayed. PublicNode (602eed3b) gives the same: 185,529 vectors, 50 of 50, 250 of 250 and 300 of 300.",
    "source": f"eth_call on {ARC} and {PN} (2026-11-27) ; {W}/battery.log ; {W}/targeted.log ; {W}/callsem.log ; {W}/pmdiff.log ; {W}/pmdiff2.log ; {W}/swaps.log ; {W}/replay.log ; {W}/pn/", "relevance": "none"}]},
 {"chainId": 5042, "lens": "L2",
  "summary": "Two Arc builds now serve eth_simulateV1 (PublicNode 602eed3b and drpc 8e8edb7a). On both, a currency synced in one transaction is empty in the next transaction of the same simulated block, and the 23 multi-transaction scenarios give 137 of 137 reference results. The simulation path applies Arc's native value hook.",
  "deltas": [
   {"delta": "stalesync.py: a bare sync of an overridden token in transaction 1 leaves both synced slots at zero for transaction 2, and transaction 3's unlock reads zero and settles nothing; the control inside one transaction reads the token and 0x1234. Same result on PublicNode and drpc.",
    "source": f"eth_simulateV1 on {PN} and {DRPC} (2026-11-27) ; {W}/pn/out/stalesync-arc-publicnode.json ; {W}/pn/out/stalesync-arc-drpc.json ; src/libraries/CurrencyReserves.sol:11-36", "relevance": "low"},
   {"delta": "The 23 scenarios of cycle 28 with a 30,000,000 gas block (Arc's block gas limit; the default 400,000,000 block is refused with 'Client adjustable limit reached'): 137 of 137 calls equal the reference on PublicNode and on drpc.",
    "source": f"eth_simulateV1 on {PN} and {DRPC} (2026-11-27) ; {W}/pn/scen-arc-pn.json ; {W}/pn/scen-arc-drpc.json", "relevance": "low"},
   {"delta": "A value-carrying CALL of 1 wei from an overridden contract returns 0, 1, 1, 0 to address zero, 0xb0b, precompile 0x01 and the 0x3600 token face, both through eth_call and through eth_simulateV1 on PublicNode, which is the Arc hook result cycle 33 recorded for all four builds.",
    "source": f"eth_call and eth_simulateV1 on {PN} (2026-11-27) ; {W}/pn/valuecall_sim.json", "relevance": "low"}]},
 {"chainId": 5042, "lens": "L4", "summary": "Nothing new on Arc's special addresses: the 0x3600 face still refuses a value-carrying call on the simulation path as on eth_call.", "deltas": []},
 {"chainId": 5042, "lens": "L6",
  "summary": "No Arc hardfork is scheduled. Hardfork list, changelog and lock file on main are byte equal to cycle 33's copies and end at Zero8, and no tag after v0.8.6 exists.",
  "deltas": [
   {"delta": "crates/execution-config/src/hardforks.rs, CHANGELOG.md and Cargo.lock on main equal cycle 33's copies; raw fetches of v0.8.7, v0.8.7-rc1, v0.8.6-rc2, v0.9.0 and v0.9.0-rc1 return 404; the image registry has nothing after 0.8.6.",
    "source": f"{RAWA}/main/crates/execution-config/src/hardforks.rs ; {RAWA}/main/CHANGELOG.md ; {CS}/tags/list", "relevance": "none"}]},
]

cleared = [
 {"chainIds": [4217], "lens": "L1",
  "check": "Do the cycle 28 to 31 binary lifts of v1.19.1 (arithmetic handlers with ruint mul_mod_by_ref, div_rem_by_ref, rem_by_ref, add_mod_by_ref and div_rem_bits_plus_one, jump destination analysis, keccak, transient storage) speak for the v1.19.2 binary that mainnet runs?",
  "result": "Yes for x86_64. Every handler root of opcodes 0x00 to 0x0b, 0x10 to 0x1d, 0x20, 0x35 to 0x3e, 0x50 to 0x9f, 0xf1, 0xf3, 0xfa and 0xfd in the three dispatch tables was walked with its callees to eight levels: 729 functions and 64,139 instructions. All arithmetic, comparison, shift, BYTE, SIGNEXTEND, EXP, KECCAK256, MLOAD, MSTORE, MCOPY, JUMP, JUMPI, TLOAD, TSTORE and stack trees are equal after address normalisation, including the five ruint routines, and the four jump destination routines are equal. Differences are limited to the call frame entry and three context field offsets in the CALL family and SSTORE paths, which match the evm2 7c9f3b6d nested transaction guard. So the results that FullMath.mulDiv (src/libraries/FullMath.sol:24, 48, 112), SqrtPriceMath (src/libraries/SqrtPriceMath.sol:252), TickMath (src/libraries/TickMath.sol:61-63, 80-111, 142-150) and the transient delta and lock code (src/libraries/CurrencyDelta.sol:21-39, src/libraries/Lock.sol:13) depend on come from the same machine code that was lifted and run before.",
  "source": f"{BIN}tempo-v1.19.2-x86_64-unknown-linux-gnu.tar.gz ; {W}/results/bincmp_d8.json ; {W}/results/coldcmp_d8.json ; {W}/scripts/bincmp.py"},
 {"chainIds": [4217], "lens": "L1",
  "check": "Is the evm2 JIT (evm2-jit crates in Cargo.lock) compiled into the v1.19.2 release?",
  "result": "No. The x86_64 binary contains no evm2-jit or evm2_jit string and no LLVM C API symbol, as for v1.19.1. Every PoolManager call runs on the interpreter that was compared.",
  "source": f"{W}/dl/x_x86_64 (strings) ; {W}/dl/tempo-main-Cargo.lock"},
 {"chainIds": [4217], "lens": "L1",
  "check": "Reruns of battery.py, targeted.py, callsem.py, pmdiff.py, pmdiff2.py, swaps.py and replay.py on tempo/v1.19.2-c0c9372.",
  "result": "185,529 vectors and 50 call semantics cases as specified, 1,034 mined swaps exact. The ten pmdiff and six pmdiff2 differences are the known gas-limited open-limit swaps: the first differing call is an init or swap that ran out of gas, eight of ten become identical with 20 times the gas, and the set equals cycle 33's.",
  "source": f"{W}/battery.log ; {W}/targeted.log ; {W}/callsem.log ; {W}/pmdiff_explain.log ; {W}/pmdiff2.log ; {W}/swaps.log"},
 {"chainIds": [4217], "lens": "L2",
  "check": "Does any production code on the main branch start a transaction while a user transaction of the Tempo chain runs, which would clear the lock and deltas of an open unlock (src/PoolManager.sol:104-114)?",
  "result": "No. The 17 production call sites on main are the 11 of v1.19.2, the payload builder's prewarming on a separate pooled EVM (present at c0c9372 too), and five in zone crates that execute a zone chain. The interpreter still has no check that refuses a nested transact, so the search must be repeated for the T15 release.",
  "source": f"{W}/results/callers_main.txt ; {RAWT}/main/crates/payload/builder/src/prewarming.rs"},
 {"chainIds": [4217], "lens": "L2",
  "check": "Cycle 25 lead: if T15 switches the replay candidate test to is_payment_v3, can a replayed action reach a PoolManager call?",
  "result": "No. is_payment_v3 differs from v2 only in allowing trailing bytes on static payment calls and TIP-1166 voucher signatures on channel reserve settle and close; every call must still be a TIP-1045 call to a TIP-20 token or the channel reserve, so a transaction that calls the PoolManager or a router is never a candidate. The parallel builder flag is still hidden and off by default.",
  "source": f"{RAWT}/main/crates/primitives/src/transaction/envelope.rs ; {RAWT}/main/crates/payload/builder/src/prewarming.rs ; {RAWT}/main/crates/node/src/node.rs"},
 {"chainIds": [4217], "lens": "L4",
  "check": "From T15, what does a take of a TIP-20 currency to a zone deposit address do inside the PoolManager (src/PoolManager.sol:291-297)?",
  "result": "The delta is debited first (line 294), then the token precompile credits the portal and calls its depositVirtual in the same frame; a revert of the portal reverts the transfer and so the take, which restores the delta. A take naming a deposit address from inside another precompile's frame is refused. A successful deposit is the taker's own choice of recipient, which F-135 already records with its asynchronous refund. No other user's balance or delta is touched.",
  "source": f"{RAWT}/main/crates/precompiles/src/tip20/mod.rs ; src/PoolManager.sol:291-297"},
 {"chainIds": [5042], "lens": "L2",
  "check": "L-1278 and the cycle 34 critic gap: is transient storage reset between transactions on an Arc build, so a sync or an open delta cannot leak into the next transaction (src/libraries/CurrencyReserves.sol:11-36, src/PoolManager.sol:349-365)?",
  "result": "Yes on PublicNode (v0.8.5, 602eed3b) and drpc (v0.8.6, 8e8edb7a), the first two Arc builds with a simulation method. A sync in one transaction is invisible to the next, the 23 scenarios match 137 of 137, and the simulation path applies Arc's value hook. The official build 37812c61 and Blockdaemon's db2d22c1 refuse the method, so they are tested through single calls only.",
  "source": f"eth_simulateV1 on {PN} and {DRPC} (2026-11-27) ; {W}/pn/"},
 {"chainIds": [5042], "lens": "L1",
  "check": "Reruns on the official Arc endpoint and on PublicNode.",
  "result": "185,529 vectors, 50 call semantics cases, 250 and 300 PoolManager scripts identical to Ethereum on both endpoints; 6,525 mined swaps exact and 25 multi-step swaps replayed on the official endpoint.",
  "source": f"{W}/battery.log ; {W}/targeted.log ; {W}/callsem.log ; {W}/pmdiff.log ; {W}/pmdiff2.log ; {W}/swaps.log ; {W}/replay.log ; {W}/pn/"},
 {"chainIds": [5042], "lens": "L6",
  "check": "Arc upgrades in the next six months.",
  "result": "None is published: no hardfork after Zero8 in source, no tag or image after v0.8.6. Nothing changes for funds in the PoolManager on a known date.",
  "source": f"{RAWA}/main/crates/execution-config/src/hardforks.rs ; {CS}/tags/list"},
]

leads = [
 {"chainIds": [4217], "lens": "L1",
  "question": "Do the aarch64 v1.19.2 binary's handler trees equal the aarch64 v1.19.1 binary that cycle 28 lifted, as the x86_64 ones do?",
  "why": "Only the x86_64 build was compared. Validators on arm64 hardware run the other build.", "priority": "low"},
 {"chainIds": [4217], "lens": "L2",
  "question": "When the T15 release is published, does any new caller of transact, system_call or execute_tx run on the Tempo chain's EVM while a user transaction is in progress, and is the frame entry routine at 0x4af9600 of v1.19.2 (the nested transaction guard) still the only one?",
  "why": "A nested transaction would clear the lock and deltas of an open unlock. No production code does it on v1.19.2 or main, and the interpreter does not refuse it.", "priority": "medium"},
 {"chainIds": [5042], "lens": "L1",
  "question": "Which source and image correspond to 37812c61 (official endpoint), 8e8edb7a (drpc's v0.8.6) and db2d22c1 (Blockdaemon), and which of them the validators run?",
  "why": "The published images are 602eed3b and b1179556 only. Results on the other three rest on their answers alone.", "priority": "low"},
]

lead_results = [
 {"leadId": "L-1278", "outcome": "cleared",
  "answer": "arc-rpc.publicnode.com answers web3_clientVersion reth/v2.2.0-508cbdf and arc_getVersion v0.8.5 (602eed3b). It gives Arc's answers: the value-carrying call returns 0, 1, 1, 0 to address zero, 0xb0b, 0x01 and the 0x3600 face through eth_call and eth_simulateV1, 185,529 vectors match, callsem 50 of 50, pmdiff 250 of 250 and pmdiff2 300 of 300. stalesync.py shows the synced currency empty in the next transaction, and the 23 scenarios give 137 of 137 reference results with a 30,000,000 gas block; drpc (v0.8.6, 8e8edb7a) also serves the method and gives the same two results. Commit 508cbdf7d6ba49b4ce735d678863897067fa381a is in circlefin/arc-reth, tag v2.2.0-arc.2, which arc-node's Cargo.lock names for 103 reth crates at 602eed3b and v0.8.6; the USDC blocklist on native transfers was not exercised because that needs a listed account."},
 {"leadId": "L-1261", "outcome": "cleared",
  "answer": "Circle's images are on docker.cloudsmith.io/circle/arc-network (arc-execution, arc-consensus), not ghcr.io (ghcr refuses a pull token for circlefin/arc-node). The image configs carry no labels, so there is no revision annotation; the binaries embed the commit. Published builds are v0.8.5 at 602eed3b702728cabb16be716a8fd5eb8e99a027 and v0.8.6 at b11795567992a7bf51e7f538ae37e7f19d076e13, whose evm.rs and Cargo.lock equal the v0.8.6 tag. No image carries 37812c61, 8e8edb7a or db2d22c1. Both public images carry reth base 508cbdf, the commit PublicNode and Blockdaemon report. L-1236, L-1219 and L-1196 stay open for the three unpublished builds."},
]

out = {"unit": "stablecoin-l1", "_lenses": ["L1", "L2", "L4", "L6"], "profiles": profiles, "findings": [],
       "cleared": cleared, "leads": leads, "leadResults": lead_results}
json.dump(out, open('research/network-risk/cycles/035/stablecoin-l1.research.json', 'w'), indent=1)
print('written')
