# For each deployment of the Klik fee hook: is the pending fee ledger of a token applied to a pool that pairs the token with a foreign currency?
# Read-only: eth_call, debug_traceCall where the endpoint offers it.
import sys, json
from lib import *
from config import CFG
from summ import census, load
from probe import ecall, key, w, a, SEL, cd, EOA, MINP, MAXP
from trace import trace, show
from sim import pool_id
DEP = {1: ['0xcba49142a75da64a679f32a159f4316f11a7e0cc', '0x1d06faa7ff674ccfd8a5736c0c0973cb0a8fa0cc', '0x6d01769ab90674d0d56b155f57003284e1b460cc'], 130: ['0x9463925bdeee2be5eade2a60857442b4a15ca0cc'], 57073: ['0x71b7a448b96a01de73b0caf1267d33558d2620cc'], 42161: ['0x71b7a448b96a01de73b0caf1267d33558d2620cc'],
       4663: ['0x41b82571eaaed65f18ad3428f066cd23b9b3a0cc'], 43114: ['0xb2c964edbac922f006a09bd293b6c42ee147e0cc'], 143: ['0xdd1e195f536e5375ada2eeb179270ac23af8e0cc'], 4217: ['0x50995539e4afaca479bb59b0d795d94e0efea0cc'], 8453: ['0x5b0a864213d49f23ed2a6635cc42b3b4fe7720cc', '0x64746dca345c5652bc251597bd99562216a7a0cc', '0xf85f1f3082cfbc5e1149972309b25054e4d420cc']}
TR = {1: 'https://eth.drpc.org', 130: 'https://unichain.drpc.org', 4663: 'https://robinhood.drpc.org', 43114: 'https://avalanche.drpc.org', 143: 'https://rpc.monad.xyz', 4217: 'https://rpc.mainnet.tempo.xyz', 8453: 'https://base.drpc.org', 42161: 'https://arbitrum.drpc.org', 57073: 'https://ink.drpc.org'}
FQ = '0x1111111111111111111111111111111111111112'
def sv(x):
    try:
        b = bytes.fromhex(x[2:]); l = int.from_bytes(b[32:64], 'big'); return b[64:64 + l].decode('utf8', 'replace')
    except Exception: return None
def swapcd(name, k, zfo):
    d = cd(name, EOA, k)
    if not zfo: d = d.replace(w(1) + w(-10 ** 18) + w(MINP), w(0) + w(-10 ** 18) + w(MAXP))
    return d
res = []
for cid, hooks in DEP.items():
    if len(sys.argv) > 1 and str(cid) not in sys.argv[1:]: continue
    n = net(cid); pm = n['poolManager']; u = n['rpc']
    for hook in hooks:
        rows = [r for r in load(cid) if r[6] == hook]
        ver = sv(ecall(u, {'to': hook, 'data': sel('VERSION()')})[1]); fac = '0x' + ecall(u, {'to': hook, 'data': sel('factory()')})[1][-40:]
        pend = {}; quote = {}
        for r in rows:
            for t, q in ((r[2], r[3]), (r[3], r[2])):
                if t in pend: continue
                ok, v, _ = ecall(u, {'to': hook, 'data': sel('pendingClaims(address)') + adr(t)})
                pend[t] = int(v, 16) if ok and v != '0x' else 0; quote[t] = q
        nz = sorted([(v, t) for t, v in pend.items() if v > 0], reverse=True)
        e = dict(chainId=cid, hook=hook, version=ver, factory=fac, pools=census(cid)[0].get(hook, 0), tokensWithPending=len(nz), block=int(rpc(u, 'eth_blockNumber', []), 16))
        print('\n#### %d %s %s pools %d factory %s tokens with pending %d' % (cid, hook, ver, e['pools'], fac, len(nz)))
        # claims the hook holds per quote currency
        qs = {}
        for v, t in nz: qs.setdefault(quote[t], 0); qs[quote[t]] += v
        e['pendingByQuote'] = {}
        for q, tot in qs.items():
            cl = int(call(u, pm, 'balanceOf(address,uint256)', adr(hook) + adr(q)), 16)
            e['pendingByQuote'][q] = dict(sumPending=str(tot), hookClaims=str(cl)); print('   quote', q, 'sum pending', tot, 'hook claims at PoolManager', cl)
        if not nz:
            res.append(e); continue
        v, t = nz[0]; r = [x for x in rows if t in (x[2], x[3])][-1]
        c0, c1 = (FQ, t) if int(FQ, 16) < int(t, 16) else (t, FQ)
        k = key(c0, c1, r[4], r[5], hook); sellZfo = (c0 == t)
        ok, out, _ = ecall(u, {'from': EOA, 'to': pm, 'data': '0x' + SEL['initialize'] + k + w(1 << 96)})
        e['token'] = t; e['pending'] = str(v); e['realQuote'] = quote[t]; e['initForeignQuote'] = (ok, out[:80])
        print('   token', t, 'pending', v, 'real quote', quote[t], '| initialize (foreign quote, token) by an ordinary account ->', ok, out[:80])
        for nme in ('beforeSwap',):
            for lab, zfo in (('sell', sellZfo), ('buy', not sellZfo)):
                ok, out, _ = ecall(u, {'from': pm, 'to': hook, 'data': '0x' + swapcd(nme, k, zfo)})
                e['call_%s_%s' % (nme, lab)] = out[:60]; print('   eth_call %s %s on foreign key ->' % (nme, lab), out[:80])
                try:
                    tr = trace(TR[cid], {'from': pm, 'to': hook, 'data': '0x' + swapcd(nme, k, zfo)})
                    pmcalls = []
                    def walk(c):
                        for x in c.get('calls', []) or []:
                            if x.get('to', '').lower() == pm.lower() and x.get('type') == 'CALL':
                                i = x['input']; pmcalls.append((i[:10], i[10:]))
                            walk(x)
                    walk(tr)
                    for s_, args in pmcalls:
                        nm = {'0xf5298aca': 'burn', '0x156e29f6': 'mint', '0x0b0d9c09': 'take'}.get(s_, s_)
                        words = [args[i:i + 64] for i in range(0, len(args), 64)]
                        print('      trace: hook calls PoolManager.%s(%s)' % (nm, ', '.join(x.lstrip('0')[:40] or '0' for x in words[:3])))
                        e.setdefault('trace_%s_%s' % (nme, lab), []).append((nm, words[:3]))
                except Exception as ex: print('      trace unavailable:', repr(ex)[:100])
        res.append(e)
json.dump(res, open('raw/klik_test%s.json' % ('_' + '_'.join(sys.argv[1:]) if len(sys.argv) > 1 else ''), 'w'), indent=1)
