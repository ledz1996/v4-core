# Which Klik pools cannot swap today because the hook's pending fee entry exceeds the claims it holds? Uses the deployed V4 Quoter with eth_call. Read-only.
import sys, json
from lib import *
from summ import load
from probe import ecall, key, w, a, EOA, dec_err
from keccak import keccak256
QSEL = keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))').hex()[:8]
def quote(u, quoter, k, zfo, amt):
    data = '0x' + QSEL + w(32) + k + w(1 if zfo else 0) + w(amt) + w(0x100) + w(0)
    return ecall(u, {'from': EOA, 'to': quoter, 'data': data})
DEP = {1: ['0x1d06faa7ff674ccfd8a5736c0c0973cb0a8fa0cc', '0x6d01769ab90674d0d56b155f57003284e1b460cc', '0xcba49142a75da64a679f32a159f4316f11a7e0cc'], 130: ['0x9463925bdeee2be5eade2a60857442b4a15ca0cc'], 4663: ['0x41b82571eaaed65f18ad3428f066cd23b9b3a0cc'], 143: ['0xdd1e195f536e5375ada2eeb179270ac23af8e0cc'], 4217: ['0x50995539e4afaca479bb59b0d795d94e0efea0cc']}
out = []
for cid, hooks in DEP.items():
    n = net(cid); pm = n['poolManager']; u = n['rpc']; quoter = n['contracts'].get('Quoter')
    for hook in hooks:
        rows = [r for r in load(cid) if r[6] == hook]
        claims = {}; res = []
        for r in rows:
            for t, q in ((r[2], r[3]), (r[3], r[2])):
                ok, v, _ = ecall(u, {'to': hook, 'data': sel('pendingClaims(address)') + adr(t)})
                p = int(v, 16) if ok and v != '0x' else 0
                if p == 0: continue
                if q not in claims: claims[q] = int(call(u, pm, 'balanceOf(address,uint256)', adr(hook) + adr(q)), 16)
                k = key(r[2], r[3], r[4], r[5], hook)
                # buy the token with a dust amount of the quote currency
                zfo = (q == r[2])
                ok2, qr, _ = quote(u, quoter, k, zfo, 1000) if quoter else (None, 'no quoter', None)
                res.append(dict(pool=r[1], token=t, quote=q, pending=str(p), hookClaims=str(claims[q]), short=p > claims[q], quoterOk=ok2, quoter=qr[:160]))
        short = [x for x in res if x['short']]; fail = [x for x in res if x['quoterOk'] is False]
        print('\n#### %d %s pools with pending %d; pending > hook claims: %d; quoter reverts: %d; quoter ok: %d' % (cid, hook, len(res), len(short), len(fail), sum(1 for x in res if x['quoterOk'])))
        import collections
        print('   quoter results for short pools:', collections.Counter(x['quoter'][:70] for x in short).most_common(4))
        print('   quoter results for other pools:', collections.Counter(x['quoter'][:70] if not x['quoterOk'] else 'ok' for x in res if not x['short']).most_common(4))
        for x in short[:6]: print('   short', x['pool'][:14], 'token', x['token'], 'quote', x['quote'], 'pending', x['pending'], 'claims', x['hookClaims'], '->', x['quoter'][:90])
        out.append(dict(chainId=cid, hook=hook, block=int(rpc(u, 'eth_blockNumber', []), 16), pools=res))
json.dump(out, open('raw/klik_frozen.json', 'w'), indent=1)
