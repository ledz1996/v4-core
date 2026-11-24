"""Totals per network for the research file, merging the analyze3 runs (later files override earlier ones per
transaction) and the analyze2 runs of part one."""
import json, os
from collections import Counter
A3 = {137: ['an3-137'], 56: ['an3-56', 'an3b-56', 'an3c-56'], 4663: ['an3-4663', 'an3-4663b', 'an3c-4663'],
      99901: ['an3-99901', 'an3b-99901'], 43114: ['an3-43114', 'an3b-43114'], 143: ['an3-143', 'an3b-143'], 4326: ['an3-4326', 'an3b-4326'],
      5042: ['an3-5042', 'an3b-5042', 'an3c-5042']}
A2 = {137: 'an2-137', 56: 'an2-56', 4663: 'an2-4663', 99901: 'an2-99901'}
tot = {}
for cid, fs in A3.items():
    R = {}
    for f in fs:
        p = 'raw/%s.json' % f
        if not os.path.exists(p): continue
        for r in json.load(open(p))['results']: R[r['tx']] = r
    if not R: continue
    C = [r for r in R.values() if 'result' in r]
    nat = [r for r in C if 'native' in r]
    natc = Counter()
    for r in nat:
        leg = r['currencies']['0x' + '0' * 40]; net = int(leg['out']) - int(leg['in'])
        natc['via ' + r['native'].get('via', '?')] += 1
        if not r['native']['otherPmTxInBlock']:
            natc['alone'] += 1; natc['aloneBalanceAgrees' if int(r['native']['balanceDiff']) == -net else 'aloneBalanceDisagrees'] += 1
        if 'systemLogs' in r['native']:
            o, i = map(int, r['native']['systemLogs']); natc['systemLogsAgree' if o - i == int(leg['owed']) else 'systemLogsDisagree'] += 1
    ev = Counter()
    for r in C:
        for k, v in r.get('eventKinds', {}).items(): ev[k] += v
    t = {'txRead': len(R), 'txChecked': len(C), 'result': dict(Counter(r['result'] for r in C)),
         'differs': [{'tx': r['tx'], 'block': r['block'], 'diff': {c: v['diff'] for c, v in r['currencies'].items() if v['diff'] != '0'}} for r in C if r['result'] != 'exact'],
         'events': dict(ev), 'removalEvents': sum(r['removals'] for r in C), 'collectEvents': sum(r['collects'] for r in C),
         'txWithSwap': sum(1 for r in C if r['swaps']), 'swapsReplayed': sum(r['swaps'] for r in C), 'ticksCrossed': sum(r['crossed'] for r in C),
         'feeEventsAfterSwapInTx': sum(r['feesAfterSwap'] for r in C), 'txWithOtherTxOnPool': sum(1 for r in C if r['otherTxEventsOnPools']),
         'txWithReturnDeltaHook': sum(1 for r in C if r.get('returnDeltaHooks')), 'txInitializingPool': sum(1 for r in C if r.get('initializedInBlock')),
         'flips': sum(r['flips'] for r in C), 'storageWordsCompared': sum(sum(r['storageCompared'].values()) for r in C),
         'bitmapWordsCompared': sum(r['storageCompared'].get('words', 0) for r in C),
         'storageMismatch': [{'tx': r['tx'], 'what': r['storageMismatch']} for r in C if r['storageMismatch']],
         'legsPaid': sum(1 for r in C for v in r['currencies'].values() if int(v['out']) > 0),
         'nativeLegs': len(nat), 'native': dict(natc), 'aside': dict(Counter(r['aside'] for r in R.values() if r.get('aside'))),
         'errors': sum(1 for r in R.values() if 'error' in r), 'blocks': [min(r['block'] for r in R.values()), max(r['block'] for r in R.values())]}
    if cid in A2 and os.path.exists('raw/%s.json' % A2[cid]):
        R2 = json.load(open('raw/%s.json' % A2[cid]))['results']; C2 = [r for r in R2 if 'result' in r]
        t['analyze2'] = {'txRead': len(R2), 'txChecked': len(C2), 'result': dict(Counter(r['kind'] + ' ' + r['result'] for r in C2)),
                         'storageMismatch': sum(1 for r in C2 if r['storageMismatch']), 'aside': dict(Counter(r['aside'] for r in R2 if r.get('aside')))}
    tot[cid] = t; print(cid, json.dumps({k: v for k, v in t.items() if k not in ('differs',)}))
    for d in t['differs']: print('   differs', d)
json.dump(tot, open('totals.json', 'w'), indent=1)
