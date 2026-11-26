"""Summarises scan-<cid>.jsonl: counts of (a), (b), extra checks, task (c), receipt agreement, and a native balance
reconciliation of the PoolManager over the covered block range (eth_getBalance at both ends, read-only).
Usage: analyse.py <cid> <url>   (writes raw/summary-<cid>.json)"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from rpcu import call
cid, url = sys.argv[1], sys.argv[2]
W = os.path.join(os.path.dirname(__file__), '..', 'raw')
L = json.load(open(os.path.join(W, 'list-%s.json' % cid)))
R = [json.loads(l) for l in open(os.path.join(W, 'scan-%s.jsonl' % cid))]
meta = [r for r in R if r.get('meta')]
tx = {}
for r in R:
    if 'tx' in r and 'fail' not in r: tx[r['tx']] = r
fails = [r for r in R if 'fail' in r]
failed_ids = {r.get('tx') or r.get('block') for r in fails}
fails = [r for r in fails if not ((r.get('tx') and r['tx'] in tx) or (r.get('block') and any(t['block'] == r['block'] for t in tx.values())))]
blocks = {r['block']: r['nTx'] for r in R if r.get('blockDone')}
T = list(tx.values())
cand = {l['tx'] for l in L['logs'].values()}
S = {'chainId': int(cid), 'listRange': [L.get('coveredLo'), L['hi']], 'candidates': len(cand), 'candidateBlocks': len({l['block'] for l in L['logs'].values()}),
     'tracedTx': len(T), 'tracedCandidates': sum(1 for t in T if t['tx'] in cand), 'tracedNonCandidateWithPMFrame': sum(1 for t in T if t['tx'] not in cand),
     'blocksTraced': len(blocks), 'txInTracedBlocks': sum(blocks.values()), 'unresolvedFailures': len(fails), 'failSamples': fails[:5],
     'pmFrames': sum(t['nPM'] for t in T), 'deltaFrames': sum(t['nDelta'] for t in T), 'unlockFrames': sum(t['nUnlock'] for t in T),
     'A': [[t['tx'], t['A']] for t in T if t['A']], 'B': [[t['tx'], t['B']] for t in T if t['B']],
     'X1_alreadyUnlockedAtTop': [t['tx'] for t in T if t['X1']], 'X2_lockedInsideUnlock': [t['tx'] for t in T if t['X2']],
     'settleChecks': sum(t['settleChecks'] for t in T), 'settleMismatch': [[t['tx'], t['bad']] for t in T if t['bad']],
     'txWithFailedUnlock': sum(1 for t in T if t['failedUnlock']), 'txWithFailedThenCompletedUnlock': sum(1 for t in T if t['laterOkUnlock']),
     'traceVsReceiptStatusMismatch': [t['tx'] for t in T if t['status'] is not None and (t['status'] == 1) != t['ok']],
     'logsMismatch': [t['tx'] for t in T if t['logsEq'] is False], 'logsCompared': sum(1 for t in T if t['logsEq'] is not None),
     'successfulTx': sum(1 for t in T if t['ok']), 'meta': meta}
# task (c)
ends = [t for t in T if t['ok'] and t['endSynced']]
byblock = collections.defaultdict(list)
for t in T: byblock[t['block']].append(t)
cres = []
for e in ends:
    nxt = sorted([t for t in byblock[e['block']] if t['idx'] > e['idx'] and t['nPM']], key=lambda x: x['idx'])
    cres.append({'tx': e['tx'], 'synced': e['endSynced'], 'next': nxt[0]['tx'] if nxt else None,
                 'nextBad': nxt[0]['bad'] if nxt else None, 'nextSettles': nxt[0]['settleChecks'] if nxt else None})
S['c_endSynced'] = cres
# native reconciliation over traced blocks only when the whole range was traced block by block is not possible;
# report PoolManager balance change over the list range against the traced native in/out.
lo, hi = L.get('coveredLo'), L['hi']
if lo is not None:
    b0, e0 = call(url, 'eth_getBalance', [L['pm'], hex(lo - 1)]); b1, e1 = call(url, 'eth_getBalance', [L['pm'], hex(hi)])
    net = sum(t['natIn'] - t['natOut'] for t in T if t['ok'] and lo <= t['block'] <= hi)
    S['native'] = {'balanceAtLoMinus1': b0 if e0 is None else e0, 'balanceAtHi': b1 if e1 is None else e1, 'tracedNet': net,
                   'tracedOut': sum(t['natOut'] for t in T if t['ok']), 'tracedIn': sum(t['natIn'] for t in T if t['ok'])}
    if e0 is None and e1 is None:
        S['native']['untracedDelta'] = int(b1, 16) - int(b0, 16) - net
    S['native']['clientVersion'] = call(url, 'web3_clientVersion', [])
json.dump(S, open(os.path.join(W, 'summary-%s.json' % cid), 'w'), indent=1)
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 6 else len(v)) for k, v in S.items() if k not in ('meta', 'failSamples')}, indent=0))
