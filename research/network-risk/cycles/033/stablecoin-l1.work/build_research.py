"""Builds cycles/033/stablecoin-l1.research.json from the notes of this cycle. Read-only work; no transactions."""
import json, os
W = "research/network-risk/cycles/033/stablecoin-l1.work"
TR = "https://raw.githubusercontent.com/tempoxyz/tempo"
ER = "https://raw.githubusercontent.com/DaniPopes/evm2"
E_OLD = "35aa32800b147b00e616d4e1869a3835aa86701f"
E_NEW = "7c9f3b6deb23005fc84596ba1b13a6492d942014"
AR = "https://raw.githubusercontent.com/circlefin/arc-node"
TEMPO = "https://rpc.mainnet.tempo.xyz"
ARC = "https://rpc.mainnet.arc.io"

profiles = [
 {"chainId": 4217, "lens": "L1",
  "summary": "The endpoint answers tempo/v1.19.2-c0c9372, the commit of tag tempo/v1.19.2, which moves evm2 from 35aa3280 to 7c9f3b6d and keeps ruint 1.21.1. Every interpreter, integer, jump analysis, memory and storage file of evm2 is byte equal between the two revisions; the changes are an inspector-only refund counter and nested transaction guard, a per-frame memory limit lowered from 4 GiB to 100 MiB, a modexp shortcut and an EIP-3607 gate, none of which changes a result the PoolManager can reach. All six tool reruns match the specification on v1.19.2.",
  "deltas": [
   {"delta": "tempo/v1.19.2 (c0c9372) pins evm2 7c9f3b6d instead of 35aa3280; ruint stays 1.21.1; the tag's Cargo.lock is byte equal to c0c9372's. Of the 138 evm2 source files fetched at both revisions, 13 differ and one (precompiles/bn254/differential.rs) is new, and none of them is under interpreter/, bytecode/analysis or evm/state/storage.rs.",
    "source": f"{TR}/c0c9372/Cargo.lock ; {TR}/tempo/v1.19.2/Cargo.lock ; {ER}/{E_NEW}/crates/evm2/src/evm/mod.rs ; {W}/evm2_35aa328_7c9f3b6.diff", "relevance": "low"},
   {"delta": "evm2 7c9f3b6d sets DEFAULT_MEMORY_LIMIT to 100 MiB per frame (was 2^32 - 1 bytes), and Tempo does not override it. Memory gas still follows 3 per word plus words squared over 512, so 100 MiB costs about 2.1e10 gas against a 500,000,000 block gas limit, which buys at most about 16 MB. eth_call on Tempo v1.19.2 at 50,000,000 gas expanded to 4 MiB and returned the stored word, and failed at 8 MiB with out of gas during memory expansion, as specified.",
    "source": f"{ER}/{E_NEW}/crates/evm2/src/version/mod.rs ; {ER}/{E_NEW}/crates/evm2/src/version/gas_params.rs ; {TR}/c0c9372/crates/evm/src/handler/config.rs ; eth_call on {TEMPO} (2026-11-27) in {W}/memory_vectors.log", "relevance": "none"},
   {"delta": "v1.19.2 has no release note on the Tempo changelog page or node operator table (newest listed: v1.19.1 of 25 November) and no binary at download.tempo.xyz/binaries (newest: v1.19.1), so the shipped-binary lifts of cycles 28 to 31 cannot be repeated for the running build.",
    "source": "https://tempo.com/developers/docs/changelog ; https://tempo.com/developers/docs/guide/node/network-upgrades ; https://download.tempo.xyz/binaries", "relevance": "low"}]},
 {"chainId": 4217, "lens": "L2",
  "summary": "Within the EVM, BALANCE of the PoolManager and SELFBALANCE still return zero on v1.19.2 while eth_getBalance answers the large sentinel, and a value-carrying call is still refused. The only state-layer changes in v1.19.2 are take_logs buffer handling (same logs returned) and a T15-gated skip of cold account loads in precompile storage, which is inactive because T15 has no activation time.",
  "deltas": [
   {"delta": "crates/precompiles/src/storage/evm.rs makes sload_journal and sstore_journal call account_with_skip(address, skip_cold_load && spec.is_t15()); every other caller file of transact, system_call and validate_tx that cycle 19 listed is byte equal between a9d6748 and c0c9372.",
    "source": f"{TR}/c0c9372/crates/precompiles/src/storage/evm.rs ; {TR}/a9d6748/crates/precompiles/src/storage/evm.rs ; {W}/tempo_file_diff.txt", "relevance": "low"},
   {"delta": "SELFBALANCE and BALANCE(PoolManager) return 0 inside eth_call on v1.19.2; eth_getBalance(PoolManager) returns 0x9612...c9b2; a call with value 1 is refused with 'value transfer not allowed'.",
    "source": f"eth_call and eth_getBalance on {TEMPO} (2026-11-27, latest)", "relevance": "none"}]},
 {"chainId": 4217, "lens": "L5",
  "summary": "Deployment facts reread on 2026-11-27 at block 51,069,075 equal networks.json: 24,009 bytes with sha256 prefix f017c3da36573b60, owner 0xcfb4...811b with 7,068 bytes of code, protocol fee controller unset.",
  "deltas": []},
 {"chainId": 4217, "lens": "L6",
  "summary": "T14 (8 December 2026 15:00 UTC, timestamp 1,796,742,000) now lands on v1.19.2; the 23 multi-transaction scenarios ran on v1.19.2 with and without a T14 block time and all 137 calls matched the reference both times. T15 and T16 are unchanged: target dates only, no activation time in code.",
  "deltas": [
   {"delta": "The upgrades page is byte equal to cycle 31's copy: T14 mainnet 8 December 2026 15:00 UTC; T15 target 15 December 2026 with activation set at release; T16 target mid-January 2027 with scope not final. crates/hardfork/src/constants.rs and lib.rs are byte equal between a9d6748 and c0c9372.",
    "source": f"https://docs.tempo.xyz/docs/protocol/upgrades ; {TR}/c0c9372/crates/hardfork/src/constants.rs", "relevance": "low"},
   {"delta": "eth_simulateV1 on v1.19.2 at block 51,069,413 with blockOverrides time 1,796,745,600: 137 of 137 scenario calls equal to the reference, as without the override.",
    "source": f"eth_simulateV1 on {TEMPO} (2026-11-27); {W}/scen-4217-t14.json ; {W}/scen-4217-now.json", "relevance": "low"}]},
 {"chainId": 5042, "lens": "L1",
  "summary": "arc_getVersion still names four builds: 37812c61 (v0.8.6-rc1, official), 8e8edb7a (v0.8.6, drpc), 602eed3b (v0.8.5, PublicNode) and db2d22c1 (v0.8.5, Blockdaemon). Only 602eed3b is fetchable from circlefin/arc-node. crates/evm/src/evm.rs is byte equal at v0.8.5, v0.8.6 and main, and no tag after v0.8.6 exists.",
  "deltas": [
   {"delta": "Raw fetches of Cargo.lock and crates/evm/src/evm.rs by full commit return 404 for 37812c61, 8e8edb7a and db2d22c1a71092b7f7af3d9dda170cb300c84332 and 200 for 602eed3b; tags v0.8.7, v0.8.7-rc1, v0.8.6-rc2, v0.9.0 and v0.9.0-rc1 return 404.",
    "source": f"{AR}/602eed3b702728cabb16be716a8fd5eb8e99a027/crates/evm/src/evm.rs ; {AR}/v0.8.6/crates/evm/src/evm.rs ; {W}/arc_tags.log ; arc_getVersion on {ARC}, https://arc.drpc.org, https://arc-rpc.publicnode.com, https://rpc.blockdaemon.mainnet.arc.io in {W}/arc_version.log", "relevance": "low"}]},
 {"chainId": 5042, "lens": "L2",
  "summary": "A value-carrying CALL from an overridden contract gave the same success flags on all four Arc builds: it fails to address zero and to the 0x3600 USDC token face, and succeeds to a plain address and to precompile 0x01. The PoolManager's native balance and USDC face balance still satisfy face = floor(native / 10^12).",
  "deltas": [
   {"delta": "Value call results per build (zero, plain 0xb0b, 0x01, 0x3600...): 37812c61 0/1/1/0, 8e8edb7a 0/1/1/0, 602eed3b 0/1/(rate-limited)/0, db2d22c1 0/1/1/0.",
    "source": f"eth_call with state override on four Arc endpoints (2026-11-27) in {W}/arc_valuecall_probe.json", "relevance": "low"},
   {"delta": "At block 0x1fdddc5 the PoolManager holds 2,460,607,087,804,558,794,715,662 wei native and 2,460,607,087,804 face units; the native remainder below one face unit is 558,794,715,662 wei.",
    "source": f"eth_getBalance and eth_call balanceOf on {ARC} (2026-11-27) in {W}/arc_face_residue.log", "relevance": "low"}]},
 {"chainId": 5042, "lens": "L5",
  "summary": "Deployment facts reread on 2026-11-27 at block 33,414,309 equal networks.json: 24,009 bytes with sha256 prefix 6eb21c69298b064e, owner 0xbca3...5a75 with 7,310 bytes, protocol fee controller 0x2f2b...3782 with 3,480 bytes.",
  "deltas": []},
 {"chainId": 5042, "lens": "L6",
  "summary": "No Arc hardfork is scheduled: crates/execution-config/src/hardforks.rs, Cargo.lock and CHANGELOG.md on main are byte equal to cycle 31's copies and end at Zero8. Base fee stayed at 20 gwei over the last 10,240 blocks.",
  "deltas": [
   {"delta": "eth_feeHistory over blocks 33,404,200 to 33,414,439: base fee 20 gwei in every block, maximum gas used ratio 0.41.",
    "source": f"eth_feeHistory on {ARC} (2026-11-27) in {W}/arc_feehistory.json", "relevance": "none"}]},
]

cleared = [
 {"chainIds": [4217, 5042], "lens": "L1",
  "check": "Reruns on 2026-11-27 of battery.py (99,985 vectors), targeted.py (85,544), pmdiff.py (250 scripts in two passes, because the Ethereum reference endpoint failed on five scripts in the first pass and three others in the second), pmdiff2.py (300 scripts), swaps.py and replay.py on Tempo tempo/v1.19.2-c0c9372 and Arc 37812c61.",
  "result": "No opcode vector differs on either chain. Every pmdiff script is identical on Arc; on Tempo the scripts that differ are the same ten pmdiff scripts (9, 14, 29, 67, 79, 81, 86, 147, 175, 233) and six pmdiff2 scripts (71, 82, 189, 196, 210, 295) that cycle 31 traced to Tempo's gas pricing. 1,031 Tempo swaps and 5,978 Arc swaps pass the tick relation (one Arc swap sits exactly on a tick boundary, which the relation allows), and 25 multi-step Arc swaps replay to the unit. So FullMath.mulDiv, TickMath and the swap step compute the specified values on v1.19.2.",
  "source": f"{W}/battery.log ; {W}/targeted.log ; {W}/pmdiff.json ; {W}/pmdiff-rerun.json ; {W}/pmdiff2.json ; {W}/swaps.log ; {W}/replay.log ; src/libraries/FullMath.sol:14 ; src/libraries/TickMath.sol:57"},
 {"chainIds": [4217], "lens": "L1",
  "check": "Do the evm2 changes from 35aa3280 to 7c9f3b6d, which v1.19.2 ships, touch the code that computes the PoolManager's arithmetic, comparisons, shifts, jumps, KECCAK256, MCOPY, CALLDATALOAD, memory, storage or transient storage?",
  "result": "No. The 138 evm2 files were fetched at both revisions. interpreter/instructions (arithmetic, bitwise, i256, control, memory, system, host, crypto), interpreter/memory.rs, bytecode/analysis and its x86 and aarch64 kernels, and evm/state/storage.rs and journal.rs are byte equal. The 14 changed or added files hold an inspector refund counter and a guard for a transaction dispatched while one runs (evm/mod.rs, used only under an inspector), take_logs buffer reuse (evm/state/mod.rs, same logs), a modexp shortcut for a missing modulus (result zero as before), a BAL code hash seeded from alloy-eip7928's CodeChange::code_hash, which is computed from the private code bytes, an EIP-3607 gate on EIP-7702, and the memory limit. src/ calls no modexp, bn254 or KZG precompile, and none of these changes alters a value that CurrencyDelta's keccak slots or the pool libraries read.",
  "source": f"{ER}/{E_OLD}/crates/evm2/src/evm/mod.rs ; {ER}/{E_NEW}/crates/evm2/src/evm/mod.rs ; {W}/evm2_35aa328_7c9f3b6.diff ; https://static.crates.io/crates/alloy-eip7928/alloy-eip7928-0.4.13.crate ; src/libraries/CurrencyDelta.sol:10-14"},
 {"chainIds": [4217], "lens": "L1",
  "check": "Can the 100 MiB per-frame memory limit that v1.19.2 introduces make a PoolManager call or a caller's frame fail where Ethereum would succeed?",
  "result": "No. Memory expansion to 100 MiB costs about 2.1e10 gas under the unchanged formula, and Tempo's block gas limit is 500,000,000, so gas runs out before about 16 MB. The live check matched: 4 MiB succeeded and 8 MiB ran out of gas at the 50,000,000 eth_call cap. The PoolManager's own memory use is a few kilobytes.",
  "source": f"{ER}/{E_NEW}/crates/evm2/src/version/mod.rs ; {ER}/{E_NEW}/crates/evm2/src/version/gas_params.rs ; {W}/memory_vectors.log"},
 {"chainIds": [4217], "lens": "L1",
  "check": "Could Tempo validators still on v1.19.1 and those on v1.19.2 compute a different result for a PoolManager transaction?",
  "result": "No difference was found for any path the PoolManager reaches. The consensus-visible changes between the builds are the memory limit (unreachable by gas), the EIP-3607 gate (Tempo's version keeps EIP-7702), the modexp shortcut (same output and gas) and the T15-gated cold load skip (inactive). The interpreter and storage files are byte equal. Tempo's execution crates that cycle 19 listed as transaction callers (block.rs, handler.rs, handler/config.rs, instructions.rs, evm.rs, context.rs, the TIP-20 precompile, the fee manager, storage credits, the zone executor and the payload builder) are byte equal between a9d6748 and c0c9372.",
  "source": f"{W}/tempo_file_diff.txt ; {TR}/c0c9372/crates/evm/src/block.rs ; {TR}/c0c9372/crates/hardfork/src/gas_params.rs"},
 {"chainIds": [4217], "lens": "L6",
  "check": "T14 rehearsal on v1.19.2: the 23 multi-transaction scenarios of cycle 28 (state carried across calls, transient storage reset between them) under a block time after 1,796,742,000.",
  "result": "137 of 137 calls equal to the reference with and without the T14 time, so the lock, the delta count and the settlement logic behave the same after T14 on the new build.",
  "source": f"eth_simulateV1 on {TEMPO} (2026-11-27); {W}/scen-4217-t14.json ; {W}/scen-4217-now.json ; src/PoolManager.sol:104-114"},
 {"chainIds": [5042], "lens": "L3",
  "check": "Lead L-1247: whether the face rounding loop on Arc (sync of the 0x3600 face, a forced native send, settle, take) can pay. Measured base fee and gas prices on the current builds, and looked for a cheaper forced send.",
  "result": "The base fee was 20 gwei in all 10,240 blocks to 33,414,439. Of 3,301 transactions in 2,000 sampled blocks (types 0, 2 and 4), none paid below 20 gwei. The PoolManager has no receive or fallback function, and a native settle after a token sync reverts with NonzeroNativeValue, so a forced send still needs SELFDESTRUCT. A contract created earlier can SELFDESTRUCT under EIP-6780 for about 7,600 gas, which is cheaper than CREATE plus SELFDESTRUCT. The loop's gain is bounded by the residue anyway. After one round the PoolManager's native balance is a multiple of 10^12, so the gain is only the remainder present at that moment: 558,794,715,662 wei (about 0.00000056 USD) at block 0x1fdddc5. One round's gas at 20 gwei is far above that, and no repeat yields more. The loop costs more than it can take.",
  "source": f"{W}/arc_feehistory.json ; {W}/arc_txgas.json ; {W}/arc_face_residue.log ; src/PoolManager.sol:279-288 ; src/PoolManager.sol:349-364 ; src/types/Currency.sol:90-96"},
 {"chainIds": [5042], "lens": "L2",
  "check": "Does the Blockdaemon build db2d22c1 or any other Arc build behave differently in the native value frame hook on the arms a native take can meet?",
  "result": "No difference on the arms tested. A value-carrying CALL fails to address zero and to the 0x3600 face and succeeds to a plain address and to precompile 0x01 on all four builds, matching F-125 and F-049. evm.rs is byte equal at v0.8.5 (602eed3b), v0.8.6 and main.",
  "source": f"{W}/arc_valuecall_probe.json ; {AR}/v0.8.5/crates/evm/src/evm.rs ; src/types/Currency.sol:40-52"},
 {"chainIds": [4217, 5042], "lens": "L5",
  "check": "PoolManager bytecode, owner and protocol fee controller reread on both networks (critic gap of cycle 32: last read in cycle 27).",
  "result": "Equal to networks.json on both: code length 24,009 with the recorded sha256 prefixes, the same owner and fee controller addresses and code lengths.",
  "source": f"eth_getCode and eth_call owner() and protocolFeeController() on {TEMPO} block 51,069,075 and {ARC} block 33,414,309 (2026-11-27) in {W}/l5_parity.json"},
]

leads = [
 {"chainIds": [4217], "lens": "L1",
  "question": "When Tempo publishes v1.19.2 binaries or a later release at download.tempo.xyz, do the shipped arithmetic, jump analysis, keccak, memory and storage routines still match the lifts of cycles 28 to 31, given that the evm2 source files behind them are byte equal?",
  "why": "The endpoint runs a build with a tag and source but no published binary or release note, so every binary-level result describes v1.19.1.",
  "priority": "low"},
]

leadResults = [
 {"leadId": "L-1236", "outcome": "inconclusive",
  "answer": "db2d22c1a71092b7f7af3d9dda170cb300c84332 is not fetchable from circlefin/arc-node (Cargo.lock and crates/evm/src/evm.rs return 404 by full hash), so its source is still unknown. On behaviour it matches 602eed3b and the other two builds. A value-carrying CALL gives the same success flags to address zero (fails), to the 0x3600 face (fails), to a plain address and to precompile 0x01 (succeed). Cycle 32 found that a failed-frame native transfer is undone on it as well. evm.rs is byte equal at v0.8.5, v0.8.6 and main."},
 {"leadId": "L-1247", "outcome": "cleared",
  "answer": "The base fee was 20 gwei in every one of the last 10,240 Arc blocks. No sampled transaction (3,301 in 2,000 blocks) paid below it, and no zero-price class appeared. SELFDESTRUCT from a contract created earlier is a cheaper forced send than CREATE plus SELFDESTRUCT. The loop's gain is bounded by the native remainder below one face unit, which one round empties: 558,794,715,662 wei on 2026-11-27. So it pays at no gas price."},
 {"leadId": "L-1219", "outcome": "inconclusive",
  "answer": "No source names the build each proposer runs. Block headers carry only the base fee, and no new arc-node tag or page appeared. All four builds that public endpoints answer from (37812c61, 8e8edb7a, 602eed3b, db2d22c1) agree on the opcode battery for the official build and on the native value hook arms probed for all four."},
 {"leadId": "L-1196", "outcome": "inconclusive",
  "answer": "arc_getVersion still names v0.8.6-rc1 at 37812c61, v0.8.6 at 8e8edb7a and v0.8.5 at 602eed3b, plus v0.8.5 at db2d22c1 on Blockdaemon, in three of three samples each. No tag after v0.8.6 exists, and frame_init and the blocklist hook in evm.rs are unchanged at v0.8.5, v0.8.6 and main. The validators' build remains unknown."},
]

out = {"unit": "stablecoin-l1", "_lenses": ["L1", "L2", "L5", "L6"], "profiles": profiles, "findings": [],
       "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(out, open("research/network-risk/cycles/033/stablecoin-l1.research.json", "w"), indent=1)
print("written")
