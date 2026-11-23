# Step 1 and the first half of step 2: the priced tokens worth more than 1,000 USD at the PoolManager today, their code,
# the contracts that balanceOf(PoolManager) touches (eth_createAccessList) and the selectors of all of them.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from base import *
from value import values
from tokcode import parse
SLOTS = ['0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', '0xa3f0ad74e5423aebfd80e3ef4346578335a9a72aeaee59ff6cb3582b35133d50',
         '0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3', '0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7']
def prices(cid):
    """token -> (price, decimals, symbol) from the cycle 5 price file or from this cycle's files for the three unpriced networks."""
    out = {}
    fn = os.path.join(RAW5, 'prices_%d.json.gz' % cid)
    if os.path.exists(fn):
        for t, p in jz(fn).items(): out[t] = p
    for f in ('prices3_%d.json.gz', 'pricesall_%d.json.gz'):
        fn = os.path.join(RAW6, f % cid)
        if os.path.exists(fn):
            d = jz(fn)
            for t, p in (d.get('llama') or d.get('prices') or {}).items(): out.setdefault(t, p)
    return out
# senders with a native balance where the node checks funds; extra endpoints where the listed ones lack the method
ACLFROM = {43114: '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7'}
ACLURL = {480: ['https://480.rpc.thirdweb.com'], 43114: ['https://avalanche-c-chain-rpc.publicnode.com', 'https://avalanche.drpc.org']}
def usdv(b, p):
    try: return b / 10 ** p['decimals'] * p['price']
    except OverflowError: return 1e30
def rr(cid, method, params, rot=0, tries=6):
    us = urls2(cid); last = None
    for k in range(tries):
        try: return rpc(us[(rot + k) % len(us)], method, params, timeout=60, tries=1)
        except Exception as e: last = str(e)[:200]; time.sleep(0.4 * (k + 1))
    return {'error': last}
def run(cid, minusd=1000.0, workers=6):
    pm = net(cid)['poolManager'].lower()
    pr = prices(cid)
    d, rows = universe(cid)
    cand = [r['token'] for r in rows if r['token'] in pr and pr[r['token']].get('price') is not None and pr[r['token']].get('decimals') is not None and r['token'] != '0x' + '0' * 40
            and usdv(int(r.get("bal2") or 0), pr[r["token"]]) > minusd * 0.5]
    # live balance
    bal = {}
    def jb(t):
        r = ecall(cid, t, sel('balanceOf(address)') + adr(pm), rot=hash(t) % 5)
        return t, int(r[2:66], 16) if isinstance(r, str) and len(r) >= 66 else None
    with ThreadPoolExecutor(workers) as ex:
        for t, b in ex.map(jb, cand): bal[t] = b
    targets = []
    for t in cand:
        if bal[t] is None: continue
        usd = usdv(bal[t], pr[t])
        if usd > minusd: targets.append((usd, t))
    targets.sort(reverse=True)
    print(cid, net(cid)['name'], 'candidates', len(cand), 'targets', len(targets), flush=True)
    out = {}
    def job(x):
        usd, t = x; rot = hash(t) % 5
        o = dict(usd=usd, sym=pr[t].get('symbol'), bal=str(bal[t]), dec=pr[t]['decimals'], conf=pr[t].get('confidence'))
        c = rr(cid, 'eth_getCode', [t, 'latest'], rot)
        if not isinstance(c, str): o['err'] = 'code ' + str(c)[:100]; return t, o
        p = parse(c); o['size'] = p['size']; o['sels'] = p['sels']; o['deleg'] = p['deleg']
        impl = set()
        for s in SLOTS:
            v = rr(cid, 'eth_getStorageAt', [t, s, 'latest'], rot)
            if isinstance(v, str) and int(v, 16) and int(v, 16) < 2 ** 160: impl.add('0x%040x' % int(v, 16))
        for e in p.get('emb') or []:
            if int(e, 16) > 2 ** 24 and e != '0x' + 'f' * 40: impl.add(e.lower())
        acl = rr(cid, 'eth_createAccessList', [{'from': ACLFROM.get(cid, A), 'to': t, 'data': sel('balanceOf(address)') + adr(pm)}, 'latest'], rot, tries=3)
        if not (isinstance(acl, dict) and 'accessList' in acl):
            for u in ACLURL.get(cid, []):
                try: acl = rpc(u, 'eth_createAccessList', [{'from': ACLFROM.get(cid, A), 'to': t, 'data': sel('balanceOf(address)') + adr(pm)}, 'latest'], timeout=40, tries=3); break
                except Exception as e: acl = {'error': str(e)[:150]}
        rel = {}
        if isinstance(acl, dict) and 'accessList' in acl:
            o['acl'] = True
            for e in acl['accessList']:
                a = e['address'].lower()
                if a != t and int(a, 16) > 0xffff: rel[a] = 'acl'
        else: o['acl'] = False; o['aclErr'] = str(acl)[:120]
        for a in impl: rel[a] = 'impl'
        # beacon -> implementation()
        for a in list(rel):
            r = ecall(cid, a, '0x5c60da1b', rot=rot, tries=2)
            if isinstance(r, str) and len(r) == 66 and 2 ** 24 < int(r, 16) < 2 ** 160:
                b = '0x%040x' % int(r, 16)
                if b != t and b not in rel: rel[b] = 'impl'
        o['rel'] = {}
        for a, k in rel.items():
            c2 = rr(cid, 'eth_getCode', [a, 'latest'], rot)
            if isinstance(c2, str) and len(c2) > 2:
                p2 = parse(c2); o['rel'][a] = dict(kind=k, size=p2['size'], sels=p2['sels'])
                # one more hop for proxies among the related contracts
                for s in SLOTS[:1]:
                    v = rr(cid, 'eth_getStorageAt', [a, s, 'latest'], rot)
                    if isinstance(v, str) and int(v, 16) and int(v, 16) < 2 ** 160:
                        a3 = '0x%040x' % int(v, 16)
                        if a3 not in rel and a3 not in o['rel']:
                            c3 = rr(cid, 'eth_getCode', [a3, 'latest'], rot)
                            if isinstance(c3, str) and len(c3) > 2: o['rel'][a3] = dict(kind='impl-of:' + a, size=len(c3) // 2 - 1, sels=parse(c3)['sels'])
        return t, o
    with ThreadPoolExecutor(workers) as ex:
        for n, (t, o) in enumerate(ex.map(job, targets)):
            out[t] = o
            if n % 100 == 99: print(cid, n + 1, flush=True)
    json.dump(out, gzip.open(os.path.join(RAW6, 'discover_%d.json.gz' % cid), 'wt'))
    print(cid, net(cid)['name'], 'tokens', len(out), 'acl ok', sum(1 for o in out.values() if o.get('acl')), 'with related', sum(1 for o in out.values() if o.get('rel')),
          'errs', sum(1 for o in out.values() if 'err' in o), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
