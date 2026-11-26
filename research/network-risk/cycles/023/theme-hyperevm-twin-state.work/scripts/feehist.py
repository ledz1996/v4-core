# Full-history base fee scan via eth_feeHistory (1024 blocks per call, batched 16 per request).
# usage: python3 feehist.py <url> <from> <to> <out.json>
import sys, json, time
from rpc import rpc, batch
url, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
res = {'url': url, 'clientVersionStart': rpc(url, 'web3_clientVersion', []), 'from': a, 'to': b,
       'minBaseFee': None, 'minAt': None, 'zeroBaseFeeBlocks': [], 'belowFloorBlocks': [], 'covered': 0, 'errors': []}
starts = list(range(a, b + 1, 1024))
i = 0
while i < len(starts):
    chunk = starts[i:i + 16]
    calls = [('eth_feeHistory', [hex(min(1024, b - s + 1)), hex(min(s + 1023, b)), []]) for s in chunk]
    try:
        rs = batch(url, calls, timeout=120)
    except Exception as e:
        res['errors'].append([chunk[0], str(e)[:200]]); time.sleep(10); continue
    bad = False
    for s, r in zip(chunk, rs):
        if not isinstance(r, dict) or 'baseFeePerGas' not in r:
            res['errors'].append([s, str(r)[:200]]); bad = True; break
        o = int(r['oldestBlock'], 16)
        fees = [int(x, 16) for x in r['baseFeePerGas'][:-1]]
        for k, f in enumerate(fees):
            if res['minBaseFee'] is None or f < res['minBaseFee']: res['minBaseFee'], res['minAt'] = f, o + k
            if f == 0: res['zeroBaseFeeBlocks'].append(o + k)
            if f < 100_000_000: res['belowFloorBlocks'].append(o + k)
        res['covered'] += len(fees)
    if bad: time.sleep(5); continue
    i += 16
    if i % 160 == 0:
        print(chunk[0], res['covered'], res['minBaseFee'], res['minAt'], len(res['zeroBaseFeeBlocks']), flush=True)
        json.dump(res, open(out, 'w'))
res['clientVersionEnd'] = rpc(url, 'web3_clientVersion', [])
json.dump(res, open(out, 'w'))
print('done', res['covered'], res['minBaseFee'], res['minAt'], len(res['zeroBaseFeeBlocks']), len(res['belowFloorBlocks']))
