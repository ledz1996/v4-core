"""Second pass over frames.json: for every compared transaction, pair the PoolManager frames of the
recorded tree (block execution) and of the interpreter replay by position, and for each pair with
the same input compare what the PoolManager itself produced: its output, error, logs, and the
calls it made (target, value, input) with their outputs. Also lists which frames differ only in
gasUsed. Read-only. Usage: python3 -I pmframes.py <frames.json> <out.json> [threads]"""
import sys, os, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpcq import rpc
import importlib.util
spec = importlib.util.spec_from_file_location('fm', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames_monad.py'))
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'; TR = {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}
SELS = {'0x48c89491': 'unlock', '0xa5841194': 'sync', '0x11da60b4': 'settle', '0x3dd45adb': 'settleFor', '0x0b0d9c09': 'take',
        '0x156e29f6': 'mint', '0xf5298aca': 'burn', '0x80f0b44c': 'clear', '0xf3cd914c': 'swap', '0x5a6bcfda': 'modifyLiquidity'}


def nodes(n, path='r', undone=False, out=None):
    err = 'error' in n; u = undone or err
    out.append((path, n, u))
    for i, c in enumerate(n.get('calls', []) or []): nodes(c, f'{path}.{i}', u, out)
    return out


def own(n):
    logs = [((l.get('address') or '').lower(), tuple(t.lower() for t in l.get('topics', [])), (l.get('data') or '0x').lower(), l.get('position')) for l in n.get('logs', []) or []]
    calls = [((c.get('type')), (c.get('to') or '').lower(), c.get('value') or '0x0', (c.get('input') or '0x').lower(), (c.get('output') or '0x').lower(), c.get('error')) for c in n.get('calls', []) or []]
    return ((n.get('output') or '0x').lower(), n.get('error'), logs, calls)


def one(r):
    h = r['tx']
    try:
        tx = rpc('eth_getTransactionByHash', [h]); b = int(tx['blockNumber'], 16)
        rec = rpc('debug_traceTransaction', [h, TR])
        call = {'from': tx['from'], 'to': tx['to'], 'data': tx['input'], 'value': tx['value'], 'gas': tx['gas']}
        if tx.get('accessList'): call['accessList'] = tx['accessList']
        if tx.get('authorizationList'): call['authorizationList'] = tx['authorizationList']
        rep = rpc('debug_traceCall', [call, hex(b - 1), TR])
    except Exception as e:
        return {'tx': h, 'err': str(e)[:200]}
    A = nodes(rec, out=[]); B = {p: (n, u) for p, n, u in nodes(rep, out=[])}
    pairs = 0; same = 0; diff = []; kinds = {}; gas_only = []
    for p, n, u in A:
        m = B.get(p)
        if m is None: continue
        if (n.get('to') or '').lower() == PM and (m[0].get('to') or '').lower() == PM and (n.get('input') or '').lower() == (m[0].get('input') or '').lower():
            pairs += 1; k = SELS.get((n.get('input') or '')[:10], (n.get('input') or '')[:10]); kinds[k] = kinds.get(k, 0) + 1
            if own(n) == own(m[0]): same += 1
            else: diff.append({'path': p, 'sel': k, 'undone': u, 'rec': str(own(n))[:600], 'rep': str(own(m[0]))[:600]})
        if n.get('gasUsed') != m[0].get('gasUsed') and (n.get('input') or '') == (m[0].get('input') or '') and own(n) == own(m[0]):
            gas_only.append({'path': p, 'to': (n.get('to') or '').lower(), 'sel': (n.get('input') or '')[:10], 'rec': n.get('gasUsed'), 'rep': m[0].get('gasUsed'),
                             'gasRec': n.get('gas'), 'gasRep': m[0].get('gas')})
    return {'tx': h, 'pairs': pairs, 'same': same, 'diff': diff[:10], 'nDiff': len(diff), 'kinds': kinds, 'gasOnly': gas_only[:20], 'nGasOnly': len(gas_only),
            'revertedUnlockThenCompleted': r.get('completedUnlockAfterRevert'), 'identicalEvents': r.get('divergence') is None}


def main():
    d = json.load(open(sys.argv[1])); out = sys.argv[2]; th = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    sel = [r for r in d['results'] if 'diffs' in r and (r['divergence'] or r['gasUsedDiffFrames'])]
    print('re-reading', len(sel), flush=True)
    res = []
    with cf.ThreadPoolExecutor(th) as ex:
        for i, x in enumerate(ex.map(one, sel)):
            res.append(x)
            if i % 200 == 0: print(i, flush=True)
    ok = [x for x in res if 'pairs' in x]
    summ = {'reread': len(sel), 'ok': len(ok), 'errors': len(res) - len(ok), 'pmPairsSameInput': sum(x['pairs'] for x in ok),
            'pmPairsSameOwnResult': sum(x['same'] for x in ok), 'pmPairsDifferent': sum(x['nDiff'] for x in ok),
            'txsWithPmPairDifferent': sum(1 for x in ok if x['nDiff']), 'byKind': {},
            'revertedUnlockThenCompletedTxs': sum(1 for x in ok if x['revertedUnlockThenCompleted']),
            'revertedUnlockThenCompletedTxsAllPmPairsSame': sum(1 for x in ok if x['revertedUnlockThenCompleted'] and x['nDiff'] == 0 and x['pairs']),
            'framesDifferingOnlyInGasUsed': sum(x['nGasOnly'] for x in ok), 'gasOnlyTargets': {}}
    for x in ok:
        for k, v in x['kinds'].items(): summ['byKind'][k] = summ['byKind'].get(k, 0) + v
        for g in x['gasOnly']: summ['gasOnlyTargets'][g['to']] = summ['gasOnlyTargets'].get(g['to'], 0) + 1
    json.dump({'summary': summ, 'results': res}, open(out, 'w'), indent=1); print(json.dumps(summ, indent=1))


main()
