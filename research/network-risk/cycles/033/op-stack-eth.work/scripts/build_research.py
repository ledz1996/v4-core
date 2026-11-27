import json, os
R = "/home/user/v4-core/research/network-risk"
W = "research/network-risk/cycles/033/op-stack-eth.work"
WA = f"{R}/cycles/033/op-stack-eth.work"
OUT = f"{R}/cycles/033/op-stack-eth.research.json"
CH = [10, 8453, 130, 7777777, 480, 57073, 1868]
LOGS = f"file:{W}/out/battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.log, clientver.txt"
build = {10: "op-reth/v2.8.1-72207294 and op-reth/v0.0.0-dev-unknown", 8453: "reth/v2.5.2-9e380dd/base/v1.5.6",
         130: "op-reth/v2.10.0-rc.4-65e80332", 7777777: "conduit-op-reth/v2.5.1-8f0ccac", 480: "world-chain/v2.8.2-9596311",
         57073: "op-reth/v2.10.0-rc.4-65e80332 (rpc-gel) and op-reth/v0.0.0-dev-unknown (rpc-qnd)", 1868: "op-reth/v2.10.0-rc.4-65e80332"}
# swaps.log and replay.log of this cycle: (swaps, boundary, pairs, single step exact, multi, other, replayed, maxSteps)
sw = {10: (2424, 19, 989, 986, 3, 0, 3, 2), 8453: (2443, 0, 1420, 1295, 125, 0, 25, 12), 130: (6535, 0, 6250, 6176, 74, 0, 25, 3),
      7777777: (459, 0, 331, 316, 7, 8, 15, 11), 480: (121, 0, 80, 79, 1, 0, 1, 2), 57073: (2971, 0, 2425, 2405, 20, 0, 20, 2),
      1868: (467, 0, 406, 405, 1, 0, 1, 2)}
pin = json.load(open(f"{WA}/out/pin-op.json"))
pq = json.load(open(f"{WA}/out/pin-ink-qnd.json"))
l5 = json.load(open(f"{WA}/out/l5read.json"))
share = pin["versionSamples"]; v281 = share.get("op-reth/v2.8.1-72207294/x86_64-linux", 0); vdev = share.get("op-reth/v0.0.0-dev-unknown/x86_64-linux", 0)
p = v281 / (v281 + vdev); rounds = pin["rounds"]; miss = (1 - p) ** rounds; nchunks = (pin["vectorsPerRound"] + 599) // 600
pin_txt = (f"OP Mainnet's endpoint routes every request, and every item of a JSON-RPC batch, to one of its two builds on its own: a batch of "
           f"[web3_clientVersion, eth_blockNumber, web3_clientVersion] came back with v2.8.1 first and the dev build last, so no call can be tied to a build, "
           f"and a call that returns GAS, NUMBER, SELFBALANCE and BASEFEE gives the same words on both. The 185,529 battery and targeted vectors were therefore sent "
           f"{rounds} times in {nchunks} chunks of 600 ({pin['perBuild']['all']['vectors']:,} vector answers in all) with {len(pin['perBuild']['all']['mismatches'])} mismatches and {pin['perBuild']['all']['errors']} errors. "
           f"The version answers sampled in the same batches were {v281} for v2.8.1-72207294 and {vdev} for the dev build, a v2.8.1 share of {p:.2f}, "
           f"so under independent routing the chance that a given chunk never reached v2.8.1 is {miss:.3f}, about {miss * nchunks:.0f} of {nchunks} chunks. "
           f"This covers both builds for almost every vector, but it is a sampling argument, not a pin.")
ink_txt = (f"Ink's second endpoint rpc-qnd, which answers op-reth/v0.0.0-dev-unknown on all {sum(pq['versionSamples'].values())} version samples, ran the 185,529 battery and targeted vectors "
           f"once with {len(pq['perBuild']['all']['mismatches'])} mismatches. networks.json lists rpc-gel, so the main battery run covers the tagged build there.")
REG = "https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/op.toml"
LAG_DOC = "https://docs.optimism.io/op-stack/protocol/hardforks/lagoon"
SDM_DOC = "https://docs.optimism.io/op-stack/features/sdm"
LAG_OV = "https://specs.optimism.io/protocol/lagoon/overview.html"
LAG_EE = "https://specs.optimism.io/protocol/lagoon/exec-engine.html"
BASE_UP = "https://docs.base.org/upgrades/overview"
LAG = [10, 130, 57073, 1868]

profiles = []
for c in CH:
    n, b, pr, s, m, o, rp, ms = sw[c]
    d1 = [{"delta": f"Rerun on 2026-11-27 at {build[c]}, the builds cycles 29 and 31 recorded: 99,985 battery and 85,544 targeted vectors give the specified word, pmdiff set 1 gives 250 of 250 and set 2 gives 300 of 300 scripts identical to the Ethereum reference, {n:,} mined swaps satisfy the tick relation with 0 mismatches ({b} sit on a tick boundary as Pool.swap leaves them), {s:,} of {pr:,} paired swaps match one step of computeSwapStep to the unit, and {rp} of the {m + o} others were replayed through the whole swap loop with 0 failures (longest {ms} steps).", "source": LOGS, "relevance": "none"}]
    if c == 10:
        d1.append({"delta": pin_txt, "source": f"file:{W}/out/pin-op.json; file:{W}/out/pin-op.log; https://mainnet.optimism.io", "relevance": "low"})
    if c == 57073:
        d1.append({"delta": ink_txt, "source": f"file:{W}/out/pin-ink-qnd.json; https://rpc-qnd.inkonchain.com", "relevance": "none"})
    if c == 480:
        d1.append({"delta": "The 23 multi-transaction scenarios of cycle 28 ran through eth_simulateV1 on the QuickNode public endpoint listed on chainlist.org, which names world-chain/v2.8.2-9596311 before and after every scenario. All 23 equal the pyevm reference byte for byte. World Chain is now covered by every set the other six chains ran.", "source": f"file:{W}/out/scen-480-qn.log; file:{W}/out/scen-480-qn.json; https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro; https://chainlist.org/chain/480", "relevance": "none"})
    if c in LAG:
        sm = "Every vector, script and mined swap matches the specification at today's build. No client, interpreter or integer library release appeared since cycle 31."
    elif c == 8453:
        sm = "Every vector, script and mined swap matches the specification at base v1.5.6. No Base tag after v1.6.0-rc.9 exists, and the crates it pins have no newer release."
    elif c == 480:
        sm = "Every vector, script, mined swap and now all 23 multi-transaction scenarios match the specification at world-chain v2.8.2."
    else:
        sm = "Every vector, script and mined swap matches the specification at today's build, and no new client release appeared."
    if c == 10:
        sm += " Both builds behind the endpoint answered the vectors, by sampling over eight rounds."
    profiles.append({"chainId": c, "lens": "L1", "summary": sm, "deltas": d1})
    d2 = []
    if c in LAG:
        d2.append({"delta": "Lagoon adds Sequencer Defined Metering: the sequencer may append one post-exec transaction (type 0x7D) that is not executed as code and carries gas refunds per transaction index. The refund is settled inside the same transaction by crediting the sender and debiting the fee recipients. It is not user-submittable. Before Lagoon a block with such a transaction is invalid.", "source": f"{SDM_DOC}; {LAG_OV}", "relevance": "low"})
    profiles.append({"chainId": c, "lens": "L2", "summary": ("Lagoon brings Sequencer Defined Metering, which moves ETH between a transaction's sender and the fee vaults outside EVM execution; the PoolManager is neither." if c in LAG else "Nothing new on storage, transient storage or transaction boundaries since cycle 31."), "deltas": d2})
    r = l5[str(c)]
    profiles.append({"chainId": c, "lens": "L5", "summary": f"Bytecode, owner and protocol fee controller reread at block {r['block']:,}; all equal networks.json and cycle 27.",
                     "deltas": [{"delta": f"eth_getCode of the PoolManager gives {r['codeLen']:,} bytes with sha256 prefix {r['codeSha256']}; owner() is {r['owner']} with {r['ownerCodeLen']} bytes of code and protocolFeeController() is {r['protocolFeeController']} with {r['protocolFeeControllerCodeLen']} bytes, the same values networks.json records. No change since cycle 27.", "source": f"file:{W}/out/l5read.json; {r['rpc']}", "relevance": "none"}]})
    if c in LAG:
        d6 = [{"delta": "The OP docs Lagoon page (Upgrade 22) still lists OP Sepolia and Unichain Sepolia with interop and Ink Sepolia and Soneium Minato without, at 1796918401 (10 December 2026 16:00:01 UTC), and the four mainnets at 1799683201 (11 January 2027 16:00:01 UTC), subject to governance approval. The spec is marked not finalized. Its execution layer list is reduced BLS12-381 input sizes, post-execution transactions and Sequencer Defined Metering, plus the interop transaction pool.", "source": f"{LAG_DOC}; {LAG_OV}; {LAG_EE}", "relevance": "low"}]
        sm6 = "Lagoon is the only fork in the next six months; its dates are unchanged and it adds no opcode change."
    elif c == 8453:
        d6 = [{"delta": "The Base upgrades page still lists Everest (Base Transactions, EIP-8430: batching, sponsorship, token gas payments) as TBD on Base Sepolia and Base Mainnet; Denim (5 November 2026) is the last activated upgrade.", "source": BASE_UP, "relevance": "low"}]
        sm6 = "Everest still has no date, so no fork is scheduled in the next six months."
    else:
        d6 = []
        sm6 = "The superchain-registry config is byte identical to cycle 31, with no fork after Karst scheduled."
    profiles.append({"chainId": c, "lens": "L6", "summary": sm6, "deltas": d6})

cleared = [
 {"chainIds": CH, "lens": "L1", "check": "Opcode battery (99,985 vectors) and targeted set (85,544 vectors: MULMOD and mulDiv at the ruint 1.21.0 fault condition, ADDMOD at overflow, division by full width divisors, shifts at every limb boundary, SIGNEXTEND, BYTE, SAR, JUMPI condition words, KECCAK256, MCOPY overlaps, CALLDATALOAD past the end) at the builds the endpoints report on 2026-11-27.", "result": "Every vector on all seven chains returns the specified word. The 512 bit product and remainder of FullMath (src/libraries/FullMath.sol:24, 48, 112), the sign mask of TickMath (src/libraries/TickMath.sol:63), the signed division of TickBitmap (src/libraries/TickBitmap.sol:24-26, 57, 64), the byte tables of BitMath (src/libraries/BitMath.sol:22, 45) and the keccak slot of CurrencyDelta (src/libraries/CurrencyDelta.sol:14) therefore see Ethereum results.", "source": f"file:{W}/out/battery.log; file:{W}/out/targeted.log"},
 {"chainIds": [10], "lens": "L1", "check": "Both builds behind mainnet.optimism.io (op-reth v2.8.1-72207294 and the unversioned dev build) on the full vector set, which the cycle 32 critic asked for.", "result": pin_txt, "source": f"file:{W}/out/pin-op.json; https://mainnet.optimism.io"},
 {"chainIds": [57073], "lens": "L1", "check": "The unversioned op-reth build behind rpc-qnd.inkonchain.com on the full vector set.", "result": ink_txt, "source": f"file:{W}/out/pin-ink-qnd.json"},
 {"chainIds": CH, "lens": "L1", "check": "The deployed PoolManager bytecode under one state on each chain: pmdiff set 1 (250 scripts of pool math) and set 2 (300 scripts of hook, token and native call paths).", "result": "550 of 550 scripts give the Ethereum reference bytes on all seven chains, including the revert selectors of the error paths and the native payouts.", "source": f"file:{W}/out/pmdiff.log; file:{W}/out/pmdiff2.log"},
 {"chainIds": CH, "lens": "L1", "check": "Mined swaps of the newest window on each chain against the tick relation and the single-step formulas, and the multi-step ones replayed through the Pool.swap loop from storage at their block.", "result": "15,420 swaps satisfy the tick relation with no mismatch (19 on OP Mainnet sit on a tick boundary as src/libraries/Pool.sol leaves them); 11,662 of 11,901 paired swaps match one step to the unit; 90 of the 239 others were replayed through the whole loop and all 90 match, the longest with 12 steps on Base. Block production computed the source's math on these chains.", "source": f"file:{W}/out/swaps.log; file:{W}/out/replay.log"},
 {"chainIds": [480], "lens": "L1", "check": "Lead L-1183: the 23 multi-transaction scenarios of cycle 28 on World Chain through an endpoint that serves eth_simulateV1 and names its build.", "result": "The QuickNode public endpoint listed on chainlist.org answers world-chain/v2.8.2-9596311 and serves eth_simulateV1. All 23 scenarios (tick flips on full removal, extsload and exttload arrays, sync then exttload, owner and controller paths, donations at the int128 edge, malformed calldata and delegatecall into the PoolManager, swaps with protocol fees) equal the reference byte for byte.", "source": f"file:{W}/out/scen-480-qn.log; https://chainlist.org/chain/480"},
 {"chainIds": CH, "lens": "L1", "check": "Client and library releases since cycle 31: op-reth tags v2.10.1, v2.10.2, v2.10.0-rc.5, v2.11.0-rc.1, v2.11.0, v2.9.1, v2.12.0-rc.1 in the optimism monorepo; Base v1.5.7, v1.6.0, v1.6.0-rc.10, rc.11; world-chain v2.8.4, v2.9.0, v2.9.0-rc.2, rc.3, v2.9.1, v2.10.0-rc.1; and the newest crate versions of ruint, revm-interpreter, revm-bytecode, op-revm and alloy-evm.", "result": "None of the listed tags exists (HTTP 404 on raw.githubusercontent.com; the existing v2.8.2, v2.9.0, v2.10.0, v1.6.0-rc.9, v2.8.3 and v2.9.0-rc.1 were read in earlier cycles). The crates.io index ends at ruint 1.21.1 (1.21.0 yanked), revm-interpreter 43.0.2, revm-bytecode 43.0.0, op-revm 20.0.0 and alloy-evm 0.39.0, all already read. Every endpoint reports the build string of cycle 31, and all seven superchain-registry files are byte identical to cycle 31.", "source": f"file:{W}/web/tagprobe.txt; https://index.crates.io/ru/in/ruint; https://index.crates.io/re/vm/revm-interpreter; {REG}; file:{W}/out/clientver.txt"},
 {"chainIds": LAG, "lens": "L2", "check": "Lagoon Sequencer Defined Metering: does the out-of-EVM ETH movement of the post-exec refund reach the PoolManager's balance or a settlement decision.", "result": "The refund credits the sender of the rebated transaction and debits the fee recipients; the post-exec transaction is not executed as code and is not user-submittable. The PoolManager is a contract and is never a transaction sender or fee recipient. Native settlement counts msg.value, not the balance (src/PoolManager.sol:349-365), and an ERC-20 settle compares balanceOf before and after inside the same transaction (src/PoolManager.sol:279-286, 357-359), so a credit to an EOA after execution changes no delta. Refunds never exceed measured gas, and GAS inside execution is unchanged.", "source": f"{SDM_DOC}; {LAG_OV}"},
 {"chainIds": LAG, "lens": "L6", "check": "Upcoming forks in the next six months, assumed to ship: Lagoon on OP Mainnet, Unichain, Ink and Soneium (11 January 2027), its testnets (10 December 2026), and Base Everest.", "result": "Lagoon changes no opcode. Its execution changes are lower BLS12-381 input limits (src/ builds no input for those precompiles; a smaller limit can only make a caller-chosen call fail and revert that caller's unlock, src/types/Currency.sol:48), SDM (cleared above), and on OP Mainnet and Unichain the interop messaging and ETH liquidity predeploys cleared in earlier cycles. Funds already in the PoolManager are untouched by the fork. Everest has no date on Base and is outside the window as published; World Chain and Zora have no scheduled fork.", "source": f"{LAG_DOC}; {LAG_EE}; {BASE_UP}"},
 {"chainIds": CH, "lens": "L5", "check": "Deployed bytecode, owner and protocol fee controller of each PoolManager, last read in cycle 27.", "result": "Code length and sha256 prefix, owner address and code length, and protocol fee controller address and code length equal networks.json on all seven chains. The owner on Unichain and Ink (0x2bad8182c09f50c8318d769245bea52c32be46cd) has no code; that is a governance matter already on record.", "source": f"file:{W}/out/l5read.json"},
]
leads = [
 {"chainIds": LAG, "lens": "L6", "question": "On 10 December 2026, rerun the battery, both script sets and the SDM receipt check on OP Sepolia, Unichain Sepolia, Ink Sepolia and Soneium Minato once Lagoon is active there, and read the Lagoon op-reth tag when it is published.", "why": "Lagoon cannot be rehearsed through a time override, and the release that carries it is not yet tagged, so its interpreter and integer library pins are unknown.", "priority": "medium"},
 {"chainIds": [10], "lens": "L1", "question": "Find a way to tie an eth_call on mainnet.optimism.io to one build (a provider endpoint that pins v2.8.1, or an answer field that differs between the builds), or obtain the source of the unversioned dev build.", "why": "Coverage of the two builds now rests on routing being independent; about nine of 310 chunks may have reached only one build.", "priority": "low"},
]
leadResults = [{"leadId": "L-1183", "outcome": "cleared", "answer": "The QuickNode public World Chain endpoint (listed on chainlist.org) names world-chain/v2.8.2-9596311 and serves eth_simulateV1. All 23 scen28 scenarios ran there on 2026-11-27 and equal the pyevm reference byte for byte, with the build string recorded before and after every scenario."}]
doc = {"unit": "op-stack-eth", "_lenses": ["L1", "L2", "L5", "L6"], "profiles": profiles, "findings": [], "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(doc, open(OUT, "w"), indent=1)
print("wrote", OUT, len(profiles), "profiles")
