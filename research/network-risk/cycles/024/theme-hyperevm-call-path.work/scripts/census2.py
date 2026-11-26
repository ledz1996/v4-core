# Task 3 (L-1017) census extension: every block in a contiguous range after the cycle 23 census, read in full
# from a nanoreth replica (which lists HyperCore system transactions with gas price 0), grouped by sender and target.
# Flags any gas price 0 transaction whose target is the PoolManager or whose input carries the PoolManager address,
# and any transaction from the PoolManager. No sampling seed: the range is contiguous.
# usage: census2.py <replica> <from> <to> <out.json>
import json, sys, time, collections
from rpc import rpc, batch
R, A, B, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
PM = '12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
res = {'replica': R, 'from': A, 'to': B, 'cvStart': rpc(R, 'web3_clientVersion', []), 'blocks': 0, 'txs': 0, 'zero': 0,
       'bySender': collections.Counter(), 'byTarget': collections.Counter(), 'flag': [], 'zeroNotLeading': [], 'errors': [], 'minBaseFee': None}
b = A
while b <= B:
    ch = list(range(b, min(b + 10, B + 1)))
    try:
        rb = batch(R, [('eth_getBlockByNumber', [hex(x), True]) for x in ch], timeout=120)
    except Exception as e:
        res['errors'].append([b, str(e)[:150]]); time.sleep(6); continue
    if any(not isinstance(r, dict) or 'transactions' not in r for r in rb):
        res['errors'].append([b, 'bad block ' + str([r for r in rb if not isinstance(r, dict) or 'transactions' not in r][0])[:120]]); time.sleep(6); continue
    for r in rb:
        res['blocks'] += 1; txs = r['transactions']; res['txs'] += len(txs)
        bf = int(r.get('baseFeePerGas') or '0x0', 16)
        if res['minBaseFee'] is None or bf < res['minBaseFee']: res['minBaseFee'] = bf
        zi = []
        for t in txs:
            if PM in t['from'].lower(): res['flag'].append(['fromPM', t['hash']])
            gp = t.get('gasPrice')
            if gp is not None and int(gp, 16) == 0:
                res['zero'] += 1; zi.append(int(t['transactionIndex'], 16))
                res['bySender'][t['from'].lower()] += 1; res['byTarget'][(t.get('to') or 'create').lower() + ' ' + t['input'][:10]] += 1
                if PM in (t.get('to') or '').lower() or PM in t['input'].lower(): res['flag'].append(['zeroTouchesPM', t['hash']])
        if zi != list(range(len(zi))): res['zeroNotLeading'].append(int(r['number'], 16))
    b += 10
    if res['blocks'] % 1000 == 0:
        print(b, res['blocks'], res['zero'], len(res['flag']), flush=True); json.dump(res, open(out, 'w'))
    time.sleep(0.3)
res['cvEnd'] = rpc(R, 'web3_clientVersion', [])
json.dump(res, open(out, 'w'), indent=0)
print('done', res['blocks'], res['txs'], res['zero'], len(res['flag']), len(res['zeroNotLeading']), res['minBaseFee'])
