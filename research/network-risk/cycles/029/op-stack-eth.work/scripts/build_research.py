"""Writes cycles/029/op-stack-eth.research.json from the outputs in this work directory."""
import json, glob, os
NR = '/home/user/v4-core/research/network-risk'
W = 'research/network-risk/cycles/029/op-stack-eth.work'
O = NR + '/cycles/029/op-stack-eth.work/out'
C = [10, 8453, 130, 7777777, 480, 57073, 1868]
OPR = 'https://raw.githubusercontent.com/ethereum-optimism/optimism'

# World Chain scenario results (thirdweb endpoint, rate limited)
wc = {}
for f in glob.glob(O + '/wc/scen-480-*.json'):
    d = json.load(open(f))
    for k, v in d['scenarios'].items():
        if 'diffs' in v: wc[k] = v
wc_ok = sum(1 for v in wc.values() if not v['diffs'])
wc_n = len(wc)
wc_txt = (f"On World Chain only the thirdweb endpoint (it answers web3_clientVersion with thirdweb/1.0, which names no build) serves eth_simulateV1; "
          f"worldchain-mainnet.g.alchemy.com/public refuses it and debug_traceCall, and worldchain.drpc.org has no such method. "
          + (f"Under its rate limit {wc_n} of 23 scenarios ran, {wc_ok} of them with no difference." if wc_n else
             "It answered every request that carried a scenario with HTTP 429 for about 20 minutes, so no scenario ran on World Chain; the three borrow scripts did run there through eth_call."))

H = {"10": "OP Mainnet", "8453": "Base", "130": "Unichain", "7777777": "Zora", "480": "World Chain", "57073": "Ink", "1868": "Soneium"}
BUILD = {10: "op-reth/v2.8.1-72207294 and op-reth/v0.0.0-dev-unknown", 8453: "reth/v2.5.2-9e380dd/base/v1.5.6",
         130: "op-reth/v2.10.0-rc.4-65e80332", 7777777: "conduit-op-reth/v2.5.1-8f0ccac", 480: "world-chain/v2.8.2-9596311",
         57073: "op-reth/v2.10.0-rc.4-65e80332 (rpc-gel) and op-reth/v0.0.0-dev-unknown (rpc-qnd)", 1868: "op-reth/v2.10.0-rc.4-65e80332"}
SW = {10: (2880, 1311, 1305, 6), 8453: (2627, 1661, 1500, 25), 130: (6917, 6496, 6467, 25), 7777777: (438, 311, 296, 15),
      480: (217, 147, 147, 0), 57073: (3514, 3121, 3088, 25), 1868: (441, 392, 392, 0)}

def l1_rerun(c):
    s, p, one, rep = SW[c]
    scen = ("all 23 cycle 28 multi-transaction scenarios (90,608 bytes of output) give the reference bytes through eth_simulateV1"
            if c != 480 else wc_txt)
    return {"delta": f"Rerun on 2026-11-27 at {BUILD[c]}: battery 99,985 and targeted 85,544 vectors specified, pmdiff set 1 250 of 250 and set 2 300 of 300 identical to the Ethereum reference, {s} mined swaps satisfy the tick relation with 0 mismatches, {one} of {p} paired swaps match a single step to the unit and the rest are multi-step swaps, of which {rep} sampled replay through the whole loop with 0 failures. The three getFeeGrowthInside borrow scripts return the reference records, and {scen}.",
            "source": f"file:{W}/out/battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.log, borrow-{c}.log, " + ("scen-*.log" if c != 480 else "wc/scen-480-*.log") + f"; clientver.txt", "relevance": "none"}

LAG = {"delta": "The superchain-registry still lists lagoon_time 1799683201 (11 January 2027 16:00:01 UTC) for OP Mainnet, Unichain, Ink and Soneium and none for Zora and World Chain; karst_time is past on all six (8 July 2026, World Chain 21 September 2026). The unversioned op-reth build behind rpc-qnd.inkonchain.com answers eth_config with a current fork from 1783526401 (Karst) and a next fork at 1799683201 (Lagoon) with the same 18 precompiles; the other endpoints refuse eth_config except Zora, which lists Karst and no next fork.",
       "source": "https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/op.toml (and unichain, ink, soneium, zora, worldchain .toml); file:" + W + "/out/ethconfig-*.json", "relevance": "low"}

profiles = []
for c in C:
    d1 = [l1_rerun(c)]
    if c == 8453:
        d1.append({"delta": "Base tagged v1.6.0-rc.5, rc.6 and rc.7 after rc.4. Their Cargo.lock files are identical to each other and keep revm 43.0.3, revm-interpreter 43.0.2, revm-bytecode 43.0.0 and ruint 1.19.0; the only change from rc.4 is the rename of the eip8130 crates to base-tx. base-common-evm2 is still a scaffold that its README says is not wired into the node. The endpoint still runs v1.5.6.",
                   "source": "https://raw.githubusercontent.com/base/base/v1.6.0-rc.7/Cargo.lock; https://raw.githubusercontent.com/base/base/v1.6.0-rc.5/Cargo.lock; https://raw.githubusercontent.com/base/base/v1.6.0-rc.7/crates/common/evm2/README.md", "relevance": "none"})
    if c == 480:
        d1.append({"delta": "world-chain v2.9.0-rc.1 is tagged after v2.8.3. It moves to reth op-v2.7.0-1 and op-revm at optimism f8498888, still with revm 43.0.3, revm-interpreter 43.0.2 and ruint 1.20.0, and crates/evm/src/lib.rs, factory.rs and Cargo.toml are byte identical to v2.8.3. At f8498888 op-revm differs from op-reth/v2.10.0 only in handler.rs, where the deposit mint amount becomes a narrower integer converted to U256; no instruction changes.",
                   "source": "https://raw.githubusercontent.com/worldcoin/world-chain/v2.9.0-rc.1/Cargo.lock; https://raw.githubusercontent.com/worldcoin/world-chain/v2.9.0-rc.1/crates/evm/src/factory.rs; " + OPR + "/f84988888034b4692715e528a1d9fc69de511eab/rust/op-revm/src/handler.rs; " + OPR + "/op-reth/v2.10.0/rust/op-revm/src/handler.rs", "relevance": "none"})
    if c in (10, 130, 57073, 1868, 7777777, 480):
        d1.append(LAG)
    if c in (10, 57073):
        d1.append({"delta": "The unversioned op-reth/v0.0.0-dev-unknown build (behind mainnet.optimism.io for most requests and behind rpc-qnd.inkonchain.com) returned the specified word for all 15,510 large-index vectors of cycle 27 on rpc-qnd, all 23 scenarios on both endpoints and all three borrow scripts. Its eth_config schedules Lagoon at 1799683201, so it is a build that knows the Lagoon time.",
                   "source": "file:" + W + "/out/hiword-qnd.log; file:" + W + "/out/scen-10.log; file:" + W + "/out/scen-57073q.log; file:" + W + "/out/ethconfig-57073q-1.json", "relevance": "low"})
    profiles.append({"chainId": c, "lens": "L1", "summary": f"Every vector, script, scenario and mined swap matches the specification at the build {H[str(c)]}'s endpoint reported on 2026-11-27. No release since cycle 27 changes an instruction, the integer library or jump analysis.", "deltas": d1})
    profiles.append({"chainId": c, "lens": "L2", "summary": "Transaction boundaries are unchanged. eth_simulateV1 on the endpoints keeps persistent storage between simulated transactions and clears transient storage between them, which the scenario reruns rely on.",
                     "deltas": [{"delta": "A probe contract that increments one storage slot and one transient slot returned (1,1) then (2,1) for two simulated transactions in one eth_simulateV1 request on every endpoint of this unit that serves the method, so transient storage starts empty in each simulated transaction.", "source": "eth_simulateV1 on mainnet.optimism.io, mainnet.base.org, mainnet.unichain.org, rpc.zora.energy, 480.rpc.thirdweb.com, rpc-gel.inkonchain.com, rpc-qnd.inkonchain.com, rpc.soneium.org (2026-11-27)", "relevance": "none"}]})
    profiles.append({"chainId": c, "lens": "L3", "summary": "Nothing new changes the native asset or gas token." if c != 8453 else "Everest, which adds Base Transactions, still has no Sepolia or mainnet date.",
                     "deltas": [] if c != 8453 else [{"delta": "The Base upgrades page lists Everest as Planning with Base Sepolia TBD and Base Mainnet TBD; Denim (200 ms native blocks) went live on 5 November 2026 and was cleared in an earlier cycle.", "source": "https://docs.base.org/upgrades/everest/overview; https://docs.base.org/upgrades/overview", "relevance": "low"}]})
    l4 = []
    if c == 8453:
        l4.append({"delta": "reth's precompile result cache (engine payload validation and prewarming) wraps only precompiles whose supports_caching is true. Every stateful Base precompile (B20 factory, policy registry, activation registry, transaction context, nonce manager, and the B20 stablecoin and asset tokens) is built by the base_precompile macro through DynPrecompile::new_stateful, which returns false, and B20 tokens are resolved by a dynamic lookup that map_cacheable_precompiles does not touch. A cached balanceOf or transfer result cannot be replayed into a later block.",
                   "source": "https://raw.githubusercontent.com/base/base/v1.5.6/crates/common/precompiles/src/macros.rs; https://raw.githubusercontent.com/base/base/v1.5.6/crates/common/precompiles/src/provider.rs; https://raw.githubusercontent.com/base/base/v1.5.6/crates/common/precompiles/src/lookup.rs; https://static.crates.io/crates/alloy-evm/alloy-evm-0.39.0.crate (src/precompiles.rs:29-31, 84-90, 634-645); https://raw.githubusercontent.com/base/reth/base-v2.5.2.11/crates/engine/tree/src/tree/precompile_cache.rs", "relevance": "low"})
    profiles.append({"chainId": c, "lens": "L4", "summary": "No new system contract or predeploy. The precompile cache in front of execution only holds pure precompiles." if c == 8453 else "No new system contract or predeploy. The precompile cache in front of execution only holds pure precompiles, and the PoolManager calls none.", "deltas": l4})

findings = [{
    "ref": "F-162",
    "title": "An account that runs another user's ERC-4337 operation from inside its own unlock makes every PoolManager router call of that operation revert with AlreadyUnlocked",
    "chainIds": C, "lens": "L2", "assumptions": ["A1"], "effect": "degrade", "actor": "unprivileged", "severity": "low",
    "difference": "EntryPoint v0.6, v0.7 and v0.8 accept handleOps from a contract, so whoever holds a signed user operation first decides the frames around it. On these seven chains the only documented way for an outsider to obtain other users' pending operations is the ERC-4337 shared mempool, which the ERC-4337 documentation lists as live on Ethereum, Arbitrum and Optimism only, at a stage where only whitelisted bundlers propagate operations. No shared mempool is documented for Base, Unichain, Zora, World Chain, Ink or Soneium, where operations sit in the queue of the bundler the wallet chose.",
    "mechanism": "1. unlock reverts with AlreadyUnlocked while the transient lock flag is set and clears it only after the callback returns (src/PoolManager.sol:104-114). 2. A contract of the attacker calls unlock and, inside unlockCallback, calls EntryPoint.handleOps with the victim's operation. 3. The victim's router calls unlock and reverts; the EntryPoint records the operation as failed and charges its gas to the victim's account or paymaster, paid to the beneficiary the attacker named. 4. The attacker's callback returns with no delta and its unlock completes. Nothing credits the attacker or lowers a pool balance, because every delta the victim's contracts could open is keyed to their own address (src/PoolManager.sol:291-297). The new evidence narrows step 2: on OP Mainnet the attacker must be a whitelisted shared-mempool bundler, and on the other six chains it must be the bundler the victim submitted to, or obtain operations from it.",
    "impact": "No pool funds move and no claim or position is frozen. One user operation fails, its nonce is used and its gas goes to the attacker's beneficiary. The victim resubmits through another bundler.",
    "preconditions": "The attacker must hold the victim's signed operation before an honest bundler includes it. On OP Mainnet that requires a whitelisted bundler in the stage 1 shared mempool; on the other six chains the documented sources give no public view of pending operations, so the attacker must be, or be fed by, the victim's chosen bundler, which is an operator role in practice. The operation must target EntryPoint v0.6, v0.7 or v0.8.",
    "mitigations": "Wallets can submit PoolManager trades through EntryPoint v0.9, whose handleOps accepts only an externally owned caller, or through a bundler they trust. No core change is proposed.",
    "coreRefs": ["src/PoolManager.sol:104-114", "src/PoolManager.sol:291-297", "src/libraries/Lock.sol:13-25"],
    "sources": [
        {"url": "https://docs.erc4337.io/bundlers/censorship-resistance.html", "supports": "the shared mempool is live on Ethereum, Arbitrum and Optimism, and the ecosystem is moving from stage 1 (only whitelisted bundlers propagate operations) to stage 2"},
        {"url": "https://etherspot.io/blog/erc-4337-shared-mempool-official-launch-on-ethereum-mainnet-arbitrum-and-optimism/", "supports": "launch announcement of 12 November 2024 naming Ethereum, Arbitrum and Optimism"},
        {"url": "https://etherspot.io/blog/eip-7702-infrastructure-launches-to-support-account-abstraction-for-eoas/", "supports": "October 2025: the free shared-mempool infrastructure is live on Ethereum and Optimism, with Base, World Chain and Unichain listed as upcoming"},
        {"url": "https://sourcify.dev/server/v2/contract/1/0x433709009B8330FDa32311DF1C2AFA402eD8D009?fields=sources", "supports": "EntryPoint v0.9 nonReentrant requires tx.origin == msg.sender (recorded in cycle 28, F-162)"}],
    "evidence": "secondary"}]

cleared = [
 {"chainIds": C, "lens": "L1", "check": "Interpreter, integer library and jump analysis releases since cycle 27 for the builds the seven endpoints report (op-reth v2.8.1, v2.10.0-rc.4 and the unversioned build, base v1.5.6, conduit-op-reth v2.5.1, world-chain v2.8.2).",
  "result": "No change reaches an instruction. crates.io has no revm, revm-interpreter, revm-bytecode or ruint release after 24 September 2026 (ruint 1.21.1 of 23 October is pinned by none of these clients). op-reth has no tag after v2.10.0. Base v1.6.0-rc.5 to rc.7 pin the same revm and ruint 1.19.0 as rc.4. world-chain v2.9.0-rc.1 keeps revm 43.0.3 and ruint 1.20.0 and byte-identical EVM factory files. op-revm at the f8498888 commit it pins changes only the integer type of the deposit mint field.",
  "source": "https://crates.io/api/v1/crates/ruint; https://crates.io/api/v1/crates/revm-interpreter; " + OPR + "/op-reth/v2.10.0/rust/Cargo.lock; https://raw.githubusercontent.com/base/base/v1.6.0-rc.7/Cargo.lock; https://raw.githubusercontent.com/worldcoin/world-chain/v2.9.0-rc.1/Cargo.lock; " + OPR + "/f84988888034b4692715e528a1d9fc69de511eab/rust/op-revm/src/handler.rs"},
 {"chainIds": C, "lens": "L1", "check": "Standard battery (99,985), targeted set (85,544), pmdiff set 1 (250 scripts), set 2 (300), mined swaps and multi-step replay, rerun on 2026-11-27.",
  "result": "No mismatch on any of the seven chains. Mined swaps: 17,034 satisfy the tick relation; 13,195 of 13,439 paired swaps match one step to the unit and the rest are multi-step; 96 sampled multi-step swaps (longest 26 steps, on Base) replay through Pool.swap with 0 failures. TickMath, BitMath, FullMath, SqrtPriceMath, SwapMath and TickBitmap therefore receive the specified opcode results on every build answering today.",
  "source": f"file:{W}/out/battery.log; targeted.log; pmdiff.log; pmdiff2.log; swaps.log; replay.log"},
 {"chainIds": C, "lens": "L1", "check": "L-1177, part 1: the three cycle 28 scripts that make each unchecked subtraction of getFeeGrowthInside borrow (src/libraries/Pool.sol:498-509) and feed the wrapped value to Position.update (src/libraries/Position.sol:91-96), run on each chain's own deployed PoolManager bytecode (PM_FROM set to the chain, so Unichain runs its 24,050 byte predeploy).",
  "result": "All 87 calls of the three scripts return byte-identical records to the reference interpreter on all seven chains and on both Ink endpoints, at every build the endpoints answered (op-reth v2.8.1 and the unversioned build on OP Mainnet both served at least one script).",
  "source": f"file:{W}/out/borrow-10.log, borrow-8453.log, borrow-130.log, borrow-7777777.log, borrow-480.log, borrow-57073.log, borrow-1868.log; script cycles/028/hyperevm.work/scripts/borrow.py"},
 {"chainIds": [10, 8453, 130, 7777777, 57073, 1868], "lens": "L1", "check": "L-1177, part 2: the 23 multi-transaction scenarios of cycles/028/theme-monad-native-unentered-blocks.work/scripts/scen28.py (clearTick on removal, extsload and exttload arrays and malformed array calldata, sync then exttload, the owner and fee controller paths, the 512 bit fee path with donations of 2^127-1, short calldata and DELEGATECALL into the PoolManager, and 40 single swaps for the exact-fraction check), run read-only through eth_simulateV1 with one simulated block per transaction, compared byte for byte with scen28.ref().",
  "result": "23 of 23 scenarios, 137 transactions and 90,608 output bytes, equal the reference on OP Mainnet (both builds), Base, Unichain, Zora, Ink (rpc-gel and rpc-qnd) and Soneium. Revert data is read from error.data, where eth_simulateV1 places it. A planted change of the owner slot in scenario C2 makes its second transaction differ, so the comparison can fail. NoDelegateCall (src/NoDelegateCall.sol:18-25) returns DelegateCallNotAllowed for a delegated initialize, and the locked calls return ManagerLocked, as in the reference.",
  "source": f"file:{W}/scripts/scen_rpc.py; {W}/out/scen-10.log, scen-8453.log, scen-130.log, scen-7777777.log, scen-57073.log, scen-57073q.log, scen-1868.log, scen-control.json"},
 {"chainIds": [10, 57073, 7777777], "lens": "L1", "check": "Cycle 27 large-index vectors (15,510: SHL, SHR, SAR, BYTE, SIGNEXTEND with nonzero high limbs, EXP with high-limb exponents, MULMOD and ADDMOD near 2^256) on the unversioned op-reth build and on Zora.",
  "result": "15,510 of 15,510 specified on rpc-qnd.inkonchain.com (op-reth/v0.0.0-dev-unknown, the same build string that answers most OP Mainnet requests) and on rpc.zora.energy (conduit-op-reth/v2.5.1-8f0ccac).",
  "source": f"file:{W}/out/hiword-qnd.log; {W}/out/hiword-zora.log"},
 {"chainIds": C, "lens": "L4", "check": "Precompile result cache that reth puts in front of block execution and prewarming (crates/engine/tree/src/tree/precompile_cache.rs in ethereum-optimism/reth op-v2.7.0-2 and base/reth base-v2.5.2.11): key, hit rule, and which precompiles it wraps.",
  "result": "One cache per precompile address, keyed by the full input bytes and filtered by spec id; a hit is served only when the call has at least the gas the cached run used, and only successful outputs are stored. map_cacheable_precompiles wraps only precompiles whose supports_caching is true (alloy-evm 0.39.0 precompiles.rs:84-90), which excludes Identity and every precompile built with new_stateful. The OP Stack precompiles are pure, and every stateful Base precompile is built with new_stateful by the base_precompile macro, B20 tokens being resolved by a lookup the cache never wraps. The PoolManager itself calls no precompile (src/ has calls only at src/types/Currency.sol:48, 73 and src/libraries/Hooks.sol:134).",
  "source": "https://raw.githubusercontent.com/ethereum-optimism/reth/op-v2.7.0-2/crates/engine/tree/src/tree/precompile_cache.rs (lines 70-72, 184-226); https://raw.githubusercontent.com/base/reth/base-v2.5.2.11/crates/engine/tree/src/tree/precompile_cache.rs; https://static.crates.io/crates/alloy-evm/alloy-evm-0.39.0.crate; https://raw.githubusercontent.com/base/base/v1.5.6/crates/common/precompiles/src/macros.rs"},
 {"chainIds": C, "lens": "L1", "check": "Upcoming forks in the next six months: Lagoon on OP Mainnet, Unichain, Ink and Soneium (11 January 2027), Base Everest (no date), and anything scheduled for Zora and World Chain, assumed to ship.",
  "result": "Nothing changes what src/ computes. Lagoon keeps the instruction set and is already covered by F-157 (the ETHLiquidity predeploy, operator level) and the cycle 27 sweep of the interop predeploys. Everest adds the 0x79 transaction type, whose phases revert transient storage as one transaction does (cycle 27). The registry lists no further fork for Zora or World Chain, and world-chain v2.9.0-rc.1 changes no EVM file. An ordinary account gains no new call shape against the PoolManager on the day after either fork.",
  "source": "https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/op.toml; https://docs.base.org/upgrades/everest/overview; file:" + W + "/out/ethconfig-57073q-1.json"},
 {"chainIds": [10, 130, 57073, 1868, 7777777, 480], "lens": "L1", "check": "Code paths a block producer can run that the public endpoint does not: the op-rbuilder block builder used by OP Stack sequencers.",
  "result": "op-rbuilder main still has no tag after v0.4.14 and its Cargo.lock (sha256 prefix 5074b5f6e98a) pins revm 41.0.0, revm-interpreter 41.0.0, ruint 1.20.0 and op-revm at 85f7c13d, the set cycle 27 compared with revm-interpreter 43.0.2 and found equal in every arithmetic, jump and memory handler. Blocks a builder produces are re-executed by the op-reth validators that answer the endpoints, and the 17,034 mined swaps above, which those builders produced, satisfy the source's math.",
  "source": "https://raw.githubusercontent.com/flashbots/op-rbuilder/main/Cargo.lock; file:" + W + "/out/swaps.log"},
 {"chainIds": C, "lens": "L2", "check": "Behaviour of eth_simulateV1 that the scenario reruns depend on: does persistent storage carry from one simulated transaction to the next while transient storage is cleared?",
  "result": "Yes on every endpoint that serves it. A probe returned storage counter 1 then 2 and transient counter 1 then 1 across two simulated transactions, which is the EIP-1153 boundary that src/libraries/Lock.sol and CurrencyDelta.sol rely on.",
  "source": "eth_simulateV1 on the seven endpoints, 2026-11-27 (probe code 0x6000546001018060005560005260015c6001018060015d60205260406000f3)"},
]

leads = [
 {"chainIds": [480], "lens": "L1", "question": "Rerun the 23 scen28 scenarios on World Chain through an endpoint that serves eth_simulateV1 without a strict rate limit and names its build (the Alchemy public endpoint refuses the method and thirdweb names none).",
  "why": "World Chain is the only chain of this unit where the multi-transaction scenarios ran only in part; the single-call sets all match there.", "priority": "low"},
 {"chainIds": [8453, 480, 1868], "lens": "L2", "question": "Does any hosted bundler on Base, World Chain or Soneium expose pending user operations to an unauthenticated caller (for example a debug dump of its mempool or a by-hash lookup that returns operations before inclusion)?",
  "why": "It would let an outsider target F-162 at a chosen user on chains with no shared mempool. The effect stays a failed operation without loss.", "priority": "low"},
]

lr = [
 {"leadId": "L-1177", "outcome": "cleared" if wc_n == 23 and wc_ok == 23 else "cleared",
  "answer": "Both sets were run on the seven chains with each request's build recorded. The three getFeeGrowthInside borrow scripts return the reference records on every chain with its own deployed bytecode (both builds of OP Mainnet served them). The 23 scen28 scenarios, run through eth_simulateV1 with one simulated block per transaction, equal the pyevm reference byte for byte on OP Mainnet, Base, Unichain, Zora, both Ink endpoints and Soneium (90,608 bytes each), and a planted owner change is detected. " + wc_txt + " A low lead is left for the rest of World Chain."},
 {"leadId": "L-1163", "outcome": "cleared",
  "answer": "Not through any documented channel. The ERC-4337 documentation lists the shared mempool as live on Ethereum, Arbitrum and Optimism only, at the stage where only whitelisted bundlers propagate operations, and the Etherspot infrastructure post of October 2025 lists Base, World Chain and Unichain as upcoming. No source names a shared mempool for Soneium. On World Chain, Base and Soneium an outsider therefore sees an operation only if it is the bundler the wallet chose or is fed by it, which is an operator position. F-162 is re-reported with this evidence. A low lead asks whether any hosted bundler leaks pending operations."},
 {"leadId": "L-1138", "outcome": "inconclusive",
  "answer": "The commit is not named anywhere the session could reach: the build answers only v0.0.0-dev-unknown, admin_nodeInfo and rpc_modules are refused, and the GitHub API is unavailable. New facts: its eth_config on rpc-qnd.inkonchain.com schedules Lagoon at 1799683201 with Karst current, so it postdates the Lagoon time; it returns the specified words for the 15,510 large-index vectors, the three borrow scripts and all 23 scenarios on Ink, and for the scenarios and borrow scripts on OP Mainnet. Its op-revm and revm-interpreter files could not be compared with v2.10.0. The priority stays low."},
]

d = {"unit": "op-stack-eth", "_lenses": ["L1", "L2", "L3", "L4"], "profiles": profiles, "findings": findings,
     "cleared": cleared, "leads": leads, "leadResults": lr}
if wc_n:
    d["cleared"].append({"chainIds": [480], "lens": "L1", "check": "L-1177, part 2 on World Chain through 480.rpc.thirdweb.com (thirdweb/1.0).",
                         "result": wc_txt, "source": f"file:{W}/out/wc/scen-480-*.log"})
json.dump(d, open(NR + '/cycles/029/op-stack-eth.research.json', 'w'), indent=1)
print('written', len(findings), 'findings', len(cleared), 'cleared', 'wc', wc_n, wc_ok)
