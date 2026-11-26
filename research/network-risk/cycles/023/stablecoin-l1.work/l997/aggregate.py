"""Aggregate the L-997 first pass (raw/r2_*.jsonl, raw/run_*.jsonl) and second pass (raw/prefix*.jsonl). Writes aggregate.json."""
import json, glob, os, collections
H = os.path.dirname(os.path.abspath(__file__)); os.chdir(H)
PM = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
p1 = {}
for f in sorted(glob.glob('raw/run_*.jsonl')) + sorted(glob.glob('raw/r2_*.jsonl')):
    for l in open(f):
        try: r = json.loads(l)
        except Exception: continue
        p1[r['tx']] = r
p2 = {}
for f in sorted(glob.glob('raw/prefix*.jsonl')):
    for l in open(f):
        try: r = json.loads(l)
        except Exception: continue
        p2[r['tx']] = r
def bad(r):
    if 'logsEqual' not in r: return False
    return (not r['logsEqual']) or r['statusRef'] != r['statusChain'] or bool(r.get('pmSlotMismatch')) or r.get('pmNativeEqual') is False or any(x[-1] is False for x in r['recipients'])
def pmfields(r):
    m = r.get('logMismatch') or {}
    return [x for x in m.get('chain', []) + m.get('ref', []) if x[0] == PM]
out = {'firstPass': len(p1)}
uns = [r for r in p1.values() if 'unsupported' in r or 'error' in r]
out['unsupported'] = collections.Counter(((r.get('unsupported') or r.get('error'))[:60]) for r in uns).most_common()
ran = [r for r in p1.values() if 'logsEqual' in r]
out['ran'] = len(ran); b1 = [r for r in ran if bad(r)]; out['firstPassDiffer'] = len(b1)
out['firstPassMatch'] = len(ran) - len(b1)
good = [r for r in ran if not bad(r)]
out['firstPassMatchSlotsCompared'] = sum(1 for r in good if 'pmSlotMismatch' in r)
out['firstPassMatchSlotWords'] = sum(r.get('pmSlots', 0) for r in good if 'pmSlotMismatch' in r)
out['firstPassMatchLogs'] = sum(r['logsChain'] for r in good)
res = collections.Counter(); left = []; slotc = collections.Counter()
for r in b1:
    q = p2.get(r['tx'])
    if q is None: res['no second pass'] += 1; left.append(r['tx']); continue
    if 'unsupported' in q or 'error' in q: res['second pass unsupported: ' + (q.get('unsupported') or q.get('error'))[:50]] += 1; continue
    ok_status = q['statusRef'] == q['statusChain']; slots = not q.get('pmSlotMismatch')
    if q.get('pmSlotMismatch') is None: res2slot = 'slots not compared (a later transaction of the block touches the PoolManager)'
    else: res2slot = 'slots compared'
    slotc[res2slot] += 1
    if q['logsEqual'] and ok_status and slots: res['match after block prefix'] += 1; continue
    other = sorted(set(q.get('diffAddrs', [])) - {PM})
    if ok_status and slots and q.get('pmLogsEqual'):
        res['PoolManager logs and slots match; other logs differ: ' + ','.join(a[:10] for a in other)[:80]] += 1; continue
    res['PoolManager differs'] += 1; left.append(q['tx'])
def pmsame(r):
    m = r.get('logMismatch') or {'chain': [], 'ref': []}
    return not any(x[0] == PM for x in m['chain'] + m['ref']) and r['statusRef'] == r['statusChain'] and not r.get('pmSlotMismatch')
out['notRerunAfterEarlierTx'] = sum(1 for h in left if p1[h]['index'] > 0)
out['notRerunFirstInBlockPmSame'] = sum(1 for h in left if p1[h]['index'] == 0 and pmsame(p1[h]))
out['notRerunFirstInBlockPmDiffer'] = sum(1 for h in left if p1[h]['index'] == 0 and not pmsame(p1[h]))
out['secondPass'] = dict(res); out['secondPassSlots'] = dict(slotc); out['unresolved'] = left
json.dump(out, open('aggregate.json', 'w'), indent=1); print(json.dumps(out, indent=1)[:3000])
