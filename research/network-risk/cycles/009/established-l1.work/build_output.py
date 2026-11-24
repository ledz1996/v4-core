"""Writes research/network-risk/cycles/009/established-l1.research.json from the notes of this
cycle and the raw files in raw/. Usage: python3 build_output.py"""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
W = 'research/network-risk/cycles/009/established-l1.work/raw/'


def L(n): return json.load(open(os.path.join(H, 'raw', n)))


def fits(c):
    r = L(f'l565_{c}.json')
    return r, [p for p in r['pools'] if p['fit']]


r137, f137 = fits(137); r56, f56 = fits(56); r43, f43 = fits(43114)
p137, p56 = f137[0], f56[0]
a1, a2 = f43[0], f43[1]

AV_CODE = 'https://proxy.golang.org/github.com/ava-labs/avalanchego/@v/v1.15.3.zip'
LIBEVM = 'https://proxy.golang.org/github.com/ava-labs/libevm/@v/v1.13.15-0.20261028200218-d398bc4dbe41.zip'
CORETH = 'https://proxy.golang.org/github.com/ava-labs/avalanchego/graft/coreth/@v/v1.15.3.zip'
BOR = 'https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/'
BSC = 'https://raw.githubusercontent.com/bnb-chain/bsc/v1.8.2/'
RBSC = 'https://raw.githubusercontent.com/bnb-chain/reth-bsc/v0.1.4-hotfix/'

ENDPOINTS = ('Polygon: https://polygon-bor-rpc.publicnode.com (bor v2.11.1-private) and https://rpc-mainnet.matic.quiknode.pro (bor v2.11.1-private); '
             'BNB Smart Chain: https://bsc-dataseed1.bnbchain.org (Geth v1.8.2-4e1c8247) and https://bsc-rpc.publicnode.com (reth-bsc v0.1.4-hotfix-23b510f); '
             'Avalanche: https://api.avax.network/ext/bc/C/rpc and https://avalanche-c-chain-rpc.publicnode.com (both avalanchego/1.15.3 commit 983815fd)')


def gas_sentence(cid, p, rr, cap, capname):
    k = p['fit']
    n = (cap - max(k['base'], 0)) // k['perCrossing']
    w = (cap - max(k['base'], 0)) // k['perEmptyStep']
    return (f"Pool {p['poolId']} (fee {p['key'][2]}, tick spacing {p['key'][3]}, no hook) at block {rr['block']}: {p['matched']} Quoter calls whose output equalled the step by step replay of Pool.swap to the unit, "
            f"up to {p['maxCross']} initialized crossings and {p['maxEmpty']} other steps in one quote. The least squares fit gives {k['perCrossing']:,} gas per initialized crossing and {k['perEmptyStep']:,} gas per step that ends on an uninitialized word boundary, "
            + (f"with a fixed part of {k['base']:,} gas. " if k['base'] >= 0 else f"with a constant term of {k['base']:,} gas, so the linear fit is only approximate for small quotes. ")
            + f"At {cap:,} gas ({capname}) that is about {n:,} crossings or about {w:,} empty words in one transaction.")


s137 = gas_sentence(137, p137, r137, 33554432, 'the Polygon transaction cap')
s56 = gas_sentence(56, p56, r56, 16777216, 'the BNB Smart Chain transaction cap')
s43a = gas_sentence(43114, a1, r43, 80000000, 'the C-Chain block gas limit, which is the only bound')
s43b = gas_sentence(43114, a2, r43, 80000000, 'the C-Chain block gas limit')

profiles = [
    {"chainId": 137, "lens": "L1", "summary": "Public endpoints report bor v2.11.1-private and v2.11.2. The core/vm directory is the same in both tags, and v2.11.2 changes peering and the Go toolchain only. The optional switch dispatch interpreter, read in full, computes what the default loop computes. Both bor endpoints passed all 185,529 opcode vectors and gave the Ethereum bytes for every script that did not run out of gas.",
     "deltas": [
         {"delta": "Fifteen files of core/vm (instructions, interpreter, analysis, jump table, eips, memory, stack, evm, gas tables and the jump destination cache) are byte identical at tags v2.11.1 and v2.11.2, and so are params/config.go, params/protocol_params.go, core/state_transition.go, core/state/statedb.go, core/state/transient_storage.go and core/parallel_state_processor.go. go.mod changes the Go version from 1.26.10 to 1.26.11 and klauspost/compress from v1.18.1 to v1.20.2. The release notes list peer rotation, fork ID handling, a sequence store producer fix and the two dependency updates.",
          "source": "https://github.com/0xPolygon/bor/releases/tag/v2.11.2 and raw files under https://raw.githubusercontent.com/0xPolygon/bor/v2.11.1/ and " + BOR + " (diff in " + W.replace('raw/', 'src/bor/') + ")", "relevance": "none"},
         {"delta": "core/vm/interpreter_dispatch.go (794 lines) is a second interpreter loop, used only when EnableEVMSwitchDispatch is set (internal/cli/server/config.go line 937 sets it false by default). It inlines the arithmetic, comparison, bitwise, shift, PUSH, DUP, SWAP, JUMP and JUMPI opcodes on a fixed 1024 word stack and accumulates their constant gas, which it charges before STOP, JUMP, JUMPI, JUMPDEST, INVALID and every other opcode. Operand order, stack bounds and the uint256 calls match the jump table versions. SAR sends a shift of exactly 256 to uint256 SRsh instead of the sign fill branch, and SRsh returns zero or all ones there, which is the specified result. Because the uninlined opcodes, including GAS, CALL, SSTORE and LOG, are charged before they run, a frame that runs out of gas fails at the same side effect as in the default loop.",
          "source": BOR + "core/vm/interpreter_dispatch.go", "relevance": "low"},
         {"delta": "The two publicnode instances reported different build hashes for the same private version, bor/a863b8e5cce1/v2.11.1-private and bor/f2a2d63e69f6/v2.11.1-private, and QuickNode reports bor/qn-lsn-fra-12486/v2.11.1-private. OnFinality reports bor v2.11.2 with Go 1.26.11. drpc still reports Geth/v10.0.0/drpc.",
          "source": "rpc web3_clientVersion on 2026-11-24, " + W + "client_versions.txt and client_versions_wide.txt", "relevance": "low"},
         {"delta": "Polygon Labs ended support for the Polygon fork of Erigon on 1 August 2026 and archived the repository. Its README says existing deployments keep syncing only until the next Bor hardfork. None of the 14 Polygon endpoints probed on 2026-11-24 reported Erigon.",
          "source": "https://forum.polygon.technology/t/sunsetting-erigon-support/21872 and https://github.com/0xPolygon/erigon", "relevance": "none"}]},
    {"chainId": 137, "lens": "L2", "summary": "Nothing new. The state and transient storage code of Bor is unchanged between v2.11.1 and v2.11.2.",
     "deltas": [{"delta": "core/state/statedb.go, core/state/journal.go and core/state/transient_storage.go are byte identical at tags v2.11.1 and v2.11.2.", "source": BOR + "core/state/transient_storage.go", "relevance": "none"}]},
    {"chainId": 137, "lens": "L3", "summary": "Lead L-565 measured the gas of one tick crossing through the deployed Quoter. It is about 27,700 gas on Polygon, a little above the 25,000 that cycle 8 computed.",
     "deltas": [{"delta": s137, "source": "rpc https://polygon-bor-rpc.publicnode.com eth_call to Quoter 0x31AB0Dea31FC0ad5A54F03cD59C896eCD067447B and extsload on the PoolManager, 2026-11-24; " + W + "l565_137.json", "relevance": "low"}]},
    {"chainId": 137, "lens": "L4", "summary": "The three Bor system contracts were hashed so later cycles can see a change at a glance.",
     "deltas": [{"delta": "At the latest block on 2026-11-24, 0x0000000000000000000000000000000000001000 holds 14,347 bytes (keccak 59b19ae59c23bbd4...), 0x...1001 holds 6,332 bytes (aa002524bd13fa0f...) and 0x...1010 holds 5,315 bytes (82c4ebd167e81e53...).", "source": "rpc https://polygon-bor-rpc.publicnode.com eth_getCode, 2026-11-24; " + W + "l4_probe.txt", "relevance": "none"}]},
    {"chainId": 56, "lens": "L1", "summary": "The BNB Smart Chain clients now serve both public endpoints with different interpreters, geth v1.8.2 and reth-bsc v0.1.4-hotfix on stock revm. Both passed all 185,529 vectors and gave the Ethereum bytes for all 550 scripts. Jenner does not change the instruction set. Both clients refuse to run code at the block's coinbase address.",
     "deltas": [
         {"delta": "reth-bsc builds its EVM with EthInstructions::new_mainnet_with_spec (src/evm/api/mod.rs line 90), so every opcode is the stock revm-interpreter 35.0.1 instruction with ruint 1.18.0 (Cargo.lock). The only frame level change is the coinbase rule below. The battery, the targeted set, pmdiff and pmdiff2 had not run on reth-bsc before this cycle.", "source": RBSC + "src/evm/api/mod.rs", "relevance": "low"},
         {"delta": "geth v1.8.2 core/vm/interpreter.go lines 96 to 98 return ErrCoinbaseAsContract when the frame's address is the block coinbase, and reth-bsc ports the rule in frame_run (src/evm/api/mod.rs lines 235 to 270), burning the frame's gas. Ethereum has no such rule. A call from the PoolManager to an address that holds code fails when that address is the coinbase of the block.", "source": BSC + "core/vm/interpreter.go", "relevance": "low"},
         {"delta": "The master branch still carries version 1.8.2 and its CHANGELOG lists v1.8.2 as the release that schedules Jenner for 2026-12-08 02:30 UTC (1796697000). core/vm/jump_table.go at v1.8.2 has no Jenner instruction set: the newest is Osaka, followed by Amsterdam and Verkle sets that mainnet does not use.", "source": "https://raw.githubusercontent.com/bnb-chain/bsc/master/CHANGELOG.md and " + BSC + "core/vm/jump_table.go", "relevance": "none"}]},
    {"chainId": 56, "lens": "L2", "summary": "reth-bsc clears transient storage at the end of every transaction, committed or discarded, as the revm journal does on Ethereum.",
     "deltas": [{"delta": "The BscHandler ends each transaction with journal commit_tx (src/evm/handler.rs line 302). In revm-context 16.0.1, which Cargo.lock pins, JournalInner::commit_tx and discard_tx both clear transient_storage (src/journal/inner.rs lines 137 to 188). A transaction is treated as a system transaction only when its caller is the block beneficiary, its target is a system contract and its gas price is zero (src/evm/api/mod.rs detect_system_transaction).", "source": RBSC + "src/evm/handler.rs and https://static.crates.io/crates/revm-context/revm-context-16.0.1.crate", "relevance": "none"}]},
    {"chainId": 56, "lens": "L3", "summary": "Lead L-565 measured about 17,000 gas per tick crossing on BNB Smart Chain, which matches the 16,500 that cycle 8 computed from opcode prices.",
     "deltas": [{"delta": s56, "source": "rpc https://bsc-dataseed1.bnbchain.org eth_call to Quoter 0x95C086d7fE28AdD842ee220fef225a777474d781 and extsload on the PoolManager, 2026-11-24; " + W + "l565_56.json", "relevance": "low"}]},
    {"chainId": 56, "lens": "L4", "summary": "Jenner has not activated. The CAS20 addresses still hold no code, and the prefix rule that will turn them into precompiles fixes 80 bits of the address.",
     "deltas": [
         {"delta": "At block 135,445,070 (timestamp 1,795,515,281, 1,181,719 seconds before JennerTime) 0x70, 0x7020000000000000000000000000000000000001, 0x7020000000000000000000000000000000000002, 0xCA5F000000000000000000000000000000000000 and 0xca52000000000000000000000000000000000001 hold no code.", "source": "rpc https://bsc-dataseed1.bnbchain.org eth_getCode, 2026-11-24; " + W + "l4_probe.txt", "relevance": "low"},
         {"delta": "After Jenner, reth-bsc routes an address to a CAS20 precompile by prefix: bytes 0 and 1 equal 0xca52, bytes 2 to 9 are zero and byte 10 is 0 or 1 (is_cas20_address and resolve in src/evm/precompiles/cas20/mod.rs). The rule applies to every such address whether or not a token was created there.", "source": RBSC + "src/evm/precompiles/cas20/mod.rs", "relevance": "low"}]},
    {"chainId": 43114, "lens": "L1", "summary": "Leads L-567 and L-585 are answered: since block 95,921,105 (Helicon, 2026-09-22 15:00 UTC) the C-Chain decides blocks through vms/saevm only, and avalanchego 1.15.3 registers no other C-Chain VM. Its interpreter is libevm, whose core/vm files equal go-ethereum v1.13.15 except for hooks in evm.go, with holiman/uint256 v1.2.4. Both endpoints passed all 185,529 vectors and all 550 scripts, and 197,259 swaps mined after Helicon satisfy the tick relation.",
     "deltas": [
         {"delta": "node/node.go line 1240 registers saevm.Factory for constants.EVMID and no other factory, and vms/saevm/cchain/factory.go creates the C-Chain SAE VM. upgrade/upgrade.go line 41 sets HeliconTime to 2026-09-22 15:00 UTC on mainnet. On chain, block 95,921,104 has no settledHeight field and block 95,921,105 (timestamp 1,790,089,200) is the first with settledHeight, settledExcess and the other SAE header fields.", "source": AV_CODE + " and rpc https://api.avax.network/ext/bc/C/rpc eth_getBlockByNumber binary search, 2026-11-24; " + W + "avax_sae_activation.json", "relevance": "low"},
         {"delta": "Twelve core/vm files of libevm d398bc4dbe41 (instructions, interpreter, analysis, jump table, eips, memory, memory table, stack, common, contract, gas table, operations_acl) are identical to go-ethereum v1.13.15 once import paths are normalised. evm.go adds a precompile override hook, an argument override hook that wraps the StateDB, a contract creation hook and a preprocessing gas charge, which the C-Chain sets to zero (vms/saevm/cchain/libevm/vm/hooks.go line 43). go.mod pins holiman/uint256 v1.2.4. The C-Chain therefore runs the Cancun instruction set of a two year old go-ethereum, without CLZ and without EIP-7702.", "source": LIBEVM + " compared with https://raw.githubusercontent.com/ethereum/go-ethereum/v1.13.15/core/vm/instructions.go", "relevance": "low"},
         {"delta": "The go-ethereum vulnerability list names no EVM consensus fault introduced after v1.10.8. The last EVM consensus flaw it lists (GETH-2021-02) was fixed in v1.10.8, before the v1.13.15 base of libevm.", "source": "https://geth.ethereum.org/docs/vulnerabilities/vulnerabilities.json", "relevance": "none"}]},
    {"chainId": 43114, "lens": "L2", "summary": "On the live SAE path each transaction is applied by core.ApplyTransaction of libevm, whose StateDB.Prepare replaces the transient storage map before the transaction runs.",
     "deltas": [{"delta": "vms/saevm/saexec/execution.go lines 346 to 364 call core.ApplyTransaction once per transaction. libevm core/state_transition.go line 436 calls StateDB.Prepare, and core/state/statedb.go line 1335 sets transientStorage to a new map there. The cycle 1 and 2 clearances on transient storage, written for coreth, therefore hold for the path that is live.", "source": AV_CODE + " and " + LIBEVM, "relevance": "none"}]},
    {"chainId": 43114, "lens": "L3", "summary": "Lead L-565 measured 27,000 to 33,000 gas per tick crossing on the C-Chain, well above the 16,500 that cycle 8 computed under the assumption of Ethereum prices.",
     "deltas": [{"delta": s43a + " " + s43b, "source": "rpc https://avalanche-c-chain-rpc.publicnode.com eth_call to Quoter 0xf27e532878B622d6b916F524E8711880107D4eF0 and extsload on the PoolManager, 2026-11-24; " + W + "l565_43114.json", "relevance": "low"}]},
    {"chainId": 43114, "lens": "L4", "summary": "The precompile set after Helicon is the Granite set: the three native asset addresses revert, P256 sits at 0x100, and warp at 0x0200000000000000000000000000000000000005.",
     "deltas": [{"delta": "graft/coreth params/hooks_libevm.go lines 119 to 193 select PrecompiledContractsGranite (DeprecatedContract at 0x0100000000000000000000000000000000000000, ...01 and ...02, P256Verify at 0x100) and warp when Durango is active. eth_call from the PoolManager address to the three native asset addresses reverted with empty data, the warp address answered invalid function selector, and 0x100 returned empty data. A native take to 0x0100000000000000000000000000000000000000, the address that collects base fees, therefore reverts.", "source": CORETH + " and rpc https://api.avax.network/ext/bc/C/rpc eth_call, 2026-11-24; " + W + "l4_probe.txt", "relevance": "low"}]},
]

finding = {
    "ref": "F-111",
    "title": "A run of dust positions bounds how far one swap can move the price inside the gas cap, and the Quoter now measures the cost per crossing on all three chains",
    "chainIds": [56, 137, 43114], "lens": "L3", "assumptions": ["A9"], "effect": "degrade", "actor": "unprivileged", "severity": "low",
    "difference": "BNB Smart Chain caps a transaction at 16,777,216 gas and Polygon at 33,554,432 gas. The C-Chain has no transaction cap below its block limit of 80,000,000 gas. Measured through the deployed Quoter on 2026-11-24, one initialized tick crossing in Pool.swap costs about 17,000 gas on BNB Smart Chain, about 27,700 on Polygon and 27,000 to 33,000 on the C-Chain, and one step over an empty bitmap word about 5,600, 9,200 and 4,900 to 6,400 gas.",
    "mechanism": "1. Pool.swap runs one loop step per initialized tick and per bitmap word it reaches (src/libraries/Pool.sol:344-437). A step that ends on an initialized tick calls crossTick, which reads the liquidity word and rewrites both fee growth words of the tick (src/libraries/Pool.sol:602-611). A step over an empty word reads one bitmap slot (src/libraries/TickBitmap.sol:85-121). 2. This cycle replayed the loop step by step against live storage read through extsload and called quoteExactInputSingle on the deployed Quoter at the same block, for about 60 exact input amounts per pool and direction. Every quote whose state the endpoint served returned the replay's output to the unit, so the counts of crossings and empty steps per quote are exact. 3. " + s56 + " 4. " + s137 + " 5. " + s43a + " 6. Cycle 8 computed 16,500 gas per crossing for BNB Smart Chain and Avalanche and 25,000 for Polygon. The measurement confirms BNB Smart Chain and Polygon and shows that the C-Chain costs more than its Ethereum price assumption, so the bound there is about 2,400 to 2,950 crossings per block, not 4,800. 7. As before, any account can add one unit of liquidity on consecutive ticks of a pool with tick spacing 1 to lengthen the walk, a swapper can still cross the range in several transactions with sqrtPriceLimitX96, and liquidity removal touches two ticks without a loop (src/libraries/Pool.sol:146-236).",
    "impact": "No funds are taken and no withdrawal is blocked. Swaps that must cross more initialized ticks than the cap allows need several transactions, and single call integrations across that range revert. The largest single quote measured this cycle used 1,788,771 gas on BNB Smart Chain, 4,964,889 on Polygon and 5,737,630 on Avalanche.",
    "preconditions": "A pool with small tick spacing and a price move that must cross the range. The attacker pays gas and a few base units of both currencies per tick.",
    "mitigations": "Routers and liquidators should bound each swap with sqrtPriceLimitX96 and continue in another transaction. Interfaces can count initialized ticks on a route through extsload. On Avalanche the per crossing figure of this cycle should replace the computed one in any gas budget.",
    "coreRefs": ["src/libraries/Pool.sol:344-437", "src/libraries/Pool.sol:602-611", "src/libraries/TickBitmap.sol:85-121", "src/libraries/Pool.sol:146-236"],
    "sources": [
        {"url": "rpc https://bsc-dataseed1.bnbchain.org eth_call Quoter 0x95C086d7fE28AdD842ee220fef225a777474d781, 2026-11-24; " + W + "l565_56.json", "supports": "BNB Smart Chain gas per crossing and per empty word"},
        {"url": "rpc https://polygon-bor-rpc.publicnode.com eth_call Quoter 0x31AB0Dea31FC0ad5A54F03cD59C896eCD067447B, 2026-11-24; " + W + "l565_137.json", "supports": "Polygon gas per crossing and per empty word"},
        {"url": "rpc https://avalanche-c-chain-rpc.publicnode.com eth_call Quoter 0xf27e532878B622d6b916F524E8711880107D4eF0, 2026-11-24; " + W + "l565_43114.json", "supports": "Avalanche gas per crossing and per empty word"},
        {"url": "https://raw.githubusercontent.com/0xPolygon/bor/v2.11.1/params/protocol_params.go", "supports": "Polygon MaxTxGas 1 << 25"},
        {"url": BSC + "params/protocol_params.go", "supports": "BNB Smart Chain MaxTxGas 1 << 24 (read in cycle 8)"}],
    "evidence": "primary"}

cleared = [
    {"chainIds": [137, 56, 43114], "lens": "L1", "check": "Opcode battery (99,985 vectors) and targeted set (85,544 vectors) of tools/opdiff on two endpoints per chain, including reth-bsc and both bor endpoints, which no earlier run covered: " + ENDPOINTS + ".",
     "result": "All six endpoints returned the specified word for all 185,529 vectors, with no error. The arithmetic, shift, sign extension, byte, MULMOD and ADDMOD edges that FullMath, TickMath, BitMath, SqrtPriceMath, TickBitmap and BalanceDelta depend on are computed to specification by geth v1.8.2, reth-bsc on revm-interpreter 35.0.1 with ruint 1.18.0, bor v2.11.1-private and libevm on uint256 v1.2.4.",
     "source": W + "battery.json and " + W + "targeted.json"},
    {"chainIds": [137, 56, 43114], "lens": "L1", "check": "pmdiff (250 scripts, 12,322 PoolManager calls) and pmdiff2 (300 scripts, 16,263 calls, hook and token doubles) of tools/opdiff on the same six endpoints, against the Ethereum reference whose hashes equal those in opcodes/pmdiff2.json.",
     "result": "BNB Smart Chain (both clients) and Avalanche (both endpoints) returned the Ethereum bytes for all 550 scripts. The two bor endpoints differed on 19 pmdiff and 20 pmdiff2 scripts, and the indices are exactly those that opcodes/pmdiff.json and opcodes/pmdiff2.json record for Polygon and attribute to swaps that ran out of gas at 25 million gas under PIP-88 prices.",
     "source": W + "pmdiff.json and " + W + "pmdiff2.json"},
    {"chainIds": [43114], "lens": "L1", "check": "Mined swaps since Helicon. OPCODES.md rests Avalanche on 59 swaps; this cycle read every Swap log of the PoolManager from block 96,905,540 to 101,247,539, all after the first SAE block 95,921,105, through the publicnode endpoint in 40,000 block ranges.",
     "result": "197,259 swaps, all of which satisfy the tick relation (197,086 exact and 173 on a tick boundary). Of 173,872 swaps paired with the swap before them, 173,179 match a single step outcome of SwapMath.computeSwapStep to the unit, 677 took several steps and 16 crossed liquidity. Of the 41 sampled for a full replay, 8 replayed to the unit and 33 could not be replayed because the endpoint no longer serves the state of those blocks. Block execution on the SAE path computes the pool math as the source does.",
     "source": W + "swaps-deep-43114.json and " + W + "replay-deep-43114.json"},
    {"chainIds": [137, 56], "lens": "L1", "check": "Mined swaps on Polygon (blocks 97,832,911 to 97,872,910) and BNB Smart Chain (blocks 135,437,753 to 135,443,752), with full replays of the multi step and crossing swaps.",
     "result": "Polygon: 20,521 swaps, all pass the tick relation, 18,870 of 19,010 pairs match one step to the unit, and all 36 sampled multi step and crossing swaps replay to the unit (longest 48 steps). BNB Smart Chain: 7,463 swaps, all pass the tick relation, 6,572 of 6,635 pairs match one step, and all 25 sampled multi step swaps replay to the unit (longest 41 steps). These blocks were produced by validators, so the result covers the block production path, BlockSTM on Polygon included.",
     "source": W + "swaps-deep-137.json, " + W + "replay-deep-137.json, " + W + "swaps.json and " + W + "replay.json"},
    {"chainIds": [43114], "lens": "L1", "check": "Leads L-567 and L-585: which execution path decides C-Chain mainnet blocks under avalanchego 1.15.3.",
     "result": "Only vms/saevm. node/node.go line 1240 registers saevm.Factory for the EVM VM ID, HeliconTime is 2026-09-22 15:00 UTC (upgrade/upgrade.go line 41), the first block with SAE header fields is 95,921,105 at exactly that time, and release v1.15.2 is titled Removed Coreth and requires nodes that last ran before Helicon to bootstrap past it on v1.15.0 or v1.15.1 first. The coreth module that 1.15.3 still imports supplies only the chain parameters and precompile set (params/hooks_libevm.go). The cycle 8 clearances that read saevm therefore describe the live path.",
     "source": AV_CODE + "; https://github.com/ava-labs/avalanchego/releases/tag/v1.15.2; https://docs.avax.network/docs/nodes/architecture/execution/continuous-execution; " + W + "avax_sae_activation.json"},
    {"chainIds": [43114], "lens": "L1", "check": "Interpreter and integer library of the live C-Chain path.",
     "result": "libevm d398bc4dbe41 keeps go-ethereum v1.13.15 core/vm unchanged apart from hooks in evm.go, and avalanchego registers hooks that only wrap the StateDB, set PREVRANDAO from the difficulty after Shanghai and charge zero preprocessing gas (vms/saevm/cchain/libevm/vm/hooks.go lines 43 to 63). The integer library is holiman/uint256 v1.2.4, the release go-ethereum shipped through 2024. The storage slot transform of F-040 is the only semantic change and sits in the StateDB, not in the interpreter.",
     "source": LIBEVM + " and " + AV_CODE},
    {"chainIds": [43114], "lens": "L2", "check": "Transient storage lifetime on the SAE executor that is live since Helicon.",
     "result": "saexec calls core.ApplyTransaction once per transaction (vms/saevm/saexec/execution.go lines 346 to 364), and libevm's state transition calls StateDB.Prepare, which installs a new transient storage map (core/state_transition.go line 436, core/state/statedb.go line 1335). No delta, lock flag or synced currency can survive into the next transaction.",
     "source": AV_CODE + " and " + LIBEVM},
    {"chainIds": [137], "lens": "L1", "check": "Whether the optional switch dispatch interpreter of Bor v2.11.x, which a validator can enable with evm-switch-dispatch, computes a different result for any opcode the PoolManager uses.",
     "result": "No. The file was read in full. Every inlined opcode takes its operands in the jump table order and calls the same uint256 method, the stack checks are the same, JUMP and JUMPI check the jump destination before moving the program counter, and JUMPI tests the whole condition word. SAR with a shift of exactly 256 reaches SRsh, which returns zero for a non-negative value and all ones for a negative value, as specified. Constant gas of the inlined opcodes is charged before the next opcode that can have an effect, so the GAS opcode and every call see the same remaining gas. The setting is off by default.",
     "source": BOR + "core/vm/interpreter_dispatch.go and " + BOR + "internal/cli/server/config.go"},
    {"chainIds": [137], "lens": "L1", "check": "Whether Bor v2.11.2, released 2026-11-19 and served by OnFinality, changes execution relative to v2.11.1.",
     "result": "No. core/vm, the state code, the chain config, the protocol parameters and the parallel state processor are byte identical at the two tags. The release changes peering, fork ID handling and a sequence store producer path, and moves to Go 1.26.11.",
     "source": "https://github.com/0xPolygon/bor/releases/tag/v2.11.2 and " + BOR + "core/vm/instructions.go"},
    {"chainIds": [137], "lens": "L1", "check": "Lead L-580: rerun the battery against a bor endpoint and check whether any public Polygon RPC still runs Erigon.",
     "result": "Both bor endpoints (publicnode and QuickNode, v2.11.1-private) passed the 185,529 vectors and the 550 scripts with the same results as the drpc run of OPCODES.md. Polygon Labs ended Erigon support on 1 August 2026, and none of the 14 endpoints probed reported Erigon.",
     "source": W + "battery.json, " + W + "client_versions_wide.txt and https://forum.polygon.technology/t/sunsetting-erigon-support/21872"},
    {"chainIds": [56], "lens": "L1", "check": "Whether reth-bsc, which serves https://bsc-rpc.publicnode.com, replaces any instruction.",
     "result": "No. It uses the stock revm-interpreter 35.0.1 instruction table for the configured spec (src/evm/api/mod.rs line 90). The battery, the targeted set and both pmdiff sets gave the specified results there.",
     "source": RBSC + "src/evm/api/mod.rs"},
    {"chainIds": [56], "lens": "L2", "check": "Transient storage and system transaction detection in reth-bsc.",
     "result": "commit_tx and discard_tx of revm-context 16.0.1 clear the transient map at the end of every transaction, and a transaction is a system transaction only when its caller is the block beneficiary with a zero gas price and a system contract as target. An ordinary account cannot be the beneficiary.",
     "source": RBSC + "src/evm/handler.rs and https://static.crates.io/crates/revm-context/revm-context-16.0.1.crate"},
    {"chainIds": [56], "lens": "L1", "check": "The BNB Smart Chain rule that code cannot run at the block coinbase address (geth v1.8.2 core/vm/interpreter.go lines 96 to 98, reth-bsc src/evm/api/mod.rs lines 235 to 270): can an ordinary account use it against the PoolManager.",
     "result": "No. The coinbase is the signing address of the validator that produced the block, so only a validator can choose it, and it has code only if the validator delegated its own key through EIP-7702. A hook or token at that address would fail in that validator's blocks, which hurts only pools that chose such a contract. A native take to an address without code is not affected, because the rule applies only when code runs. Recorded with actor operator.",
     "source": BSC + "core/vm/interpreter.go"},
    {"chainIds": [56], "lens": "L4", "check": "Whether an ordinary account can place a contract at an address that becomes a CAS20 precompile at Jenner, so that the code of a hook or currency changes after pools are created (A7).",
     "result": "Not feasible. The prefix rule fixes 0xca52 and eight zero bytes and limits byte 10 to two values, about 81 fixed bits, so a CREATE2 search for such an address needs about 2^80 hashes. Before Jenner these addresses hold no code, so sync and settle of such a currency revert in balanceOf and no account can be credited in it.",
     "source": RBSC + "src/evm/precompiles/cas20/mod.rs and rpc https://bsc-dataseed1.bnbchain.org eth_getCode, 2026-11-24"},
    {"chainIds": [43114], "lens": "L4", "check": "What the PoolManager does when an ordinary caller names an Avalanche precompile address after Helicon (P1 and P2).",
     "result": "The three native asset addresses run DeprecatedContract and revert, warp rejects a call without a valid selector, and P256 at 0x100 returns empty data and moves nothing. A take to the native asset addresses therefore reverts, and a take naming 0x100 as currency succeeds with empty data and debits the caller the full amount, as for any address without code. No call moves value that the caller does not owe.",
     "source": CORETH + " and rpc https://api.avax.network/ext/bc/C/rpc eth_call from the PoolManager address, 2026-11-24"},
]

leads = [
    {"chainIds": [56], "lens": "L1", "question": "After Jenner activates on 2026-12-08 02:30 UTC, do battery.py, targeted.py, pmdiff.py and pmdiff2.py still give the published results on both geth v1.8.2 and reth-bsc, and does the CAS20 prefix lookup of reth-bsc agree with go-bsc on which addresses are precompiles?",
     "why": "The two clients implement the prefix routing separately. A disagreement on which address is a precompile would make the two clients execute a call from the PoolManager differently.", "priority": "medium"},
    {"chainIds": [137], "lens": "L1", "question": "Which source commit do the private Bor builds a863b8e5cce1 and f2a2d63e69f6 that publicnode reports as v2.11.1-private correspond to, and do validators run them?",
     "why": "The public v2.11.1 tag was read and tested, but Polygon has shipped private builds before publishing source, and two instances of one provider report different build hashes.", "priority": "low"},
    {"chainIds": [43114], "lens": "L3", "question": "Why does one tick crossing cost 27,000 to 33,000 gas on the C-Chain against about 17,000 on BNB Smart Chain, which charges Ethereum prices? Read the gas table selected by the coreth chain rules for SLOAD and SSTORE after Helicon.",
     "why": "The per crossing figure sets how many ticks one swap can cross. The measurement is primary, but the cause was not read.", "priority": "low"},
]

lead_results = [
    {"leadId": "L-580", "outcome": "cleared", "answer": "battery.py and targeted.py ran against https://polygon-bor-rpc.publicnode.com (bor/a863b8e5cce1 and bor/f2a2d63e69f6, v2.11.1-private) and https://rpc-mainnet.matic.quiknode.pro (bor v2.11.1-private): 185,529 of 185,529 vectors as specified on both. pmdiff and pmdiff2 on both gave the same 19 and 20 gas limited differences as the drpc run. OnFinality reports bor v2.11.2, whose core/vm equals v2.11.1, but rate limited the test. Polygon Labs ended support for its Erigon fork on 1 August 2026 and archived the repository, and none of the 14 endpoints probed reported Erigon."},
    {"leadId": "L-585", "outcome": "cleared", "answer": "avalanchego 1.15.3 decides C-Chain blocks through vms/saevm only: node/node.go line 1240 registers saevm.Factory for the EVM VM ID, HeliconTime on mainnet is 2026-09-22 15:00 UTC, and block 95,921,105 at that timestamp is the first with SAE header fields. On that path transient storage is reset per transaction by libevm StateDB.Prepare, the storage slot transform of F-040 is in vms/saevm/cchain/libevm/extstate, and the transaction type rule read in cycle 8 is in vms/saevm/worstcase. The cycle 8 clearances on transaction types, storage folding and transient storage hold for the live path."},
    {"leadId": "L-567", "outcome": "cleared", "answer": "Same answer as L-585. The saevm path read in cycle 8 has decided every C-Chain block since 95,921,105. 197,259 swaps mined on that path from block 96,905,540 satisfy the tick relation, and 173,179 of 173,872 pairs match a single step to the unit."},
    {"leadId": "L-565", "outcome": "finding", "answer": "Measured through the deployed Quoters at blocks " + f"{r56['block']:,}, {r137['block']:,} and {r43['block']:,}" + ", with the simulated output equal to the Quoter output on every served quote: about 17,000 gas per initialized crossing and 5,600 per empty word on BNB Smart Chain, about 27,700 and 9,200 on Polygon, and 27,000 to 33,000 and 4,900 to 6,400 on Avalanche. The bound of F-111 becomes about 983 crossings per transaction on BNB Smart Chain, about 1,210 on Polygon and about 2,400 to 2,950 per block on Avalanche. F-111 is restated with the measured figures."},
]

out = {"unit": "established-l1", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": [finding], "cleared": cleared, "leads": leads, "leadResults": lead_results}
json.dump(out, open('/home/user/v4-core/research/network-risk/cycles/009/established-l1.research.json', 'w'), indent=1)
print('written')
