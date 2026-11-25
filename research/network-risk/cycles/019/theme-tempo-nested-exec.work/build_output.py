#!/usr/bin/env python3
"""Writes ../theme-tempo-nested-exec.research.json from the readings and the probe outputs in this directory."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
T = 'https://raw.githubusercontent.com/tempoxyz/tempo/a9d6748/'
E = 'https://raw.githubusercontent.com/DaniPopes/evm2/35aa32800b147b00e616d4e1869a3835aa86701f/'
pl = json.load(open(os.path.join(H, 'probe_latest.json')))
pt = json.load(open(os.path.join(H, 'probe_t14.json')))
cr = json.load(open(os.path.join(H, 'carry.json')))
n_probe = len(pl['results'])
changed = sum(1 for r in pl['results'] + pt['results'] if r.get('changedByProbe'))
errors = sum(1 for r in pl['results'] + pt['results'] if r.get('error') or r.get('unexpected'))
ok_l = sum(1 for r in pl['results'] if r.get('probeSuccess') == 1)
ok_t = sum(1 for r in pt['results'] if r.get('probeSuccess') == 1)
carry_ok = all(c['calls'][1]['returnData'] == '0x' + '00' * 128 for c in cr['runs'])
assert changed == 0 and errors == 0 and carry_ok

cleared = [
 {"chainIds": [4217], "lens": "L2",
  "check": "Every non-test caller of enter_execution in evm2 35aa3280 (the was_running flag) and what it does with the transient storage map.",
  "result": "enter_execution (crates/evm2/src/evm/mod.rs:454-458) only sets running and the guard puts the old value back on drop (mod.rs:1230-1239). It has five callers: execute_precompile (mod.rs:407), inspect_log (mod.rs:969), execute_tx (mod.rs:1315), execute_message_inspected (mod.rs:1456) and run_interpreter (mod.rs:1854). Four of them run a precompile, an inspector hook, a message or an interpreter frame inside the transaction that is already running, on the same State and therefore on the same transient map, which is what a CALL does on Ethereum. The fifth, execute_tx, is the entry of a top-level transaction and is reached only from transact and transact_with_inspector. The flag exists so that setters can refuse changes while code runs (mod.rs:421-443). It does not start a second transaction.",
  "source": E + "crates/evm2/src/evm/mod.rs (lines 407, 454-458, 969, 1230-1239, 1315, 1456, 1854)"},
 {"chainIds": [4217], "lens": "L2",
  "check": "Where evm2 creates, clears and copies the transient map: clear_transaction_state, ExecutedTx resolution, committed_copy, take_transient_storage, rollback.",
  "result": "The map is a field of State (crates/evm2/src/evm/state/mod.rs:58-59). clear_transaction_state empties it with the journal, logs and warm sets (state/mod.rs:555-569). It runs when an executed transaction is committed, discarded or detached (tx.rs:222-245), when a transaction or system call fails (mod.rs:1318-1320, system.rs:133-136), after validate_tx (mod.rs:1346) and when the backing database is replaced (state/mod.rs:269-272 through Evm::set_database at mod.rs:700-702). committed_copy builds a new State with an empty map (state/mod.rs:135-150) and has no caller outside tests in evm2 or in the 578 Rust files of the Tempo workspace. take_transient_storage removes the slots of one named address (state/mod.rs:873-878). Each TSTORE is journaled (state/mod.rs:837-866) and rollback restores it (state/mod.rs:911-918), so a reverted frame or batch puts the PoolManager's slots back. Nothing clears the map between frames: execute_initial_frame in crates/evm2/src/ethereum/mod.rs contains no clearing step.",
  "source": E + "crates/evm2/src/evm/state/mod.rs (lines 58-59, 135-150, 555-569, 837-918), crates/evm2/src/evm/tx.rs:222-245"},
 {"chainIds": [4217], "lens": "L2",
  "check": "Every non-test caller of transact, call_tx, validate_tx, system_call, execute_system_call, committed_copy, set_database and take_transient_storage in the Tempo workspace at a9d6748 (all 52 members including consensus, payload builder, transaction pool, precompiles, precompile macros, zones) and in evm2 (including evm2-jit and evm2-inspectors).",
  "result": "None runs while a user transaction is on the call stack. Block level: the EIP-2935 history system call before the first transaction (crates/evm/src/block.rs:858-870) and the committee system call after the last one (block.rs:554-603, called from finish_with_block_access_list at block.rs:1043-1048); evm2's own block executor runs transact once per block transaction and its system calls before or after them (crates/evm2/src/block/ethereum/execution.rs:188, 213, 285-458). Separate EVM instances: the pool validator (crates/transaction-pool/src/validator.rs:572), the payload prewarm workers (crates/payload/builder/src/prewarming.rs:181-194), the zone sequencer, payload and RPC crates (crates/zones/evm/src/executor.rs:306, crates/zones/payload/src/builder.rs:865, crates/zones/payload/src/prewarming.rs:176, crates/zones/node/src/rpc/mod.rs:1507), genesis (crates/evm/src/genesis.rs:76, 104) and the fuzz harness. The system transaction handler calls execute_system_call as the body of the system transaction itself, at its start (crates/evm/src/handler/config.rs:512-536), and only for the fixed system signature (crates/primitives/src/transaction/envelope.rs:234-236). No precompile, the fee manager, the account keychain, the payment channel reserve, the T14 configurable account shim or the batch handler calls any of these functions. Evm::transact has no running check (mod.rs:1285-1288), so the guarantee rests on there being no such caller, which the search confirms for this revision.",
  "source": T + "crates/evm/src/block.rs (lines 554-603, 858-870, 1043-1048); crates/evm/src/handler/config.rs:512-536; search list in cycles/019/theme-tempo-nested-exec.work/callers_all.txt"},
 {"chainIds": [4217], "lens": "L2",
  "check": "Storage credit settlement drains transient slots at the end of a transaction (take_transient_storage).",
  "result": "settle_storage_credit_refunds takes only the slots of 0x1060000000000000000000000000000000000000 (crates/evm/src/handler/config.rs:444-490) and is called from settle_transaction (config.rs:251-256), which the AA handler calls after execute_batch has returned (crates/evm/src/handler.rs:1704-1720). By then every user frame, and so every PoolManager.unlock, has finished. The PoolManager's slots are keyed by its own address (state/mod.rs:832-838) and are never selected.",
  "source": T + "crates/evm/src/handler/config.rs:444-490 and crates/evm/src/handler.rs:1704-1720"},
 {"chainIds": [4217], "lens": "L2",
  "check": "Nested calls made by precompiles (TIP-20 zone deposit forwarding) and T14 batch calls: map shared, emptied or cleared?",
  "result": "The only precompile in production that calls user code is TIP-20 deposit_virtual (crates/precompiles/src/tip20/mod.rs:1073-1115), which goes through the storage provider's call (crates/precompiles/src/storage/evm.rs:677-740). That runs a message with Host::execute_call on the same Evm, so it shares the map like a CALL and is journaled; the provider refuses it inside a checkpoint or past the nested call limit (evm.rs:689-695), and deposit_virtual refuses it from inside another precompile (tip20/mod.rs:1081-1088). The callee sees msg.sender equal to the token, so a reentry into the PoolManager from the portal has the token as its own locker with its own deltas, which is ordinary CALL semantics; the payout side of that path is F-135. A batch of calls in one Tempo transaction runs each call as a top-level frame on the same State under one checkpoint (crates/evm/src/handler.rs:1284-1371) with the same sender, which matches a smart account multicall on Ethereum: an unlock has relocked before its call returns (src/PoolManager.sol:104-114), and a sync left open by one call of the batch belongs to the same sender.",
  "source": T + "crates/precompiles/src/storage/evm.rs:677-740; crates/precompiles/src/tip20/mod.rs:1073-1115; crates/evm/src/handler.rs:1284-1371"},
 {"chainIds": [4217], "lens": "L2",
  "check": f"Read-only probe: driver unlocks the PoolManager, syncs pathUSD and mints 1 to open a delta, then calls {n_probe} precompile and control paths and reads the lock, delta count, synced currency, reserves and its delta with exttload before and after, on eth_call at latest and on eth_simulateV1 at block time 1796745600 (T14 rules).",
  "result": f"In all {2 * n_probe} runs the five slots after the probe call equal the slots before it: lock 1, count 1, currency pathUSD, reserves as synced, delta -1. {ok_l} of {n_probe} probe calls succeeded at latest and {ok_t} at T14 time, the rest reverted inside the precompile and were rolled back without touching the PoolManager's slots. The paths include TIP-20 approve, transfer and a transfer to a zone-style address, fee manager setUserToken, storage credit setBudget, keychain revokeKey, DEX withdraw, the channel reserve, the T14 configurable account address, and a contract that writes SSTORE and TSTORE. Endpoint tempo/v1.19.1-a9d6748 before and after. A second simulation left pathUSD synced at the end of one transaction and read all four slots as zero in the next transaction of the same block, at latest and at T14 time.",
  "source": "rpc https://rpc.mainnet.tempo.xyz eth_call and eth_simulateV1, cycles/019/theme-tempo-nested-exec.work/probe_latest.json, probe_t14.json, carry.json"},
]

out = {
 "unit": "theme-tempo-nested-exec",
 "profiles": [],
 "findings": [],
 "cleared": cleared,
 "leads": [
  {"chainIds": [4217], "lens": "L2",
   "question": "At each Tempo release after v1.19.1 (the T15 release and any that moves the evm2 revision), does any precompile, handler hook or block step call Evm::transact, call_tx, validate_tx, system_call, set_database or State::committed_copy while a transaction is running?",
   "why": "evm2's transact has no running check (crates/evm2/src/evm/mod.rs:1285-1288) and an ExecutedTx clears the whole transient map when it resolves (tx.rs:222-245). One such caller reachable from a user call would reset the PoolManager's lock and delta count inside an open unlock (src/PoolManager.sol:112), and the safety on Tempo rests only on the absence of callers, which this cycle checked for a9d6748 alone.",
   "priority": "low"}
 ],
 "leadResults": [
  {"leadId": "L-874", "outcome": "cleared",
   "answer": "Every non-test caller of enter_execution, transact, call_tx, validate_tx, system_call, execute_system_call, committed_copy, set_database and take_transient_storage in evm2 35aa3280 and the whole Tempo workspace at a9d6748 was listed. enter_execution is a reentrancy flag for precompiles, inspector hooks, messages and frames of the running transaction, which share the transient map as a CALL does. No production code starts a transaction while a user transaction runs: system calls run before or after the block's transactions, the system transaction handler is itself a top-level transaction, and pool, prewarm, zone and RPC paths use separate EVM instances. committed_copy has no production caller. take_transient_storage drains only the storage credit precompile's slots after all user frames. A read-only probe on 28 precompile and control paths at latest and at T14 time changed no PoolManager transient slot, and transient state does not carry between simulated transactions."},
  {"leadId": "L-325", "outcome": "cleared",
   "answer": "The remaining parts were read at the current revisions (evm2 35aa3280, Tempo a9d6748): evm2-jit, evm2-inspectors and the other evm2 crates, crates/consensus, crates/zones/node and the precompile macro crate contain no non-test call of committed_copy, call_tx, transact, set_database (mod.rs:700-702) or the other entry points during a user call. The database replacement has no production caller at all."}
 ]
}
dst = os.path.join(H, '..', 'theme-tempo-nested-exec.research.json')
json.dump(out, open(dst, 'w'), indent=1)
print('wrote', os.path.abspath(dst))
