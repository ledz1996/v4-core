"""Builds theme-go-binaries-storage-journal.research.json from the outputs in out/."""
import json, glob, os
W = '/home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work/'
OUTF = '/home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.research.json'
R = 'research/network-risk/cycles/032/theme-go-binaries-storage-journal.work/'
nets = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))
nets = nets if isinstance(nets, list) else nets.get('networks', nets)
ALL = [n['chainId'] for n in nets]
GO = [56, 137, 43114]
OTHERS = [c for c in ALL if c not in GO + [42161, 4663]]


def j(p):
    return json.load(open(W + p))


ts = {os.path.basename(p)[:-5]: j('out/ts/' + os.path.basename(p)) for p in sorted(glob.glob(W + 'out/ts/*.json'))}
st = {os.path.basename(p)[:-5]: j('out/st/' + os.path.basename(p)) for p in sorted(glob.glob(W + 'out/st/*.json'))}
kk = {os.path.basename(p)[:-5]: j('out/kk/' + os.path.basename(p)) for p in sorted(glob.glob(W + 'out/kk/*.json'))}
fs = []
for p in sorted(glob.glob(W + 'out/faults/summary-*.json')):
    fs += json.load(open(p))
kf = {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(W + 'out/faults/kk-*.json'))}
live = {c: j('out/live-%d.json' % c) for c in (56, 137, 43114, 42161, 4663)}


def tsline(k, r):
    return '%s: %d sequences, %d reads, %d stores, %d reverts, %d equal-value writes, %d mismatches, %d model errors, map key sizes %s' % (
        k, r['sequences'], r['reads'], r['stores'], r['reverts'], r['equalWrites'], len(r['mismatches']), len(r['errors']),
        sorted({x[1] for x in r['mapKeySizes'] or []}))


ts_txt = '; '.join(tsline(k, r) for k, r in ts.items())
ts_bad = sum(len(r['mismatches']) + len(r['errors']) for r in ts.values())
st_txt = '; '.join('%s: %d sequences, %d reads, %d stores, %d reverts, %d original-value checks, %d dirty-set checks, %d steps on an account created in the transaction, %d base reads, %d mismatches, %d errors' % (
    k, r['sequences'], r['reads'], r['stores'], r['reverts'], r['committedChecks'], r['dirtyChecks'], r['newAccountSteps'],
    r['baseReads'], len(r['mismatches']), len(r['errors'])) for k, r in st.items())
st_bad = sum(len(r['mismatches']) + len(r['errors']) for r in st.values())
kk_txt = '; '.join('%s: %d sequences, %d hashes, %d cache hits, %d misses, %d stores, %d LoadOrStore that found the other worker\'s entry, %d hasherBuf overwrites, %d runs at a small cap, %d mismatches, %d errors' % (
    k, r['sequences'], r['hashes'], r['hits'], r['misses'], r['stored'], r['loaded'], r['overwrites'], r['capRuns'],
    len(r['mismatches']), len(r['errors'])) for k, r in kk.items())
kk_bad = sum(len(r['mismatches']) + len(r['errors']) for r in kk.values())
f_txt = '; '.join('%s %s: %d of %d sequences flagged' % (f['target'], f['fault'], f['mismatchSeqs'] + f['errorSeqs'], f['sequences']) for f in fs)
f_txt += '; ' + '; '.join('bor %s: %d mismatches' % (k, len(v['mismatches'])) for k, v in kf.items())
f_missed = [f for f in fs if f['mismatchSeqs'] + f['errorSeqs'] == 0] + [k for k, v in kf.items() if not v['mismatches']]


def cv(c):
    d = live[c]
    return '%s block %s, before %s, after %s, variants %s' % (d['url'], d['block'], d['clientBefore'].get('result'), d['clientAfter'].get('result'),
                                                            ','.join('%s=%s' % (k, v.get('equal')) for k, v in d['variants'].items()) if isinstance(d['variants'], dict) else
                                                            ','.join(str(v.get('equal')) for v in d['variants']))


live_txt = '; '.join('%d: %s' % (c, cv(c)) for c in live)
live_ok = all((all(v.get('equal') for v in (d['variants'].values() if isinstance(d['variants'], dict) else d['variants']))) for d in live.values())

src = lambda f, l, s: {'url': 'src/%s:%s' % (f, l), 'supports': s}

doc = {
    'unit': 'theme-go-binaries-storage-journal',
    'profiles': [],
    'findings': [],
    'cleared': [
        {'chainIds': GO, 'lens': 'L2',
         'check': 'Transient storage path of the shipped bsc v1.8.2, bor v2.11.2 (StateDB and the BlockSTM V2 ParallelStateDB) and avalanchego v1.15.3 binaries, amd64 and arm64, run in the cycle 31 x86-64 and AArch64 models with the Go map calls stubbed (scripts/tsgo.py): opTstore, opTload, the vm.StateDB itab methods SetTransientState and GetTransientState of each StateDB type, (*StateDB).Snapshot and RevertToSnapshot with the snapshot id lookup, journal append and revert (ParallelStateDB: appendJournal and parallelJournalEntry.revert), transientStorage Get and Set, and the journalEntry itab methods of transientStorageChange, all read from the file. Sequences: the cycle 31 Nitro generator unchanged (seed 31_1211_01) over the PoolManager delta, count, lock and reserve slots, with nested snapshots up to depth 6, reverts at each depth, equal-value writes, writes of zero, near-collision keys one bit, one limb or one byte apart, and a key that differs only in bit 248.',
         'result': ('Every read equals tools/opdiff/pyevm.py. ' if ts_bad == 0 else 'NOT ALL READS MATCH, see outputs. ') + ts_txt +
                   '. The bsc map is keyed by the 52-byte address and slot; bor, bor ParallelStateDB and avalanchego use a map of 20-byte addresses to maps of 32-byte slots, so the whole key reaches the runtime map calls. The bit-248 key returns its own value on Avalanche, so no bit of a transient key is cleared (avalanchego extstate.(*StateDB).SetTransientState is a tail jump to libevm (*StateDB).SetTransientState at 0x1466a20). The bsc, bor and avalanchego binaries were read as data only; the arm64 runs and the amd64 runs use the same sequences.',
         'source': R + 'out/ts/ (bsc-amd64.json, bor-amd64.json, bor-par-amd64.json, avax-amd64.json and the arm64 files); scripts/tsgo.py; src/libraries/CurrencyDelta.sol:14-39, src/libraries/NonzeroDeltaCount.sol:14-32, src/libraries/Lock.sol:13-25, src/libraries/CurrencyReserves.sol:17-36'},
        {'chainIds': [56], 'lens': 'L2',
         'check': 'Persistent storage path of the shipped bsc v1.8.2 binaries (amd64 and arm64) in the models (scripts/stgo.py): opSload, opSstore, (*StateDB).GetCommittedState (the original value the SSTORE gas function reads), GetState, SetState, getStateObject, getOrNewStateObject, createObject, (*stateObject).GetState, getState, GetCommittedState, SetState with its inlined setState, (*journal).storageChange with its sync.Pool, append, revert, revertToSnapshot, and the *storageChange and createObjectChange journalEntry methods. The reader interface is a stub serving base state, so first reads after an inner revert go through the binary path that fills originStorage. Cases: slot written back to its original value, slot written twice in one frame, slot first read after an inner revert, account created inside a frame (reader returns no account) and then reverted. Seed 32_1226_02.',
         'result': ('No mismatch. ' if st_bad == 0 else 'MISMATCHES, see outputs. ') + st_txt +
                   '. After every step the SLOAD value equals pyevm, GetCommittedState equals the value at transaction start, the binary dirtyStorage equals the set of slots whose value differs from the original, and after every revert the journal length equals its length at the snapshot with no dirties entry left at zero.',
         'source': R + 'out/st/bsc-amd64.json, out/st/bsc-arm64.json; scripts/stgo.py'},
        {'chainIds': [56], 'lens': 'L2',
         'check': 'BNB Chain binary-only state structures on the persistent storage path, read from the v1.8.2 source (raw.githubusercontent.com/bnb-chain/bsc/v1.8.2/core/state/journal.go, state_object.go, statedb.go) and the binary: storageChangePool (sync.Pool of *storageChange), journal.storageEntries, stateReadList (BAL access list), stateReaderWithCache (the Hertz fix read cache behind needBadSharedStorage) and the trie prefetcher.',
         'result': 'A reverted write cannot reach any of them. The pool hands out a fresh entry per SetState and only takes entries back in journal.reset at the end of the transaction, when the journal entries are dropped as well; journal.copy builds its entries from the pool but keeps an empty storageEntries, so copied entries are never returned. stateReadList records keys read, not values. stateReaderWithCache and the prefetcher serve and warm committed values only; writes stay in dirtyStorage until Finalise. The binary journal.append at 0x10be9c2 compares the itab with go:itab.*storageChange and appends to journal+0x40, matching the source.',
         'source': 'https://raw.githubusercontent.com/bnb-chain/bsc/v1.8.2/core/state/journal.go'},
        {'chainIds': [137], 'lens': 'L2',
         'check': 'L-1225: bor v2.11.2 64-byte keccak cache in opKeccak256 (core/vm/instructions.go:265-278 at tag v2.11.2), read from the amd64 and arm64 binaries and run in the models (scripts/kk.py, seed 32_1225_01).',
         'result': 'The cache is vm.BoundedCache[[64]uint8, common.Hash], built per block by newSharedBlockCaches (core/blockchain.go:1268-1289 at v2.11.2) and shared by the prefetcher goroutine and all BlockSTM V2 workers through vm.Config; it is not process-wide. Load calls sync.(*Map).Load and Store calls internal/sync HashTrieMap.LoadOrStore after two runtime.convTnoptr calls that box copies of the 64-byte key and the 32-byte value; the count is an atomic add (lock xadd on amd64, ldaxr/stlxr or ldaddal on arm64). opKeccak256 passes the key and evm.hasherBuf by value on the stack (amd64 0xb4dc22-0xb4dc84), so the stored value is a copied array, not a slice into hasherBuf. The key type is [64]uint8 with TFlagRegularMemory and equal function memequal_varlen with size word 64, so lookup hashes and compares all 64 bytes. ' + kk_txt +
                   '. Two workers with separate hasherBuf share one cache; inputs of other lengths overwrite a worker hasherBuf between its Store and the other worker Load; a stored entry from the other worker between Load and Store is found by LoadOrStore and not counted twice. Every result equals Keccak-256 of the input. CurrencyDelta.sol:14 hashes 64 bytes and goes through this cache; Position.sol:60 hashes 58 bytes and does not.',
         'source': R + 'out/kk/; https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/vm/instructions.go; https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/blockchain.go'},
        {'chainIds': [137], 'lens': 'L2',
         'check': 'bor v2.11.2 ParallelStateDB (BlockSTM V2 worker state) storage, transient storage and revert, read from raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/state/parallel_statedb.go, parallel_statedb_journal.go and parallel_statedb_validate.go; its transient path also ran from the binary (first entry).',
         'result': 'SetState journals the previous value with a flag for whether the slot was already in localStorage; revert puts the previous value back when it was, and deletes the local entry otherwise, so reads fall through to the MV store or base state, which hold the transaction-start value. FlushToMVStore publishes only localStorage, so a reverted write is not published; its key stays in WriteKeys, which only drives MarkEstimate and CleanupEstimate. GetCommittedState caches the first read of the MV store or base and is not touched by local writes. Transient storage is a fresh map from Prepare per transaction and is restored with transientStorage.Set. RevertToSnapshot uses the same id lookup as StateDB and truncates journal, balance ops, logs and transfers. Validation compares writer and incarnation, or the value. No step reads a reverted value.',
         'source': 'https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/state/parallel_statedb.go'},
        {'chainIds': GO, 'lens': 'L2',
         'check': 'Task 4: call family control flow of bsc v1.8.2, bor v2.11.2 and avalanchego v1.15.3 (libevm) EVM.Call, from the tagged source and the order of calls in the amd64 binaries (scripts/callflow.py, out/callflow-*.txt).',
         'result': 'All three take Snapshot after the depth and CanTransfer checks and before Exist, CreateAccount, Transfer, the precompile and Run, and call RevertToSnapshot whenever the returned error is non-nil. bsc skips CanTransfer and Transfer only when the caller is params.SystemAddress (isSystemCall, evm.go:291-293), which no transaction can be sent from; its stateful precompiles (CAS20 included) run through runPrecompile inside the same snapshot. libevm Call spends preprocessing gas before the snapshot, only for depth 0 with hooks registered. No client-only step sits between snapshot and revert that writes PoolManager state.',
         'source': 'https://raw.githubusercontent.com/bnb-chain/bsc/v1.8.2/core/vm/evm.go'},
        {'chainIds': GO, 'lens': 'L2',
         'check': 'Task 5: planted faults in in-memory copies of the model text (scripts/plant.py, kk.py): journal entry skipped, revert-loop exit off by one, one TLOAD/SLOAD key limb left unswapped, revert that restores zero (not on avalanchego, whose Set has no zero test), slot written back to its original value left dirty (bsc storage), keccak cache key that loses its last 8 bytes and a cached value zeroed (bor).',
         'result': ('Every planted fault was caught. ' if not f_missed else 'NOT ALL FAULTS CAUGHT: %s. ' % f_missed) + f_txt,
         'source': R + 'out/faults/'},
        {'chainIds': [56, 137, 43114, 42161, 4663], 'lens': 'L2',
         'check': 'Live eth_call probe with state overrides on the deployed PoolManager (cycle 31 live_nitro.py copied unchanged as scripts/live.py): unlock, initialize a pool of two never-deployed currencies, add liquidity, swap, let a helper swap and revert (nested variant: a second helper inside), read deltas and storage back, settle with ERC-6909 claims; kept variant must revert.',
         'result': ('All variants return the reference bytes. ' if live_ok else 'A VARIANT DIFFERS. ') + live_txt +
                   '. The BNB Chain endpoint answers Geth/v1.8.2 built with go1.26.10, while the released binary read here is built with go1.25.14, so it is another build. The Polygon endpoint answers bor v2.11.1-private from two commits, not the v2.11.2 binary read. The Avalanche endpoint answers avalanchego 1.15.3 at commit 983815fd, the released build. The Nitro endpoints answer the b72783f release named in cycle 31.',
         'source': R + 'out/live-56.json, out/live-137.json, out/live-43114.json, out/live-42161.json, out/live-4663.json'},
        {'chainIds': OTHERS, 'lens': 'L2',
         'check': 'Applicability of this theme to the other 16 networks.',
         'result': 'This theme reads the shipped binaries of BNB Chain, Polygon and Avalanche and the Nitro storage revert; it does not apply to the other networks, whose clients are covered by their own units.',
         'source': 'research/network-risk/cycles/032/plan.json'},
    ],
    'leads': [
        {'chainIds': [42161, 4663], 'lens': 'L2',
         'question': 'Run storageChange.revert and stateObject.setState of the Nitro b72783f binaries in the models with stgo.py adapted to Nitro struct offsets (L-1227 is still answered only by live calls).',
         'why': 'slot0, liquidity, ticks, positions and ERC-6909 balances are persistent storage; only the live reverted-swap probe covers the Nitro persistent revert.', 'priority': 'low'},
        {'chainIds': [137, 43114], 'lens': 'L2',
         'question': 'Run the persistent storage path of bor v2.11.2 StateDB and ParallelStateDB (with the MV store read stubbed) and of avalanchego v1.15.3 libevm with extstate key transform in the models, as stgo.py does for bsc.',
         'why': 'Persistent storage revert was modelled from the binary for bsc only this cycle; bor ParallelStateDB was read from source.', 'priority': 'low'},
    ],
    'leadResults': [
        {'leadId': 'L-1225', 'outcome': 'cleared', 'answer': 'Per-block cache shared by the prefetcher and BlockSTM V2 workers; sync.Map plus atomic count; key and value boxed as copied arrays; full 64-byte compare. Modelled interleavings and two planted faults; no wrong hash.'},
        {'leadId': 'L-1226', 'outcome': 'cleared', 'answer': 'Transient path of bsc, bor (StateDB and ParallelStateDB) and avalanchego binaries on both architectures, and the bsc persistent path, match pyevm on every read; faults caught. bor and avalanchego persistent storage were not modelled from the binary.'},
        {'leadId': 'L-1227', 'outcome': 'inconclusive', 'answer': 'The Nitro persistent storage revert was not lifted this cycle; the live reverted-swap probe on Arbitrum One and Robinhood Chain again returned the reference bytes.'},
    ],
}
json.dump(doc, open(OUTF, 'w'), indent=1)
print('written', ts_bad, st_bad, kk_bad, f_missed)
