# For Klik tokens on Ethereum whose pending fee entry exceeds the hook's claims in some pool: list every pool of the token on the hook,
# who initialized it and how much liquidity it has. Read-only.
import json
from lib import *
from probe import ecall
from summ import load
d = json.load(open('raw/klik_frozen.json'))
n = net(1); u = n['rpc']; sv = n['contracts']['StateView']; out = []
for e in d:
    if e['chainId'] != 1: continue
    fac = '0x' + ecall(u, {'to': e['hook'], 'data': sel('factory()')})[1][-40:]
    toks = {}
    for p in e['pools']: toks.setdefault(p['token'], []).append(p)
    for t, ps in toks.items():
        if not any(p['short'] for p in ps): continue
        for r in [r for r in load(1) if r[6] == e['hook'] and t in (r[2], r[3])]:
            tx = rpc(u, 'eth_getTransactionByHash', [r[7]])
            liq = int(call(u, sv, 'getLiquidity(bytes32)', r[1][2:]), 16)
            p = [x for x in ps if x['pool'] == r[1]]
            q = r[3] if r[2] == t else r[2]
            rec = dict(hook=e['hook'], token=t, pool=r[1], quote=q, block=r[0], initFrom=tx['from'], initTo=tx['to'], initSel=tx['input'][:10], liquidity=str(liq), short=p[0]['short'] if p else None, quoter=((p[0]['quoter'] or '')[:40] if p else None), factory=fac)
            out.append(rec)
            print(e['hook'][:8], 'token', t[:10], 'pool', r[1][:10], 'quote', q[:10], 'blk', r[0], 'init from', tx['from'][:10], 'to', tx['to'][:10], tx['input'][:10], 'liq', liq, 'short', rec['short'], flush=True)
json.dump(out, open('raw/klik_frozen_pools.json', 'w'), indent=1)
