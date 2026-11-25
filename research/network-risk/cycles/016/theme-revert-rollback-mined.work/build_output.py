"""Build cycles/016/theme-revert-rollback-mined.research.json from the raw results of this unit."""
import json, os
W = '/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/'
OUT = '/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.research.json'
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
S = json.load(open(W + 'raw/summary.json'))
NAMES = {n['chainId']: n['name'] for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
TRACE = {4217: 'https://rpc.mainnet.tempo.xyz', 56: 'https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3', 43114: 'https://avalanche.drpc.org',
         42161: 'https://arbitrum.drpc.org', 4663: 'https://robinhood.drpc.org', 10: 'https://optimism.drpc.org', 8453: 'https://base.drpc.org', 130: 'https://unichain.drpc.org'}
LOGS = {4217: 'https://rpc.mainnet.tempo.xyz', 56: 'https://bsc-rpc.publicnode.com', 43114: 'https://api.avax.network/ext/bc/C/rpc', 42161: 'https://arb1.arbitrum.io/rpc',
        4663: 'https://rpc.mainnet.chain.robinhood.com', 10: 'https://mainnet.optimism.io', 8453: 'https://base-rpc.publicnode.com', 130: 'https://mainnet.unichain.org'}
cleared, leads = [], []

# Task 1, one entry per network that serves call traces
for c in (4217, 56, 43114, 42161, 4663, 10, 8453, 130):
    v = S.get(str(c))
    if not v or 'scan' not in v: continue
    s = v['scan']; rp = v.get('replay')
    t = (f"{NAMES[c]}: {s['traced']} of {s['txs']} transactions that emitted PoolManager logs in blocks {s['blocks'][0]:,} to {s['blocks'][1]:,} were read with debug_traceTransaction (callTracer with logs). "
         f"In {s['undoneThenOkTx']} of them a frame into the PoolManager was undone (it or a frame above it failed) and a later PoolManager frame of the same transaction was not, "
         f"and in {s['revertedThenCompletedUnlockTx']} an unlock that had been entered and undone was followed by an unlock that completed. ")
    if c == 4217:
        t += ("Receipt status equals the trace status in every transaction. Every receipt carries one log more than the trace, a TIP-20 Transfer from pathUSD to the fee manager 0xfeec000000000000000000000000000000000000 at the end, which is the fee the protocol charges outside the call tree; "
              "with that log removed the receipt logs equal the surviving trace logs in order in all 51 transactions checked. The reference replay cannot run Tempo transactions, because the TIP-20 tokens the pools use are precompiles (code 0xef at 0x20c0...) that pyevm does not implement. ")
    else:
        t += f"Receipt status differs from the trace in {s['statusMismatch']} and receipt logs differ from the surviving trace logs in {s['logsMismatch']}. "
    if rp and rp['replayed']:
        t += (f"{rp['replayed']} of the transactions were rerun whole in the reference interpreter from the prestateTracer state of the parent block ({rp['withRevertedThenCompletedUnlock']} with a reverted and then completed unlock, {rp['withUndonePayment']} with sync, settle, take or mint inside an undone frame, {rp['undonePmFramesInReplayed']} undone PoolManager frames in all). "
              f"The own success flag of all {rp['pmFrames']} PoolManager frames is the same in order, the top level status is the same in {rp['statusEqual']}, "
              f"and the final value of all {rp['slots']} storage slots the chain changed ({rp['pmSlots']} of them PoolManager slots) is the same, with {rp['storageMismatch']} differences. "
              f"Logs are equal in {rp['logsEqual']}; ")
        if rp['logsDifferOnlyInEntryPoint']: t += f"in the other {rp['logsDifferOnlyInEntryPoint']} the only difference is the gas figures in the ERC-4337 EntryPoint UserOperationEvent, because the reference does not model gas. "
        else: t = t.rstrip('; ') + '. '
        un = [u for u in rp['unsupported']]
        if un: t += f"{len(un)} more could not be rerun ({'; '.join(sorted(set(un)))[:220]}). "
    ex = (v.get('exampleRevertedThenCompletedUnlock') or [])[:2]
    res = ("No transaction shows a later PoolManager frame that succeeds on the chain and fails in the reference, or the other way round, so neither the block producer nor the tracing node kept an unlock flag, delta, count or synced reserve of an undone frame. "
           "src/libraries/Lock.sol:10-27, NonzeroDeltaCount.sol:12-32, CurrencyDelta.sol:28-41 and CurrencyReserves.sol:15-38 get the rollback they rely on, and unlock (src/PoolManager.sol:104-114) saw a locked manager after each undone unlock.")
    if c == 4217: res = ("In the one hit, 0xba5c0224452fbe54eb5198aad0bba1cf5a4b86db6e40eb4f4265024a79bdfa27, an unlock that swapped reverted and the next unlock (take, sync, settle, swap) completed on chain with status 1, which it could not have done had the unlock flag survived (src/PoolManager.sol:105). "
                         "The receipt the producer wrote agrees with the trace the RPC node computed. There is no independent reference rerun on Tempo, so the check rests on the node's own re-execution and the producer's receipt.")
    if c == 42161:
        t = t.replace(f"in blocks {s['blocks'][0]:,} to {s['blocks'][1]:,}", f"in blocks {s['windows'][0][0]:,} to {s['windows'][0][1]:,} and {s['windows'][1][0]:,} to {s['windows'][1][1]:,}, each traced within seconds of its block because https://arbitrum.drpc.org answers 'historical state is not available' for older ones,")
        res = ("In the hit, 0x33050352c9e5c462c3f86d454679d163a822785ba932ba6b8f3dae35c12dfd4b, an unlock that ran sync, settle, swap and take reverted and the next unlock ran sync, settle, swap and take and completed with status 1, which it could not have done had the unlock flag survived (src/PoolManager.sol:105) or had a delta survived (src/PoolManager.sol:112). "
               "The reference rerun of this transaction was not made: the immediate rerun failed on an import error in this unit's script, and by the time it was repeated the endpoint had dropped the parent state. The Robinhood Chain reruns above cover the Nitro rollback by reference; that chain reported the same Nitro release as Arbitrum One in the cycle 12 critic note of state/ledger.json.")
    if c == 130: res = ("No reverted unlock occurs in the window; the undone frames are extsload reads inside quotes that reverted. " + res)
    src = f"debug_traceTransaction and eth_getTransactionReceipt on {TRACE[c]} and eth_getLogs on {LOGS[c]}, 2026-11-25" + ((", examples " + ", ".join(ex)) if ex else '') + "; prestateTracer reruns in cycles/016/theme-revert-rollback-mined.work/replay.py with pyevm_tx.py; src/PoolManager.sol:104-114"
    cleared.append({"chainIds": [c], "lens": "L2", "check": "Task 1, mined transactions with a reverted and then completed PoolManager frame: " + t.strip(), "result": res, "source": src})

# networks with no trace access
cleared_no = {
    5042: "Arc: https://rpc.mainnet.arc.io answers debug_traceTransaction, debug_traceCall and eth_simulateV1 with -32601 method not supported, and https://arc.drpc.org answers 400 Bad Request for both tracers. No mined transaction of this shape can be identified from receipts, because an undone frame leaves no log.",
    99901: "Elysium: https://rpc.elysium.kinetiq.xyz answers debug_traceTransaction and debug_traceCall with HTTP 401 Unauthorized; it serves eth_simulateV1, which re-executes on the endpoint and is not producer evidence.",
    42220: "Celo: the PoolManager emitted logs in 149 transactions over the 145,000 blocks before 83,683,500 and in none of the last 4,000 blocks. https://celo-json-rpc.stakely.io and https://celo.api.onfinality.io/public accept debug_traceTransaction but answer 'state at block #83,672,348 is pruned' for a transaction about 11,000 blocks old; https://forno.celo.org answers 403 and https://celo-rpc.publicnode.com answers -32601.",
}
for c, txt in cleared_no.items():
    leads.append({"chainIds": [c], "lens": "L2", "question": f"Find a mined {NAMES[c]} transaction in which an undone PoolManager unlock is followed by a completed unlock, through an archive trace endpoint or an explorer that lists failed internal calls. {txt}",
                  "why": "Task 1 of this unit could not be answered on this network. Simulated calls (callsem.py, and the halt sweep of this unit) show the rollback on the RPC node; no producer evidence exists for it.", "priority": "low"})

leads.append({"chainIds": [4217, 8453, 4663, 42161], "lens": "L2",
  "question": "Extend the whole-transaction reference rerun (pyevm_tx.py) with models of the node-implemented contracts it stopped at, TIP-20 tokens on Tempo, B20 tokens on Base and ArbGasInfo (0x6c) on the Nitro chains, and rerun the reverted-then-completed unlock transactions it could not run, starting with Tempo 0xba5c0224452fbe54eb5198aad0bba1cf5a4b86db6e40eb4f4265024a79bdfa27.",
  "why": "On these networks the producer evidence for rollback of an undone frame rests on the node's own trace for the transactions that use precompile tokens, which are the pools whose token state the reference cannot follow. Constructed calls show that B20 and TIP-20 transfers roll back, so the expected answer is no difference.", "priority": "low"})

# Task 2
H = json.load(open(W + 'raw/halt_all.json')); F = json.load(open(W + 'raw/halt_fix.json'))
att = sum(r['sweepAttempts'] + F.get(str(r['chain']), {}).get('attempts', 0) for r in H)
fails = sum(r['sweepFails'] + F.get(str(r['chain']), {}).get('fails', 0) for r in H)
leaks = sum(r['sweepLeaks'] + F.get(str(r['chain']), {}).get('leaks', 0) for r in H) + sum(len(r['kindsLeak']) for r in H)
gs = {r['chain']: r['successGas']['1'] for r in H}
cleared.append({"chainIds": ALL, "lens": "L2",
  "check": ("Task 2, halts other than REVERT, constructed with eth_call and state overrides against the deployed PoolManager of each of the 21 networks (HaltProbe.sol, halt.py, halt_fix.py in the work directory). A probe frame writes its own transient slot and then either (variant 1) enters unlock and, in the callback, mints 5 claims, syncs a currency and writes a second slot, or (variant 2) syncs a currency outside unlock, and then halts. "
            "Kinds: REVERT as control, INVALID (0xfe), stack overflow by unbounded internal recursion, out of gas by an endless loop, and, under STATICCALL, a TSTORE by the probe, PoolManager.sync and PoolManager.unlock. A later frame then reads the unlock flag, the nonzero delta count, the probe's delta, the synced currency and reserves with exttload (src/Exttload.sol:10-15), the probe's claim balance and the probe's own two slots. "
            f"In a second test the call into the probe was given every gas value from 1 up to the first value at which it succeeds (step 1 over the last 8,000 gas below that value and step 9 or coarser below), so that out of gas falls at every reachable point inside the PoolManager, the callback and the balanceOf staticcall: {att:,} attempts, {fails:,} of them failing. "
            f"The first successful gas is {gs[1]:,} on most networks, {gs[143]:,} on Monad, {gs[4326]:,} on MegaETH and {gs[4217]:,} on Tempo, where creating a storage slot costs more."),
  "result": (f"No leak on any network: {leaks} failed attempts read back a write. The successful controls show every written slot (synced currency 0x{0xc0ffee16:040x} and reserves 1000 plus the attempt id, the probe slots 7 and 9), so the reads can see a write that survives. "
             "A static call into PoolManager.sync or unlock fails at its first TSTORE (src/libraries/Lock.sol:13, src/libraries/CurrencyReserves.sol:29-30) and writes nothing, so a static violation cannot leave a write by construction. PoolManager never catches a failed callee: the hook call bubbles the failure (src/libraries/Hooks.sol:134-137), token and native payouts revert (src/types/Currency.sol:48-52 and 73-83), and the callback is a plain high level call (src/PoolManager.sol:110), so a halt in any of them reverts the whole unlock. "
             "On MegaETH the simulated call runs on the RPC node, not the closed sequencer (OPCODES.md, MegaETH row)."),
  "source": "eth_call with state overrides on the rpc URL of each network in state/networks.json, 2026-11-25, results in cycles/016/theme-revert-rollback-mined.work/raw/halt_all.json and raw/halt_fix.json; https://eips.ethereum.org/EIPS/eip-1153 (a reverted frame undoes its transient writes and those of inner calls); src/libraries/Lock.sol:10-27; src/PoolManager.sol:104-114, 279-288"})
dep = {r['chain']: r['depth'] for r in H}
cleared.append({"chainIds": ALL, "lens": "L2",
  "check": "Task 2, call depth 1024: how deep a chain of self calls with all gas gets under a 30,000,000 gas eth_call, and what the PoolManager does when a call it makes fails for depth.",
  "result": (f"The chain stops at depth 358 on 18 networks, 357 on Tempo and 291 on MegaETH (98/100 forwarding), well short of 1,024, because each level keeps 1/64 of the gas: (63/64)^1024 is 9.9e-8, so reaching depth 1,024 needs about 10^10 gas at the top, and (98/100)^1024 is 1.0e-9 on MegaETH. "
             "Where depth were reached, the failed outgoing call returns 0 without halting the PoolManager frame, and every outgoing call of the PoolManager turns a failure into a revert (src/libraries/Hooks.sol:137, src/types/Currency.sol:52 and 83, src/PoolManager.sol:110), so the unlock reverts and its transient writes go with it."),
  "source": "eth_call depthRun() with state override on every rpc URL in state/networks.json, 2026-11-25 (raw/halt_all.json); src/libraries/Hooks.sol:131-137; src/types/Currency.sol:40-83"})
TR = json.load(open(W + 'raw/token_rollback.json'))
cleared.append({"chainIds": [8453, 4217, 42220, 5042], "lens": "L2",
  "check": ("Tokens the node implements natively, inside frames that revert or halt: the probe TokenRollbackProbe.sol was placed by state override at the PoolManager address of Base, Tempo, Celo and Arc so that it holds what the PoolManager holds, and it transferred 1 unit of Base B20 OUSD (0xB2000000000000000000002fEb517dFeC7415344) and AMDc (0xb2000000000000000000000d8ce462e99ee7a47b), Tempo TIP-20 pathUSD (0x20c0000000000000000000000000000000000000), the CELO ERC-20 face (0x471EcE3750Da237f93B8E339c536989b8978a438) and the Arc USDC face (0x3600000000000000000000000000000000000000) "
            "inside a frame that then reverted, hit INVALID, overflowed the stack or ran out of gas, and under STATICCALL; on Celo and Arc also a native value transfer read back through the face. A take or settle inside an undone frame is only safe if these precompile balances roll back with the transient delta."),
  "result": ("All eight cases roll back: in every halted or static case the sender and recipient balances of both faces read afterwards equal those before, and the successful control moves one unit (raw/token_rollback.json). Ethereum USDC was run as a bytecode control with the same result. "
             "On Arc a native transfer of 1 wei lowers the sender's face balance by one face unit (10^12 wei) and the recipient's face shows 0, because the face reports floor(balance / 10^12); this is the rounding of the existing two-face hazard (F-100, F-108), and one face unit is worth 10^-6 USDC, far below the gas of a round."),
  "source": "eth_call with state overrides on https://base-rpc.publicnode.com, https://rpc.mainnet.tempo.xyz, https://forno.celo.org and https://rpc.mainnet.arc.io, 2026-11-25; src/PoolManager.sol:291-297, 349-364; src/types/Currency.sol:60-94"})
cleared.append({"chainIds": [42161, 4663, 10, 8453, 56, 4217], "lens": "L2",
  "check": "Task 2 on mined data: out of gas inside a hook, token or callback frame below a PoolManager frame. The call trees of all scan hits on OP Mainnet, Robinhood Chain, Base, BNB Smart Chain and Tempo were walked for failed frames below a PoolManager frame (ooghunt.py).",
  "result": "No out of gas below a PoolManager frame occurs in these transactions; every failure is a REVERT. 20 failures are under an unlock that itself reverted, as the source requires (src/PoolManager.sol:110). Two on Base sit below a successful swap: hook 0xd6155ce86ff3a33f52493e08cf77d7bbdf21fffc caught a reverting call of its own (selector 0xda1e42b9) and answered the PoolManager normally, so the PoolManager caught nothing; both transactions replay equal in the reference. The out of gas case was therefore tested by construction in the gas sweep above.",
  "source": "debug_traceTransaction callTracer on https://optimism.drpc.org, https://robinhood.drpc.org, https://base.drpc.org, https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3 and https://rpc.mainnet.tempo.xyz for the hits in raw/scan_*.json, 2026-11-25; txs 0x9c802e8addf18f375cc3fb5d806300069b98cf76098aa0b91ab3ec5910aa1c50 and 0x9e28af105e45706fb75e46937a1247599acc484e230ab0a995fee0e4edb62415 on Base; src/libraries/Hooks.sol:134-137"})

# Task 3
AA = {c: json.load(open(W + f)) for c, f in ((8453, 'raw/aa2_8453.json'), (1, 'raw/aa2_1.json'), (137, 'raw/aa2_137.json'), (42161, 'raw/aa2_42161.json'), (10, 'raw/aa2_10.json'), (4663, 'raw/aa_4663.json'), (130, 'raw/aa_130.json'))}
aa_txt = "; ".join(f"{NAMES[c]} {a['pmTxs']:,} PoolManager transactions in blocks {a['blocks'][0]:,} to {a['blocks'][1]:,}, {a['bundles']} bundles, {a['multiSenderBundles']} with two or more senders, {len(a['sharedPm'])} where two senders reached the PoolManager" for c, a in AA.items())
SYNC = ("sync needs no unlock and leaves the synced currency and reserves in transient storage until a settle by anyone resets it (src/PoolManager.sol:279-288, 349-364). A first party that leaves a sync gains nothing: settle credits msg.sender or the named recipient (src/PoolManager.sol:300-307, 364), so a credit from a stale sync goes to the second party. "
        "The second party can lose only through its own integration. If it pays native value without its own sync, settle reverts with NonzeroNativeValue (src/PoolManager.sol:356, recorded as F-071). If it pays an ERC-20 without syncing first, it is credited the balance change since the first party's sync: a take of its own after that sync makes the subtraction at src/PoolManager.sol:360 revert or under-credits it, and unlock then reverts with CurrencyNotSettled (src/PoolManager.sol:112). No path moves another user's pool balance or claims.")
cleared.append({"chainIds": ALL, "lens": "L2",
  "check": ("Task 3, ERC-4337 bundles on every network, which join several users' operations into one transaction. Whether transient storage is cleared between operations, and a mined bundle in which two unrelated senders' operations both called the PoolManager. Bundles among PoolManager transactions (UserOperationEvent of EntryPoint 0.6, 0.7 and 0.8, aa.py): " + aa_txt + "."),
  "result": ("Transient storage is not cleared between operations: EIP-1153 discards it only at the end of the transaction, and the EntryPoint runs every operation as a nested call of the one handleOps transaction. The unlock flag and the deltas cannot pass from one operation to the next, because unlock clears the flag and requires every delta to be zero before it returns (src/PoolManager.sol:104-114). Only the synced currency and reserves can. "
             "No mined bundle with two senders' PoolManager calls was found: the only multi-sender bundles have one operation that reaches the PoolManager, for example Base 0x61046bec99fa8dc23efda3e63f0bedc7e18b233fb191c09ff26edfbaced2b66c (EntryPoint 0.6, senders 0x0de04d745d88dc18e7c519f1935a3e27917e795f and 0xcbeebaf9d1f94a6678dad25e14afd2fb042bc579, only the second calls unlock, sync, settle, swap, mint and take). " + SYNC),
  "source": "https://eips.ethereum.org/EIPS/eip-1153; eth_getLogs, eth_getTransactionReceipt and debug_traceTransaction on the endpoints in aa.py, 2026-11-25 (raw/aa2_*.json, raw/aa_*.json); src/PoolManager.sol:104-114, 279-288, 300-307, 349-364"})
cleared.append({"chainIds": [4217], "lens": "L2",
  "check": "Task 3, Tempo type 0x76 batched and sponsored transactions: does transient storage survive between the calls of a batch, and can two unrelated users share it?",
  "result": ("The calls of a batch share one transient map: execute_batch takes one checkpoint before the first call, runs every call with the transaction's caller as sender, rolls the checkpoint back when any call fails and keeps all writes otherwise (handler.rs execute_batch, lines 1284-1366 on main). Every call has the same msg.sender, so only the signer's own calls share the state, and a fee sponsor pays fees without becoming a caller. "
             "Two unrelated users cannot share a batch, so no mined transaction of that kind can exist; zone portal batches are the one Tempo context that joins parties and are recorded as F-135. " + SYNC),
  "source": "https://raw.githubusercontent.com/tempoxyz/tempo/main/crates/evm/src/handler.rs (execute_batch, lines 1267-1366), fetched 2026-11-25; src/PoolManager.sol:279-288, 349-364"})
cleared.append({"chainIds": [999], "lens": "L2",
  "check": "Task 3, HyperEVM system transactions: are they joined with user transactions so that transient storage is shared?",
  "result": "No. The public replay client builds the environment for each system transaction and each signed transaction separately, calls transact once per transaction and commits state after each (run.rs lines 99-168 and the loop over system_txs at line 217). Each system transaction is its own transaction and starts with empty transient storage, so nothing joins it with a user's PoolManager call. The validator itself is closed (F-120).",
  "source": "https://raw.githubusercontent.com/hyperliquid-dex/hyper-evm-sync/main/src/run.rs, fetched 2026-11-25; src/libraries/Lock.sol:10-27"})
cleared.append({"chainIds": [10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196], "lens": "L2",
  "check": "Task 3, OP Stack deposit transactions: are deposits joined with other transactions?",
  "result": "No. The deposit specification processes each deposit as a transaction of its own with its own receipt, sender and gas accounting, and the revm journal used by op-reth clears transient storage in commit_tx, discard_tx and finalize at the end of every transaction (inner.rs lines 141, 174 and 207) and restores it on checkpoint_revert (line 622). A deposit therefore shares no transient state with a user's PoolManager call.",
  "source": "https://specs.optimism.io/protocol/deposits.html; https://raw.githubusercontent.com/bluealloy/revm/main/crates/context/src/journal/inner.rs, both fetched 2026-11-25"})
cleared.append({"chainIds": [42161, 4663, 99901], "lens": "L2",
  "check": "Task 3, Arbitrum retryable redeems, automatic and manual: does a redeem run inside the transaction that scheduled it?",
  "result": "No. A redeem is returned by TxProcessor.ScheduledTxes as a new transaction (tx_processor.go lines 924-957) and the block processor applies it after the originating transaction as a transaction of its own, keeping the group's redeems and checkpoint (block_processor.go lines 91 and 126-159), and every transaction passes through StateDB.Prepare, which resets transient storage before code runs (state_transition.go lines 735-736). A redeem shares no transient state with the transaction that created or redeemed it.",
  "source": "https://raw.githubusercontent.com/OffchainLabs/nitro/master/arbos/block_processor.go; https://raw.githubusercontent.com/OffchainLabs/nitro/master/arbos/tx_processor.go; https://raw.githubusercontent.com/OffchainLabs/go-ethereum/master/core/state_transition.go, all fetched 2026-11-25"})
cleared.append({"chainIds": ALL, "lens": "L1",
  "check": "The reference interpreter tools/opdiff/pyevm.py, used by earlier cycles to judge PoolManager behaviour, was extended here for whole mined transactions and gave one wrong result first.",
  "result": ("pyevm.py gives a DELEGATECALL frame CALLVALUE 0 instead of the value of the calling frame (tools/opdiff/pyevm.py:205 passes 0 as value). This unit's copy (pyevm_tx.py) carries the value through and also adds block context, logs, ecrecover, modexp, EIP-7702 designators and an approximate GAS. The PoolManager build contains no DELEGATECALL (OPCODES.md, bytecode census), and the delegate calls of pmdiff6.py run inside the unlock callback, which the PoolManager calls without value, so no earlier PoolManager comparison is affected."),
  "source": "tools/opdiff/pyevm.py:195-205; tools/opdiff/pmdiff6.py:5-6 and 62; research/network-risk/OPCODES.md:146"})

rep = [v['replay'] for v in S.values() if 'replay' in v]
nrep = sum(r['replayed'] for r in rep); nrtc = sum(r['withRevertedThenCompletedUnlock'] for r in rep); npm = sum(r['pmFrames'] for r in rep); nsl = sum(r['slots'] for r in rep)
lr = [{"leadId": "L-547", "outcome": "inconclusive",
       "answer": ("Answered on eight of the eleven networks the task names, with a reverted and then completed unlock on seven. Mined transactions in which an undone unlock is followed by an unlock that completes exist on Tempo (0xba5c0224452fbe54eb5198aad0bba1cf5a4b86db6e40eb4f4265024a79bdfa27), BNB Smart Chain (18 of 1,490 traced), Avalanche (0x95051c7cb718ea109a63be8c55a7b51d7e1306def99fd5b7e59b35308f0c25a6), Arbitrum One (0x33050352c9e5c462c3f86d454679d163a822785ba932ba6b8f3dae35c12dfd4b), Robinhood Chain (2), OP Mainnet (2) and Base (6), and in every one the later unlock completed. "
                  "Unichain had undone frames that were extsload reads only. "
                  f"{nrep} such transactions were rerun whole in the reference interpreter from parent-block state, {nrtc} of them with a reverted and then completed unlock: all {npm} PoolManager frames end the same way and all {nsl} changed storage slots end equal. "
                  "Arc, Elysium and Celo remain open: Arc and Elysium serve no trace method to the public, and Celo's tracing endpoints have pruned the state of every PoolManager transaction within reach. "
                  f"Halt kinds other than REVERT leak nothing on any of the 21 networks in {att:,} constructed attempts.")}]
doc = {"unit": "theme-revert-rollback-mined", "profiles": [], "findings": [], "cleared": cleared, "leads": leads, "leadResults": lr}
json.dump(doc, open(OUT, 'w'), indent=1)
print('written', len(cleared), 'cleared', len(leads), 'leads')
