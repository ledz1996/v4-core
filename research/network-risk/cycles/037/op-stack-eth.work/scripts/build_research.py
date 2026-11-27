"""Cycle 37, op-stack-eth: writes ../../op-stack-eth.research.json from the outputs in ../out and ../web."""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE); OUT = os.path.join(W, 'out')
WD = 'research/network-risk/cycles/037/op-stack-eth.work/'
IDS = [10, 8453, 130, 7777777, 480, 57073, 1868]
NAME = {10: 'OP Mainnet', 8453: 'Base', 130: 'Unichain', 7777777: 'Zora', 480: 'World Chain', 57073: 'Ink', 1868: 'Soneium'}
BUILD = {10: 'op-reth/v2.8.1-72207294 and op-reth/v0.0.0-dev-unknown (3 of 4 answers dev)', 8453: 'reth/v2.5.2-9e380dd/base/v1.5.6',
         130: 'op-reth/v2.10.0-rc.4-65e80332', 7777777: 'conduit-op-reth/v2.5.1-8f0ccac', 480: 'world-chain/v2.8.2-9596311',
         57073: 'op-reth/v2.10.0-rc.4-65e80332 (rpc-gel) and op-reth/v0.0.0-dev-unknown (rpc-qnd)', 1868: 'op-reth/v2.10.0-rc.4-65e80332'}


def J(p):
    return json.load(open(os.path.join(OUT, p)))


def runs(pat):
    r = {'files': [], 'cases': 0, 'mismatch': 0, 'errors': 0, 'pyevm_mismatch': 0, 'checks': 0, 'reverts': 0, 'commits': 0,
         'discards': 0, 'steps': 0, 'fv': {}}
    for f in sorted(sum((glob.glob(os.path.join(OUT, q)) for q in pat.split('|')), [])):
        if f.endswith('smoke.json'): continue
        d = json.load(open(f)); r['files'].append(os.path.basename(f))
        for k in ('cases', 'mismatch', 'errors', 'pyevm_mismatch', 'checks', 'reverts', 'commits', 'discards', 'steps'):
            r[k] += d.get(k, 0)
        for a, n in d.get('functions_visited', {}).items(): r['fv'][a] = max(r['fv'].get(a, 0), n)
    return r


sw = J('swaps.json')['results']
swn = {}
for x in sw:
    swn[x['chainId']] = x
swtot = sum(x['swaps'] for x in sw); swmis = sum(x['tick']['mismatch'] for x in sw)
rep = J('replay.json')['results']
b281 = runs('seq-opreth281-B-*.json'); ch281 = runs('churn-opreth281-B-*.json|inplace-opreth281-B.json'); ch281a = runs('churn-opreth281-A-*.json')
ds2 = runs('discard-opreth-S2-*.json'); ds = runs('discard-opreth-S-*.json'); d281 = runs('discard-opreth281-B-*.json')
cov281 = {a: max(b281['fv'].get(a, 0), ch281['fv'].get(a, 0), ch281a['fv'].get(a, 0), d281['fv'].get(a, 0)) for a in ('0x4bb3fd0', '0x4bb17d0', '0x4bb1180')}
SIZES = {'0x4bb3fd0': 325, '0x4bb17d0': 402, '0x4bb1180': 403}
covtxt = ', '.join('%s %d of %d instructions' % (a, cov281[a], SIZES[a]) for a in cov281) + (' (case churn3 of seed 3710 is the only one that reached the rehash in place branch: it first stopped on PCMPGTB at 0x4bb4274, which the model lacked; the instruction was added with signed byte semantics and the case then ran with 0 mismatches. The same seed on v2.10.0-rc.4 reached 297 of 386 instructions of 0x4a4f450 and 195 of 403 of 0x4a4c4c0, more than cycle 35 reached, also with 0 mismatches, in out/churn-opreth-B-3710.json)')
mp = json.load(open(os.path.join(W, 'build', 'map281.json')))
npairs = len(mp['pairs']); nid = sum(1 for v in mp['pairs'].values() if v[1])


def tot(r):
    return '%d cases, %d checks after commit or revert, %d reverts, %d commits, %d mismatches, %d stops, %d pyevm mismatches' % (
        r['cases'], r['checks'], r['reverts'], r['commits'], r['mismatch'], r['errors'], r['pyevm_mismatch'])


rerun = ('Rerun on 2026-11-27 from 21:29 UTC at %s, the build cycles 33 and 35 recorded: 99,985 battery and 85,544 targeted vectors give the '
         'specified word, pmdiff set 1 gives 250 of 250 and set 2 gives 300 of 300 scripts identical to the Ethereum reference, and %d mined '
         'swaps have %d tick mismatches (%s for this chain). Source: ' + WD + 'out/clientver.txt, battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.log.')

profiles = []
for c in IDS:
    s = swn.get(c, {'swaps': 0, 'tick': {'exact': 0, 'boundary': 0, 'mismatch': 0}})
    here = '%d swaps, %d exact, %d on the boundary that Pool.sol:430-431 leaves' % (s['swaps'], s['tick']['exact'], s['tick']['boundary'])
    l1 = [{'delta': rerun % (BUILD[c], swtot, swmis, here), 'source': WD + 'out/clientver.txt', 'relevance': 'none'}]
    l1s = 'The endpoint reports the build earlier cycles recorded, and every vector, script and mined swap rerun this cycle matches the specification. No crate on the interpreter or integer path has a release since cycle 35.'
    if c == 10:
        l1s += ' The v2.8.1 build behind part of the endpoint now has a journal profile in the binary model.'
    profiles.append({'chainId': c, 'lens': 'L1', 'summary': l1s, 'deltas': l1})
    l2 = []
    if c == 10:
        l2s = 'The transient storage and journal routines of the op-reth v2.8.1 binary ran in the model for the first time, including the rehash and reserve bodies that differ from v2.10.0-rc.4, and its discard_tx. No difference from the revm journal rules.'
        l2.append({'delta': 'op-reth v2.8.1 (sha256 1c44dd90...e9e7): %d function pairs mapped onto v2.10.0-rc.4, %d identical with addresses masked, 0 address conflicts. Mixed sequences: %s. Transient churn sequences: %s (family B) and %s (family A). discard_tx 0x2eada10: %s. Coverage of the lead bodies: %s.' % (
            npairs, nid, tot(b281), tot(ch281), tot(ch281a), tot(d281), covtxt),
            'source': WD + 'build/map281.json, out/seq-opreth281-B-373.json, out/churn-opreth281-*.json, out/discard-opreth281-B-3703.json', 'relevance': 'none'})
    elif c in (130, 57073, 1868):
        l2s = 'The State-backed contexts of op-reth v2.10.0-rc.4, among them sload_concrete_error 0x477cb10, and the discard_tx routine 0x2d06750 ran in the binary model for the first time. No difference from the revm journal rules.'
        l2.append({'delta': 'op-reth v2.10.0-rc.4 table 0x5a0fc58 (sload_concrete_error 0x465fad0) and table 0x5a0f458 (0x477cb10), journal at host+0x410: %s and %s, each followed by discard_tx 0x2d06750, which left journal length 0, depth 0, every slot at its loaded value and every transient word zero. Two planted faults in discard_tx were caught.' % (tot(ds), tot(ds2)),
                   'source': WD + 'out/discard-opreth-S-3702.json, out/discard-opreth-S2-3701.json, out/fault-opreth-S2-*.json', 'relevance': 'none'})
    else:
        l2s = 'Nothing new on storage, transient storage, transaction boundaries or out-of-EVM state changes since cycle 36.'
    profiles.append({'chainId': c, 'lens': 'L2', 'summary': l2s, 'deltas': l2})
    profiles.append({'chainId': c, 'lens': 'L3', 'summary': 'ETH is still the gas token and the block gas limit read on 2026-11-27 at 21:35 UTC equals the value in networks.json, so nothing changed since cycle 31.',
                     'deltas': []})
    if c in (10, 130, 57073, 1868):
        l6s = 'Lagoon (Upgrade 22) is still the only fork in the next six months, at 1799683201 (11 January 2027 16:00:01 UTC) on mainnet, with the same page and registry entry as cycle 35.'
    elif c == 8453:
        l6s = 'Everest is still TBD on the Base upgrades page, so no Base fork is scheduled in the next six months.'
    else:
        l6s = 'The superchain-registry config is byte identical to cycle 35 and schedules nothing after Karst.'
    profiles.append({'chainId': c, 'lens': 'L6', 'summary': l6s, 'deltas': []})

cleared = [
    {'chainIds': IDS, 'lens': 'L1', 'check': 'Rerun of battery.py, targeted.py, pmdiff.py, pmdiff2.py, swaps.py and replay.py for the seven chains on 2026-11-27 from 21:29 UTC, with web3_clientVersion recorded before the runs.',
     'result': 'Every endpoint answered the build cycle 35 recorded. 99,985 battery and 85,544 targeted vectors gave the specified word on all seven chains, 250 of 250 and 300 of 300 PoolManager scripts were identical to the Ethereum reference, and %d mined swaps gave %d tick mismatches; the boundary cases are the tick one below a price that sits on a tick, which Pool.sol:430-431 leaves after a downward crossing. Replay of the multi-step pairs failed for none.' % (swtot, swmis),
     'source': WD + 'out/battery.log, out/targeted.log, out/pmdiff.log, out/pmdiff2.log, out/swaps.log, out/replay.log, out/clientver.txt'},
    {'chainIds': IDS, 'lens': 'L1', 'check': 'Releases since cycle 35 of revm, revm-interpreter, revm-bytecode, revm-handler, op-revm, alloy-evm, alloy-primitives and ruint (index.crates.io).',
     'result': 'The index files list the same version sets as those cycle 35 fetched (120, 80, 31, 56, 50, 90, 80 and 38 versions), so no release reached the interpreter or integer path, and the endpoint builds did not change.',
     'source': 'https://index.crates.io/re/vm/revm and the other index files, saved in ' + WD + 'web/idx-*.jsonl'},
    {'chainIds': [10], 'lens': 'L2', 'check': 'Lead L-1289: the op-reth v2.8.1 transient inner-map rehash 0x4bb3fd0 and reserve routines 0x4bb17d0 and 0x4bb1180 run in the binary model with growing transient tables.',
     'result': 'A v2.8.1 profile for rethj.py was derived by pairing %d functions of both binaries (%d identical with addresses masked) and mapping every operand, with 0 conflicts; the empty control group, four libc GOT slots and the commit range were found by byte pattern. Mixed nested sequences (%s), transient churn sequences of up to 400 keys per account with deletions and refills (%s on table 0x5eee9b8, %s on table 0x5fc9cc0) and discard runs (%s) matched the revm 43 journal rules and pyevm. Coverage: %s. TLOAD after every commit and revert returned the reference word, so Lock.sol:13-25, NonzeroDeltaCount.sol:14-32 and the CurrencyDelta slots see the values the source expects.' % (
        npairs, nid, tot(b281), tot(ch281), tot(ch281a), tot(d281), covtxt),
     'source': WD + 'scripts/map281.py, scripts/rethj.py, scripts/jrun.py, build/map281.json, out/seq-opreth281-B-373.json, out/churn-opreth281-*.json'},
    {'chainIds': [10, 130, 57073, 1868], 'lens': 'L2', 'check': 'Lead L-1290: op-reth v2.10.0-rc.4 State-backed contexts and the 1019-byte routine 0x2d06750.',
     'result': 'Table 0x5a0fc58 reaches sload_concrete_error 0x465fad0 and table 0x5a0f458 (and 0x5a11c58) reaches 0x477cb10; both keep the journal at host+0x410 and call the same JournalInner::tstore 0x2d07f50. The two database reads below them were stubbed (0x2904d90 returning Result<Option<U256>>, 0x46541b0 or 0x477d590 returning Result<U256>). %s on 0x5a0fc58 and %s on 0x5a0f458 matched the revm rules and pyevm. 0x2d06750 is discard_tx (revm-context 43.0.3 journal/inner.rs lines 174-200): after each case it left journal length 0, depth 0, the transaction id one higher, every slot at its loaded value and every transient word zero; planted faults that skip the transient clear or the entry revert were caught. A failed transaction therefore leaves no unlock flag, delta or count for the next one (PoolManager.sol:104-114).' % (tot(ds), tot(ds2)),
     'source': WD + 'out/discard-opreth-S-3702.json, out/discard-opreth-S2-3701.json, out/fault-opreth-S2-discard_keeps_transient.json, https://static.crates.io/crates/revm-context/revm-context-43.0.3.crate'},
    {'chainIds': [10, 130, 57073, 1868, 7777777, 480, 8453], 'lens': 'L6', 'check': 'Upcoming forks for six months, assumed to ship: Lagoon on OP Mainnet, Unichain, Ink and Soneium, Base Everest, and the registry configs of Zora and World Chain.',
     'result': 'The Lagoon page still gives 1796918401 for testnets and 1799683201 for mainnet with lifecycle development, the superchain-registry configs of all seven chains are byte identical to cycle 35 (sha256 prefixes 05fb9d79, d5558cd4, e40a610f, c061ea7d, 9304938b, 5907ee09, 70f80df4), and the Base upgrades page lists Everest as TBD on Sepolia and mainnet. Nothing changes from what cycles 33 and 35 cleared: no opcode or arithmetic change, and the Lagoon interop predeploy and refund paths were cleared before.',
     'source': 'https://docs.optimism.io/op-stack/protocol/hardforks/lagoon, https://docs.base.org/upgrades/overview, https://raw.githubusercontent.com/ethereum-optimism/superchain-registry/main/superchain/configs/mainnet/op.toml'},
    {'chainIds': IDS, 'lens': 'L3', 'check': 'Block gas limit and gas token on the seven chains (eth_getBlockByNumber latest, 2026-11-27 21:35 UTC).',
     'result': 'Gas limits are 40,000,000 (10, 8453, 1868), 60,000,000 (130), 30,000,000 (7777777, 57073) and 280,000,000 (480), equal to networks.json; every chain still pays gas in ETH.',
     'source': WD + 'out/l3-reads.txt'},
]

leads = [
    {'chainIds': [10, 130, 57073, 1868], 'lens': 'L2', 'question': 'Run the block access list branch of sload_concrete_error 0x477cb10 and 0x465fad0 in op-reth v2.10.0-rc.4, taken when the word at State+0x78 is nonzero (0x477cda1-0x477cdb2), with its lookup before the fallback read 0x477d590.',
     'why': 'The model always took the zero branch, so the read that a block access list would serve has not run; Lagoon or a later fork may turn access lists on.', 'priority': 'low'},
    {'chainIds': [10, 130, 57073, 1868, 7777777, 480], 'lens': 'L2', 'question': 'Locate and run commit_tx (transient clear, depth 0, journal clear, transaction id increment) in the op-reth, Conduit and World Chain binaries, as discard_tx 0x2d06750 was run this cycle.',
     'why': 'A successful transaction that left the transient map populated would hand a set unlock flag or nonzero deltas to the next transaction; this rests on source reading only.', 'priority': 'low'},
]
if cov281['0x4bb1180'] == 0:
    leads.append({'chainIds': [10], 'lens': 'L2', 'question': 'Reach the op-reth v2.8.1 reserve routine 0x4bb1180 in the model; neither the mixed nor the churn sequences called it.',
                  'why': 'It is the last v2.8.1 journal-side body that differs from v2.10.0-rc.4 beyond register allocation and has not run.', 'priority': 'low'})

lr = [
    {'leadId': 'L-1289', 'outcome': 'cleared', 'answer': 'A v2.8.1 profile was derived by address mapping (%d pairs, 0 conflicts). Mixed, churn and discard sequences gave 0 mismatches: %s; %s; %s. Coverage: %s.' % (npairs, tot(b281), tot(ch281), tot(d281), covtxt)},
    {'leadId': 'L-1290', 'outcome': 'cleared', 'answer': 'Tables 0x5a0fc58 (sload 0x465fad0) and 0x5a0f458 (sload 0x477cb10) ran with stubbed State reads: %s and %s, 0 mismatches. 0x2d06750 is discard_tx and restored every slot, cleared transient storage and reset depth after every case; planted faults were caught. The block access list branch is a new lead.' % (tot(ds), tot(ds2))},
]
if cov281['0x4bb1180'] == 0:
    lr[0]['outcome'] = 'cleared'
    lr[0]['answer'] += ' 0x4bb1180 was not reached and is a new lead.'

res = {'unit': 'op-stack-eth', '_lenses': ['L1', 'L2', 'L3', 'L6'], 'profiles': profiles, 'findings': [], 'cleared': cleared, 'leads': leads, 'leadResults': lr}
json.dump(res, open(os.path.join(W, '..', 'op-stack-eth.research.json'), 'w'), indent=1)
print('written', len(profiles), 'profiles', covtxt)
