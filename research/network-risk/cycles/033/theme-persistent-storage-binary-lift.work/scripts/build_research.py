"""Write ../theme-persistent-storage-binary-lift.research.json from the run outputs in out/."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(W), 'theme-persistent-storage-binary-lift.research.json')
R = lambda p: json.load(open(os.path.join(W, p)))
WD = 'research/network-risk/cycles/033/theme-persistent-storage-binary-lift.work/'
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
THEME = [42161, 4663, 137, 43114, 10, 8453, 130, 57073, 1868]
NA = [c for c in ALL if c not in THEME]


def st(name):
    r = R('out/st/%s.json' % name)
    return r


def cnt(r, keys):
    return ', '.join('%s %s' % (k, '{:,}'.format(r[k])) for k in keys if k in r)


def mm(r):
    return '%d sequences with a mismatch and %d with a model error' % (len(r['mismatches']), len(r['errors']))


runs = {n: st(n) for n in ['nitro-amd64', 'nitro-arm64', 'nitro-bal-amd64', 'bor-amd64', 'bor-arm64', 'bormv-amd64',
                           'bormv-arm64', 'borpar-amd64', 'borpar-arm64', 'avax-amd64', 'avax-arm64']
        if os.path.exists(os.path.join(W, 'out/st/%s.json' % n))}
K = ['sequences', 'reads', 'stores', 'reverts', 'committedChecks', 'dirtyChecks', 'writeSetChecks', 'newAccountSteps']


def line(n):
    r = runs.get(n)
    if not r:
        return '%s: not run' % n
    return '%s: %s; %s' % (n, cnt(r, K), mm(r))


faults = {}
for t in ('nitro', 'bor', 'borpar', 'avax'):
    p = os.path.join(W, 'out/faults/%s-summary.json' % t)
    if os.path.exists(p):
        faults[t] = json.load(open(p))
fault_txt = []
for t, s in faults.items():
    fault_txt.append('%s-amd64: ' % t + '; '.join('%s caught in %d of %d sequences (%d model errors)' % (
        x['fault'], x['mismatchSeqs'], x['sequences'], x['errorSeqs']) for x in s))
cmpr = R('out/cmp-opreth281-amd64.json')
pin = R('out/pin-op-10.json')
ar = R('out/arith-opreth281-amd64-0.json') if os.path.exists(os.path.join(W, 'out/arith-opreth281-amd64-0.json')) else None
nfn = len(runs['nitro-amd64']['functions'])
bfn = len(runs['bor-amd64']['functions'])
pfn = len(runs['borpar-amd64']['functions'])
afn = len(runs['avax-amd64']['functions'])

doc = {
    'unit': 'theme-persistent-storage-binary-lift',
    'profiles': [],
    'findings': [],
    'cleared': [
        {'chainIds': [42161, 4663], 'lens': 'L2',
         'check': 'Task 1 (L-1246). Persistent storage path of the Nitro v3.13.0-rc.9+b72783f release binaries (sha256 a142fcbe...3962 amd64, ba1fec28...4923 arm64, equal to cycles/023/arbitrum-family.work/raw/nitro-binaries.sha256), read as data and run in the cycle 31 x86-64 and AArch64 models with the Go map calls stubbed: opSload, opSstore, the vm.StateDB itab methods GetState, SetState, GetCommittedState and GetStateAndCommittedState, (*StateDB).Snapshot, RevertToSnapshot, (*journal).snapshot, revertToSnapshot, revert, append, stateObject.GetCommittedState, getState, SetState, storageChange.revert through the journalEntry itab, createObjectChange.revert, getStateObject, getOrNewStateObject, createObject, newObject (%d functions per build). Struct offsets were read from the relabelled disassembly (pclntab names; scripts/ndump.py): StateDB reader +0x20/+0x28, stateObjects +0x60, stateObjectsDestruct +0x68, block access list pointer +0xe0, journal +0xf8 (entries +0x8, dirties +0x20, validRevisions +0x28, nextRevisionId +0x40); stateObject originStorage +0xa0, dirtyStorage +0xa8, pendingStorage +0xb0. Sequences are the cycle 32 stgo.py generator (seed 32_1226_02) over the PoolManager slot shapes: a slot written back to its original value, written twice in one frame, first read after an inner revert, and the storage of an account created inside a frame. %s. %s. %s.' % (
             nfn, line('nitro-amd64'), line('nitro-arm64'), line('nitro-bal-amd64')),
         'result': 'Every SLOAD equals pyevm.py, GetCommittedState (the original value SSTORE gas reads) equals the value at transaction start for every touched slot, dirtyStorage equals the slots whose value differs from the original, and after every revert the journal length equals the length at the snapshot and no dirties entry with count zero is kept. A word that a hook, token or callback writes in a frame that then reverts returns to its earlier value, so slot0, liquidity, ticks, positions, fee growth and ERC-6909 balances read at src/libraries/Pool.sol:83-91 and src/ERC6909.sol:17 cannot keep a reverted write on Arbitrum One or Robinhood Chain.',
         'source': WD + 'out/st/nitro-amd64.json, out/st/nitro-arm64.json, out/st/nitro-bal-amd64.json; scripts/stnitro.py; dis/st-nitro-amd64.txt'},
        {'chainIds': [42161, 4663], 'lens': 'L2',
         'check': 'Arbitrum-only steps on the persistent storage path of the b72783f binaries. Read from the disassembly with pclntab line numbers (build/pcline, TEXTBASE 0x45d7c0) and from https://raw.githubusercontent.com/OffchainLabs/go-ethereum/master/core/state/journal.go and journal_arbitrum.go (the fork commit pinned by v3.13.0-rc.9 could not be read: https://github.com/OffchainLabs/nitro/tree/v3.13.0-rc.9/go-ethereum answered HTTP 403, and the binary\'s statedb.go line numbers do not match the fork at f3a966e or master).',
         'result': 'Three Arbitrum-only steps sit on the path and none can hold or return a storage word. (1) (*journal).snapshot copies s.arbExtraData.unexpectedBalanceDelta (StateDB+0, a *big.Int) into each revision and revertToSnapshot restores it (journal.go:85-90 on the fork master); it is a balance accounting value, not storage. (2) (*journal).append and revert type-assert every entry to possibleZombie (journal_arbitrum.go:84-93) to count zombie entries; only createZombieChange has an isZombie method in the binary (pclntab), and a storageChange passes through unchanged. (3) StateDB+0xe0 points to an EIP-7928 construction block access list (core/types/bal/bal.go:58-100 in the pclntab); with a live list, a reverted SSTORE left a StorageRead record of the key and no value (scripts/nbalprobe.py), and the 1,005 sequences with the list enabled match. No arbos or stylus function is in the closure of opSload and opSstore, so ArbOS state backing and the Stylus storage cache are not on the PoolManager\'s own SLOAD and SSTORE path.',
         'source': WD + 'scripts/nbalprobe.py, dis/st-nitro-amd64-closure.txt, dl/src/nitrogeth-master-core_state_journal.go:85-90, dl/src/nitrogeth-master-core_state_journal_arbitrum.go:84-93'},
        {'chainIds': [137], 'lens': 'L2',
         'check': 'Task 2 (L-1246), bor v2.11.2 serial StateDB, amd64 and arm64 binaries of cycle 31, %d functions: opSload, opSstore, the StateDB itab storage methods, Snapshot, RevertToSnapshot, journal append and revert, storageChange.revert, stateObject.GetCommittedState and SetState, getStateObject with its closures, getOrNewStateObject, createObject, newObject, the FlatDiff overlay calls (flat diff pointer nil). Offsets: StateDB stateObjects +0x58, stateObjectsDestruct +0x60, reader +0x18 (Account itab+0x18, Storage itab+0x30), mvHashmap +0x78, journal +0x120; stateObject mutex +0xe0, originStorage +0xe8, dirtyStorage +0xf0, pendingStorage +0xf8. Run with mvHashmap nil (block import and eth_call) and non-nil with blockstm.(*MVHashMap).Read stubbed to return depIdx -1 and incarnation -1, the MVReadResultNone answer the store gives when no lower transaction index wrote the key (statedb.go:594-657 at https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/state/statedb.go). Stubs besides the map calls: internal/sync Mutex.Lock (sets the state word the inlined Unlock clears), crypto.Keccak256Hash for newObject\'s address hash, maps.(*Map).Clone for the worker\'s deep copy. %s. %s. %s. %s.' % (
             bfn, line('bor-amd64'), line('bor-arm64'), line('bormv-amd64'), line('bormv-arm64')),
         'result': 'Reads, original values, the dirty set and the journal length after every revert equal the reference in both modes. In the MVHashMap mode a write lands in the worker\'s writeMap with the writer StateDB as its value (statedb.go:659-668) and reaches the store only through FlushMVWriteSet (statedb.go:685-689); the comment at core/blockstm/mvhashmap.go:429 of the same tag marks this V1 path as test-only.',
         'source': WD + 'out/st/bor-amd64.json, out/st/bormv-amd64.json, scripts/stgo2.py; https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/state/statedb.go'},
        {'chainIds': [137], 'lens': 'L2',
         'check': 'Task 2, bor v2.11.2 ParallelStateDB, the BlockSTM V2 worker state, %d functions from the binaries: opSload, opSstore, (*ParallelStateDB).GetState, GetCommittedState, SetState, Snapshot, RevertToSnapshot, appendJournal, (*parallelJournalEntry).revert (jump table on the entry kind), readStoreWait, priorDestructedAt, recordStoreReadEx with read tracking on. Offsets: base +0x10, store +0x20, localStorage +0x38, journalEntries +0xc8, trackReads +0x110, committedCache +0x1c0. Stubs: blockstm.(*MVStore).ReadVersionFull returns (nil, -1, 0, false, false), the answer for a key no lower transaction of the block has written (the first transaction of a block, or any untouched key), and (*SafeBase).GetState returns the pre-block word, as reader.Storage does in the serial path. Check: after every step the binary\'s localStorage equals the write set the journal must leave (every SSTORE not undone by a revert, kept even when equal to the original value). %s. %s.' % (
             pfn, line('borpar-amd64'), line('borpar-arm64')),
         'result': 'Every read, every original value and every write set after a revert equals the reference. A BlockSTM worker\'s reverted write cannot be seen by another worker before the transaction finishes: SetState keeps the word in localStorage only (https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/state/parallel_statedb.go:1040-1073, the comment at 1053 says storage writes are always deferred), the store receives localStorage only in FlushToMVStore (:495-525), and the V2 executor calls it after Execute returns (https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/blockstm/v2_executor.go:445-449). Since the revert removes or restores the localStorage entry (parallel_statedb_journal.go:73-79), the flushed set holds the post-revert words.',
         'source': WD + 'out/st/borpar-amd64.json, out/st/borpar-arm64.json; https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/state/parallel_statedb.go; https://raw.githubusercontent.com/0xPolygon/bor/v2.11.2/core/blockstm/v2_executor.go'},
        {'chainIds': [43114], 'lens': 'L2',
         'check': 'Task 2, avalanchego v1.15.3 (libevm v1.13.15-0.20261028200218-d398bc4dbe41), amd64 and arm64, %d functions: opSload, opSstore, the itab methods of the C-Chain wrapper vms/saevm/cchain/libevm/extstate.StateDB (the only vm.StateDB itab besides *state.StateDB), libevm GetState, SetState, GetCommittedState, transformStateKey, options.As, the registered (*partitionStateKeysHook).TransformStateKey, Snapshot, RevertToSnapshot, journal revert, (*storageChange).revert, createObjectChange.revert, getStateObject, createObject, newObject. The hook was registered in the model as RegisterExtras(partitionStateKeysHook{}) does (extstate/statedb.go:31-33 at https://raw.githubusercontent.com/ava-labs/avalanchego/v1.15.3/vms/saevm/cchain/libevm/extstate/statedb.go): core/state.registeredExtras points to the binary\'s own itab. Trie path (snap nil): stateObject.trie GetStorage and Database.OpenStorageTrie stubbed to serve the base word for the physical key the binary asks for. The reference clears bit 248 of every SLOAD and SSTORE key (storageKey, statedb.go:53-56) and checks the libevm 1.13 dirty rule (every slot with a value-changing SetState stays dirty, reverted or not, except for an account whose creation was reverted). %s. %s. The first 5,005-sequence amd64 run, before the reference dropped the dirty slots of an account whose creation was reverted, flagged 216 sequences, all on the new account, all with the binary lacking only slots of the object createObjectChange.revert removed (journal.go:154-157 at https://raw.githubusercontent.com/ava-labs/libevm/d398bc4dbe41/core/state/journal.go); it is kept as out/st/avax-amd64-first-run.json.' % (
             afn, line('avax-amd64'), line('avax-arm64')),
         'result': 'Every read, original value and dirty set equals the reference with the transform applied, including %s steps on keys with bit 248 set. The binary clears bit 248 in GetState, SetState and GetCommittedState alike (post-AP1, preAP1 false). Two PoolManager slots alias only if they differ in bit 248 alone: mapping slots are keccak outputs (src/PoolManager.sol:93, src/ERC6909.sol:17, src/libraries/Pool.sol:83-91) and struct offsets add at most 3, so an alias needs a keccak output pair at XOR distance 2^248, which no caller can search for; constant slots are below 2^248.' % '{:,}'.format(runs.get('avax-amd64', {}).get('bit248Steps', 0)),
         'source': WD + 'out/st/avax-amd64.json, out/st/avax-arm64.json, scripts/stgo2.py; https://raw.githubusercontent.com/ava-labs/libevm/d398bc4dbe41/core/state/statedb.libevm.go'},
        {'chainIds': [42161, 4663, 137, 43114], 'lens': 'L2',
         'check': 'Task 5: planted faults in in-memory copies of the model text of the amd64 builds (scripts/plant2.py; the binaries are not changed): revert_zero (the restored word stored from the Go zero register), revert_committed (the revert always drops the dirty or local entry, so the committed word comes back in place of the pre-frame word), skip_journal (the storage journal append in SetState removed), snap_off_by_one (the journal revert loop stops one entry early), key_limb (one byte swap of the SLOAD key removed), and on Avalanche transform_off (the bit 248 clear removed). ' + ' '.join(fault_txt),
         'result': 'Every planted fault is caught by the read, original value, dirty or write set checks, so the zero-mismatch runs are not a property of a check that cannot fail.',
         'source': WD + 'out/faults/*-summary.json, scripts/plant2.py'},
        {'chainIds': [10], 'lens': 'L1',
         'check': 'Task 4 (L-1241). The op-reth v2.8.1 image us-docker.pkg.dev/oplabs-tools-artifacts/images/op-reth:v2.8.1 (index annotation org.opencontainers.image.revision 722072949ce583f361424a160082186ee14cac71, the 72207294 that mainnet.optimism.io names) was fetched anonymously for amd64; manifest sha256 e01d3c5a..., layer sha256 adbb0612... both equal the registry digests; binary sha256 1c44dd9073b45730. Read with readelf and objdump only. The 256-entry instruction table was found by the handler-sharing pattern of the cycle 32 v2.10.0-rc.4 table (%d distinct handlers; 16 candidate per-spec tables in v2.8.1, 17 in v2.10.0-rc.4, which differ only in the EXP gas variant). The 25 arithmetic, comparison and shift handlers, the jump destination analysis function and everything they reach by direct call were compared instruction by instruction with addresses masked (scripts/cmp_reth.py), then the 73-function arithmetic closure was mapped to v2.8.1 and run in the cycle 32 model (arith.py, shard 0 of 4)%s. The same comparison was made for SLOAD, SSTORE, TLOAD and TSTORE and their direct callees. Then 2,000 vectors (send2000.py sample, seed 3205) were sent to https://mainnet.optimism.io in 50-vector batches, each one JSON-RPC batch request [web3_clientVersion, eth_call, web3_clientVersion] and counted only when both versions agree (scripts/pin_op.py, order seed 33_1241_04): %s requests, %s unpinned.' % (
             cmpr['distinctHandlersOld'],
             (': %s cases, %s mismatches, %s errors, %s emulated instructions, the same instruction count as v2.10.0-rc.4 shard 0' % ('{:,}'.format(ar['cases']), ar['mismatches'], ar['errors'], '{:,}'.format(ar.get('steps', 0)))) if ar else '',
             pin['requests'], pin['unpinned']),
         'result': 'All 25 handlers and the jump analysis function are identical to the lifted v2.10.0-rc.4 code. Of %d functions reached, three differ: the panic payload allocator (0x40 against 0x38 bytes, ending in _Unwind_RaiseException), a vector growth helper whose max is computed in another register, and an allocation helper of the jump analysis bitmap; none is arithmetic. The storage handlers and their direct callees differ only in a max computed with swapped operands and a thread-local offset; dynamic calls into the database were not followed. Pinned answers: %s.' % (
             cmpr['deep']['functionsCompared'],
             '; '.join('%s %d vectors, %d mismatches' % (k, v['vectors'], len(v['mismatches'])) for k, v in pin['builds'].items())),
         'source': WD + 'out/cmp-opreth281-amd64.json, out/arith-opreth281-amd64-0.json, out/pin-op-10.json, dl/opreth281/fetch-log.json'},
        {'chainIds': NA, 'lens': 'L2',
         'check': 'Scope of this theme.',
         'result': 'The persistent storage revert lifted here belongs to the clients of Arbitrum One and Robinhood Chain (Nitro), Polygon (bor), Avalanche (avalanchego) and the OP Stack chains served by op-reth and Base (10, 8453, 130, 57073, 1868). It does not apply to Ethereum, Zora, World Chain, Celo, X Layer, Elysium, BNB Chain (run from its binary in cycle 32), Monad, MegaETH, Tempo, Arc and HyperEVM.',
         'source': 'research/network-risk/cycles/033/plan.json (unit task text)'},
    ],
    'leads': [
        {'chainIds': [10, 8453, 130, 57073, 1868], 'lens': 'L1',
         'question': 'Run the revm journal (checkpoint, checkpoint_commit, checkpoint_revert, sload, sstore, tload, tstore) of the op-reth and Base release binaries in a model; it reaches the database through dynamic calls and hashbrown tables that the cycle 32 x86-64 model does not yet cover.',
         'why': 'L-1235 is still answered by live eth_call sequences and by text equality between releases, not by running the shipped journal.', 'priority': 'low'},
        {'chainIds': [480], 'lens': 'L1',
         'question': 'Compare the instruction table, jump analysis and storage handlers of ghcr.io/worldcoin/world-chain:v2.8.2 (revision 95963111bf6b6623da2bbca68ca17a04230cc73d, anonymous pull allowed) with the lifted op-reth code, as was done here for op-reth v2.8.1.',
         'why': 'The World Chain build behind world-chain v2.8.2-9596311 can now be obtained; it has not been read.', 'priority': 'low'},
        {'chainIds': [137], 'lens': 'L2',
         'question': 'Run ParallelStateDB with MVStore answers other than not-found (a lower transaction\'s committed word, an ESTIMATE entry that readStoreWait waits on, a SuicidePath write) and check GetState and GetCommittedState against a serial reference of the same block.',
         'why': 'The stub returned not-found only, which is faithful for the first transaction of a block and for untouched keys; the cross-transaction branches of readStoreWait and priorDestructedAt ran only on that answer.', 'priority': 'low'},
    ],
    'leadResults': [
        {'leadId': 'L-1246', 'outcome': 'cleared',
         'answer': 'The persistent storage revert ran from the shipped binaries of Nitro b72783f (5,005 amd64, 2,005 arm64 and 1,005 amd64 sequences with a live block access list), bor v2.11.2 (serial StateDB with and without the MV hashmap, and ParallelStateDB, 5,005 amd64 and 2,005 arm64 each) and avalanchego v1.15.3 with its bit 248 transform (5,005 and 2,005). No modelled sequence leaves a persistent word, an original value or a dirty or write set different from pyevm.py after an inner revert, and every planted fault is caught. A BlockSTM worker\'s reverted write is not visible to other workers before the transaction ends.'},
        {'leadId': 'L-1235', 'outcome': 'inconclusive',
         'answer': 'The revm journal of op-reth and Base was not run from the binaries. The SLOAD, SSTORE, TLOAD and TSTORE handlers of op-reth v2.8.1 and their direct callees equal those of v2.10.0-rc.4 up to register choice and a thread-local offset, and the 2,000 pinned vectors on both OP Mainnet builds match; the cycle 32 live journal sequences remain the evidence for the journal itself.'},
        {'leadId': 'L-1241', 'outcome': 'cleared',
         'answer': 'op-reth/v2.8.1-72207294 is the published image us-docker.pkg.dev/oplabs-tools-artifacts/images/op-reth:v2.8.1 (revision 72207294...). Its 25 arithmetic handlers and its jump analysis are instruction for instruction the lifted v2.10.0-rc.4 code, and the 81,000-case arithmetic shard run from the v2.8.1 text matches. 2,000 pinned vectors match on op-reth/v2.8.1-72207294 and on op-reth/v0.0.0-dev-unknown, the unversioned build, whose binary cannot be obtained. conduit-op-reth v2.5.1 for Zora: ghcr.io refused anonymous pulls (401 for conduitxyz/op-reth, 403 for conduit-xyz/op-reth), so no binary. world-chain v2.8.2-9596311: ghcr.io/worldcoin/world-chain:v2.8.2 is pullable, revision 95963111; it was not read (new lead).'},
    ],
}
json.dump(doc, open(OUT, 'w'), indent=1)
print('wrote', OUT)
