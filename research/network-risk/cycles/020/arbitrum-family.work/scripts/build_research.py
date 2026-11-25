"""Write cycles/020/arbitrum-family.research.json from the results gathered in this work directory."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(W), "arbitrum-family.research.json")
REL = "research/network-risk/cycles/020/arbitrum-family.work"

l898 = None
p = os.path.join(W, "raw", "l898", "upgraded_scan.json")
if os.path.exists(p):
    l898 = json.load(open(p))
scan_fail = ("a batched scan got -32005 rate limited for all 844 batches, and a paced single-request scan of the 3,274 windows "
             "from 48,956,737 to 52,230,552 ran at about one request every three seconds and was stopped unfinished "
             "(raw/l898/scan.log, raw/l898/upgraded_scan_batch_ratelimited.json)")

ALL = [42161, 4663, 99901]

profiles = [
    {"chainId": 42161, "lens": "L1",
     "summary": "Arbitrum One still answers as nitro v3.13.0-rc.9+b72783f on go1.27.3 (linux-arm64) at ArbOS 61, and every opdiff rerun of 2026-11-25 matches the specification. The holiman/uint256 release the Nitro trees pin is still v1.3.2; the unreleased master of that library rewrites division, signed division and signed comparison and was tested here against exact integers.",
     "deltas": [
         {"delta": "holiman/uint256 master is at pseudo-version v1.3.3-0.20261122165954-de2a0381 (2026-11-22) and differs from v1.3.2 in Div (a new shift path for every power of two divisor), Mod and Div through new udiv and umod routines, SDiv, SMod, Slt, Sgt, Eq and Bytes32. Nitro master, Nitro v3.12.4, OffchainLabs/go-ethereum master and upstream go-ethereum master and v1.17.4 all still pin v1.3.2, so no running node has the new code. FullMath.mulDiv divides by a power of two three times (src/libraries/FullMath.sol:62, 67, 73), so the first Nitro release that moves past v1.3.2 would route every 512 bit mulDiv through the new shift path.",
          "source": "https://proxy.golang.org/github.com/holiman/uint256/@v/master.info and https://raw.githubusercontent.com/holiman/uint256/de2a0381370eaae1264142bf98a6ebb3bc90fe41/uint256.go and https://raw.githubusercontent.com/OffchainLabs/nitro/master/go.mod (fetched 2026-11-25)",
          "relevance": "low"},
         {"delta": "No ArbOS upgrade after ArbOS 61 is proposed or scheduled for Arbitrum One: getScheduledUpgrade() returns zeros at block 527,501,559 and the DAO network upgrades table ends at ArbOS 61. The only chain-parameter change in flight is the Glamsterdam L1 pricing AIP, which is gated on Ethereum's fork and changes the L1 fee only. Ethereum's Glamsterdam may slip to between mid-January and May 2027.",
          "source": "https://docs.arbitrum.foundation/network-upgrades and https://forum.arbitrum.foundation/t/constitutional-aip-update-arbitrum-one-and-nova-l1-pricing-parameters-for-ethereum-glamsterdam/31555 and https://cointelegraph.com/news/ethereum-glamsterdam-could-slip-to-may-2027 and eth_call 0x6b getScheduledUpgrade() on https://arb1.arbitrum.io/rpc (raw/arbos_state.txt)",
          "relevance": "none"}]},
    {"chainId": 42161, "lens": "L2", "summary": "Nothing new. The reverted-then-completed unlock transaction 0x33050352 still has no public historical trace, so its reference rerun stays open.", "deltas": []},
    {"chainId": 42161, "lens": "L3", "summary": "Native token management and transaction filtering are still off (both getters return zero at block 527,501,559).", "deltas": []},
    {"chainId": 42161, "lens": "L4", "summary": "The 337-address precompile and system address scan from the PoolManager address gives the same answers as in cycle 18.", "deltas": []},
    {"chainId": 4663, "lens": "L1",
     "summary": "Robinhood Chain answers as the same private rc.9 build and every rerun matches the specification. Its public endpoint served the amd64 build at 18:17 UTC and the arm64 build at 18:22 UTC on 2026-11-25, so one URL is backed by both architectures.",
     "deltas": [
         {"delta": "web3_clientVersion on https://rpc.mainnet.chain.robinhood.com returned nitro/v3.13.0-rc.9+b72783f-20261116T155937Z/linux-amd64/go1.27.3 and five minutes later the same string with linux-arm64. Every result of this cycle for the chain may come from either build; both gave the specified answers in cycle 9 and the reruns here.",
          "source": f"{REL}/raw/clientVersions.log",
          "relevance": "none"}]},
    {"chainId": 4663, "lens": "L2", "summary": "Nothing new.", "deltas": []},
    {"chainId": 4663, "lens": "L3", "summary": "Transaction filtering is still on from timestamp 1,782,295,200 (F-001) and native token management is off.", "deltas": []},
    {"chainId": 4663, "lens": "L4", "summary": "No ArbOS upgrade is scheduled and the chain still has two chain owners. The notices page lists no upgrade after the September 2026 feed changes.",
     "deltas": []},
    {"chainId": 99901, "lens": "L1",
     "summary": "Elysium still answers as nitro/vlocal+unknown-unknown on go1.25.12. That Go release carries the prove pass code behind Go issue 82839 unchanged, and it predates the pass order that produces Go issue 81863. The version string is what Nitro prints when the binary carries no linker stamps, and go1.25.12 is the toolchain directive of the public Nitro v3.12.4 and master trees.",
     "deltas": [
         {"delta": "go1.25.12 and go1.25.9 contain the same factsTable.update code as go1.26.10 for the x+delta constant case and the look-through of value-preserving extensions (prove.go lines 1000-1120 identical), which is the code CL 858581 changes to fix issue 82839. The CL is still open on master, so no Go release holds the fix.",
          "source": "https://go.googlesource.com/go/+/refs/tags/go1.25.12/src/cmd/compile/internal/ssa/prove.go and https://go-review.googlesource.com/c/go/+/858581",
          "relevance": "low"},
         {"delta": "In go1.25.12 the branchelim pass runs after dead auto elim (compile.go pass list), and the CondSelect producers that issue 81863 depends on (CL 685676 of 2025-07-24 and CL 715044 of 2025-10-28) landed on master after the go1.25 branch. go1.25.x is therefore outside the range of the dead store miscompile.",
          "source": "https://go.googlesource.com/go/+/refs/tags/go1.25.12/src/cmd/compile/internal/ssa/compile.go and https://go-review.googlesource.com/c/go/+/841425",
          "relevance": "none"}]},
    {"chainId": 99901, "lens": "L2", "summary": "No change. The canonical bridge proxies on HyperEVM were created in transaction 0x867cae6d at HyperEVM block 48,956,737 with their first implementations set in that transaction.",
     "deltas": []},
    {"chainId": 99901, "lens": "L3", "summary": "HYPE remains the native gas token; native token management and transaction filtering are off.", "deltas": []},
    {"chainId": 99901, "lens": "L4", "summary": "The HyperCore read precompile and the ElysiumCoreWriter predeploy are still announced for about four weeks after the 9 November 2026 mainnet and are not scheduled on chain (getScheduledUpgrade() returns zeros at block 10,768,196). No address or ABI is published yet.",
     "deltas": []},
]

findings = [
    {"ref": "F-136",
     "title": "Elysium's node release and the consensus replay build of all three chains are inside the source range of Go issue 82839, and no EVM path searched has the faulty shape",
     "chainIds": ALL, "lens": "L1", "assumptions": ["A10"], "effect": "degrade", "actor": "operator", "severity": "info",
     "difference": "On Ethereum the execution clients are built with supported Go releases. Elysium's public node reports go1.25.12, and the state that the parent chains of all three networks accept is computed by the consensus-v61 replay binary built with go1.25.9 for WebAssembly (F-119). Both releases contain the prove pass code that Go issue 82839 reports: factsTable.update repeats a fact ext(x) op w on x with a constant w that can be wider than x, and the x+delta case then truncates w and can declare a reachable branch impossible. The text of prove.go lines 1000 to 1120 is the same in go1.25.9, go1.25.12 and go1.26.10, and the fix (CL 858581) is still unmerged. The same releases are outside the range of issue 81863, because branchelim runs after dead auto elim in go1.25 and the passes that create CondSelect earlier arrived only in go1.26.",
     "mechanism": "A miscompile of this kind changes a result only where Go source compares a sign-extended narrow integer plus a constant with a constant that does not fit the narrow type. Cycle 18 searched the interpreter, state and type packages of seven client trees, among them Nitro's go-ethereum fork at 0e44603, and holiman/uint256 v1.3.2, and found no such comparison; the only narrow signed widening on the opcode path is the int8 conversion in the SIGNEXTEND helper, which is never compared. This cycle ran the same search over OffchainLabs/go-ethereum f1c5f02, the fork the consensus-v61 replay machine pins, including its six Arbitrum-specific files in core/vm and core/state: 16 lower-tier candidates (conversions of untyped constants such as params.CallCreateDepth to int, and pointer selections that only matter for issue 81863), and no A1, A2 or A3 site. So no code that computes MULMOD in src/libraries/FullMath.sol:24 and 48, SDIV and SMOD in src/libraries/TickBitmap.sol:24-26, SIGNEXTEND and SAR in src/libraries/TickMath.sol:61-63, or the return data copy in src/libraries/Hooks.sol:148 has the shape. The answers agree: the battery (99,985), the targeted set (85,544), pmdiff (249 compared scripts) and pmdiff2 (300) match on Elysium as on the rc.9 endpoints.",
     "impact": "No loss path found. If a site of the faulty shape existed in the replay binary only, the sequencer and an honest validator would compute different states for a block that runs it, which stalls confirmations and withdrawals without moving pool funds.",
     "preconditions": "A comparison of the issue 82839 shape in code the Elysium node or the replay binary runs for an EVM instruction. None was found. Nitro's own arbos and precompiles packages and Elysium's unpublished tree were not searched.",
     "mitigations": "Operators can rebuild with a Go release that contains CL 858581 once one ships. Nothing for pool creators or liquidity providers to do.",
     "coreRefs": ["src/libraries/FullMath.sol:24", "src/libraries/FullMath.sol:48", "src/libraries/TickBitmap.sol:24-26", "src/libraries/TickMath.sol:61-63", "src/libraries/Hooks.sol:148"],
     "sources": [
         {"url": "https://go.googlesource.com/go/+/refs/tags/go1.25.12/src/cmd/compile/internal/ssa/prove.go", "supports": "go1.25.12 has the unguarded x+delta constant derivation and the extension look-through (lines 1034-1060 and 1097-1115)"},
         {"url": "https://go.googlesource.com/go/+/refs/tags/go1.25.9/src/cmd/compile/internal/ssa/prove.go", "supports": "go1.25.9, the replay build's compiler, has the same text"},
         {"url": "https://go-review.googlesource.com/c/go/+/858581", "supports": "the 82839 fix guards exactly that derivation and is still NEW on master (updated 2026-11-16)"},
         {"url": "https://go.googlesource.com/go/+/refs/tags/go1.25.12/src/cmd/compile/internal/ssa/compile.go", "supports": "branchelim runs after dead auto elim in go1.25.12"},
         {"url": "https://go-review.googlesource.com/c/go/+/841425", "supports": "the 81863 fix names CL 685676 and CL 715044 as the cause; both merged on master after the go1.25 branch"},
         {"url": "https://raw.githubusercontent.com/OffchainLabs/go-ethereum/f1c5f02/core/vm/interpreter.go", "supports": "source of the replay machine's go-ethereum fork that was searched"},
         {"url": "https://rpc.elysium.kinetiq.xyz", "supports": "web3_clientVersion nitro/vlocal+unknown-unknown/linux-amd64/go1.25.12 on 2026-11-25 (raw/clientVersions.log)"}],
     "evidence": "primary"},
]

cleared = [
    {"chainIds": ALL, "lens": "L1",
     "check": "Cycle 20 reruns of battery.py (99,985 vectors), targeted.py (85,544), pmdiff.py (250 scripts), pmdiff2.py (300 scripts), callsem.py (50) and the 337-address precompile scan, with web3_clientVersion logged before each step.",
     "result": "No mismatch. battery and targeted match on all three chains. pmdiff: 249 of 250 scripts identical on each chain, the 250th not compared because the Ethereum reference call failed at the endpoint. pmdiff2: 300 of 300 identical on Arbitrum One and Robinhood Chain, 299 of 300 on Elysium with one script different. Earlier cycles traced Elysium's single different script to script 189, a native swap that runs out of the gas the endpoint grants; pmdiff2.py records only counts, so the index was not re-identified this cycle. callsem 50 of 50 as specified. The precompile scan answers equal cycle 18's at all 337 addresses after the rate-limited Elysium answers were fetched again. The builds were nitro v3.13.0-rc.9+b72783f on go1.27.3 (Arbitrum One arm64, Robinhood Chain both amd64 and arm64) and nitro/vlocal+unknown-unknown on go1.25.12 (Elysium).",
     "source": f"{REL}/raw/ (battery.json, targeted.json, pmdiff.json, pmdiff2.json, callsem.json, precscan.json, precfix.log, clientVersions.log)"},
    {"chainIds": ALL, "lens": "L1",
     "check": "Mined swaps rerun with swaps.py and replay.py on 2026-11-25: tick relation of getTickAtSqrtPrice and the single-step relations of SwapMath.computeSwapStep.",
     "result": "Arbitrum One 5,916 swaps, Robinhood Chain 5,697 and Elysium 4,102 all satisfy the tick relation (src/libraries/TickMath.sol, src/libraries/Pool.sol swap loop). Of the 5,237, 4,932 and 3,663 paired swaps none falls outside the single-step outcomes or the multi-step class. Multi-step replays: Robinhood Chain 25 of 25 to the unit, the longest 49 steps, Elysium 14 of 14, Arbitrum One 2 of 6 (the other 4 at blocks the endpoint no longer serves).",
     "source": f"{REL}/raw/swaps.json, {REL}/raw/replay.json, swaps.log, replay.log"},
    {"chainIds": ALL, "lens": "L1",
     "check": "Differential test of holiman/uint256 v1.3.2 (pinned by every Nitro and go-ethereum tree read) and of the unreleased master de2a0381 against math/big, for the 21 operations the interpreter calls, with the operand aliasing of the go-ethereum handlers (result written into the last operand's stack slot) and MulDivOverflow.",
     "result": "22,693,433 vectors: every pair of 1,053 edge values (each 2^k, 2^k-1, 2^k+1 and -2^k, tick and price limits, 2^96, 2^128) for the two-operand operations, plus 200,000 random and limb-pattern triples per operation with the modulus 2^256-1 of FullMath on a third of the MULMOD and MULDIV triples. No mismatch in either version. A copy of master with one shift constant changed in the new power of two path of Div fails 35,873 DIV and 50,057 SDIV vectors, so the test sees a fault in exactly the path FullMath.sol:62, 67 and 73 would take.",
     "source": f"{REL}/scripts/u256diff/main.go, {REL}/raw/u256diff.txt, {REL}/raw/u256/"},
    {"chainIds": ALL, "lens": "L1",
     "check": "Opcodes that the forks Nitro tracks would add (CLZ 0x1e from EIP-7939, SLOTNUM 0x4b from EIP-7843, SWAPN, DUPN and EXCHANGE 0xe6 to 0xe8 from EIP-8024) against the PoolManager bytecode built from this checkout.",
     "result": "A linear disassembly of the 24,009 byte runtime finds none of these bytes outside push data, so assigning them changes no instruction the PoolManager executes. EIP-8024 keeps 0x5b and the push range out of its immediates, so jump destination analysis of existing code is unchanged. Nitro v3.12.4 already builds against go-ethereum glamsterdam-devnet-8 for its tests, which is where such opcodes would come from.",
     "source": "research/network-risk/build/PoolManager.json; https://eips.ethereum.org/EIPS/eip-8024; https://eips.ethereum.org/EIPS/eip-7939; https://eips.ethereum.org/EIPS/eip-7843; https://raw.githubusercontent.com/OffchainLabs/nitro/v3.12.4/Makefile line 62"},
    {"chainIds": ALL, "lens": "L4",
     "check": "Upcoming forks for the next six months: getScheduledUpgrade() on all three chains, the Arbitrum DAO upgrade table, Robinhood Chain's notices page, and Elysium's roadmap.",
     "result": "Nothing is scheduled on chain (all three return zeros on 2026-11-25). Arbitrum One has no ArbOS proposal after ArbOS 61; the Glamsterdam L1 pricing change only sets parentGasFloorPerToken and perBatchGasCharge through ArbOwner and changes no call result. Robinhood Chain lists no consensus change after ArbOS 61. Elysium's only announced change is the HyperCore read precompile and ElysiumCoreWriter predeploy, which stays under L-770. If each ships as described, funds already in the PoolManager are touched only by the Elysium change, and only through a currency or hook that names the new addresses.",
     "source": "https://docs.arbitrum.foundation/network-upgrades; https://docs.robinhood.com/chain/notices-and-upgrades/; https://elysium.kinetiq.xyz/docs/what-is-elysium; raw/arbos_state.txt"},
]

scan_note = "not finished"
if l898:
    scan_note = f"{l898['windows']} windows of 1,000 blocks from {l898['start']:,} to {l898['head']:,}, {len(l898['errors'])} windows failed, {len(l898['logs'])} Upgraded or AdminChanged logs"
leads = [
    {"chainIds": ALL, "lens": "L1",
     "question": "When a Nitro release moves holiman/uint256 past v1.3.2, which revision does it pin, and does the u256diff harness in cycles/020/arbitrum-family.work/scripts/u256diff still find no mismatch on that revision, including its power of two Div path, udiv, umod, SDiv and Slt?",
     "why": "FullMath.mulDiv divides by a power of two three times per 512 bit call (src/libraries/FullMath.sol:62, 67, 73) and TickBitmap.compress uses SDIV and SLT, so the new library paths would sit under every swap the day the release is adopted, with no second client on the chain.",
     "priority": "medium"},
    {"chainIds": ALL, "lens": "L1",
     "question": "Do Nitro's own arbos, arbos/programs and precompiles packages at the consensus-v61 tag contain a comparison of the Go issue 82839 shape on a path that runs for a PoolManager transaction (gas accounting, StartTxHook, retryable redeem, L1 pricing)?",
     "why": "The replay binary is built with go1.25.9, inside the range; only the go-ethereum fork and uint256 were searched. A site there would split the replay from the sequencer for affected blocks.",
     "priority": "low"},
]

leadResults = [
    {"leadId": "L-784", "outcome": "inconclusive",
     "answer": "Elysium still reports nitro/vlocal+unknown-unknown/linux-amd64/go1.25.12 (2026-11-25). Nitro's nitroversion package prints \"local\" when no tag or branch was stamped by the linker and \"unknown\" for a missing commit time, so the binary was built without Nitro's Makefile stamps. go1.25.12 is the toolchain directive of the public v3.12.4 and master go.mod, which points to a public tree built with its default toolchain, while the rc.9 endpoints report go1.27.3. The commit itself is still unknown. All vectors and scripts give the same answers as the rc.9 endpoints."},
    {"leadId": "L-864", "outcome": "inconclusive",
     "answer": "The pin of rc.9 is still unreadable: go.mod at v3.13.0-rc.9, rc.10, rc.11, v3.13.0, v3.13.1, v3.12.5, v3.12.6 and b72783f returns 404 on 2026-11-25. Instead the fork that the consensus-v61 replay pins (f1c5f02), including its Arbitrum files in core/vm and core/state, was searched with the cycle 18 shape scanner: no issue 82839 site and only pointer selections for issue 81863 that do not touch the opcode path (raw/scan-nitro-geth-f1c5f02.json)."},
    {"leadId": "L-876", "outcome": "finding",
     "answer": "go1.25.12 is inside the source range of issue 82839: its prove.go factsTable.update has the same unguarded x+delta constant step and the same extension look-through as go1.26.10, which the fix CL 858581 changes; the CL is still unmerged, so go1.25.12 holds no fix. go1.25.12 is outside the range of issue 81863: branchelim runs after dead auto elim in its pass list, and the changes that let CondSelect reach dead store elimination (CL 685676 and CL 715044) landed on master after the 1.25 branch; deadstore.go in go1.25.12 has no CondSelect case and needs none. The same holds for go1.25.9, the replay build. Recorded as an update to F-136."},
    {"leadId": "L-770", "outcome": "inconclusive",
     "answer": "Not answerable on 2026-11-25: getScheduledUpgrade() on Elysium returns zeros at block 10,768,196, arbOSVersion is 116 (ArbOS 61), and the roadmap still dates the HyperCore upgrade to about four weeks after 9 November without addresses or selectors. The precompile scan from the PoolManager address equals cycle 18's at all 337 addresses. precscan.py and precfix.py are in this cycle's work directory for the rerun."},
    {"leadId": "L-142", "outcome": "inconclusive",
     "answer": "The rc.9 source is still private (same 404s as above). Answers of the running build match the consensus-v61 behaviour on every rerun of this cycle, including the 337-address precompile scan."},
    {"leadId": "L-252", "outcome": "inconclusive",
     "answer": "The rc.9 source is still unpublished, so arbos/programs/api.go and arbos/block_processor.go at b72783f could not be read. No Stylus activation is possible on the three chains (F-128), which keeps the Stylus side out of reach of ordinary accounts in the meantime."},
    {"leadId": "L-835", "outcome": "inconclusive",
     "answer": "Still no public endpoint serves the historical trace: drpc answers historical state is not available, publicnode, meowrpc and onfinality do not expose debug_traceTransaction, blastapi allows only core methods, Tenderly and 1rpc are rate or plan limited, ankr needs a key (raw/l835_trace_probe.txt)."},
    {"leadId": "L-798", "outcome": "inconclusive",
     "answer": "The only transaction of this lead still not rerun is Arbitrum One 0x33050352 (L-835), and its trace is still not served. The Tempo, Base and Robinhood reruns of cycle 17 stand."},
]

if l898 is not None and not l898["errors"]:
    CT = "0x867cae6de4d67146b3f9157fef0ba8b82bf862b507ed54e64d45da70ec602e8b"
    later = [(lg["address"].lower(), int(lg["blockNumber"], 16), lg["topics"][0][:10], lg["topics"][1] if len(lg["topics"]) > 1 else lg["data"][:66])
             for lg in l898["logs"] if lg["transactionHash"].lower() != CT]
    increate = sum(1 for lg in l898["logs"] if lg["transactionHash"].lower() == CT)
    leadResults.append({"leadId": "L-898", "outcome": "cleared" if not later else "finding",
        "answer": "The four proxies were all created in HyperEVM transaction 0x867cae6de4d67146b3f9157fef0ba8b82bf862b507ed54e64d45da70ec602e8b at block 48,956,737, whose receipt sets the first implementations: 0xce59f8b6 to 0x748c47ee, 0x503d5721 to 0xc0399320, 0x37c92ba3 to 0xcd2fa60a and 0x7f3ff53a to 0x90eea97b. A scan of Upgraded and AdminChanged logs on the four proxies from that block to head (" + scan_note + f") finds {increate} events in the creation transaction and " + ("no later upgrade or admin change, so the Inbox and Bridge have never pointed at another implementation." if not later else "these later events: " + json.dumps(later)) + " The scan used rpc.hyperliquid.xyz eth_getLogs, which reads logs from receipts and does not depend on archive state."})
else:
    leadResults.append({"leadId": "L-898", "outcome": "inconclusive",
        "answer": "The creation transaction is 0x867cae6de4d67146b3f9157fef0ba8b82bf862b507ed54e64d45da70ec602e8b at HyperEVM block 48,956,737; its receipt sets 0xce59f8b6 to 0x748c47ee, 0x503d5721 to 0xc0399320, 0x37c92ba3 to 0xcd2fa60a and 0x7f3ff53a to 0x90eea97b. The log scan to head did not complete: " + scan_fail + ". A complete answer needs an endpoint or explorer API without this rate limit; the scan script scripts/l898_scan.py is ready."})

doc = {"unit": "arbitrum-family", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings,
       "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(doc, open(OUT, "w"), indent=1)
print("wrote", OUT)
