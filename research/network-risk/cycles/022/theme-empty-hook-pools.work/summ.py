import json, glob
for fn in sorted(glob.glob('raw/detail_*.json')):
    d = json.load(open(fn)); cid = d['chainId']
    for p in d['pools']:
        gated = [f for f in p['flags'] if f in ('beforeRemove', 'afterRemove', 'beforeDonate', 'afterDonate')]
        lv = p['livePositions']
        if not lv and not p['activeLiquidity']: continue
        print(cid, p['poolId'][:12], p['kind'], p['hook'], 'gated', gated, 'L', p['activeLiquidity'], 'live', len(lv), 'third', p['thirdPartyLive'], 'creator', (p['creator'] or '')[:10],
              'c0', p['currency0'][:10], 'c1', p['currency1'][:10])
        for q in lv: print('      ', q['sender'][:10], q['tickLower'], q['tickUpper'], q['liquidity'], 'from', [x[:10] for x in q['addFrom']], 'owner', (q['tokenOwner'] or '')[:12], 'a0 %.3g a1 %.3g' % (q['amount0raw'] or 0, q['amount1raw'] or 0), 'third', q['thirdParty'])
