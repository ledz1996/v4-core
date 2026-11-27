"""Writes cycle 37 ethereum-reference.research.json from the outputs in ../out."""
import json, os, collections
H = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(H, '..')
O = os.path.join(W, 'out')
OUTF = os.path.join(W, '..', 'ethereum-reference.research.json')
WR = 'research/network-risk/cycles/037/ethereum-reference.work'

pr = json.load(open(os.path.join(O, 'rpcshapes-pocket-rounds.json')))
rot = collections.Counter(pr['rotation'])
tot = sum(rot.values())
eri = {k: v for k, v in rot.items() if k.startswith('erigon/3.8')}
eri_n = sum(eri.values())
calls = pr['agree'] + pr['differ'] + pr['noAnswer']
rot_txt = ', '.join(f"{k.split('/linux')[0].split('/x86')[0]} {v}" for k, v in rot.most_common())
share = eri_n / tot
p_none = (1 - share) ** calls
gw = json.load(open(os.path.join(O, 'rpcshapes-gateways.json')))
gw_agree = sum(e['agree'] for e in gw['endpoints'].values())
gw_diff = sum(e['differ'] for e in gw['endpoints'].values())
gw_none = sum(e['noAnswer'] for e in gw['endpoints'].values())
swaps = open(os.path.join(O, 'swaps-eth.log')).read().strip().splitlines()[-1]

SRC_POCKET = f"rpc: eth_call with state overrides and web3_clientVersion on https://eth.api.pocket.network, 2026-11-27 ({WR}/out/rpcshapes-pocket-rounds.json, pocket-rotation.json)"

pocket_answer = (
    f"Partly answered. The pocket gateway (eth.api.pocket.network) rotates each request, batch elements included, over reth v2.11.0, reth v2.10.1, "
    f"Geth v1.17.9 and two erigon builds that carry the frame cache: erigon/3.8.1-cf6f1413 (go1.27.3) and erigon/3.8.2-8a3f3b2c (go1.27.2). "
    f"In a 60-request sample 18 answers named erigon 3.8.1. The 20 reentry scenarios of the cycle 36 theme (same seed) were sent {pr['rounds']} times "
    f"through it, with a separate web3_clientVersion after every call. All {pr['agree']} of {calls} answers equal the reference interpreter's bytes "
    f"({pr['differ']} differ, {pr['noAnswer']} unanswered). The rotation samples taken between the calls named an erigon 3.8 build {eri_n} times out of {tot} "
    f"({rot_txt}). No answer can be tied to one backend. A batch is split per element, and erigon and geth return the same error texts, block context "
    f"defaults, block override handling and override validation, so nothing in an answer marks it as erigon's. At an erigon 3.8 share of {share:.2f}, "
    f"the chance that none of the {calls} calls reached an erigon 3.8 backend is about {p_none:.0e}. It is still a statistical result for the set, not a "
    f"per-scenario one. ethereum-mainnet.gateway.tatum.io still refuses eth_call on its free plan. rpcfree.com says its own RPC is paused."
)

doc = {
    "unit": "ethereum-reference",
    "_lenses": ["L1", "L2", "L3", "L6"],
    "profiles": [
        {"chainId": 1, "lens": "L1",
         "summary": "No opcode result on any Ethereum build reached on 2026-11-27 differs from the specification. New this cycle: holiman/uint256 master moved to 908714a0, which changes only ExpMod, a routine no client's opcode handlers call. Erigon builds 3.8.1 and 3.8.2, which carry the per-frame SLOAD cache, answer behind the pocket gateway, and the PoolManager reentry scenarios sent through it all return the reference bytes.",
         "deltas": [
             {"delta": "holiman/uint256 master is now 908714a05a47 (2026-11-27 20:57 UTC; cycle 35 read de2a038). Against de2a038, div.go, mod.go, conversion.go and decimal.go are byte equal. uint256.go adds usquare, a 512 bit square with ten word multiplications, and rewrites ExpMod: a uint64 modulus loop with bits.Rem64, a short-exponent loop through MulMod, and for other moduli below 2^192 a modulus shifted left to four words so reduce4 serves every step, with a final Mod by the real modulus. usquare is called only inside ExpMod. No client pins this commit: erigon main pins 808a9d02b85f, erigon release/3.8 pins 087f4b32f234, geth master pins v1.3.2. ExpMod serves no opcode handler; erigon main's MODEXP precompile has its own loop on MulModWithReciprocal and geth's uses a patched math/big.",
              "source": "https://proxy.golang.org/github.com/holiman/uint256/@v/master.info ; https://proxy.golang.org/github.com/holiman/uint256/@v/v1.3.3-0.20261127205719-908714a05a47.zip (uint256.go 479-510, 1395-1494) ; https://raw.githubusercontent.com/erigontech/erigon/main/go.mod (line 66) ; https://raw.githubusercontent.com/erigontech/erigon/release/3.8/go.mod (line 62) ; https://raw.githubusercontent.com/ethereum/go-ethereum/master/go.mod (line 43) ; https://raw.githubusercontent.com/erigontech/erigon/main/execution/vm/contracts.go (lines 585-670) ; https://raw.githubusercontent.com/ethereum/go-ethereum/master/core/vm/contracts.go (line 33)",
              "relevance": "none"},
             {"delta": "The pocket gateway rotates requests, batch elements one by one, over erigon/3.8.1-cf6f1413 and erigon/3.8.2-8a3f3b2c besides reth v2.11.0, reth v2.10.1 and Geth v1.17.9. This is the first public path found on which eth_call reaches an erigon build with the frame cache. erigon v3.8.1's interpreter.go, instructions.go, journal.go and transient_storage.go are byte equal to v3.8.2's. Its read_paths.go and intra_block_state.go lack v3.8.2's parallel-executor fixes: a self-destruct read from the version map is an earlier transaction's, a re-probe after a flush, and EIP-161 removal of touched empty accounts in the parallel write set. The v3.8.2 notes say these fix valid blocks rejected by parallel execution and a rare race that could validate a stale balance, nonce or code hash.",
              "source": SRC_POCKET + " ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.1/execution/vm/interpreter.go ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.1/execution/state/read_paths.go ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.1/execution/state/intra_block_state.go ; https://github.com/erigontech/erigon/releases/tag/v3.8.2",
              "relevance": "low"},
             {"delta": "No other client release since cycle 35. erigon main's vm and state files are byte equal to the copies of cycles 35 and 36, and tags v3.8.3, v3.9.0 and v3.9.0-rc.1 and branch release/3.9 return 404. geth master's interpreter files equal cycle 29's copy and v1.17.10 is still the newest tag. reth main reads 2.11.0 with evm2 e80df9c4, and tags v2.11.1, v2.12.0 and v2.12.0-rc.1 return 404. ruint is 1.21.1, revm 43.0.3. Nethermind's newest image is 2.3.0-rc (2026-11-23), master reads 2.4.0-preview and pins Int256 1.15.0, the newest Int256 on nuget.",
              "source": "https://raw.githubusercontent.com/erigontech/erigon/main/execution/vm/instructions.go ; https://raw.githubusercontent.com/erigontech/erigon/main/db/version/app.go (lines 33-36) ; https://raw.githubusercontent.com/ethereum/go-ethereum/master/version/version.go ; https://proxy.golang.org/github.com/ethereum/go-ethereum/@v/list ; https://raw.githubusercontent.com/paradigmxyz/reth/main/Cargo.toml (lines 2, 451-454) ; https://crates.io/api/v1/crates/ruint ; https://crates.io/api/v1/crates/revm ; https://hub.docker.com/v2/repositories/nethermind/nethermind/tags ; https://raw.githubusercontent.com/NethermindEth/nethermind/master/Directory.Build.props ; https://api.nuget.org/v3-flatcontainer/nethermind.numerics.int256/index.json",
              "relevance": "none"},
         ]},
        {"chainId": 1, "lens": "L2",
         "summary": "Nothing new on transient storage or transaction boundaries. The frame cache of erigon 3.8.1 and 3.8.2 now ran behind a live endpoint on PoolManager reentry, statistically, with no stale read visible in any answer.",
         "deltas": []},
        {"chainId": 1, "lens": "L3",
         "summary": "No change to the native asset, gas, or the block gas limit (60,000,000 by GASLIMIT in eth_call on five endpoints). eth_call defaults (gas 49,978,998 left at the first opcode, BASEFEE and GASPRICE 0, ORIGIN and CALLER zero) are the same on erigon 3.6 to 3.7, Geth v1.17.5 and v1.17.10 and reth v2.11.0.",
         "deltas": []},
        {"chainId": 1, "lens": "L6",
         "summary": "Nothing new on forks. eth_config still shows fork id 0x07c9462e and no next fork. EIP-7773, 7778, 8024, 8037, 8038, 8081 and 8141 are byte equal to cycle 35's copies, and ethereum.org still says 'Mainnet date not yet set' for Glamsterdam.",
         "deltas": []},
    ],
    "findings": [],
    "cleared": [
        {"chainIds": [1], "lens": "L1",
         "check": "battery.py, targeted.py, pmdiff.py (250 scripts), pmdiff2.py (300 scripts), swaps.py and replay.py rerun for chain 1 on ethereum-rpc.publicnode.com (reth v2.11.0-b9abbcc).",
         "result": f"99,985 battery and 85,544 targeted vectors match. The 250 and 300 script reference hashes equal cycle 35's one for one. 39,761 mined swaps from block 26,508,600 onward give the exact tick from the source's math (39,757 exact, 4 on a boundary, 0 mismatches), and of 36,117 paired swaps 33,377 match a single-step formula to the unit, 2,733 took several steps and 7 crossed liquidity. All 32 sampled multi-step and other swaps replay to the unit. The math these exercise is FullMath.mulDiv (src/libraries/FullMath.sol:24), getTickAtSqrtPrice and the swap loop.",
         "source": f"{WR}/out/battery-eth.json, targeted-eth.json, pmdiff-eth.json, pmdiff2-eth.json, swaps-eth.json, replay-eth.json ; rpc: eth_call, eth_getLogs and eth_getStorageAt on https://ethereum-rpc.publicnode.com, 2026-11-27"},
        {"chainIds": [1], "lens": "L1",
         "check": "L-1317: the 20 reentry scenarios of cycle 36 (hook reentry from beforeSwap, beforeAddLiquidity, beforeRemoveLiquidity and beforeDonate, around src/PoolManager.sol:196-206 and src/libraries/TickBitmap.sol:73) sent through the pocket gateway, which rotates over erigon 3.8.1 and 3.8.2 builds that carry the frame cache.",
         "result": f"{pr['agree']} of {calls} answers equal the reference interpreter's bytes; none differs. Between the calls, {eri_n} of {tot} clientVersion samples named an erigon 3.8 build. A stale slot0 or bitmap word on an erigon backend would have changed the returned deltas and the extsload record. The result holds for the set, not for each scenario on erigon, because no answer can be tied to a backend.",
         "source": SRC_POCKET},
        {"chainIds": [1], "lens": "L1",
         "check": "The same 20 scenarios on six other endpoints whose backends are hidden or are older erigon: eth.drpc.org, eth.api.pocket.network (one pass), ethereum-rpc.blockreq.com (erpc), rpc-eth.blockmachine.io, rpc.swiftnodes.io (erigon 3.6.0) and api.blockvectra.com (erigon 3.7.0).",
         "result": f"{gw_agree} of {gw_agree + gw_diff + gw_none} answers equal the reference ({gw_diff} differ, {gw_none} unanswered).",
         "source": f"{WR}/out/rpcshapes-gateways.json ; rpc: eth_call with state overrides on the six endpoints, 2026-11-27"},
        {"chainIds": [1], "lens": "L1",
         "check": "Can an eth_call answer be tied to the client that ran it on a rotating gateway? Six error probes (INVALID, REVERT with data, out of gas, bad jump, stack underflow, intrinsic gas), twelve block-context opcodes with gas, from and gasPrice omitted, a block override as fourth parameter, and eleven state override shapes, on erigon 3.6.0, 3.7.0 and 3.7.1, Geth v1.17.5 and v1.17.10 and reth v2.11.0.",
         "result": "reth differs from both Go clients in error texts and in rejecting an unknown override field. Erigon and geth differ only in the text for intrinsic gas too low, which is not an execution answer. Every value a contract can read, and every override rule, is the same. So an eth_call answer from a gateway cannot be tied to erigon. Batches are split per element on the pocket gateway, so bracketing inside a batch does not work either.",
         "source": f"{WR}/out/fingerprint-known.json, ctxprobe-known.json, ovprobe-known.json ; {WR}/scripts/fingerprint.py, ctxprobe.py, ovprobe.py ; rpc: eth_call on https://eth.blocktailor.com, https://rpc.swiftnodes.io/rpc/eth, https://api.blockvectra.com/v1/eth_mainnet/public, https://public-eth.nownodes.io, https://ethereum-rpc.publicnode.com, https://eth.blockrazor.xyz, 2026-11-27"},
        {"chainIds": [1], "lens": "L1",
         "check": "uint256 master 908714a0: does its change reach a value the PoolManager computes?",
         "result": "No. Only ExpMod and the new usquare change; Div, Mod, SDiv, SMod, MulMod, MulModWithReciprocal, AddMod, the shifts, Exp, reduce4 and Reciprocal are byte equal to de2a038. ExpMod backs no opcode. The PoolManager's only route to MODEXP (0x05) is a take naming it as recipient or currency (P1, P2). P1 sends empty input, which gives an empty result with no exponentiation, and P2's 68 byte transfer call reads as lengths far above the EIP-7823 cap and fails. No client pins the commit. A Go harness to run ExpMod against math/big was refused in this session, so the routine itself was read, not run.",
         "source": "https://proxy.golang.org/github.com/holiman/uint256/@v/v1.3.3-0.20261127205719-908714a05a47.zip ; src/types/Currency.sol:44-80 ; src/PoolManager.sol:291-297 ; https://raw.githubusercontent.com/erigontech/erigon/main/execution/vm/contracts.go"},
        {"chainIds": [1], "lens": "L1",
         "check": "erigon v3.8.1, served behind the pocket gateway: does it run the same frame cache, journal and stamp as v3.8.2, which cycle 36 modelled, and do its parallel-executor differences meet eth_call?",
         "result": "interpreter.go, instructions.go, journal.go and transient_storage.go are byte equal to v3.8.2's, so cycle 36's model of the cache covers v3.8.1. read_paths.go and intra_block_state.go differ only in version map paths of the parallel block executor. eth_call runs one message on a serial state, so those paths do not serve it. On a node that executes blocks in parallel, the faults v3.8.2 fixed end in a rejected valid block or a different state root, which is a fault of that node and not a transfer an account can direct.",
         "source": "https://raw.githubusercontent.com/erigontech/erigon/v3.8.1/execution/vm/interpreter.go ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.1/execution/state/read_paths.go ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.1/execution/state/intra_block_state.go ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/execution/state/read_paths.go ; https://github.com/erigontech/erigon/releases/tag/v3.8.2"},
        {"chainIds": [1], "lens": "L6",
         "check": "Upcoming forks within six months, assumed shipped: Glamsterdam with the 20 EIPs that EIP-7773 schedules, and Hegota (EIP-8081), against what cycles 14 to 35 cleared.",
         "result": "EIP-7773, 7778, 8024, 8037, 8038, 8081 and 8141 are byte equal to cycle 35's copies, eth_config equals cycle 35's object (fork id 0x07c9462e, no next fork), and ethereum.org says 'Testing on testnets, Mainnet date not yet set'. The earlier clearances stand: the new opcodes are absent from the decoded bytecode, src never branches on gas (src/types/Currency.sol:48 and :73, src/libraries/Hooks.sol:134), and native settle credits msg.value only (src/PoolManager.sol:352-354), so ETH credited outside a call is booked to no one. Erigon v3.8.x and main already carry the Amsterdam paths next to the frame cache. On the day after the fork the client mix will include them.",
         "source": f"https://raw.githubusercontent.com/ethereum/EIPs/master/EIPS/eip-7773.md ; https://raw.githubusercontent.com/ethereum/EIPs/master/EIPS/eip-8081.md ; https://ethereum.org/roadmap/glamsterdam/ ; rpc: eth_config on https://ethereum-rpc.publicnode.com, 2026-11-27 ({WR}/out/eth_config.json)"},
    ],
    "leads": [
        {"chainIds": [1], "lens": "L1",
         "question": "Can the 20 reentry scenarios be tied one by one to the erigon 3.8.1 and 3.8.2 backends of the pocket gateway, through a session or sticky routing option of that gateway or a provider that names its erigon 3.8 endpoint, and do they return the reference bytes there?",
         "why": "This cycle's result for the frame cache on a live node is statistical over the set. A per-scenario answer would close F-165's live test.",
         "priority": "low"},
        {"chainIds": [1], "lens": "L1",
         "question": "When a client pins holiman/uint256 908714a0 or later, run its ExpMod (the usquare and shifted-modulus paths) against math/big on mixed modulus widths and confirm that no opcode handler calls it.",
         "why": "The routine is new today and was read, not run, because a Go harness was refused in this session. It matters only if a client routes MODEXP or an opcode through it.",
         "priority": "low"},
    ],
    "leadResults": [
        {"leadId": "L-1317", "outcome": "inconclusive", "answer": pocket_answer},
        {"leadId": "L-1285", "outcome": "inconclusive",
         "answer": "There is still no erigon v3.9.0 tag, rc tag or release/3.9 branch on 2026-11-27 (raw.githubusercontent.com 404). main is 3.9.0-dev, pins uint256 808a9d02b85f, and its execution/vm and execution/state files are byte equal to the copies of cycles 35 and 36. So the rerun of build/herigon and scripts/erigon_fastpaths.py would test the same code. uint256 master moved to 908714a0 today, changing only ExpMod. A 3.9.0 release that pins it inherits no change on the opcode paths. The rerun steps stand for the day 3.9.0 is tagged."},
    ],
}
json.dump(doc, open(OUTF, 'w'), indent=1)
print('wrote', OUTF, 'calls', calls, 'agree', pr['agree'], 'erigon share', share, 'p_none', p_none)
