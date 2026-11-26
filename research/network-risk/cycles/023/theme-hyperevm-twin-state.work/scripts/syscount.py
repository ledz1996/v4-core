# For blocks where the replica shows gas price 0 txs, compare their count, senders and targets with the official
# endpoint's eth_getSystemTxsByBlockNumber. Sample: first 150 such blocks of the census, sorted by number.
import json, sys, time
from rpc import rpc, batch
O = 'https://rpc.hyperliquid.xyz/evm'
c = json.load(open('../raw/census.json'))
bl = sorted([int(b) for b, e in c['blocks'].items() if e.get('zero')])[:150]
res = {'clientVersionStart': rpc(O, 'web3_clientVersion', []), 'blocks': len(bl), 'equal': 0, 'diff': []}
for i in range(0, len(bl), 10):
    ch = bl[i:i + 10]
    for k in range(5):
        try: r = batch(O, [('eth_getSystemTxsByBlockNumber', [hex(b)]) for b in ch]); break
        except Exception as e: time.sleep(8); r = None
    for b, s in zip(ch, r or [None] * len(ch)):
        rep = [(z[1].lower(), (z[2] or '').lower(), z[3]) for z in c['blocks'][str(b)]['zero']]
        off = [(t['from'].lower(), (t.get('to') or '').lower(), t['input'][:10]) for t in s] if isinstance(s, list) else None
        if off == rep: res['equal'] += 1
        else: res['diff'].append([b, rep, off])
    time.sleep(1)
res['clientVersionEnd'] = rpc(O, 'web3_clientVersion', [])
json.dump(res, open('../raw/syscount.json', 'w'), indent=0)
print(res['blocks'], res['equal'], len(res['diff']), res['diff'][:2])
