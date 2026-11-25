"""Combine pass one (raw/replay_*.jsonl) and pass two (raw/prefix.jsonl) into raw/summary.json."""
import json, glob, collections
P1 = {}
for f in sorted(glob.glob('raw/replay_*.jsonl')):
    for l in open(f):
        r = json.loads(l); P1[r['tx']] = r
P2 = {}
for f in sorted(glob.glob('raw/prefix*.jsonl')):
    for l in open(f):
        r = json.loads(l); P2[r['tx']] = r
S = json.load(open('raw/selection.json'))
def bad1(r):
    b = []
    if not r['logsEqual']: b.append('logs')
    if r['statusRef'] != r['statusChain']: b.append('status')
    if r.get('pmSlotMismatch'): b.append('slots')
    if r.get('pmNativeEqual') is False: b.append('pmnative')
    if any(x[-1] is False for x in r['recipients']): b.append('recip')
    return b
out = {'selected': len(S['selected']), 'window': S['window'], 'head': S['head'], 'seed': None, 'done': 0, 'unsupported': {}, 'errors': [],
       'equalPass1': 0, 'equalPass2': 0, 'residual': [], 'counts': collections.Counter()}
tot = collections.Counter()
for h in S['selected']:
    r = P1.get(h)
    if r is None: tot['notRun'] += 1; continue
    out['done'] += 1
    if 'error' in r: out['errors'].append([h, r['error']]); continue
    if 'unsupported' in r: out['unsupported'][h] = r['unsupported']; continue
    tot['replayed'] += 1
    tot['pmFrames'] += len(r['pmFrames']); tot['pmSlots'] += r['pmSlots']; tot['pmSlotsWritten'] += r['pmSlotsWritten']
    if 'pmSlotMismatch' in r: tot['txWithSlotCheck'] += 1; tot['slotsChecked'] += r['pmSlots']
    if 'pmNativeEqual' in r: tot['txWithPmBalanceCheck'] += 1
    for x in r['recipients']:
        tot['recipientsChecked' if isinstance(x[-1], bool) else 'recipientsSkipped'] += 1
    tot['logs'] += r['logsChain']
    b = bad1(r)
    if not b: out['equalPass1'] += 1; continue
    q = P2.get(h)
    if q is None: out['residual'].append([h, 'no second pass', b]); continue
    if 'unsupported' in q or 'error' in q: out['residual'].append([h, 'second pass: ' + str(q.get('unsupported', q.get('error'))), b]); continue
    b2 = []
    if not q['logsEqual']: b2.append('logs')
    if q['statusRef'] != q['statusChain']: b2.append('status')
    if q.get('pmSlotMismatch'): b2.append('slots')
    # PoolManager balance and recipient checks of pass one were made only for blocks where no other transaction moved native value of the PoolManager or recipient,
    # so a pass one difference there with an equal pass two log record is a stale start state
    if not b2:
        out['equalPass2'] += 1; continue
    out['residual'].append([h, 'pass two', b2, {k: q.get(k) for k in ('pmLogsEqual', 'pmLogs', 'pmNativeLogsEqual', 'pmNativeLogs', 'diffAddrs', 'statusRef', 'statusChain', 'pmSlotMismatch', 'notes')}])
# chain-internal check: where the PoolManager balance change of the block was read, it equals the net of the system emitter
# Transfer logs of the transaction that name the PoolManager
D = json.load(open('raw/txs.json'))
pmt = '0x' + '0' * 24 + '8366a39cc670b4001a1121b8f6a443a643e40951'; em = '0xfffffffffffffffffffffffffffffffffffffffe'
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
bc = [0, 0, []]
for h, r in P1.items():
    if 'pmNativeDeltaChain' not in r: continue
    net = 0
    for l in D['tx'][h]['rec']['logs']:
        if l['address'].lower() == em and len(l['topics']) == 3 and l['topics'][0] == T:
            v = int(l['data'], 16)
            if l['topics'][2].lower() == pmt: net += v
            if l['topics'][1].lower() == pmt: net -= v
    bc[0] += 1
    if net == int(r['pmNativeDeltaChain']): bc[1] += 1
    else: bc[2].append([h, r['pmNativeDeltaChain'], str(net)])
out['pmBalanceVsEmitterLogs'] = {'checked': bc[0], 'equal': bc[1], 'different': bc[2]}
out['counts'] = dict(tot)
json.dump(out, open('raw/summary.json', 'w'), indent=1)
print({k: v for k, v in out.items() if k not in ('residual', 'unsupported', 'errors')}, 'unsupported', len(out['unsupported']), 'errors', len(out['errors']), 'residual', len(out['residual']))
print(collections.Counter(v[:40] for v in out['unsupported'].values()))
for x in out['residual'][:30]: print(json.dumps(x)[:400])
