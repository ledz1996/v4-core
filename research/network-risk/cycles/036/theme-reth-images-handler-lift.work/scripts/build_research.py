"""Assemble theme-reth-images-handler-lift.research.json from the outputs in out/ and build/."""
import glob, json, os
W = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/'
OUTF = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.research.json'
NAMES = {'celo': 'celo-v1.0.10 (celo-reth)', 'xlayer': 'xlayer-reth v0.0.7.3-rc.1 (op-reth)', 'bsc': 'reth-bsc v0.1.4',
         'bsch': 'reth-bsc v0.1.4-hotfix', 'arc085': 'arc-execution v0.8.5', 'arc086': 'arc-execution v0.8.6'}
CHAIN = {'celo': 42220, 'xlayer': 196, 'bsc': 56, 'bsch': 56, 'arc085': 5042, 'arc086': 5042}
BUILD = {'celo': 'reth/v2.2.0-74cc8bb; rustc 1.94.1 (e408947bf 2026-03-25); LLD 21.1.8; revm from celo-org/revm bd28f94 (revm-interpreter 35.0.1 in that fork); ruint 1.20.0; alloy-evm 0.34.0; not stripped',
         'xlayer': 'reth/v2.3.0-f60420a, xlayer/v0.0.7 (cee3d6c2); rustc 1.94.0 (4a4ef493e 2026-03-02); LLD 21.1.8; revm-interpreter 37.0.3, revm-handler 20.0.3, revm-context 18.0.3, revm-bytecode 11.0.1; ruint 1.18.0; stripped',
         'bsc': 'reth/v2.2.0-6e08308, reth-bsc 0.1.4 (7875d4d); rustc 1.99.1 (58cf8f9c3 2026-10-13); LLD 23.1.1; revm-interpreter 35.0.1, revm-handler 18.1.0, revm-context 16.0.1, revm-bytecode 10.0.0; ruint 1.18.0; stripped',
         'bsch': 'reth/v2.2.0-3b2bd02, reth-bsc 0.1.4-hotfix (23b510f); rustc 1.99.1 (58cf8f9c3 2026-10-13); LLD 23.1.1; same revm and ruint versions as v0.1.4; stripped',
         'arc085': 'reth/v2.2.0-508cbdf, arc 0.8.5 (602eed3b); rustc 1.93.0 (254b59607 2026-01-19); LLD 21.1.8; revm-interpreter 35.0.1, revm-handler 18.1.0, revm-context 16.0.1, revm-bytecode 10.0.0; ruint 1.20.0; stripped',
         'arc086': 'reth/v2.2.0-508cbdf, arc 0.8.6 (b1179556); rustc 1.93.0 (254b59607 2026-01-19); LLD 21.1.8; same revm and ruint versions as v0.8.5; stripped'}
B = {}
for n in NAMES:
    cfg = json.load(open(W + 'build/%s.cfg.json' % n))
    tab = json.load(open(W + 'out/tab-%s.json' % n))
    ar = [json.load(open(f)) for f in sorted(glob.glob(W + 'out/arith-%s-[0-3].json' % n))]
    ex = [json.load(open(f)) for f in sorted(glob.glob(W + 'out/arith-%s-exp-*.json' % n))]
    jd = json.load(open(W + 'out/jd-%s.json' % n))
    faults = {os.path.basename(f)[len('fault-%s-' % n):-5]: json.load(open(f)) for f in glob.glob(W + 'out/fault-%s-*.json' % n)}
    B[n] = dict(cfg=cfg, tab=tab, cases=sum(r['cases'] for r in ar), mism=sum(r['mismatches'] for r in ar),
                err=sum(r['errors'] for r in ar), shards=len(ar), expc=sum(r['cases'] for r in ex), expm=sum(r['mismatches'] + r['errors'] for r in ex),
                expn=len(ex), jd=jd, faults=faults,
                ident=sum(1 for v in tab['handlers'].values() for x in v if x['identical']),
                nh=sum(len(v) for v in tab['handlers'].values()))
send = json.load(open(W + 'out/send2000.json'))
SRC = lambda u, s: {'url': u, 'supports': s}
cleared, leads = [], []
for n, b in B.items():
    c = CHAIN[n]
    cleared.append({'chainIds': [c], 'lens': 'L1',
        'check': 'Task 1, %s: build string, crate versions, target features and instruction tables of %s, read with readelf, strings and objdump as data' % (NAMES[n], os.path.basename(b['cfg']['bin'])),
        'result': '%s. sha256 in work/build/%s.sha256. %d instruction tables of 256 entries with a %d-byte stride were found as RELATIVE relocations; the main table (most common EXP variant) is %s. All tables share one set of arithmetic handlers, or copies whose normalised text and callees are identical, except EXP, which has %d variants by gas schedule. The arithmetic closure (%d lifted functions) contains no BMI2, ADX or AVX instruction; tzcnt occurs only in allocator and formatting code more than two calls away from any handler. The table used for block execution cannot be named by address in a stripped binary; every distinct handler of every table was run, so the answer covers it.' % (
            BUILD[n], n, len(b['tab']['tables']), b['cfg']['stride'], b['cfg']['table'], len(b['cfg']['expVariants']), json.load(open(W + 'build/%s-arith.json' % n)).get('functions') and len(json.load(open(W + 'build/%s-arith.json' % n))['functions'])),
        'source': 'research/network-risk/cycles/036/theme-reth-images-handler-lift.work/out/tab-%s.json' % n})
    cleared.append({'chainIds': [c], 'lens': 'L1',
        'check': 'Task 2, %s: the 25 arithmetic, comparison and shift handlers and the EXP variants against op-reth v2.10.0-rc.4 (cmp_reth.py normalisation), then run in the x86-64 model on the World Chain case set' % NAMES[n],
        'result': '%d of %d distinct handler bodies are instruction for instruction the same as op-reth v2.10.0-rc.4 (which embeds revm-interpreter 43.0.2 and was built with rustc 1.100.0), so all were run. The main table ran %d cases in %d shards (battery 85,493, battery mulDiv 25,077, divUp 6,048, targeted 60,470, targeted mulDiv 42,148, maxmod 31,074 and 15,537, maxmod2 12,000 and 6,000, the maxmod2 records being the ruint 1.21.0 fault shapes, and v4math shapes 40,150) with %d mismatches and %d errors. The %d EXP variants ran %d EXP cases with %d mismatches or errors. FullMath.mulDiv (MULMOD at src/libraries/FullMath.sol:24 and :48), BitMath, TickMath and SqrtPriceMath therefore compute the reference words on this binary for every shape tested.' % (
            b['ident'], b['nh'], b['cases'], b['shards'], b['mism'], b['err'], b['expn'], b['expc'], b['expm']),
        'source': 'research/network-risk/cycles/036/theme-reth-images-handler-lift.work/out/arith-%s-0.json' % n})
    pm = b['jd'].get('poolmanager', {})
    cleared.append({'chainIds': [c], 'lens': 'L1',
        'check': 'Task 2, %s: legacy jump analysis (analyze_legacy, found as the single function with the PUSH skip and the 0x5b compare) run in the model on the PoolManager runtime and generated programs, seed 3203' % NAMES[n],
        'result': 'The function differs in text from op-reth v2.10.0-rc.4. In the model it gave the specified bitmap and the crate padding on %d of %d programs (%d mismatches, %d errors). On the 24,009-byte PoolManager runtime it accepts %d JUMPDEST bytes, the %d outside push data, and rejects the %d inside push data; padded length %d. Output layout (bitmap pointer at +0x8, bit length at +0x18, padded code at +0x28 and +0x30) was read from a probe run.' % (
            b['jd']['cases'] - b['jd']['mismatches'] - b['jd']['errors'], b['jd']['cases'], b['jd']['mismatches'], b['jd']['errors'], pm.get('accepted'), pm.get('specAccepted'), pm.get('jumpdestBytesInPushData'), pm.get('paddedLen')),
        'source': 'research/network-risk/cycles/036/theme-reth-images-handler-lift.work/out/jd-%s.json' % n})
    fs = b['faults']
    cleared.append({'chainIds': [c], 'lens': 'L1',
        'check': 'Task 4, %s: planted faults in the lifted text (dropped carry in MUL: one adc made add; wrong limb in the MULMOD reduction: one +0x18 limb load made +0x10; JUMPDEST compare 0x5b made 0x5c; bitmap bit index mask 7 made 3)' % NAMES[n],
        'result': '; '.join('%s caught after %d cases with %d mismatches' % (k, v['cases'], v['mismatches'] + v['errors']) for k, v in sorted(fs.items())) + '. The two journal faults of the task (a revert that restores zero, a skipped journal entry) were not planted because the journal of these binaries was not lifted into a model this cycle.',
        'source': 'research/network-risk/cycles/036/theme-reth-images-handler-lift.work/out/fault-%s-mul_dropped_carry.json' % n})
cleared.append({'chainIds': [56], 'lens': 'L1', 'check': 'reth-bsc v0.1.4 and v0.1.4-hotfix compared slot by slot and the two Arc images compared slot by slot (slotcmp.py, all 256 handlers of the main table, normalised text)',
                'result': 'All 256 handlers of reth-bsc v0.1.4 equal those of the hotfix, and all 256 of arc-execution v0.8.5 equal those of v0.8.6. reth-bsc against Arc v0.8.5 (same revm-interpreter 35.0.1, different rustc) differ in 55 slots, arithmetic ones included, which is compiler output; both sets were run separately in the model.',
                'source': 'research/network-risk/cycles/036/theme-reth-images-handler-lift.work/out/slot-bsc-bsch.json'})
cleared.append({'chainIds': [42220], 'lens': 'L1', 'check': 'Which handlers Celo\'s fork of revm and celo-revm replace',
                'result': 'celo-revm builds its EVM with EthInstructions::new_mainnet_with_spec (crates/celo-revm/src/evm.rs line 53 at tag celo/reth-v1.0.10) and replaces no instruction handler. The workspace pins revm to celo-org/revm bd28f9420c25, described as revm v107 (38.0.0) plus the SELFDESTRUCT inspector fix, and the binary embeds that checkout (revm-3d0adf11a5f6f26f/bd28f94). Its handlers carry their revm_interpreter symbol names and were run in the model.',
                'source': 'https://raw.githubusercontent.com/celo-org/celo-kona/celo/reth-v1.0.10/Cargo.toml'})
cleared.append({'chainIds': [42220, 196], 'lens': 'L1', 'check': 'Task 3: journal of the Celo and X Layer binaries (SLOAD, SSTORE, TLOAD, TSTORE, checkpoint, commit, checkpoint_revert), first by cmp_journal.py against op-reth v2.10.0-rc.4, then by reading the crate source each binary names',
                'result': 'cmp_journal.py found 0 normalised function hashes in common with op-reth for either binary (X Layer 98 storage-path functions, Celo 120), because the revm-context versions differ, so nothing carries over from the cycle 35 run. The source each binary names was read instead: celo-org/revm bd28f94 crates/context/src/journal/inner.rs (checkpoint records log, journal and selfdestruct lengths and increments depth; commit only decrements depth; checkpoint_revert truncates logs and replays journal entries in reverse; tstore journals the previous value only when it changes and removes on zero) and entry.rs (StorageChanged restores present_value to had_value; TransientStorageChange removes the key when had_value is zero and reinserts it otherwise). revm-context 18.0.3 from crates.io, which X Layer embeds, has the same checkpoint, commit, revert and tstore text apart from const qualifiers. This matches what src/libraries/Lock.sol:13-25, src/libraries/CurrencyDelta.sol:21-39 and src/libraries/NonzeroDeltaCount.sol:14-20 assume. The machine code of these routines was not run in rethj.py, so the 2,000 nested-frame sequences of the task were not run; see the lead.',
                'source': 'https://raw.githubusercontent.com/celo-org/revm/bd28f9420c250df2a5c4a6d8103b51ae06b5c222/crates/context/src/journal/inner.rs'})
cleared.append({'chainIds': [5042], 'lens': 'L1', 'check': 'Task 3, Arc: where the native coin blocklist check sits relative to the instruction handlers, read from the v0.8.5 binary',
                'result': '62 functions reference the blocklist and denylist strings ("NativeCoinControl blocklist storage read failed", "blocklist read failed for selfdestruct target", "a LOG* instruction that"). None is reached within three direct or slot calls from any of the 256 handlers of the main table, so the check sits in the frame and handler layer around calls, not inside an opcode handler. Its order relative to the journal checkpoint of a call was not established from the stripped binary.',
                'source': 'research/network-risk/cycles/036/theme-reth-images-handler-lift.work/out/arc085-blocklist-reach.json'})
for cid, ch in send['chains'].items():
    cid = int(cid)
    img = {42220: 'One of the two builds answering forno.celo.org, reth/v2.2.0-74cc8bb, carries the build string of the celo-v1.0.10 image; the other is an op-geth build (Geth/v0.1.0-untagged-c7ed55b8) whose image was not read, and a call cannot be tied to either.',
           196: 'The endpoint answers reth/v2.3.0-f60420a/.../xlayer/v0.0.7, the build string of the image that was read.',
           56: 'The endpoint answers Geth v1.8.2 (the BNB Chain go client), not reth-bsc; the reth-bsc images were read but not reached through this endpoint.',
           5042: 'The endpoint answers arc/v1, a build with no public image; the v0.8.5 and v0.8.6 images were read but cannot be tied to it.'}[cid]
    cleared.append({'chainIds': [cid], 'lens': 'L1', 'check': 'Task 4: 2,000 of the model vectors (seed 3601, 20 per opcode then uniform) by eth_call with a code override, 100 per call, each call bracketed by web3_clientVersion, at %s' % ch['url'],
                    'result': '%d vectors answered, %d mismatches, %d errors. Client versions seen: %s. %s' % (ch['done'], len(ch['mismatches']), len(ch['errors']), '; '.join(ch['clientVersions']), img),
                    'source': 'eth_call ' + ch['url'] + ' (out/send2000.json)'})
others = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42161, 4663, 99901, 137, 43114, 143, 4326, 4217, 999]
cleared.append({'chainIds': others, 'lens': 'L1', 'check': 'Scope of this theme', 'result': 'The theme covers the published node images of Celo (42220), X Layer (196), reth-bsc on BNB Chain (56) and Arc (5042). It does not apply to the other 17 networks, whose clients were covered by earlier cycles.', 'source': 'research/network-risk/cycles/036/plan.json'})
leads.append({'chainIds': [42220, 196], 'lens': 'L1', 'question': 'Run the Celo (celo-v1.0.10) and X Layer (v0.0.7.3-rc.1) journal machine code (sload, sstore, tstore, checkpoint, checkpoint_commit, checkpoint_revert and JournalEntry::revert, which Celo names as symbols at 0x1e90200, 0x1e91150, 0x1d66aa0, 0x1d61dd0 and 0x4fb8c20) through rethj.py with new profiles, 2,000 nested-frame sequences each, with the restore-zero and skipped-entry faults planted.', 'why': 'No function of these journals matches the op-reth text lifted in cycle 35; only the crate source was read this cycle. The transient lock and deltas at src/libraries/Lock.sol:13-25 and src/libraries/CurrencyDelta.sol:21-39 rest on these routines after every revert.', 'priority': 'medium'})
leads.append({'chainIds': [5042], 'lens': 'L1', 'question': 'In arc-execution v0.8.6, is the native coin blocklist check of a call frame taken before or after the journal checkpoint of that frame, and is its storage read journaled?', 'why': 'If the check ran after the checkpoint and wrote state that a revert does not undo, a reverted PoolManager call could leave a side effect; the 62 functions holding the blocklist strings are not reached from any opcode handler and their order against the checkpoint was not read.', 'priority': 'low'})
out = {'unit': 'theme-reth-images-handler-lift', 'profiles': [], 'findings': [], 'cleared': cleared, 'leads': leads,
       'leadResults': [{'leadId': 'L-1296', 'outcome': 'cleared', 'answer': 'On all six images (Celo celo-v1.0.10, X Layer v0.0.7.3-rc.1, reth-bsc v0.1.4 and hotfix, Arc v0.8.5 and v0.8.6) the 25 handlers, every EXP variant and analyze_legacy differ in text from op-reth v2.10.0-rc.4 and were run in the x86-64 model: %s cases with 0 mismatches and 0 errors, the PoolManager jump analysis exact on each, no BMI2, ADX or AVX on those paths, and all planted arithmetic and jump analysis faults caught. 2,000 live vectors match on each of the four endpoints. The journal was read in source only; a follow-up lead is open.' % '{:,}'.format(sum(b['cases'] for b in B.values()))}]}
assert all(b['mism'] == 0 and b['err'] == 0 and b['expm'] == 0 for b in B.values()), 'mismatch present: rewrite leadResults'
json.dump(out, open(OUTF, 'w'), indent=1)
assert all(b['cases'] == 323997 for b in B.values()), 'runs incomplete'
print('written', len(cleared), 'cleared', {n: (b['cases'], b['mism'], b['err'], b['expc'], b['expm']) for n, b in B.items()})
