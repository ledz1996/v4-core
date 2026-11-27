"""Builds theme-celo-xlayer-arc-journal-lift.research.json from the saved outputs in ../out (reads only those files)."""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE); OUT = os.path.join(W, 'out')
RES = os.path.join(os.path.dirname(W), 'theme-celo-xlayer-arc-journal-lift.research.json')
WD = 'research/network-risk/cycles/037/theme-celo-xlayer-arc-journal-lift.work'


def tot(pat):
    t = {k: 0 for k in ('cases', 'mismatch', 'errors', 'pyevm_mismatch', 'checks', 'reverts', 'commits')}; files = sorted(glob.glob(os.path.join(OUT, pat)))
    for f in files:
        r = json.load(open(f))
        for k in t: t[k] += r[k]
    return t, [os.path.basename(f) for f in files]


def faults(prefix):
    r = {}
    for f in sorted(glob.glob(os.path.join(OUT, 'fault-%s-*.json' % prefix))):
        d = json.load(open(f)); name = os.path.basename(f)[len('fault-%s-' % prefix):-5]
        r[name] = 'caught' if (d['mismatch'] + d['errors'] + d['pyevm_mismatch']) > 0 and d['fault_hits'] > 0 else 'NOT CAUGHT'
    return r


def live(tag):
    r = json.load(open(os.path.join(OUT, 'live-journal-%s.json' % tag)))
    return '%d of %d equal, %d mismatches, %d RPC errors, web3_clientVersion before %s and after %s' % (
        r['equal'], r['cases'], len(r['mismatches']), r['rpcErrors'], r['clientVersionBefore'].get('result'), r['clientVersionAfter'].get('result'))


ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
OTHER = [c for c in ALL if c not in (42220, 196, 5042, 480, 7777777)]

celo, celo_f = tot('seq-celo-A-370*.json'); celoP, celoP_f = tot('seq-celo-P-*.json')
xl, xl_f = tot('seq-xlayer-A-371*.json'); xl2, xl2_f = tot('seq-xlayer-A2-*.json'); arc, arc_f = tot('seq-arc-A-372*.json')
fc, fx, fx2, fa = faults('celo-A'), faults('xlayer-A'), faults('xlayer-A2'), faults('arc-A')
fw, fz = faults('worldchain-A'), faults('conduit-A')
hook = {t: json.load(open(os.path.join(OUT, 'arc-hook-%s.json' % t))) for t in ('off', 'pn', 'bd') if os.path.exists(os.path.join(OUT, 'arc-hook-%s.json' % t))}


def hooksum(t):
    r = hook[t]
    parts = []
    for c in r['cases']:
        logs = c.get('simLogs')
        parts.append('%s: eth_call %s%s' % (c['case'], 'matches the journal rules' if c.get('matches') else 'DIFFERS' if 'matches' in c else 'no answer',
                     '' if logs is None else ', eth_simulateV1 status %s with %d log(s)' % (c.get('simStatus'), len(logs))))
    e = r['cases'][0].get('simulate', {}).get('error') if r['cases'] else None
    sim = e.get('message') if isinstance(e, dict) else e
    return '%s (web3_clientVersion %s before, %s after, block %s). %s.%s' % (r['url'], r['clientVersionBefore'].get('result'), r['clientVersionAfter'].get('result'),
                                                                          r['blockBefore'].get('result'), '; '.join(parts), (' eth_simulateV1 refused: %s.' % sim) if sim else '')


def seqtext(t, files):
    return ('%d nested-frame sequences (the 11 named shapes of cycle 36 in every file plus random ones over the lock, nonzero delta count, '
            'synced currency and reserves, CurrencyDelta and pool slot shapes, reverts at depth 1 to 4, tables that grow inside a frame), %d checks '
            'after %d reverts and %d commits: %d journal mismatches, %d model stops, %d differences from pyevm.py. Files %s, seeds in the file names.') % (
        t['cases'], t['checks'], t['reverts'], t['commits'], t['mismatch'], t['errors'], t['pyevm_mismatch'], ', '.join(files))


S_PM = [{'url': 'src/PoolManager.sol:104-114', 'supports': 'unlock sets the transient lock, runs the callback and reverts unless NonzeroDeltaCount.read() is zero'},
        {'url': 'src/libraries/CurrencyDelta.sol:28-41', 'supports': 'every delta is a TLOAD and TSTORE of keccak(target, currency)'},
        {'url': 'src/libraries/NonzeroDeltaCount.sol:12-34', 'supports': 'the open delta count is one transient word'},
        {'url': 'src/libraries/Lock.sol:10-26', 'supports': 'the lock is one transient word'},
        {'url': 'src/libraries/CurrencyReserves.sol:15-38', 'supports': 'the synced currency and reserves are two transient words'},
        {'url': 'src/PoolManager.sol:349-364', 'supports': '_settle credits msg.value for native, or balanceOf minus synced reserves'}]

cleared = []
cleared.append({'chainIds': [42220], 'lens': 'L2', 'check': 'Task 1: which instruction table of celo-reth v1.0.10 (binary sha256 ca81b870...8cbfac, build string reth/v2.2.0-74cc8bb, revm from git checkout revm-3d0adf11a5f6f26f/bd28f94) executes blocks, read from the symbols with ' + WD + '/scripts/reach.py',
                'result': 'Twenty 256-entry tables with 16-byte entries exist. The table at 0x514d468 is the engine block-validation context: its SLOAD 0x1e5a260 reaches sload_concrete_error 0x35f8cf0, the State<DB> storage read 0x36475d0 and <reth_execution_cache::cached_state::CachedStateProvider as StateProvider>::storage 0x3662cd0. The table at 0x5151468 is the payload builder (sequencer) context: its storage read 0x3645490 reaches <reth_revm::cached::CachedReadsDbMut as Database>::storage 0x3604c30. TLOAD 0x1e5bf90 and TSTORE 0x1e63f10 (JournalInner::tstore 0x1d66aa0) are shared by both. Only the database read below the journal differs between the two.',
                'source': WD + '/scripts/reach.py output on celo-reth with build/celo.nm of cycle 36; ' + WD + '/scripts/celoj.py PROFILES'})
cleared.append({'chainIds': [42220], 'lens': 'L2', 'check': 'Task 1 (L-1311): Celo journal run from the shipped machine code of table 0x514d468 in the x86-64 model (celoj.py on the cycle 36 rethj.py CPU): SLOAD 0x1e5a260, SSTORE 0x1e62160, TLOAD 0x1e5bf90, TSTORE 0x1e63f10, sload_skip_cold_load 0x1dde510, sstore_skip_cold_load 0x1de3e50, sstore_concrete_error 0x1ed9fc0, sload_concrete_error 0x35f8cf0, rustc_entry 0x3605680, reserve_rehash 0x3622bd0, JournalInner::tstore 0x1d66aa0, transient insert 0x26e20c0 and remove 0x26d7870, checkpoint 0x1f36450 and checkpoint_commit 0x1f37e30 (the EvmInternals copies of the inlined revm code, same JournalInner layout), checkpoint_revert 0x1d61dd0 and JournalEntry::revert 0x4fb8c20. Only glibc malloc, free, realloc, calloc, posix_memalign, the mem* routines, the database read 0x36475d0 and the foldhash global seed 0x5323e90 are modelled; tables are real and grow in model memory.',
                'result': seqtext(celo, celo_f) + ' The SStoreResult (original, present, new) taken at 0x1e622a5 and 0x1e62347 matched on every SSTORE.',
                'source': WD + '/out/' + celo_f[0]})
if celoP['cases']:
    cleared.append({'chainIds': [42220], 'lens': 'L2', 'check': 'Celo payload builder table 0x5151468 (SLOAD 0x1e5a3b0, SSTORE 0x1e63330, storage read 0x3645490 stubbed) on the same harness',
                    'result': seqtext(celoP, celoP_f) + ' SSTORE was checked through the slot record after each store.', 'source': WD + '/out/' + celoP_f[0]})
cleared.append({'chainIds': [42220], 'lens': 'L2', 'check': 'Celo fee currency handling and the journal, read in celo-kona at the celo/reth-v1.0.10 tag',
                'result': 'The CIP-64 debit runs in validate_against_state_and_deduct_caller (handler.rs 1056-1173) inside its own checkpoint, committed or reverted whole, after which transient storage is cleared (handler.rs 616-690). The credit runs in build_execution_result after reward_beneficiary (handler.rs 873-876), through a committing system sub-call that clears transient storage and restores transaction_id (core_contracts.rs 211-249). Both run before or after the user transaction\'s frames, never inside one, and only for allowlisted fee currencies. Neither can leave a transient word of the PoolManager behind or undo part of a user frame. This agrees with the failed-deposits row of research/network-risk/OPCODES.md (cycle 22), now read at the v1.0.10 tag.',
                'source': 'https://raw.githubusercontent.com/celo-org/celo-kona/celo/reth-v1.0.10/crates/celo-revm/src/handler.rs'})
cleared.append({'chainIds': [196], 'lens': 'L2', 'check': 'Task 2 (L-1311): X Layer journal run from the shipped op-reth of xlayer-reth v0.0.7.3-rc.1 (binary sha256 7a9230ac...019c2e, reth/v2.3.0-f60420a, xlayer/v0.0.7, revm-context 18.0.3, jemalloc linked in, no symbols), table 0x718b9e0: SLOAD 0x5fd82d0, SSTORE 0x5fda000 (sload and sstore logic inlined), TLOAD 0x5fd9a80 (Host::tload 0x50e1f20), TSTORE 0x5fe5470 (JournalInner::tstore 0x50a0540), sload_skip_cold_load 0x519e2f0, sload_concrete_error 0x38877c0, rustc_entry 0x3b21760, transient insert 0x5d24510 and remove 0x5d2f910, checkpoint 0x3cca520, commit 0x3ccac20, checkpoint_revert 0x3ca62f0 and, as a second family, the other EvmInternals copy 0x520aaf0, 0x520c130 and 0x509ef80; JournalEntry::revert 0x40deea0 in both. Found by byte search for the revm field offsets and by the RELATIVE slots the routines call through. jemalloc entry points (malloc 0x6b1f460, mallocx 0x6b22510, realloc 0x6b238e0, rallocx 0x6b238d0, sdallocx 0x6b26a20) and the database read 0x3c37d30 are modelled.',
                'result': seqtext(xl, xl_f) + ' Second family: ' + seqtext(xl2, xl2_f) + ' The SSTORE handler inlines its SStoreResult into the gas code, so each SSTORE was checked through the slot record. This build numbers SpecId densely (TSTORE needs 0xb or more, Istanbul is 6), so the runs used 0xc, Prague; the gate values do not change any journal step.',
                'source': WD + '/out/' + xl_f[0]})
cleared.append({'chainIds': [5042], 'lens': 'L2', 'check': 'Task 3 (L-1312): Arc journal run from the shipped arc-node-execution of arc-execution v0.8.6 (sha256 97ad5a38...0b84f, reth/v2.2.0-508cbdf, revm-context 16.0.1, jemalloc linked in, no symbols), table 0x4f62ef0: SLOAD 0x1f69040, SSTORE 0x1f6bcf0, TLOAD 0x1f6ad00, TSTORE 0x1f6f4a0, host sload 0x1a06980, journal sload 0x22aeb50, sstore 0x1b26a40, JournalInner::tstore 0x1a07570, tload 0x178bd50, rustc_entry 0x2c0d260, transient insert 0x2c11f30, checkpoint 0x2b9c3f0, commit 0x2b9d360, checkpoint_revert 0x19ffce0, JournalEntry::revert 0x3e88fe0. The State storage read 0x22c07c0 and jemalloc (0x41c9ff0, 0x41cad50, 0x41cc120, 0x41cc110, 0x41cdc70) are modelled.',
                'result': seqtext(arc, arc_f) + ' The SStoreResult taken at 0x1f6be5f and 0x1f6bf0e matched on every SSTORE.', 'source': WD + '/out/' + arc_f[0]})
cleared.append({'chainIds': [5042], 'lens': 'L3', 'check': 'Task 3: where Arc\'s native value hook sits against the call frame checkpoint, read in arc-node v0.8.6 crates/evm/src/evm.rs',
                'result': 'before_frame_init and check_blocklist_and_create_log (evm.rs 516-625) run in checked_frame_init before init_frame (evm.rs 807-837), so they run inside the parent frame and before the child frame takes its checkpoint and moves the value. The blocklist read is journal.sload of 0x1800000000000000000000000000000000000001 (evm.rs 438-452), a journaled read whose warm entry belongs to the parent frame. The hook writes nothing; under Zero7 its account probe is bracketed by checkpoint and checkpoint_revert (evm.rs 569-580). A rejected value call returns a reverted frame result before any balance moves. For a non-precompile call the EIP-7708 Transfer log is pushed after init_frame (evm.rs 871-891), after the child checkpoint recorded the log index, so a reverting child truncates it. The value move itself is revm\'s transfer inside the child checkpoint.',
                'source': 'https://raw.githubusercontent.com/circlefin/arc-node/v0.8.6/crates/evm/src/evm.rs'})
for t in ('off', 'pn', 'bd'):
    if t in hook:
        cleared.append({'chainIds': [5042], 'lens': 'L3', 'check': 'Task 3: live probe of the hook shapes (value call accepted or rejected by an overridden blocklist word, inside a delegate-called frame that reverts or returns, the PoolManager lock and count words and a storage word written around it, native balances and the 0x3600 ERC-20 face read before and after) by eth_call and eth_simulateV1 with overrides on ' + hook[t]['url'] + ', script ' + WD + '/scripts/arc_hook_probe.py',
                        'result': hooksum(t) + ' Expected values come from the revm journal rules; the EIP-7708 Transfer log from 0xfffffffffffffffffffffffffffffffffffffffe appears only for the accepted call in the committed frame.',
                        'source': WD + '/out/arc-hook-%s.json' % t})
fl = lambda d: ', '.join('%s %s' % kv for kv in sorted(d.items()))
cleared.append({'chainIds': [42220, 196, 5042], 'lens': 'L2', 'check': 'Task 4: planted faults in in-memory copies of the lifted code (faults.json): revert restores zero, revert restores the committed value, the drain loop skips the newest entry, checkpoint journal index plus one, the slot and transient table probes stop one group early, and re-insert zero in the transient arm of JournalEntry::revert (L-1308)',
                'result': 'Celo: %s. X Layer: %s; second family: %s. Arc: %s. Each fault was hit and the harness stopped at the first wrong record.' % (fl(fc), fl(fx), fl(fx2), fl(fa)),
                'source': WD + '/scripts/faults.json and ' + WD + '/out/fault-*.json'})
cleared.append({'chainIds': [480, 7777777], 'lens': 'L2', 'check': 'L-1308: re-insert zero in place of the previous value in the TransientStorageChange arm of JournalEntry::revert, World Chain v2.8.2 at 0x409982c (arm 0x40997af) and conduit-op-reth v2.5.1 at 0x4c932d8 (arm 0x4c93265), on the cycle 36 harness unchanged',
                'result': 'World Chain: %s. Zora: %s. The first reverted transient write that had a nonzero previous value read back zero and the check named the word.' % (fl(fw), fl(fz)),
                'source': WD + '/out/fault-worldchain-A-transient_revert_reinserts_zero.json'})
cleared.append({'chainIds': [42220, 196, 5042], 'lens': 'L2', 'check': 'Task 5: the cycle 32 nested-frame probe (200 programs, seed 3204, code overrides, eth_call) on the public endpoints, bracketed by web3_clientVersion',
                'result': 'Celo forno.celo.org: %s. X Layer rpc.xlayer.tech: %s (batches of 20 came back empty and were resent one call at a time; out/live-journal-196-batch20-refused.json). Arc rpc.mainnet.arc.io: %s. Arc arc-rpc.publicnode.com: %s. Arc rpc.blockdaemon.mainnet.arc.io: %s.' % (live('42220'), live('196'), live('5042off'), live('5042pn'), live('5042bd')),
                'source': WD + '/out/live-journal-42220.json'})
cleared.append({'chainIds': [42220, 196, 5042], 'lens': 'L2', 'check': 'Task 5: is the build that answers the image that was read',
                'result': 'Celo: forno answers reth/v2.2.0-74cc8bb, the build string inside the celo-reth v1.0.10 binary. X Layer: rpc.xlayer.tech answers reth/v2.3.0-f60420a/xlayer/v0.0.7, which the binary also carries; the endpoint does not say whether it runs rc.1 or a later v0.0.7 build. Arc: publicnode and blockdaemon answer reth/v2.2.0-508cbdf, which both the v0.8.5 and v0.8.6 images carry, so they cannot be told apart; the official endpoint answers arc/v1, which names no image, and it refuses eth_simulateV1.',
                'source': 'https://forno.celo.org (web3_clientVersion), https://rpc.xlayer.tech (web3_clientVersion), https://rpc.mainnet.arc.io (web3_clientVersion)'})
cleared.append({'chainIds': OTHER, 'lens': 'L2', 'check': 'Scope of this theme', 'result': 'This theme lifts the journals of the Celo, X Layer and Arc images and plants one fault in the World Chain and Zora transient arms. It does not apply to the other sixteen networks.', 'source': 'research/network-risk/cycles/037/plan.json'})

res = {'unit': 'theme-celo-xlayer-arc-journal-lift', 'profiles': [], 'findings': [], 'cleared': cleared,
       'leads': [
           {'chainIds': [196], 'lens': 'L1', 'question': 'Which of the 18 instruction tables of the xlayer-reth v0.0.7.3-rc.1 op-reth binary does block execution and block building select? Their state reads end in calls through a dynamic StateProvider vtable, so the static call graph does not name the database; tracing the vtable a frame passes in, or a later image with symbols, would settle it.',
            'why': 'The journal routines run were those of table 0x718b9e0; the other tables have their own sload_concrete_error copies that differ in the database call only (L-1305 stays open).', 'priority': 'low'},
           {'chainIds': [5042], 'lens': 'L2', 'question': 'Which of the 12 instruction tables of arc-node-execution v0.8.6 executes blocks, and does the ArcEvm frame_init machine code (checked_frame_init, init_deferred_frame_with_transfer_log) call before_frame_init before the child checkpoint as the source says?',
            'why': 'The journal of table 0x4f62ef0 and the hook order in source and on two endpoints were checked; the hook itself was not lifted from the stripped binary and the official endpoint names no build.', 'priority': 'low'},
           {'chainIds': [42220, 196, 5042], 'lens': 'L2', 'question': 'Lift the inlined checkpoint and commit in each binary\'s frame code (make_call_frame and frame_return) and compare them with the EvmInternals copies that were run.',
            'why': 'The runs used the EvmInternals checkpoint and commit, which read and write the same JournalInner fields; the frame code copies were found by pattern only.', 'priority': 'low'}],
       'leadResults': [
           {'leadId': 'L-1311', 'outcome': 'cleared', 'answer': 'Celo (2,124 sequences on the block-validation table, plus the builder table) and X Layer (2,124 sequences over two journal families) ran from the shipped machine code with no mismatch against the revm journal rules or pyevm.py, and the restore-zero, skipped-entry and four more planted faults were caught on both.'},
           {'leadId': 'L-1312', 'outcome': 'cleared', 'answer': 'Arc v0.8.6 ran 1,062 sequences with no mismatch and six planted faults caught. The value hook runs before the child checkpoint, reads the blocklist through the journal and writes nothing; accepted and rejected value calls inside reverted and committed frames left balances, the 0x3600 face, the lock and count words and the Transfer log as the journal rules require on the official and the publicnode endpoints.'},
           {'leadId': 'L-1308', 'outcome': 'cleared', 'answer': 'A re-insert-zero fault in the transient arm of JournalEntry::revert was caught on World Chain, Zora, Celo, X Layer and Arc.'},
           {'leadId': 'L-1307', 'outcome': 'inconclusive', 'answer': 'Not attempted in this cycle; the time went to the three new journal lifts.'}]}
json.dump(res, open(RES, 'w'), indent=1)
print(RES, len(cleared), 'cleared')
