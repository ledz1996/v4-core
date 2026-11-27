"""Build cycles/032/established-l1.research.json from the outputs in this work directory. Read-only apart from the output file."""
import json, os
W = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(W, '..', 'established-l1.research.json')
R = lambda p: json.load(open(os.path.join(W, p)))
av = R('avax/raw/43114/result.json'); av30 = R('avax/raw/43114/result-c30.json')
mm = av.get('mismatchKinds', {})
WD = 'research/network-risk/cycles/032/established-l1.work/'
BOR = 'https://raw.githubusercontent.com/0xPolygon/bor/develop/'
BSC = 'https://raw.githubusercontent.com/bnb-chain/bsc/develop/'
U256 = 'https://raw.githubusercontent.com/holiman/uint256/v1.3.2/uint256.go'
PN = 'https://polygon-bor-rpc.publicnode.com'
DS = 'https://bsc-dataseed1.bnbchain.org'
RB = 'https://bsc-rpc.publicnode.com'
AX = 'https://api.avax.network/ext/bc/C/rpc'

new_av = av['txs'] - av30['txs']
av_sentence = ('The Avalanche replay window (blocks %d to %d, 20,000 transactions) now has %d traced transactions, %d more than in cycle 30, '
               'because avax.api.pocket.network now serves debug_traceTransaction from its avalanchego 1.15.3 and 1.15.2 backends for most requests. '
               '%d transactions differ from the source model in at least one word (%s); all are a one-unit gap between the Transfer log and the balance change of an interest-bearing Aave token (avDAI 0x47afa96c, seen since cycle 23, and aAvaAAVE 0xf329e36c and aAvaSAVAX 0x513c7e3a, new), where settle credits the measured balance change, so they are token rounding and not an EVM difference. 11 window transactions still have no trace.'
               % (av['blocks'][0], av['blocks'][1], av['txs'], new_av, av['txWithMismatch'], ', '.join('%s %d' % kv for kv in mm.items()) or 'none'))

profiles = [
    {"chainId": 137, "lens": "L1", "summary": "bor develop is byte equal to the cycle 28 copies in every interpreter file read (instructions, evm, interpreter, jump_table, eips, memory, stack, contract, analysis_legacy, keccak_cache, shared_cache, mulmod_memo) and in params/config.go and go.mod, which pins holiman/uint256 v1.3.2. No tag newer than v2.11.2 exists. The rotating private v2.11.1 builds behind publicnode return the specified word on all 185,529 vectors, the 23 scenarios and the three borrow scripts.",
     "deltas": [
         {"delta": "The MULMOD memo on develop (core/vm/mulmod_memo.go, unchanged since cycle 12) calls MulModWithReciprocal with the reciprocal of the exact modulus it keys on. In uint256 v1.3.2, MulMod (uint256.go:720-748) and MulModWithReciprocal (uint256.go:688-718) take the same steps for a full-width modulus and differ only in computing Reciprocal(m) on the spot, so a build that ships the memo returns the same word as one that does not for every operand triple.", "source": U256, "relevance": "none"},
         {"delta": "bor develop go.mod now names go 1.26.11 as the language version while every publicnode build reports go1.26.10.", "source": BOR + "go.mod", "relevance": "none"}]},
    {"chainId": 137, "lens": "L2", "summary": "The 23 multi-transaction scenarios of cycle 28 (137 calls in one simulated block, transient storage cleared between transactions) ran on Polygon for the first time and every call equals the reference. All 23 multi-step mined swaps of the new window (blocks 98,030,093 to 98,042,092) replay to the unit from parent-block state read on QuikNode.",
     "deltas": []},
    {"chainId": 137, "lens": "L4", "summary": "The five Salvador targets were given their BlockAlloc code by state override and called in the shapes the PoolManager uses. A native payment with empty calldata reverts, so a take of native POL to such an address fails after the fork, and none of the five holds an ERC-6909 balance of native POL or WPOL in the PoolManager today.",
     "deltas": [
         {"delta": "Salvador writes the same 344-byte Sweeper runtime at all five targets. It has two functions, sweep() (0x35faa416), which any caller may run and which sends the account's own balance to a recovery address fixed in the code (0x4df68703...26eedc for four targets, 0xd9fd3910...610b80 for 0x5227f603), and a getter (0x78ed5d81) for that address. Every other call, including a plain value transfer, reverts, and sweep() refuses value. The five accounts hold about 15.3 million, 4.3 million, 4.2 million, 3.05 and 46.6 million POL at block 98,042,343.", "source": WD + "out/salvador_targets.json (eth_call with code override on " + PN + ")", "relevance": "low"}]},
    {"chainId": 137, "lens": "L6", "summary": "Salvador at block 98,688,600 falls at about 2026-12-08 14:00 UTC (head 98,042,343 at 08:43:12 UTC on 2026-11-27, 1.50004 s per block over the last 200,000 blocks). No tagged release carries it eleven days before activation.",
     "deltas": [
         {"delta": "eth_config on every publicnode build returns the same forkId 0x22d523b2 with activationBlock 15 and no current or last entry, so the method does not expose bor's block-numbered forks and cannot show whether a build carries Salvador.", "source": WD + "out/ethconfig-1.json (eth_config on " + PN + ")", "relevance": "none"}]},
    {"chainId": 56, "lens": "L1", "summary": "bsc develop core/vm instructions, evm, interpreter, jump_table, eips and contracts are byte equal to the cycle 28 and cycle 31 copies, v1.8.2 is still the newest tag and uint256 stays at v1.3.2. dataseed1 (Geth v1.8.2, go1.26.10) and reth-bsc v0.1.4-hotfix-23b510f on publicnode return the specified word on all 185,529 vectors.",
     "deltas": [
         {"delta": "BNB Chain's public endpoints answer from four build strings at once: dataseed2 and defibit report v1.8.2-4e1c8247-20261104 with go1.26.10, dataseed1, 3, 4 and ninicoin report v1.8.2 with go1.26.10 and no commit, the pocket gateway reports v1.8.2-54afaff4-20261103 with go1.25.14 (the release asset) and still v1.7.8 with go1.25.12, and rpc-bsc.48.club reports v1.8.2-9b93ce23 and v1.8.2-132104cd built with go1.25.5.", "source": WD + "out/bsc_dataseed_versions.txt and out/l1215_bsc.txt (web3_clientVersion on bsc-dataseed1..4.bnbchain.org, bsc-dataseed1.defibit.io, bsc-dataseed1.ninicoin.io, bsc.api.pocket.network, rpc-bsc.48.club)", "relevance": "low"}]},
    {"chainId": 56, "lens": "L2", "summary": "The 23 scenarios ran on BNB Chain for the first time: 137 of 137 calls equal the reference on dataseed1, on reth-bsc and on dataseed1 under a block time past Jenner. The 25 multi-step mined swaps of blocks 136,005,768 to 136,007,767 replay to the unit.",
     "deltas": []},
    {"chainId": 56, "lens": "L4", "summary": "A block time override of 1,796,697,100 switches the Jenner rules on in dataseed1's eth_simulateV1: a STATICCALL to 0x70 returns 32 bytes holding 1,796,697,100,000 milliseconds, while without the override it returns success with no data. Under that override every scenario call still equals the reference.",
     "deltas": [
         {"delta": "The v1.8.2 changelog lists BEP-703 Payment Lane next to BEP-702 CAS20 and BEP-706: from Jenner 5 percent of block gas is reserved by default for eligible BNB transfers and calls to governance-listed payment contracts. It changes which transactions a validator includes, and no PoolManager line reads block gas.", "source": BSC + "CHANGELOG.md", "relevance": "none"}]},
    {"chainId": 56, "lens": "L6", "summary": "Jenner stays at 1796697000 (2026-12-08 02:30 UTC) in develop params/config.go and the v1.8.2 changelog calls the upgrade mandatory for every mainnet operator. No BSC fork after Jenner has a time.",
     "deltas": [
         {"delta": "The pocket gateway still routes some BNB Chain requests to a Geth v1.7.8 backend. That release has no Jenner support, so after 02:30 UTC on 8 December such a backend would follow a chain without Jenner and answer from it unless it is upgraded or removed.", "source": WD + "out/l1215_bsc.txt (web3_clientVersion on https://bsc.api.pocket.network)", "relevance": "low"}]},
    {"chainId": 43114, "lens": "L1", "summary": "avalanchego 1.15.3 (983815fd) answers on api.avax.network and publicnode and returns the specified word on all 185,529 vectors, the 23 scenarios and the three borrow scripts. master now pins libevm a335c2ecf4df, which the unreleased 1.15.4 will carry.",
     "deltas": [
         {"delta": "Between libevm d398bc4dbe41 (pinned by 1.15.3) and a335c2ecf4df (pinned by master) the core/vm files instructions, interpreter, evm, jump_table, analysis, memory, stack, eips, contracts, gas_table, operations_acl and contract and the core/state files statedb, state_object, journal and transient_storage are byte equal. The only interpreter-side change removes the Raw caller and self addresses from the context a stateful precompile receives (core/vm/contracts.libevm.go, environment.libevm.go, libevm/libevm.go). uint256 stays at v1.2.4.", "source": "https://raw.githubusercontent.com/ava-labs/libevm/a335c2ecf4df/libevm/libevm.go", "relevance": "none"},
         {"delta": "The unreleased 1.15.4 notes on master list a minimum tip of 1 wei for non-local C-Chain transactions, a disabled local transaction journal, shutdown fixes and new RPC headers; none touches execution.", "source": "https://raw.githubusercontent.com/ava-labs/avalanchego/master/RELEASES.md", "relevance": "none"}]},
    {"chainId": 43114, "lens": "L2", "summary": av_sentence,
     "deltas": [
         {"delta": "avax.api.pocket.network now answers debug_traceTransaction with callTracer and muxTracer for most requests, from both its 1.15.3 and its 1.15.2 backends; no other public Avalanche endpoint tried serves it without a key.", "source": WD + "out/l1215_avax.txt", "relevance": "none"}]},
    {"chainId": 43114, "lens": "L4", "summary": "Nothing new. The libevm change on master narrows what a stateful precompile sees of its callers, and the PoolManager calls no Avalanche stateful precompile.",
     "deltas": []},
    {"chainId": 43114, "lens": "L6", "summary": "Igloo is still UnscheduledActivationTime on mainnet and Fuji in master upgrade/upgrade.go, and Helicon (2026-09-22) is the newest active upgrade. No Avalanche fork is scheduled in the next six months.",
     "deltas": []},
]

findings = [
    {"ref": "F-134",
     "title": "After Salvador the five rewritten Polygon accounts refuse native payments, so a take of native POL to them reverts",
     "chainIds": [137], "lens": "L4", "assumptions": ["A3", "A7"], "effect": "freeze", "actor": "governance", "severity": "low",
     "difference": "Polygon's Salvador hardfork writes a 344-byte Sweeper runtime into five accounts at block 98,688,600 through BlockAlloc in block finalisation, a code change that Ethereum has no mechanism for.",
     "mechanism": "Each target was given its BlockAlloc code by state override and called from the PoolManager address in the shapes Currency.transfer uses. A native payment with empty calldata, which is what Currency.transfer sends for native POL, reverts, because the runtime has only sweep() and a getter and no payable fallback. sweep() itself refuses value. So after the fork, take, or the native leg of any router payout, that names one of the five accounts as recipient reverts with NativeTransferFailed and the whole unlock reverts. Any caller may run sweep(), but it moves only the account's own POL to the recovery address in the code and does not touch the PoolManager.",
     "impact": "Only payments addressed to the five accounts fail. None of them holds an ERC-6909 claim on native POL or WPOL in the PoolManager at block 98,042,343, so no claim already inside the PoolManager is stranded. Funds of other users are not affected.",
     "preconditions": "Polygon governance ships and activates Salvador with this table. An ordinary account cannot add an address to BlockAlloc.",
     "mitigations": "Routers and integrators should not name the five accounts as recipients after block 98,688,600. The deployer needs no change.",
     "coreRefs": ["src/types/Currency.sol:40-52", "src/PoolManager.sol:291-298"],
     "sources": [{"url": BOR + "params/config.go", "supports": "SalvadorBlock 98,688,600 and the five BlockAlloc entries with the Sweeper runtime"},
                 {"url": WD + "out/salvador_targets.json (eth_call with code override on " + PN + ")", "supports": "native payment with empty calldata reverts, sweep() refuses value, stranger can call sweep(), recovery addresses"},
                 {"url": WD + "out/salvador_6909.txt (eth_call balanceOf on " + PN + ")", "supports": "no ERC-6909 balance of native POL or WPOL for the five accounts"}],
     "evidence": "primary"},
]

cleared = [
    {"chainIds": [137, 56, 43114], "lens": "L1", "check": "battery.py (99,985 vectors) and targeted.py (85,544 vectors) on the networks.json endpoints on 2026-11-27, and both again on reth-bsc v0.1.4-hotfix-23b510f at bsc-rpc.publicnode.com.",
     "result": "No mismatch and no error on any of the 185,529 vectors on Polygon, BNB Chain (dataseed1 and reth-bsc) and Avalanche.", "source": WD + "out/battery.log, out/targeted.log, out/battery-bsc-reth.log, out/targeted-bsc-reth.log"},
    {"chainIds": [137, 56, 43114], "lens": "L1", "check": "Script set 1 (pmdiff.py, 250 scripts) and script set 2 (pmdiff2.py, 300 scripts) with the deployed PoolManager bytecode.",
     "result": "BNB Chain and Avalanche are identical to the reference on all 550 scripts. Polygon differs on the same 19 and 20 gas-limited scripts as in cycle 30, by script number.", "source": WD + "out/pmdiff.log, out/pmdiff2.log"},
    {"chainIds": [137, 56, 43114], "lens": "L2", "check": "The 23 multi-transaction scenarios of cycle 28 (scen_rpc.py, 137 calls in one eth_simulateV1 block with state carried and transient storage cleared between transactions), never run on these networks before.",
     "result": "137 of 137 calls equal the reference on Polygon publicnode, BNB Chain dataseed1, reth-bsc (with a 50 million block gas budget, which that endpoint needs) and Avalanche.", "source": WD + "out/scen-pol.log, out/scen-bsc.log, out/scen-bsc-reth.log, out/scen-avax.log"},
    {"chainIds": [56], "lens": "L4", "check": "The 23 scenarios under Jenner rules: eth_simulateV1 on dataseed1 with block time 1,796,697,100, after checking that this override turns on the BEP-706 precompile at 0x70.",
     "result": "0x70 returns 1,796,697,100,000 under the override and empty data without it, so the Jenner rules were active. All 137 calls equal the reference.", "source": WD + "out/jenner_probe.txt and out/scen-bsc-jenner.log"},
    {"chainIds": [137, 56, 43114], "lens": "L1", "check": "The three getFeeGrowthInside borrow scripts (below range, above range, in range wrap) with each network's own PoolManager bytecode, never run on these networks before.",
     "result": "All three equal the reference on Polygon publicnode (three different private builds answered), dataseed1, reth-bsc and api.avax.network.", "source": WD + "out/borrow-137.log, out/borrow-56.log, out/borrow-43114.log; src/libraries/Pool.sol:497-509"},
    {"chainIds": [137, 56, 43114], "lens": "L3", "check": "swaps.py on the newest 2,000 blocks of each network and replay.py on the multi-step samples (Polygon parent state from QuikNode).",
     "result": "Polygon 5,811 swaps, BNB Chain 6,068 and Avalanche 47 all pass the tick relation, every pair is classified with no 'other', and 23 Polygon and 25 BNB Chain multi-step swaps replay to the unit.", "source": WD + "out/swaps.log, out/replay.log, out/replay-pol.log"},
    {"chainIds": [43114], "lens": "L2", "check": "The rest of the Avalanche replay window of cycle 25 traced on avax.api.pocket.network and replayed through the cycle 23 source model.",
     "result": av_sentence, "source": WD + "avax/raw/43114/result.json"},
    {"chainIds": [137], "lens": "L1", "check": "Whether the MULMOD memo on bor develop can return another word than stock MULMOD for any operands, read against holiman/uint256 v1.3.2.",
     "result": "No. The memo keys on the whole modulus and only replaces Reciprocal(m) with a stored copy of Reciprocal of the same m; MulMod and MulModWithReciprocal then run the same umul and reduce4 path (uint256.go:688-748), and moduli with a zero top word bypass it. FullMath.sol:24, :48 and :112 and SqrtPriceMath.sol:252 would get the same words.", "source": U256},
    {"chainIds": [137], "lens": "L1", "check": "bor develop core/vm and params files against the cycle 28 copies.",
     "result": "instructions, evm, interpreter, jump_table, eips, memory, stack, contract, analysis_legacy, keccak_cache, shared_cache, mulmod_memo, params/config.go and go.mod are byte equal by sha256.", "source": BOR + "core/vm/instructions.go"},
    {"chainIds": [56], "lens": "L1", "check": "bsc develop core/vm files against the cycle 28 and cycle 31 copies, and the uint256 pin.",
     "result": "instructions, evm, eips, jump_table and contracts are byte equal; interpreter equals the cycle 28 develop copy. go.mod pins holiman/uint256 v1.3.2.", "source": BSC + "core/vm/instructions.go"},
    {"chainIds": [43114], "lens": "L1", "check": "The libevm commit a335c2ecf4df that avalanchego master pins for the next release, against d398bc4dbe41 pinned by 1.15.3.",
     "result": "Sixteen core/vm and core/state files are byte equal. The one change removes the Raw address pair from the context given to stateful precompiles, a field that no longer exists in the type, so no remaining code can read it; the PoolManager never calls a stateful precompile.", "source": "https://raw.githubusercontent.com/ava-labs/libevm/a335c2ecf4df/core/vm/contracts.libevm.go"},
    {"chainIds": [137], "lens": "L4", "check": "The Salvador Sweeper runtime run by code override against the calls the PoolManager can make to an address (native payment from the PoolManager, sweep() with value, sweep() by a stranger, getter).",
     "result": "Native payments revert and sweep() moves only the account's own balance to its fixed recovery address; the five accounts hold no ERC-6909 native POL or WPOL claims. Recorded under F-134 at governance level.", "source": WD + "out/salvador_targets.json"},
    {"chainIds": [43114], "lens": "L6", "check": "Avalanche forks in the next six months.",
     "result": "Igloo is UnscheduledActivationTime on mainnet and Fuji in master upgrade/upgrade.go; nothing else is scheduled.", "source": "https://raw.githubusercontent.com/ava-labs/avalanchego/master/upgrade/upgrade.go"},
]

leads = [
    {"chainIds": [137], "lens": "L1", "question": "Once the bor release that carries Salvador is tagged, does its core/vm match develop (MULMOD memo, widened keccak cache), and do the battery, targeted set, scenarios and borrow scripts still match on publicnode after block 98,688,600?",
     "why": "The release that activates Salvador is not yet published, and the fork lands about 2026-12-08 14:00 UTC.", "priority": "medium"},
    {"chainIds": [56], "lens": "L6", "question": "After Jenner (2026-12-08 02:30 UTC), does bsc.api.pocket.network still route requests to its Geth v1.7.8 backend, and does that backend then answer from a chain without Jenner?",
     "why": "Integrators reading state or simulating through the gateway could see a pre-Jenner chain for CAS20 addresses and 0x70.", "priority": "low"},
]

leadResults = [
    {"leadId": "L-1191", "outcome": "inconclusive",
     "answer": "Still not visible from outside. eth_config on all five private builds returns one forkId (0x22d523b2) with no bor block forks, so it cannot show Salvador, and debug_chainConfig needs a token on publicnode. The memo question no longer matters for correctness: with uint256 v1.3.2 the memo path and stock MulMod give the same word for every operand triple (uint256.go:688-748), and the battery's MULMOD records already run many full-width moduli in one EVM instance. Salvador's only effect, the Sweeper code at five accounts, was run by code override against the PoolManager's call shapes and recorded under F-134."},
    {"leadId": "L-1215", "outcome": "inconclusive",
     "answer": "For Avalanche the lead is closed by the same provider: avax.api.pocket.network now traces from most of its 1.15.3 and 1.15.2 backends, and the rest of the window has now been traced and replayed. %s Publicnode, drpc (free plan timeout), onfinality (rate limit), 1rpc (method not allowed), blockpi, ankr and nodies (keys or paid plans) serve no trace. For BNB Chain no endpoint serves historical traces: both pocket backends (v1.8.2-54afaff4 and v1.7.8) refuse with 'required historical state unavailable (reexec=128)', publicnode reth-bsc needs a token for archive calls, drpc rate-limits and did not find the transaction, NodeReal-backed dataseed and the 48 Club endpoint do not offer the method." % av_sentence},
    {"leadId": "L-1220", "outcome": "inconclusive",
     "answer": "Validator builds are not published and no RPC method reveals them; this is an operator-level question. What the public endpoints show on 2026-11-27: dataseed2 and defibit answer v1.8.2-4e1c8247-20261104 with go1.26.10, the other dataseeds answer v1.8.2 with go1.26.10 and no commit, pocket answers the release asset v1.8.2-54afaff4-20261103 with go1.25.14 and also v1.7.8, and 48 Club answers two unpublished commits built with go1.25.5. The battery, targeted set, scenarios and borrow scripts match on every one reached."},
]

doc = {"unit": "established-l1", "_lenses": ["L1", "L2", "L4", "L6"], "profiles": profiles, "findings": findings,
       "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(doc, open(OUT, 'w'), indent=1)
print('wrote', OUT)
