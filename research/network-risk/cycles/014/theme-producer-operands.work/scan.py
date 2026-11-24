"""Scan PoolManager logs for the operand classes with no mined replay yet. Read only, no RPC.
Usage: scan.py <chainId> <out.json> <logfile...>  (collect.py .json or pcollect.py .jsonl)"""
import sys, json, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/013/theme-mined-branches.work')
from common import EV, s256
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as V
cid, out = int(sys.argv[1]), sys.argv[2]
logs = []
for p in sys.argv[3:]:
    if p.endswith('.jsonl'):
        for line in open(p): logs += json.loads(line).get('logs', [])
    else: logs += json.load(open(p))['logs']
seen = set(); L = []
for l in logs:
    k = (l['tx'], l['li'])
    if k not in seen: seen.add(k); L.append(l)
L.sort(key=lambda l: (l['b'], l['li']))
c = collections.Counter(); tx = collections.defaultdict(set); spacing = {}
def w(d, i): return int(d[2 + 64 * i:2 + 64 * (i + 1)], 16)
for l in L:
    k = EV.get(l['topics'][0], 'other'); c['log:' + k] += 1
    if k == 'Initialize':
        spacing[l['topics'][1]] = s256(w(l['data'], 1))
    if k in ('Donate', 'Approval', 'OperatorSet', 'ProtocolFeeUpdated'): tx[k].add(l['tx'])
    if k == 'Transfer6909':
        caller = w(l['data'], 0); frm = int(l['topics'][1], 16); to = int(l['topics'][2], 16)
        if frm == 0: f = 'mint'
        elif to == 0: f = 'burn:self' if caller == frm else 'burn:bySpender'
        else: f = 'transfer:self' if caller == frm else 'transferFrom:bySpender'
        c['6909:' + f] += 1; tx['6909:' + f].add(l['tx'])
    if k == 'Swap':
        d = l['data']; a0, a1, p, liq, tick = s256(w(d, 0)), s256(w(d, 1)), w(d, 2), w(d, 3), s256(w(d, 4))
        for t in (tick, tick + 1):
            if -887272 <= t <= 887272 and V.get_sqrt_price_at_tick(t) == p:
                sp = spacing.get(l['topics'][1])
                if sp is None or t % sp == 0:
                    c['swap:endsOnSpacingBoundary'] += 1; tx['swap:endsOnSpacingBoundary'].add(l['tx'])
        # SqrtPriceMath overflow fallback needs amount * sqrtPrice >= 2^256 for the input side of currency0
        for a in (abs(a0), abs(a1)):
            if a and (a * p) >> 256: c['swap:amountTimesPriceOver256'] += 1; tx['swap:amountTimesPriceOver256'].add(l['tx'])
        if max(abs(a0), abs(a1)) >> 160: c['swap:amountOver2^160'] += 1; tx['swap:amountOver2^160'].add(l['tx'])
res = {'chainId': cid, 'blocks': [L[0]['b'], L[-1]['b']] if L else None, 'counts': c, 'txCounts': {k: len(v) for k, v in tx.items()},
       'txs': {k: sorted(v) for k, v in tx.items()}, 'pools': len(spacing)}
json.dump(res, open(out, 'w'), indent=1)
print(cid, res['blocks'], dict(c), {k: len(v) for k, v in tx.items()})
