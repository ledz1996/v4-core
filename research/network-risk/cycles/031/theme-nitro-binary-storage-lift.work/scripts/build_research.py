"""Writes cycles/031/theme-nitro-binary-storage-lift.research.json from the outputs in ../out. usage: python3 -I build_research.py"""
import json
W = '/home/user/v4-core/research/network-risk/cycles/031/theme-nitro-binary-storage-lift.work/'
O = W + 'out/'
R = 'research/network-risk/cycles/031/theme-nitro-binary-storage-lift.work/'
ts = {a: json.load(open(O + 'ts-%s.json' % a)) for a in ('amd64', 'arm64')}
FAULTS = ['revert_zero', 'skip_journal', 'snap_off_by_one', 'key_limb', 'equal_skip_inverted']
fl = {a: {f: len(json.load(open(O + 'ts-fault-%s-%s.json' % (a, f)))['mismatches']) for f in FAULTS} for a in ts}
live = {k: json.load(open(O + 'live-%s.json' % k)) for k in ('42161', '42161-b', '4663', '4663-b')}
un = {}
for a in ('amd64', 'arm64'):
    try:
        un[a] = json.load(open(O + 'unreached-%s-extra.json' % a))
    except FileNotFoundError:
        un[a] = None
namecmp = json.load(open(O + 'namecmp.json'))
NITRO = [42161, 4663]


def livesum():
    out = []
    for k, d in live.items():
        v = d['variants']
        out.append('%s block %d, before %s, after %s: settled %s, kept %s, nested %s' % (
            d['url'], d['block'], d['clientBefore']['result'], d['clientAfter']['result'],
            v['settled']['equal'], v['kept']['equal'], v['nested']['equal']))
    return '; '.join(out)


def uncounts(a):
    d = un[a]
    if not d:
        return 'not run'
    return ', '.join('%s %s' % (f, v['counts']['arithmetic']) for f, v in d['functions'].items() if v['counts']['arithmetic'])


t = ts['amd64']
cleared = [
    {"chainIds": NITRO, "lens": "L2",
     "check": "Transient storage path of the Nitro b72783f release binaries run in the cycle 30 x86-64 and AArch64 models: opTstore, opTload, (*StateDB).SetTransientState, (*StateDB).GetTransientState, (*journal).append, (*journal).revert and the transientStorageChange revert and mutation methods, with the StateDB and journalEntry interface calls dispatched through the itabs read from each file. Go runtime map calls were stubbed (runtime.mapaccess1, mapassign, mapdelete, memequal, convTnoptr, growslice, mallocgcSmallNoScanSC3). %d sequences (seed 31_1211_01) over the PoolManager's delta slots keccak256(target, currency), the NonzeroDeltaCount, Lock and two reserves slots, and slots one limb or one byte away from a delta slot, with nested snapshots, reverts of inner frames, commits and %d writes of an equal value." % (t['sequences'], t['equalWrites']),
     "result": "Every one of %d reads per architecture equals tools/opdiff/pyevm.py after %d stores and %d reverts, no model error. Planted faults were caught on both architectures (mismatching sequences amd64/arm64): revert writes zero %d/%d, journal entry skipped %d/%d, snapshot index off by one %d/%d, TLOAD key loses 16 bytes %d/%d, equal-value skip inverted %d/%d. The binary keys the map by the 52-byte (address, slot) struct: the map type's key size is 52 and its hasher and equal closures are memhash_varlen and memequal_varlen over 52 bytes. SetTransientState returns early only when the stored word equals the new one, journals (address, slot, previous) before writing, and deletes the entry when the new word is zero. journal.revert undoes entries newest first down to the snapshot index and truncates the journal there; revertToSnapshot passes revision.journalIndex and truncates validRevisions to the found index. A delta written in a reverted frame does not survive in either build, so src/libraries/CurrencyDelta.sol:35-39, NonzeroDeltaCount.sol and Lock.sol read the committed word." % (
         t['reads'], t['stores'], t['reverts'], fl['amd64']['revert_zero'], fl['arm64']['revert_zero'], fl['amd64']['skip_journal'], fl['arm64']['skip_journal'],
         fl['amd64']['snap_off_by_one'], fl['arm64']['snap_off_by_one'], fl['amd64']['key_limb'], fl['arm64']['key_limb'],
         fl['amd64']['equal_skip_inverted'], fl['arm64']['equal_skip_inverted']),
     "source": R + "out/ts-amd64.json, out/ts-arm64.json, out/ts-fault-*.json, out/maptype.json, scripts/tsmodel.py, scripts/tsdrive.py; src/libraries/CurrencyDelta.sol:18-41"},
    {"chainIds": NITRO, "lens": "L2",
     "check": "Live eth_call with state overrides on the deployed PoolManagers of Arbitrum One and Robinhood Chain: a driver unlocks, initializes a pool of two never-deployed currencies, adds liquidity, swaps, lets a helper swap and revert (and in the nested variant a second helper inside it), reads delta slots, NonzeroDeltaCount, slot0 and liquidity with exttload and extsload, and settles with ERC-6909 burn and mint at the reference amounts. Reference is pyevm with storage and code loaded lazily at the same block, because neither endpoint serves debug_traceCall.",
     "result": "All three variants return the reference bytes on every run, including the reverted helper's storage writes to slot0 and liquidity and its transient deltas, and the kept variant reverts with the same data. Runs: " + livesum() + ". Both backend architectures answered.",
     "source": R + "out/live-42161.json, out/live-42161-b.json, out/live-4663.json, out/live-4663-b.json, scripts/live_nitro.py"},
    {"chainIds": NITRO, "lens": "L1",
     "check": "Control flow of opSload, opSstore, (*StateDB).GetState, SetState, (*stateObject).SetState and storageChange.revert, opCall, opStaticCall, opDelegateCall, opReturnDataCopy and (*EVM).Call, StaticCall, DelegateCall in both binaries, read from the disassembly with callee names from pclntab and interface method names from the *state.StateDB itab, compared with go-ethereum v1.17.10 core/vm/evm.go.",
     "result": "opSstore and opTstore test the read-only flag at evm+0x1a0 first; opSload and opTload call GetState and GetTransientState through itab offsets 0x130 and 0x150. EVM.Call takes Snapshot before Exist and the transfer, runs the precompile or resolveCode, SetCallCode with resolveCodeHash, Run, GasBudget.Exit, and calls RevertToSnapshot (itab 0x1a8) whenever the returned error is non-nil, then traceFrameExit, as in v1.17.10. A second RevertToSnapshot sits on the EIP-4762 code hash gas failure path. StaticCall does the zero AddBalance touch. DelegateCall has the same snapshot and revert. The call handlers absorb the child GasBudget with (*GasBudget).Absorb and refund state gas with (*Contract).refundState, which are v1.17 names. No Arbitrum-only callee appears in these functions.",
     "source": R + "out/icalls.txt, out/lst-amd64/vm.__EVM_.Call.s, https://raw.githubusercontent.com/ethereum/go-ethereum/v1.17.10/core/vm/evm.go"},
    {"chainIds": NITRO, "lens": "L1",
     "check": "Arbitrum-only additions in core/state and core/vm by function name: every function of the two packages in the amd64 pclntab compared with the function names in the go-ethereum v1.17.10 files of the same name, and every function from an _arbitrum.go file.",
     "result": "%d core/state and %d core/vm functions come from _arbitrum.go files (Stylus wasm activation and its journal entries, zombie accounts, recording, TxProcessor defaults, depth and return data accessors, Stylus gas helpers). %d core/state and %d core/vm functions in other files have no v1.17.10 name: transaction and address filtering (FilterTx, IsTxFiltered, TouchAddress, IsAddressFiltered), ExpectBalanceBurn/Mint, createZombie, the hooked StateDB forwards of these, (*Contract).Jumpdest, newArbitrumAmsterdamInstructionSet, makeDup and makePush closures. None of them is on the transient storage path, the storage journal path or the jump destination map. The journal revert has an Arbitrum zombie-entry branch reached only for createZombieChange entries." % (
         len(namecmp['arbitrumFiles']['state']), len(namecmp['arbitrumFiles']['vm']), len(namecmp['onlyInBinary']['state']), len(namecmp['onlyInBinary']['vm'])),
     "source": R + "out/namecmp.json, scripts/namecmp.py, https://raw.githubusercontent.com/ethereum/go-ethereum/v1.17.10/core/state/journal.go"},
    {"chainIds": NITRO, "lens": "L1",
     "check": "isCode and the jump destination map in both binaries (L-1206).",
     "result": "isCode returns the cached analysis when Contract.analysis is set; otherwise, when the 32-byte CodeHash at contract+0x70 is nonzero, it calls JumpDests Load(CodeHash) through the interface, and on a miss runs codeBitmapInternal over contract.Code (makeslice of len/8+5 bytes) and calls Store(CodeHash, bitmap); a zero CodeHash (initcode) gets a local analysis that is never stored. mapJumpDests.Load and Store use one map type keyed by the 32-byte hash. The bitmap is stored under the hash that EVM.Call sets with SetCallCode(resolveCodeHash(addr), resolveCode(addr)). Two codes share a bitmap only if their keccak256 hashes are equal. A scan of all amd64 text found no direct call to (*EVM).SetJumpDestCache, so the cache is the per-EVM map.",
     "source": R + "out/lst-amd64/vm.__Contract_.isCode.s, out/lst-amd64/vm.mapJumpDests.Store.s, out/xref-amd64.txt, https://raw.githubusercontent.com/ethereum/go-ethereum/v1.16.2/core/vm/contract.go"},
    {"chainIds": NITRO, "lens": "L1",
     "check": "L-1210: unreached uint256 instructions of udivrem, udivremBy1, udivremKnuth, Div, Mod, SMod, SDiv, SRsh, Exp, AddMod, MulMod, reduce4 and Reciprocal listed by address, after cycle 30's vector mix plus the targeted set and 35,428 aimed vectors (seed 31_1210_01: exponents of every bit length, signed division over all limb counts and signs, moduli of every limb count, SAR over all counts).",
     "result": "Remaining arithmetic instructions by function: amd64 %s; arm64 %s. Everything else unreached is stack growth or a bounds, divide or overflow panic. The aimed vectors reached the Exp bit-length branches for exponents whose top limb is limb 1 or 2 and the zero-result branches of SDiv and SMod, with no mismatch. The rest are paths that callers in uint256 v1.3.2 exclude: udivrem's divisor of length zero, numerator of length zero and numerator shorter than the divisor (Div, Mod and DivMod return before udivrem unless x > y > 0, AddMod passes a five-limb sum, MulMod passes eight limbs with a nonzero high half), the branch jumps that lead to panicBounds, and Reciprocal's early return for m[3] == 0 (MulMod calls it only when m[3] != 0). FullMath.mulDiv (src/libraries/FullMath.sol:24-48) issues MULMOD with modulus 2^256-1 or the denominator and DIV after the x > y checks inside the library, so it cannot reach these instructions." % (uncounts('amd64'), uncounts('arm64')),
     "source": R + "out/unreached-amd64-extra.json, out/unreached-arm64-extra.json, scripts/unreached.py, https://raw.githubusercontent.com/holiman/uint256/v1.3.2/uint256.go, https://raw.githubusercontent.com/holiman/uint256/v1.3.2/mod.go"},
    {"chainIds": NITRO, "lens": "L2",
     "check": "(*StateDB).Prepare of both binaries for the transient storage reset.",
     "result": "Prepare builds the access list when IsEIP2929 holds and then, on every path, stores a fresh map from runtime.makemap_small at StateDB+0xf0, the field that SetTransientState and GetTransientState read. It is reached through the hooked StateDB's Prepare. Transient deltas therefore start empty in each transaction.",
     "source": R + "out/lst-amd64/state.__StateDB_.Prepare.s, out/lst-arm64/state.__StateDB_.Prepare.s"},
    {"chainIds": NITRO, "lens": "L3",
     "check": "ArbOS TxProcessor hooks StartTxHook, GasChargingHook, EndTxHook and RevertedTxHook in the amd64 binary, by callee names.",
     "result": "The hooks move native balances (TransferBalance, MintBalance, takeFunds) between the sender, fee accounts, retryable escrow and deposit targets, and read or write ArbOS storage through StorageBacked types and l1pricing/l2pricing state. They call no transient storage method and write no account storage other than ArbOS state. A deposit or retryable to the PoolManager address can only add native balance, which the PoolManager credits to nobody until a caller syncs and settles, as on Ethereum. The hooks also route funds of filtered transactions to a configured recipient (FilteredFundsRecipientOrDefault), which needs chain governance.",
     "source": R + "out/lst-amd64/arbos.__TxProcessor_.StartTxHook.s, out/lst-amd64/arbos.__TxProcessor_.EndTxHook.s"},
]
leads = [
    {"chainIds": NITRO, "lens": "L2", "question": "Do storageChange.revert and (*stateObject).setState of the b72783f binaries restore the exact previous value and origin in the x86-64 and AArch64 models, including a slot written back to its original value and a slot of an account created in the same transaction?",
     "why": "This cycle ran the transient path in the models and covered storage rollback only by live eth_call. A stateObject model would close the binary side of the PoolManager's storage ledger.", "priority": "low"},
]
lr = [
    {"leadId": "L-1211", "outcome": "cleared", "answer": "The transient storage path and its journal revert of both b72783f binaries ran in the models on %d sequences and %d reads per architecture with no mismatch, and five planted faults were caught. Live eth_call on Arbitrum One and Robinhood Chain with a reverted inner swap returned the reference bytes on both backend architectures. SLOAD and SSTORE were read for control flow and checked live; the stateObject methods were not run in the model." % (t['sequences'], t['reads'])},
    {"leadId": "L-1210", "outcome": "cleared", "answer": "Unreached instructions were listed by address for both binaries. After aimed vectors the arithmetic ones left are udivrem's zero-length and short-numerator returns, two branch stubs leading to panicBounds, and Reciprocal's return for m[3] == 0, all excluded by the callers in uint256 v1.3.2; FullMath.mulDiv cannot produce those shapes."},
    {"leadId": "L-1205", "outcome": "cleared", "answer": "The call family and EVM.Call, StaticCall and DelegateCall take the snapshot before the callee runs and revert it on any error, as in go-ethereum v1.17.10, with no Arbitrum-only callee. The TxProcessor hooks touch balances and ArbOS state only."},
    {"leadId": "L-1206", "outcome": "cleared", "answer": "The jump destination bitmap is stored under the contract's 32-byte code hash in a per-EVM map; initcode is analysed locally. Two codes share a bitmap only on a keccak256 collision."},
]
res = {"unit": "theme-nitro-binary-storage-lift", "profiles": [], "findings": [], "cleared": cleared, "leads": leads, "leadResults": lr}
json.dump(res, open('/home/user/v4-core/research/network-risk/cycles/031/theme-nitro-binary-storage-lift.research.json', 'w'), indent=1)
print('written')
