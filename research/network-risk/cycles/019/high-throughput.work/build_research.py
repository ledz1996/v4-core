"""Builds cycles/019/high-throughput.research.json from the results in this work directory."""
import json, os
W = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(W, '..', 'high-throughput.research.json')
J = lambda p: json.load(open(os.path.join(W, p)))

bat = {r['chainId']: r for r in J('battery.json')['results']}
tgt = {r['chainId']: r for r in J('targeted.json')['results']}
pm1 = {r['chainId']: r for r in J('pmdiff.json')['results']}
pm2 = {r['chainId']: r for r in J('pmdiff2.json')['results']}
l836 = J('l836/l836-summary.json')['counts']

RAW = 'https://raw.githubusercontent.com'
MEGA = RAW + '/megaeth-labs/mega-evm'
MON = RAW + '/category-labs/monad'

profiles = [
    {"chainId": 143, "lens": "L1",
     "summary": "The official endpoint still answers Monad/0.16.7 and no execution release after v0.16.7 exists. Monad's own release table lists v0.16.7 for testnet only (mainnet date not given) and says v0.16.6 can be skipped, so mainnet validators are on v0.16.5 or a release the table does not show, while the public RPC runs 0.16.7. The main branch now has a revision MONAD_NEXT_AMSTERDAM beside MONAD_NEXT, and its Barrett reduction module in the 256 bit library still has no caller in the interpreter's arithmetic or in the x86 emitter. All vector and script reruns match as before.",
     "deltas": [
         {"delta": "Release table: v0.16.7 released to testnet on 2026-11-19 with no mainnet date; v0.16.6 marked as skippable. The RPC at rpc.monad.xyz answered Monad/0.16.7 at every bracket of this cycle's runs (2026-11-25 14:52 to 15:04 UTC).", "source": "https://docs.monad.xyz/developer-essentials/changelog/releases", "relevance": "low"},
         {"delta": "uint256.hpp on main adds namespace barrett (lines 1383 to 2143) with reciprocal-based udivrem, sdivrem, addmod, mulmod and mulmod_const. The interpreter's MULMOD and ADDMOD helpers (category/vm/runtime/math.hpp lines 74 to 95) call the generic addmod and mulmod, which stay a full division (uint256.hpp lines 921 to 962), and emitter.cpp and emitter.hpp contain no reference to barrett or reciprocal.", "source": MON + "/main/category/core/runtime/uint256.hpp", "relevance": "low"},
         {"delta": "revision.h on main lists MONAD_NEXT (11) and MONAD_NEXT_AMSTERDAM (12) as unordered siblings after MONAD_TEN; MONAD_LATEST_STABLE_REVISION stays MONAD_TEN.", "source": MON + "/main/category/vm/evm/monad/revision.h", "relevance": "none"}]},
    {"chainId": 143, "lens": "L2",
     "summary": "No new state model difference. The reserve balance rule is decided after a transaction has run and its outcome is a revert of the whole transaction, so no frame is reported failed while its writes are kept. Monad's prestateTracer returns the in-block pre-state of a transaction, which the whole-transaction reruns rely on.",
     "deltas": [
         {"delta": "revert_transaction (reserve_balance.cpp lines 392 to 404) evaluates dipped_into_reserve after execution for MONAD_FOUR and later; it applies to externally owned accounts only, so the PoolManager is never the account under test.", "source": MON + "/v0.16.7/category/execution/monad/reserve_balance.cpp", "relevance": "none"}]},
    {"chainId": 143, "lens": "L3",
     "summary": "No new gas or native currency difference. The 10,000 gas gap between Monad's call tracer and the cycle 18 harness matches Monad's cold account surcharge, and the 25,000 gas gap matches the new account charge for a value call, both read in v0.16.7. The same 21 and 20 scripts as in cycles 13 and 16 differ only where a heavy swap meets Monad's gas costs.",
     "deltas": [
         {"delta": "cold_account_cost is 10,000 under Monad pricing version 1 and later (traits.hpp lines 499 to 505), against 2,500 on Ethereum; a CALL with value adds 9,000, and 25,000 more only when account_exists is false (call.cpp lines 84 to 88 and 116 to 134).", "source": MON + "/v0.16.7/category/vm/evm/traits.hpp", "relevance": "none"}]},
    {"chainId": 143, "lens": "L4",
     "summary": "No new precompile or system contract. The mainnet schedule in monad_mainnet.cpp on main still ends at MONAD_TEN (2026-09-02), so no fork is scheduled.",
     "deltas": []},
    {"chainId": 4326, "lens": "L1",
     "summary": "The replica endpoint moved from mega-reth/v2.2.3-72527bc to mega-reth/v2.3.1-4499c42, a build with no public source. mega-evm main is byte identical to v1.7.4 in the lock file, toolchain, block limit, executor, constants, instruction and frame limit files, and the stateless validator now pins mega-evm v1.7.4. The public validator reproduced the sequencer's headers on all 61 blocks with a PoolManager log since block 32,815,141 and on 2,000 consecutive blocks, all produced while the new build serves RPC.",
     "deltas": [
         {"delta": "web3_clientVersion answered mega-reth/v2.3.1-4499c42@mnet-ash-rpc-2 at every bracket on 2026-11-25 (cycle 16 and the critic note recorded v2.2.3-72527bc earlier).", "source": "https://mainnet.megaeth.com/rpc", "relevance": "low"},
         {"delta": "stateless-validator main pins mega-evm tag v1.7.4 (commit cdcc66e4), revm 40.0.3 and ruint 1.17.2, and builds with nightly-2026-04-23.", "source": RAW + "/megaeth-labs/stateless-validator/main/Cargo.lock", "relevance": "none"}]},
    {"chainId": 4326, "lens": "L2",
     "summary": "No new state model difference. 23 whole-transaction reruns left over from cycle 13 were sorted frame by frame: 15 now match, and in 8 the PoolManager frames they share are equal and only the caller's number of later calls differs.",
     "deltas": []},
    {"chainId": 4326, "lens": "L3",
     "summary": "The state growth skip rule of F-062 is unchanged in mega-evm main. The cost of filling the block budget was recomputed from constants.rs: at the minimum bucket size a new slot carries no storage gas, so 1,000 new slots cost about 22.6 million gas, or 0.0000226 ETH at the 1,000,000 wei base fee read at block 32,821,732.",
     "deltas": []},
    {"chainId": 4326, "lens": "L4",
     "summary": "No new system contract or precompile. mega-evm v1.7.3 removed the REX7 spec (pull request 402), the mainnet schedule in chain.rs ends at Rex6, and the upgrade overview lists nothing after Rex6.",
     "deltas": []},
]

findings = [{
    "ref": "F-062",
    "title": "MegaETH skips every remaining candidate of a block once that block holds 1,000 new state entries, so one cheap transaction per block delays PoolManager exits for the rest of the block",
    "chainIds": [4326], "lens": "L3", "assumptions": ["A9"], "effect": "degrade", "actor": "unprivileged", "severity": "low",
    "difference": "MegaETH caps new state entries per block at 1,000 and the per-transaction cap is also 1,000, so a single transaction can use the whole block budget. After that the block builder rejects every further candidate of the block. Ethereum has no per-block cap on new state.",
    "mechanism": "An ordinary account sends one transaction that writes 1,000 fresh storage slots. Under Rex the storage gas of a new slot is the base times the bucket capacity divided by the minimum bucket size minus one, which is zero in a minimum-size bucket, so the transaction pays about 22.1 million compute gas for the stores plus the intrinsic costs, about 22.6 million gas in all. At the 1,000,000 wei base fee read at block 32,821,732 that is about 0.0000226 ETH. Once it is in a block, BlockLimiter::pre_execution_check returns an error for every later candidate of that block, a modifyLiquidity, take or burn sent to the PoolManager included. The executor leaves its state untouched for a rejected candidate and hands it back to the caller, which typically returns it to the pool, so the victim's call runs in a later block with the same amounts and checks. The PoolManager takes no part: unlock, modifyLiquidity, take and _settle do not read the block number, time or position in a block. Whether the closed sequencer keeps skipped transactions ahead of later arrivals, which would let N fillers close N consecutive blocks to later arrivals, is not stated in any public source.",
    "impact": "No funds move and no balance or delta changes. Swaps, liquidity removals and claim burns of every user are delayed by one block per filler, about one second, at about 1.95 ETH per day to fill every block at the current base fee. A longer delay needs the unconfirmed queue rule.",
    "preconditions": "The base fee stays near its floor, the sequencer does not filter the sender, and the filler lands before the victim in the block. For the amplified form, skipped transactions must keep their place in the queue.",
    "mitigations": "Exits under load can use an L1 deposit of at most 1,000,000 gas (F-105). The operator can price state growth in minimum-size buckets, raise the block limit above the per-transaction limit, or deprioritise senders that fill the budget.",
    "coreRefs": ["src/PoolManager.sol:104-114", "src/PoolManager.sol:145-184", "src/PoolManager.sol:291-297", "src/PoolManager.sol:349-365"],
    "sources": [
        {"url": MEGA + "/main/crates/mega-evm/src/block/limit.rs", "supports": "lines 880 to 890 reject every candidate once block_state_growth_used reaches the block limit; byte identical to v1.7.4 (fetched and compared 2026-11-25)"},
        {"url": MEGA + "/main/crates/mega-evm/src/constants.rs", "supports": "lines 175 to 177: SSTORE_SET_STORAGE_GAS_BASE 20,000 scaled by bucket capacity over minimum bucket size minus one; lines 206 and 211: TX_STATE_GROWTH_LIMIT and BLOCK_STATE_GROWTH_LIMIT are 1,000; line 172: intrinsic storage gas 39,000"},
        {"url": MEGA + "/main/crates/mega-evm/src/block/executor.rs", "supports": "byte identical to v1.7.4; a rejected candidate leaves executor state untouched and goes back to the caller"},
        {"url": MEGA + "/main/crates/mega-evm/src/block/chain.rs", "supports": "mainnet schedule MiniRex to Rex6 (timestamp 1787626800), nothing later"},
        {"url": "https://github.com/megaeth-labs/mega-evm/releases", "supports": "v1.7.3 removed REX7 (pull request 402); v1.7.4 of 24 November changes no execution file"},
        {"url": "https://mainnet.megaeth.com/rpc", "supports": "eth_getBlockByNumber latest on 2026-11-25: block 32,821,732, baseFeePerGas 0xf4240, gasLimit 10,000,000,000; web3_clientVersion mega-reth/v2.3.1-4499c42@mnet-ash-rpc-2"}],
    "evidence": "primary"}]

cleared = [
    {"chainIds": [143, 4326], "lens": "L1",
     "check": "Rerun of the opcode battery (99,985 vectors) and the targeted set (85,544 vectors: MULMOD and mulDiv at the ruint fault shape, ADDMOD around overflow, division by powers of two and full width divisors, shifts at every limb boundary) on Monad/0.16.7 and mega-reth/v2.3.1-4499c42, with web3_clientVersion bracketing every batch.",
     "result": f"Monad ran {bat[143]['ran']} and {tgt[143]['ran']} vectors with {bat[143]['mismatchCount']} and {tgt[143]['mismatchCount']} mismatches; MegaETH ran {bat[4326]['ran']} and {tgt[4326]['ran']} with {bat[4326]['mismatchCount']} and {tgt[4326]['mismatchCount']}. MegaETH's replica build changed since cycle 16 and answers every vector as specified. A wrong MULMOD, SAR, SIGNEXTEND, SDIV, SMOD, BYTE or shift would change src/libraries/FullMath.sol:24-48, TickMath, BitMath.sol:16-45 and TickBitmap.sol:38-73; none occurs.",
     "source": "research/network-risk/cycles/019/high-throughput.work/battery.json, targeted.json, clientversions.log; rpc https://rpc.monad.xyz and https://mainnet.megaeth.com/rpc on 2026-11-25"},
    {"chainIds": [143, 4326], "lens": "L1",
     "check": "Rerun of pmdiff (250 scripts, 12,322 PoolManager calls) and pmdiff2 (300 scripts with hook and token doubles, 16,263 calls) at 25 million gas against the Ethereum reference.",
     "result": f"pmdiff: Monad {pm1[143]['identical']} identical and {len(pm1[143]['different'])} different, MegaETH {pm1[4326]['identical']} identical and {len(pm1[4326]['different'])} different; five scripts had no Ethereum reference because ethereum-rpc.publicnode.com answered HTTP 403 for them, and every other reference hash equals cycle 16's. The Monad set of differing scripts is exactly cycle 16's, the full-range swaps that cycle 18 showed to be the gas cap. pmdiff2: Monad {pm2[143]['identical']} of 300 identical with the same {len(pm2[143]['different'])} differing scripts as cycle 16, MegaETH {pm2[4326]['identical']} of 300.",
     "source": "research/network-risk/cycles/019/high-throughput.work/pmdiff.json, pmdiff.log, pmdiff2.json, pmdiff2.log; research/network-risk/cycles/016/high-throughput.work/pmdiff.json and pmdiff2.json"},
    {"chainIds": [143, 4326], "lens": "L1",
     "check": "Mined swaps against the source math (swaps.py) and the swap loop replayed from storage at the block of each swap (replay.py).",
     "result": "Monad: 6,088 swaps in blocks 125,318,090 to 125,319,980, all 6,088 pass the tick relation exactly; of 5,851 pairs, 5,119 exact input, 658 exact output and 38 to target match one step to the unit, and 36 multi-step swaps were replayed (25 sampled, all reproduce). MegaETH: 6,044 swaps in blocks 31,260,017 to 32,822,016, all pass the tick relation; 4,871, 652 and 35 single-step matches; 115 multi-step and 38 crossed-liquidity swaps, of which the 25 and 38 sampled replay to the unit (src/libraries/SwapMath.sol:20-107, src/libraries/Pool.sol:279-470).",
     "source": "research/network-risk/cycles/019/high-throughput.work/swaps.json, swaps.log, replay.json, replay.log"},
    {"chainIds": [4326], "lens": "L1",
     "check": "Producer evidence under the new replica build (L-606, L-691, L-732): the public stateless validator (cycle 16 build, stateless-validator e1618ed7 with mega-evm v1.7.3, compiled with rustc 1.97.0) run against blocks produced since the endpoint moved to mega-reth v2.3.1.",
     "result": "All 61 blocks with a PoolManager log from 32,815,141 to 32,821,396 validated in anchored mode (witness pre-state checked against the parent header) and 2,000 consecutive blocks 32,818,000 to 32,819,999 validated in chain-following mode, with no warning or error. The validator recomputes the state root, receipts root and gas used of each block with stock revm 40.0.3, so the closed sequencer's arithmetic, transient storage handling and PoolManager storage writes in these blocks equal the stock interpreter's.",
     "source": "research/network-risk/cycles/019/high-throughput.work/anch-results.txt, anch/*.log, range-32818000-32819999.log, anchored.sh; rpc https://mainnet.megaeth.com/rpc"},
    {"chainIds": [4326], "lens": "L1",
     "check": "mega-evm releases and main since cycle 16: Cargo.toml, Cargo.lock, rust-toolchain.toml, block/chain.rs, block/limit.rs, block/executor.rs, constants.rs, evm/instructions.rs and limit/limit.rs at main and at v1.7.4.",
     "result": "All nine files are byte identical between main and v1.7.4. The lock pins revm 40.0.3, revm-interpreter 37.0.3, revm-handler 20.0.3 and ruint 1.19.0, and the toolchain is nightly-2026-04-23, the first nightly with the fix for rust-lang/rust issue 155241, adopted in v1.7.3 (pull request 411, which reports byte-identical replay of 200 Rex6 blocks under both compilers).",
     "source": MEGA + "/main/Cargo.lock and " + MEGA + "/v1.7.4/Cargo.lock (fetched and compared 2026-11-25); https://github.com/megaeth-labs/mega-evm/pull/411"},
    {"chainIds": [143, 4326], "lens": "L1",
     "check": "L-836: the 61 whole-transaction reruns of cycle 13 that still mismatched after the DELEGATECALL fix (38 Monad, 23 MegaETH), rerun with replay17.py and sorted by the first PoolManager frame whose input or output differs from the chain's call tracer.",
     "result": f"MegaETH: {l836.get('4326|all PoolManager frames equal in input, success and output', 0)} now match in every PoolManager frame's input, success and output; in {l836.get('4326|common PoolManager frames equal, caller made a different number of calls', 0)} all shared PoolManager frames are equal and the calling contract made fewer calls after two failed unlock attempts, a gas-dependent decision of the caller. Monad: {l836.get('143|all PoolManager frames equal in input, success and output', 0)} have every PoolManager frame equal (the difference is a caller frame that reverts or logs differently), {l836.get('143|common PoolManager frames equal, caller made a different number of calls', 0)} differ only in the number of later calls, {l836.get('143|caller passed a different input', 0)} receive a different input from the caller, and {l836.get('143|swap output differs after the dynamic hook 0x5ec8dd7d returned a different beforeSwap delta', 0)} differ at a swap of dynamic fee pools with hook 0x5ec8dd7d84fc91bf016d79b125d15aff97c32888. In the one of those traced in full, the hook's beforeSwap returned a different unspecified delta in the rerun for the same input; its library 0x1e32de59 (127,091 bytes) holds 154 GAS instructions and makes a STATICCALL with zero gas that fails out of gas on chain, and the reference interpreter has no gas model. No case shows the PoolManager returning a different result for the same input and the same hook answers, which the PoolManager-only replays of cycles 13 and 14 cover.",
     "source": "research/network-risk/cycles/019/high-throughput.work/l836/l836-summary.json, first-*.json, hook-0x3a286a.json, divergent-swaps.json, oog-*.json, firstpm.py, hookio.py; rpc https://rpc-mainnet.monadinfra.com and https://mainnet.megaeth.com/rpc"},
    {"chainIds": [143], "lens": "L2",
     "check": "Whether Monad's prestateTracer, which the whole-transaction reruns start from, returns the state left by earlier transactions of the same block.",
     "result": "For transaction 0x00cefb67 (index 111 of 124 in block 124,744,439) the two PoolManager slots of pool ee7e75fa that an earlier transaction of the block wrote are reported with the value that transaction wrote, not the parent-block value, and the other four slots equal the parent value. The rerun mismatches of that transaction therefore do not come from a wrong pre-state.",
     "source": "research/network-risk/cycles/019/high-throughput.work/l836/prestate-0x00cefb.json, prestate_check.py; rpc https://rpc-mainnet.monadinfra.com"},
    {"chainIds": [143], "lens": "L2",
     "check": "L-813 for Monad: does the reserve balance check report a frame as failed while keeping its writes?",
     "result": "No. revert_transaction calls dipped_into_reserve after the transaction has executed, for MONAD_FOUR and later, and a positive answer reverts the whole transaction; there is no frame-level outcome. The check skips accounts with contract code, so the PoolManager (24,009 bytes of code) is never tested, and a revert of the whole transaction discards every PoolManager write with it (src/PoolManager.sol:104-114).",
     "source": MON + "/v0.16.7/category/execution/monad/reserve_balance.cpp lines 54-130 and 392-419"},
    {"chainIds": [143], "lens": "L6",
     "check": "Upcoming Monad forks and releases in the next six months.",
     "result": "MonadMainnet::get_monad_revision on main returns MONAD_TEN from timestamp 1788359400 and names no later revision; MONAD_NEXT and MONAD_NEXT_AMSTERDAM exist in revision.h without a mainnet timestamp. The only pending mainnet step is the rolling v0.16.7 upgrade, a snapshot memory fix on top of v0.16.6, whose EVM changes (memory bounds checked once per offset, literal shifts, CLZ, block-exit writes) cycles 16 to 18 already tested against the PoolManager. Nothing changes for funds already in the PoolManager, and no new lever appears for an ordinary account.",
     "source": MON + "/main/category/execution/monad/chain/monad_mainnet.cpp lines 31-51; https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.7; https://github.com/category-labs/monad-bft/releases/tag/v0.16.7"},
    {"chainIds": [4326], "lens": "L6",
     "check": "Upcoming MegaETH forks in the next six months.",
     "result": "mega-evm v1.7.3 removed REX7 (pull request 402), chain.rs on main ends the mainnet schedule at Rex6 (1787626800), and the upgrade overview lists MiniRex to Rex6 only. No fork is scheduled, so nothing changes for funds in the PoolManager.",
     "source": "https://docs.megaeth.com/spec/network-upgrades/overview; " + MEGA + "/main/crates/mega-evm/src/block/chain.rs lines 33-50; https://github.com/megaeth-labs/mega-evm/releases"},
    {"chainIds": [143], "lens": "L1",
     "check": "Monad main, Barrett reduction module in uint256.hpp: does anything on the interpreter or compiler path of MULMOD, ADDMOD, DIV or MOD call it?",
     "result": "Not on main as read. category/vm/runtime/math.hpp lines 74 to 95 call the generic addmod and mulmod, which compute a full 512 bit product and a long division (uint256.hpp lines 921 to 962), and emitter.cpp and emitter.hpp have no reference to barrett or reciprocal. Only files fetched by path were searched; no release carries the module. FullMath.mulDiv (src/libraries/FullMath.sol:24 and :48) therefore still meets the long division on Monad.",
     "source": MON + "/main/category/core/runtime/uint256.hpp; " + MON + "/main/category/vm/runtime/math.hpp; " + MON + "/main/category/vm/compiler/ir/x86/emitter.cpp"},
]

leads = [
    {"chainIds": [143], "lens": "L1",
     "question": "When a Monad release wires the Barrett module of uint256.hpp into MULMOD, ADDMOD, DIV or MOD (interpreter helper or x86 emitter), build a harness of that release's uint256.hpp and compare udivrem, addmod, mulmod and mulmod_const with Python integers for the moduli 2^256 - 1, 2^128 and 2^96, products whose top limbs equal the modulus, and every range alias (1_65 to 193_256).",
     "why": "FullMath.mulDiv calls mulmod(a, b, not(0)) on every swap (src/libraries/FullMath.sol:24) and the bytecode holds MULMOD by 2^96 and 2^128. A reciprocal fast path is the shape of the ruint 1.21.0 fault. A harness was written this cycle (work/src/u256h.cpp) but its compilation was refused by the session's permission rules, so the module itself is untested.",
     "priority": "medium"},
    {"chainIds": [4326], "lens": "L1",
     "question": "Rerun the stateless validator over the PoolManager blocks after each change of the replica build string (now mega-reth/v2.3.1-4499c42) and after any mega-evm release, starting from block 32,821,397.",
     "why": "The sequencer and the replica are closed; the validator's agreement on block headers is the only evidence that the producer computes what stock revm computes, and it covers only blocks already validated.",
     "priority": "low"},
]

leadResults = [
    {"leadId": "L-863", "outcome": "inconclusive",
     "answer": "Both numbers match rules in Monad v0.16.7. Monad's cold_account_cost is 10,000 under pricing version 1 (traits.hpp lines 499 to 505) and is charged when access_account reports the callee cold (call.cpp lines 84 to 88), so a +10,000 gap is one access that Monad counts cold and the harness counts warm. A CALL with value adds 25,000 only when account_exists is false (call.cpp lines 131 to 134), so a -25,000 gap at precompile 4 means Monad treated that address as existing where the harness did not. eth_getBalance of 0x...04 on Monad returned 0 at the latest block, so the existence comes from the call's own state (for example an earlier value transfer in the same call) rather than chain state; which one was not traced. Both are gas only: frame results and storage were equal in cycle 18."},
    {"leadId": "L-868", "outcome": "inconclusive",
     "answer": "The trigger has not happened. Monad's release table gives v0.16.7 a testnet date (2026-11-19) and no mainnet date, and says v0.16.6 can be skipped, so validators have not moved off v0.16.5 by any public record. Rerun when a mainnet date is announced."},
    {"leadId": "L-794", "outcome": "inconclusive",
     "answer": "No Monad release after v0.16.7 exists (raw.githubusercontent.com returns 404 for v0.16.8, v0.17.0 and later tags; the release page lists v0.16.7 last), so there is no new release to rerun replay.cpp and the micro programs on. For the L-785 part, main's barrett module is not called by the interpreter helpers (math.hpp lines 74 to 95 use the generic addmod and mulmod) or by the x86 emitter (no reference in emitter.cpp or emitter.hpp). A harness to test the reduce routines was written but could not be compiled in this session; carried as a new lead."},
    {"leadId": "L-836", "outcome": "cleared",
     "answer": "All 61 remaining reruns (38 Monad, 23 MegaETH) were rerun with replay17.py and sorted by the first PoolManager frame whose input or output differs. MegaETH: 15 now match fully, 8 share equal PoolManager frames and differ in the caller's number of later calls. Monad: 19 have every PoolManager frame equal, 7 differ in the number of later calls, 2 receive a different input from the caller, and 10 differ at swaps whose dynamic hook 0x5ec8dd7d returned a different beforeSwap delta under the gas-less reference (hook library with 154 GAS instructions and a zero-gas STATICCALL). No case has the PoolManager return a different result for the same input and hook answers."},
    {"leadId": "L-732", "outcome": "inconclusive",
     "answer": "The endpoint now answers mega-reth/v2.3.1-4499c42, whose source is not public, so whether it carries the reth execution cache branch is still unknown. The public validator reproduced the sequencer's headers on 2,061 blocks produced under that build, including all 61 PoolManager blocks, and the branch cannot reach the PoolManager's storage or that of a contract an existing pool uses, as cycle 15 found."},
    {"leadId": "L-691", "outcome": "inconclusive",
     "answer": "Which mega-evm release the sequencer runs is not published. mega-evm main equals v1.7.4 in the instruction, limit and executor files, and the stateless validator pins v1.7.4. A validator built on mega-evm v1.7.3 reproduced 2,061 blocks produced this week, receipts root and gas used included, which a different forward gas or volatile data layering would change for any transaction it affects."},
    {"leadId": "L-686", "outcome": "inconclusive",
     "answer": "rust-lang/rust issue 155241 affects stable releases from 1.77 to 1.94 and nightlies up to 2026-04-22; mega-evm moved to nightly-2026-04-23 in v1.7.3 (pull request 411), and the stateless validator uses the same nightly. The toolchain of mega-reth and of the sequencer is not published, and revm 40.0.3 and ruint 1.19.0 were not searched for the closure shape. The validator used here was built with rustc 1.97.0, which carries the fix, and it agrees with the sequencer on 2,061 recent blocks, so any miscompile in the sequencer has not changed a mined result in them."},
    {"leadId": "L-685", "outcome": "inconclusive",
     "answer": "No block or vote field names a version. Monad's release table lists v0.16.7 for testnet only and calls v0.16.6 skippable, which points to v0.16.5 on mainnet validators, while rpc.monad.xyz answers Monad/0.16.7. No public source gives the share of validators on each release."},
    {"leadId": "L-813", "outcome": "cleared",
     "answer": "For Monad, the reserve balance check runs after the transaction has executed (revert_transaction in reserve_balance.cpp lines 392 to 404) and its outcome is a revert of the whole transaction; it applies only to accounts without contract code. No frame is reported failed while its writes are kept, and the PoolManager is never the tested account. The other networks named in the lead belong to other units."},
]

doc = {"unit": "high-throughput", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings,
       "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(doc, open(OUT, 'w'), indent=1)
print('wrote', os.path.abspath(OUT))
