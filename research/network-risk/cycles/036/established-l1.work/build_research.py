"""Builds cycles/036/established-l1.research.json from the out/ and dl/ files of this work directory."""
import json
W = '/home/user/v4-core/research/network-risk/cycles/036/established-l1.work'
OUT = '/home/user/v4-core/research/network-risk/cycles/036/established-l1.research.json'
RAW = 'https://raw.githubusercontent.com/'
BOR_CFG = RAW + '0xPolygon/bor/develop/params/config.go'
BSC_CFG = RAW + 'bnb-chain/bsc/develop/params/config.go'
BSC_CL = RAW + 'bnb-chain/bsc/develop/CHANGELOG.md'
AVA_UP = RAW + 'ava-labs/avalanchego/master/upgrade/upgrade.go'
AVA_REL = RAW + 'ava-labs/avalanchego/master/RELEASES.md'
RB_BSC = RAW + 'bnb-chain/reth-bsc/develop/src/hardforks/bsc.rs'
WD = 'research/network-risk/cycles/036/established-l1.work/'

profiles = [
 {"chainId": 137, "lens": "L1",
  "summary": "At 19:34 UTC on 2026-11-27 polygon-bor-rpc.publicnode.com answered from bor v2.11.1-private builds a863b8e5cce1 and 280514fa9fb7 with go1.26.10, both already listed in F-146. bor develop core/vm/eips.go, instructions.go, jump_table.go and params/config.go are byte equal to the cycle 34 copies, go.mod line 59 still pins holiman/uint256 v1.3.2, the newest uint256 on the module proxy is v1.3.2, and tags v2.11.3 and v2.12.0 do not exist. All 185,529 vectors return the specified word, script sets 1 and 2 differ only on the known gas-bound swaps (19 of 250, 20 of 300), and every mined swap of blocks 98,058,378 to 98,068,377 replays.",
  "deltas": [
   {"delta": "tools/opdiff/replay.py tries a fixed list of 31 tick spacings that does not contain 90. Two of the 18 cycle 34 Polygon multi-step swaps are in a pool of tick spacing 90 (pool 0x6b4c12ae...dc88, read from its Initialize log), so replay.py could never have reproduced them and walked every listed spacing instead. This is a gap in the review tool, not a chain difference.",
    "source": WD + "out/pol34_spacings.json; rpc: eth_getLogs Initialize on https://polygon.gateway.tenderly.co", "relevance": "none"}]},
 {"chainId": 137, "lens": "L2",
  "summary": "Rereading bor v2.11.2 core/state/parallel_statedb.go for L-1254 adds one detail to the cycle 34 reading: on a first incarnation, or without a WaitForFinal callback, handleEstimate (lines 383-392) returns false and readStoreWait (lines 332-349) answers not found, so the reader falls through to base state and correctness of that read rests on validateOne in core/blockstm/v2/executor.go (lines 629-660), which re-executes the transaction when Validate fails. The run from the binary that the lead asks for was not done.",
  "deltas": []},
 {"chainId": 137, "lens": "L4",
  "summary": "The five Salvador sweeper targets in bor develop params/config.go (lines 568-597) have no code today and hold 15,331,308, 4,295,442, 4,235,983, 3.05 and 46,626,826 POL with nonces 2, 0, 26, 4 and 0. None holds a PoolManager ERC-6909 claim of native POL or WPOL. With the sweeper code placed by override, every call shape the PoolManager can make to such an address (empty calldata with value 0 or 1, transfer, balanceOf) reverts, sweep() succeeds with empty data and the getter returns the recovery addresses 0x4df6...eedc and 0xd9fd...0b80.",
  "deltas": [
   {"delta": "The balances, nonces and PoolManager claims of the five Salvador targets were read for the first time. They hold about 70.5 million POL between them and no PoolManager claim.",
    "source": "rpc: eth_getBalance, eth_getTransactionCount, eth_getCode and PoolManager balanceOf(owner, 0) and balanceOf(owner, WPOL id) on https://polygon-bor-rpc.publicnode.com at latest, 2026-11-27; " + WD + "out/salvador_sweeper_calls.json", "relevance": "low"}]},
 {"chainId": 137, "lens": "L6",
  "summary": "Block 98,068,690 has timestamp 1,795,808,513 and the last 200,000 blocks averaged 1.500 s, which puts Salvador (block 98,688,600, bor develop params/config.go line 478) at about 2026-12-08 14:00 UTC. No tagged bor release carries Salvador yet, and Hampi stays unscheduled (line 476).",
  "deltas": []},
 {"chainId": 56, "lens": "L1",
  "summary": "dataseed1 and dataseed2 answer Geth v1.8.2 (dataseed2 also v1.8.2-4e1c8247-20261104) and publicnode answers reth-bsc v0.1.4-hotfix-23b510f. In 30 requests the pocket gateway answered Geth v1.8.2 24 times, v1.8.2-54afaff4-20261103 with go1.25.14 twice, Geth v1.7.8 twice, reth-bsc v0.1.2-968d07d once and reth-bsc v0.1.4-hotfix once. bsc develop core/vm and params files, the changelog and the uint256 v1.3.2 pin (go.mod line 46) are unchanged, v1.8.2 is the newest tag. The 185,529 vectors and script sets 1 and 2 match today and also with every eth_call carrying block time 1,796,697,100 (Jenner rules), on both Geth v1.8.2 and reth-bsc v0.1.4-hotfix. The arm64 reth-bsc image is the same commit 23b510f and pins the same revm-interpreter 35.0.1 and ruint 1.18.0 as the amd64 image.",
  "deltas": [
   {"delta": "The arm64 image ghcr.io/bnb-chain/reth-bsc:v0.1.4-hotfix-arm64 (manifest layer sha256:8753c532...20bd, binary /usr/local/bin/reth-bsc sha256 b900f81c...4d0d, ELF aarch64) names commit 23b510f8d06ca8a39034725ea3aff359e1649e28, build time 2026-11-06T02:58:42Z and build features asm_keccak, jemalloc, keccak_cache_global, and embeds revm-interpreter 35.0.1, ruint 1.18.0, alloy-primitives 1.6.0 and fixed-cache 0.1.10. It carries the CRYPTOGAMS 'Keccak1600 absorb and squeeze for ARMv8' routine, whose round constant table sits in .text at file offset 0x3e8c240. Its interpreter and integer library are the versions already read for amd64; only the keccak routine differs by platform.",
    "source": "https://ghcr.io/v2/bnb-chain/reth-bsc/manifests/v0.1.4-hotfix-arm64; https://ghcr.io/v2/bnb-chain/reth-bsc/blobs/sha256:8753c53273ef1a1fc199af0ea9ca2ab3523e9f8fb2d1a69e658005b37b9920bd", "relevance": "low"}]},
 {"chainId": 56, "lens": "L2",
  "summary": "Nothing new. 7,672 mined swaps of blocks 136,089,347 to 136,095,346 satisfy the tick relation, every paired swap matches one of the single-step outcomes or is a multi-step swap, and the 25 sampled multi-step swaps replay to the unit.",
  "deltas": []},
 {"chainId": 56, "lens": "L4",
  "summary": "Nothing new beyond F-139 and F-076. With block time 1,796,697,100 the BEP-706 precompile at 0x70 returns 1,796,697,100,000 ms on Geth v1.8.2 and on reth-bsc v0.1.4-hotfix and returns empty data without the override, which shows the override turns on Jenner for the reruns above.",
  "deltas": []},
 {"chainId": 56, "lens": "L6",
  "summary": "Jenner is still scheduled for 1,796,697,000 (2026-12-08 02:30 UTC, bsc develop params/config.go line 256, CHANGELOG v1.8.2). reth-bsc develop is unchanged since cycle 34 and keeps mainnet Jenner unscheduled (src/hardforks/bsc.rs lines 125-141), and tags v0.1.5 and v0.1.6 do not exist. The pocket gateway still rotates through Geth v1.7.8 and reth-bsc v0.1.2-968d07d, neither of which schedules mainnet Jenner.",
  "deltas": []},
 {"chainId": 43114, "lens": "L1",
  "summary": "api.avax.network and the publicnode endpoint answer avalanchego/1.15.3 commit 983815fd with go 1.26.10. avalanchego master go.mod pins holiman/uint256 v1.2.4 (line 44) and libevm v1.13.15-0.20261111112450-a335c2ecf4df (line 31), upgrade.go and RELEASES.md are byte equal to the cycle 34 copies, and tag v1.15.4 does not exist. All 185,529 vectors and script sets 1 and 2 match.",
  "deltas": []},
 {"chainId": 43114, "lens": "L2",
  "summary": "Nothing new. The 37 swaps of blocks 101,568,077 to 101,569,843 satisfy the tick relation and the 17 paired ones match a single step.",
  "deltas": []},
 {"chainId": 43114, "lens": "L4",
  "summary": "Nothing new. No precompile, predeploy or upgrade file changed since cycle 34.",
  "deltas": []},
 {"chainId": 43114, "lens": "L6",
  "summary": "avalanchego master upgrade.go has Helicon active since 2026-09-22 15:00 UTC and Igloo unscheduled (lines 68-69). The unreleased v1.15.4 notes change RPC headers, shutdown and mempool admission only.",
  "deltas": []},
]

cleared = [
 {"chainIds": [137, 56, 43114], "lens": "L1",
  "check": "battery.py (99,985 vectors) and targeted.py (85,544 vectors) on the networks.json endpoints on 2026-11-27 after 19:30 UTC: MULMOD and mulDiv with modulus 2^256-1 and full width moduli, ADDMOD, DIV, SDIV, MOD, SMOD, SIGNEXTEND, SAR, SHL, SHR, BYTE, EXP, the comparisons, JUMPI on 209 condition words, KECCAK256, MCOPY and CALLDATALOAD past the end.",
  "result": "185,529 of 185,529 words equal the specification on each of the three networks, so the 512 bit product of FullMath (src/libraries/FullMath.sol), the sign handling of TickMath, TickBitmap.compress and flipTick (src/libraries/TickBitmap.sol:16-75) and the bit scans of BitMath compute what the source says on the builds that answered.",
  "source": WD + "out/battery.log; " + WD + "out/targeted.log"},
 {"chainIds": [56], "lens": "L1",
  "check": "The same 185,529 vectors and script sets 1 and 2 on BNB Chain with every eth_call carrying blockOverrides time 1,796,697,100 (100 s after Jenner), once on bsc-dataseed1.bnbchain.org (Geth v1.8.2) and once on bsc-rpc.publicnode.com (reth-bsc v0.1.4-hotfix-23b510f). The override was checked first: precompile 0x70 returns 0x1a2537e0ee0 (1,796,697,100,000 ms) with it and empty data without it on both endpoints.",
  "result": "No mismatch on either build: 99,985 and 85,544 vectors, 250 of 250 scripts of set 1 and 300 of 300 of set 2 identical to Ethereum. Jenner rules leave the opcode results and the PoolManager's pool math, hook call parsing and token call handling unchanged.",
  "source": "rpc: eth_call with blockOverrides on https://bsc-dataseed1.bnbchain.org and https://bsc-rpc.publicnode.com, 2026-11-27; " + WD + "jenner_run.py; " + WD + "out/jen_dataseed_*.log; " + WD + "out/jen_rethbsc_*.log"},
 {"chainIds": [137, 56, 43114], "lens": "L1",
  "check": "Script set 1 (pmdiff.py, 250 scripts) and set 2 (pmdiff2.py, 300 scripts) with the deployed PoolManager bytecode against the Ethereum reference under the same state.",
  "result": "BNB Chain and Avalanche are identical on 250 of 250 and 300 of 300. Polygon is identical on 231 and 280; the 19 and 20 others end at the known swap across most of the tick range that runs out of gas on Polygon's endpoint, the same count as cycle 34.",
  "source": WD + "out/pmdiff.log; " + WD + "out/pmdiff2.log"},
 {"chainIds": [137, 56, 43114], "lens": "L1",
  "check": "swaps.py on the newest Swap events (Polygon blocks 98,058,378 to 98,068,377, BNB Chain 136,089,347 to 136,095,346, Avalanche 101,568,077 to 101,569,843) and replay.py on the multi-step samples, with Polygon state from polygon.gateway.tenderly.co.",
  "result": "6,455, 7,672 and 37 swaps all satisfy the tick relation of getTickAtSqrtPrice (src/libraries/TickMath.sol) and Pool.swap (src/libraries/Pool.sol:430-431). 25 Polygon and 25 BNB Chain multi-step swaps replay price, tick, liquidity and both amounts to the unit, up to 5 steps.",
  "source": WD + "out/swaps.log; " + WD + "out/replay36.log; " + WD + "replay_pol36.py"},
 {"chainIds": [137], "lens": "L1",
  "check": "L-1268: the 18 Polygon multi-step swaps of blocks 98,056,456 to 98,057,661 from cycles/034/established-l1.work/out/swaps.json, replayed one by one with state from polygon.gateway.tenderly.co and the tick spacing of each pool read from its Initialize log.",
  "result": "18 of 18 reproduce price, tick, liquidity and both amounts to the unit (tick spacings 1, 10, 60, 90 and 200, up to 11 steps, about 0.1 s each). The cycle 34 failures were the endpoint refusing state, and two of the swaps sit in a spacing 90 pool that replay.py's fixed spacing list does not contain.",
  "source": WD + "out/replay-pol34.log; " + WD + "replay_one.py; " + WD + "out/pol34_spacings.json"},
 {"chainIds": [137, 56, 43114], "lens": "L1",
  "check": "Upstream changes since cycle 34 on the paths that compute PoolManager words: bor develop core/vm/eips.go, instructions.go, jump_table.go, params/config.go and go.mod; bsc develop core/vm/eips.go, instructions.go, jump_table.go, params/config.go, CHANGELOG.md and go.mod; avalanchego master upgrade/upgrade.go, RELEASES.md and go.mod; reth-bsc develop Cargo.toml, Cargo.lock and src/hardforks/bsc.rs; new tags and new holiman/uint256 versions.",
  "result": "Every file is byte equal to its cycle 34 copy. bor and bsc pin uint256 v1.3.2, avalanchego pins v1.2.4 and libevm a335c2ecf4df. No tag after bor v2.11.2, bsc v1.8.2, avalanchego v1.15.3 or reth-bsc v0.1.4-hotfix exists, and v1.3.2 is the newest uint256 on the module proxy. Nothing new to read on the arithmetic, jump analysis or keccak paths.",
  "source": RAW + "0xPolygon/bor/develop/core/vm/instructions.go; " + RAW + "bnb-chain/bsc/develop/core/vm/jump_table.go; " + AVA_UP + "; " + RAW + "bnb-chain/reth-bsc/develop/Cargo.lock; https://proxy.golang.org/github.com/holiman/uint256/@v/list; https://proxy.golang.org/github.com/bnb-chain/bsc/@v/list; https://proxy.golang.org/github.com/ava-labs/avalanchego/@v/list"},
 {"chainIds": [137], "lens": "L4",
  "check": "The five Salvador sweeper targets (0xe4C4...1EC6, 0x5392...962C, 0xc91e...9b60, 0x3f70...1Ffa, 0x5227...2f8c) against every call the PoolManager can make to them after block 98,688,600, with the sweeper code from bor develop params/config.go placed by state override and from set to the PoolManager: empty calldata with value 0 and 1 (P1), transfer(PoolManager, 1) and transfer(PoolManager, 0) (P2), balanceOf(PoolManager) (P3); plus their current balance, code, nonce and PoolManager claims.",
  "result": "Every P1, P2 and P3 shape reverts with empty data, so take of native to them reverts with NativeTransferFailed (src/types/Currency.sol:44-52), take of them as a currency reverts (src/types/Currency.sol:53-87) and sync reverts (src/PoolManager.sol:279-288); no delta, claim or pool can exist in them. sweep() succeeds and sends only the target's own balance to the hard-coded recovery address. None of the five holds a PoolManager claim of native POL or WPOL today, so the code write freezes no PoolManager claim. The privileged nature of the write is F-134.",
  "source": BOR_CFG + " (lines 568-597); rpc: eth_call with code override from 0x67366782805870060151383f4bbff9dab53e5cd6 and eth_getBalance, eth_getCode, eth_getTransactionCount on https://polygon-bor-rpc.publicnode.com, 2026-11-27; " + WD + "out/salvador_sweeper_calls.json"},
 {"chainIds": [56, 137, 43114], "lens": "L6",
  "check": "Upcoming forks for the next six months, rechecked on 2026-11-27 at 19:45 UTC: BNB Chain Jenner, Polygon Salvador and Hampi, Avalanche Igloo, and anything new.",
  "result": "Jenner at 1,796,697,000 (2026-12-08 02:30 UTC) brings CAS20 (F-139, F-076), BEP-703 and the 0x70 precompile; the opcode battery and both script sets under its rules match on both BNB Chain builds. Salvador at block 98,688,600 (about 2026-12-08 14:00 UTC at the measured 1.500 s per block) writes code at five addresses that hold no PoolManager claim and that refuse every PoolManager call shape. Hampi and Igloo are unscheduled and nothing new was added to bsc, bor or avalanchego. No upgrade in the window gives an ordinary account a new way to reach pool funds.",
  "source": BSC_CFG + " (line 256); " + BSC_CL + "; " + BOR_CFG + " (lines 476-478); " + AVA_UP + " (lines 66-69); " + AVA_REL},
]

leads = [
 {"chainIds": [56], "lens": "L1",
  "question": "Run the ARMv8 CRYPTOGAMS keccak routine lifted from the arm64 reth-bsc v0.1.4-hotfix binary (sha256 b900f81c...4d0d, round constants at file offset 0x3e8c240, now in cycles/036/established-l1.work/dl/rethbsc-arm64) on the 27,681 cases of the cycle 35 keccak theme. This needs an aarch64 model; none is installed and the cycle 35 models are x86-64 only.",
  "why": "A reth-bsc validator on arm64 runs this routine; a wrong hash would split consensus from the geth validators, which is an operator-level halt rather than a loss.",
  "priority": "low"},
 {"chainIds": [137, 56, 43114], "lens": "L1",
  "question": "Add 90 and any other spacing seen in Initialize logs to SPACINGS in tools/opdiff/replay.py, or read the spacing from the Initialize log as replay_one.py does, and rerun the earlier replay windows whose failures were recorded as unreproduced.",
  "why": "A swap in a pool whose spacing is missing from the list is reported as a failure and costs a long walk, so earlier failure counts may include swaps that would replay.",
  "priority": "low"},
]

leadResults = [
 {"leadId": "L-1267", "outcome": "inconclusive",
  "answer": "No reth-bsc tag after v0.1.4-hotfix exists on 2026-11-27 (v0.1.5 and v0.1.6 return 404), and develop's src/hardforks/bsc.rs, Cargo.toml and Cargo.lock are byte equal to the cycle 34 copies, so develop still leaves mainnet Jenner unscheduled. publicnode answers reth-bsc v0.1.4-hotfix-23b510f, which schedules Jenner at 1,796,697,000. In 30 requests the pocket gateway answered Geth v1.7.8 twice and reth-bsc v0.1.2-968d07d once, so both pre-Jenner backends are still in rotation. Whether they keep answering after activation can only be checked after 2026-12-08 02:30 UTC. The hazard stays operator level: read-only callers routed to those backends would see a chain that validators do not produce."},
 {"leadId": "L-1268", "outcome": "cleared",
  "answer": "All 18 Polygon multi-step swaps of cycles/034/established-l1.work/out/swaps.json replay to the unit from state served by polygon.gateway.tenderly.co, with each pool's tick spacing taken from its Initialize log (spacings 1, 10, 60, 90 and 200, up to 11 steps). Two of them are in a spacing 90 pool that replay.py's fixed list omits. Results in cycles/036/established-l1.work/out/replay-pol34.log."},
 {"leadId": "L-1254", "outcome": "inconclusive",
  "answer": "Not run from the binary. The reading adds that on a first incarnation handleEstimate (parallel_statedb.go lines 383-392) returns false, so readStoreWait (lines 332-349) answers not found and the reader takes the base value; such a read is recorded with writer index -1 and validateOne (core/blockstm/v2/executor.go lines 629-660) re-executes the transaction when Validate fails. A divergence from serial execution would produce another state root than serial importers, so it would surface as a consensus fault rather than a silent change to PoolManager storage."},
 {"leadId": "L-1292", "outcome": "inconclusive",
  "answer": "The arm64 image was fetched from ghcr.io and read statically. It is commit 23b510f with asm_keccak and keccak_cache_global on, revm-interpreter 35.0.1 and ruint 1.18.0, the same as amd64, and it carries the CRYPTOGAMS ARMv8 keccak routine with its round constants in .text at file offset 0x3e8c240. The routine was not executed because no aarch64 model or emulator is available; a new lead records the run. The hazard remains operator level."},
]

doc = {"unit": "established-l1", "_lenses": ["L1", "L2", "L4", "L6"], "profiles": profiles,
       "findings": [], "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(doc, open(OUT, 'w'), indent=1)
print('wrote', OUT)
