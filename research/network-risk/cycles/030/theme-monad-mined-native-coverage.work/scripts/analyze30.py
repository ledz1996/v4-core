"""Replay every fetched transaction (replay30.replay_tx), compare with the mined logs of eth_getLogs, and map the program
counters to the 913 IR blocks of Monad's compiler (cycle 28 blocks.py / covtable-0.16.7.json).
Usage: python3 -I analyze30.py <blocksdir> <logs.json> <out prefix>"""
import sys, os, json, gzip, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import replay30 as RP
NR = '/home/user/v4-core/research/network-risk'
C28 = os.path.join(NR, 'cycles', '028', 'theme-monad-native-unentered-blocks.work')
sys.path.insert(0, os.path.join(C28, 'scripts')); import blocks as BL
cov = json.load(open(os.path.join(C28, 'out', 'covtable-0.16.7.json')))
OFFS = [int(r['block'], 16) for r in cov['rows']]; assert len(OFFS) == 913
code = bytes.fromhex(open(os.path.join(os.path.dirname(HERE), 'out', 'monad-pm-code.hex')).read().strip()[2:])
bd, lf, outp = sys.argv[1], sys.argv[2], sys.argv[3]
L = json.load(open(lf)); mined = collections.defaultdict(list)
for l in sorted(L['logs'], key=lambda l: (l['b'], l['i'])): mined[l['tx']].append((l['topics'], l['data']))
files = sorted(glob.glob(os.path.join(bd, '*.json.gz')))
hits = collections.Counter(); status = collections.Counter(); rows = []; mm = []; sels = collections.Counter(); ntx = 0
failed_tx = 0; failed_frames = 0; logsEq = collections.Counter(); stEq = collections.Counter(); per_block_written = {}
first_seen = {}
for fn in files:
    d = json.load(gzip.open(fn))
    for t in d.get('txs', []):
        r = RP.replay_tx(code, t, mined.get(t['hash'], []) if d['block'] <= L['reached'] else None)
        pcs = set(r.pop('pcs')); ent = [o for o in OFFS if o in pcs]
        for o in ent:
            hits[o] += 1; first_seen.setdefault(o, (d['block'], t['hash']))
        ntx += 1; status[r['status']] += 1
        for s in r['sels']: sels[s] += 1
        if r['txError']: failed_tx += 1
        failed_frames += r['failedFrames']; logsEq[str(r.get('logsEqMined'))] += 1; stEq[str(r['storageEq'])] += 1
        r['block'] = d['block']; r['entered'] = len(ent)
        if r['status'] != 'ok' or not r['storageEq'] or not r.get('logsEqMined', True) or not r['logsEqTrace']:
            mm.append(dict(r))
        per_block_written.setdefault(d['block'], {}).update(r.pop('written'))
        rows.append({k: r[k] for k in ('block', 'hash', 'i', 'status', 'txError', 'frames', 'sels', 'failedFrames', 'logsN', 'logsEqTrace', 'logsEqMined', 'storageEq', 'slotsWritten', 'entered') if k in r})
summ = {'blocksFiles': len(files), 'txs': ntx, 'status': status, 'failedTx': failed_tx, 'failedFrames': failed_frames,
        'logsEqMined': logsEq, 'storageEqDiffPost': stEq, 'selectors': sels, 'mismatches': len(mm),
        'blocksEntered': len(hits), 'blocksNotEntered': [hex(o) for o in OFFS if o not in hits]}
json.dump(summ, open(outp + '-summary.json', 'w'), indent=1)
json.dump({'hits': {hex(o): hits[o] for o in OFFS}, 'first': {hex(o): v for o, v in first_seen.items()}}, open(outp + '-hits.json', 'w'))
json.dump(mm, open(outp + '-mismatches.json', 'w'), indent=1)
json.dump(per_block_written, open(outp + '-written.json', 'w'))
with open(outp + '-rows.jsonl', 'w') as f:
    for r in rows: f.write(json.dumps(r) + '\n')
print(json.dumps({k: v for k, v in summ.items() if k != 'blocksNotEntered'}, default=str)); print('not entered', len(summ['blocksNotEntered']))
