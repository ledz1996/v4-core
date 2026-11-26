# Copied from cycles/023/theme-hyperevm-twin-state.work/scripts/official_read.py, slot file changed to slots2.json
# Phase A: read every derived PoolManager slot, the native balance and balanceOf(PoolManager) of every pooled
# currency from the official endpoint (latest only), bracketing each batch of 18 reads with eth_blockNumber.
import json, sys, time, urllib.request
O = sys.argv[1]; out = sys.argv[2]
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
S = json.load(open('../raw/slots2.json'))
slots = list(S['slots']); curs = [c for c in S['currencies'] if int(c, 16) != 0]
def post(calls):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]).encode()
    req = urllib.request.Request(O, body, {'content-type': 'application/json', 'user-agent': 'review-client/1.0'})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if isinstance(r, dict): raise RuntimeError(json.dumps(r)[:200])
    r = sorted(r, key=lambda x: x['id'])
    if any('error' in x for x in r): raise RuntimeError(json.dumps([x for x in r if 'error' in x][0])[:200])
    return [x['result'] for x in r]
def single(m, p):
    return post([(m, p)])[0]
items = [('slot', s) for s in slots] + [('native', PM)] + [('balanceOf', c) for c in curs]
def call(kind, x):
    if kind == 'slot': return ('eth_getStorageAt', [PM, x, 'latest'])
    if kind == 'native': return ('eth_getBalance', [PM, 'latest'])
    return ('eth_call', [{'to': x, 'data': '0x70a08231' + PM[2:].lower().rjust(64, '0')}, 'latest'])
res = {'endpoint': O, 'clientVersionStart': single('web3_clientVersion', []), 'reads': [], 'refusals': []}
i = 0
while i < len(items):
    ch = items[i:i + 18]
    try:
        r = post([('eth_blockNumber', [])] + [call(k, x) for k, x in ch] + [('eth_blockNumber', [])])
    except Exception as e:
        msg = str(e)[:200]
        if 'execution reverted' in msg or '-32000' in msg or '3,' in msg:
            # a balanceOf that reverts: read this chunk one by one
            for k, x in ch:
                try:
                    rr = post([('eth_blockNumber', []), call(k, x), ('eth_blockNumber', [])])
                    res['reads'].append([k, x, rr[1], int(rr[0], 16), int(rr[2], 16)])
                except Exception as e2:
                    res['reads'].append([k, x, 'ERR ' + str(e2)[:150], None, None])
                time.sleep(0.6)
            i += 18; continue
        res['refusals'].append([i, msg, time.time()]); time.sleep(8); continue
    b0, b1 = int(r[0], 16), int(r[-1], 16)
    for (k, x), v in zip(ch, r[1:-1]): res['reads'].append([k, x, v, b0, b1])
    i += 18
    if (i // 18) % 50 == 0: print(i, b0, b1, len(res['refusals']), flush=True); json.dump(res, open(out, 'w'))
    time.sleep(0.6)
res['clientVersionEnd'] = single('web3_clientVersion', [])
json.dump(res, open(out, 'w'))
print('done', len(res['reads']), len(res['refusals']))
