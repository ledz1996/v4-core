# Currency universe per network: Initialize logs of the PoolManager (currency0, currency1 are topics 2 and 3)
# and, where a Blockscout explorer answers, the ERC-20 holdings page of the PoolManager.
import sys, json, os, requests, concurrent.futures as cf
from lib import *
from config import CFG
from fetch import getlogs_range
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
def deploy_block(url, pm, head):
    lo, hi = 0, head
    try:
        if rpc(url, 'eth_getCode', [pm, hex(1)]) not in ('0x', '0x0'): return 0
        while lo + 1 < hi:
            m = (lo + hi) // 2
            if rpc(url, 'eth_getCode', [pm, hex(m)]) in ('0x', '0x0'): lo = m
            else: hi = m
        return hi
    except Exception as e:
        print('deploy search failed', url, str(e)[:100]); return 0
def scout_tokens(base, pm, maxpages=40):
    out = []; params = None
    for p in range(maxpages):
        for attempt in range(4):
            try:
                r = requests.get(base + '/api/v2/addresses/' + pm + '/tokens', params=dict(type='ERC-20', **(params or {})), timeout=30, headers={'user-agent': 'curl/8'})
                j = r.json(); break
            except Exception as e:
                j = None; time.sleep(2)
        if not j: break
        for i in j.get('items', []):
            t = i['token']
            out.append(dict(address=(t.get('address_hash') or t.get('address')).lower(), symbol=t.get('symbol'), decimals=t.get('decimals'), rate=t.get('exchange_rate'), value=i.get('value')))
        params = j.get('next_page_params')
        if not params: break
    return out
def run(cid):
    n = net(cid); c = CFG[cid]; pm = n['poolManager']; fn = 'raw/currencies_%d.json' % cid
    if os.path.exists(fn) or os.path.exists(fn + '.gz'): return cid, 'cached'
    o = {'chainId': cid, 'poolManager': pm, 'currencies': {}, 'nInit': 0}
    if c.get('scout'):
        try: o['scout'] = scout_tokens(c['scout'], pm); o['scoutUrl'] = c['scout'] + '/api/v2/addresses/' + pm + '/tokens?type=ERC-20'
        except Exception as e: o['scoutErr'] = str(e)[:200]
    if c['init']:
        u = c['init']; head = int(rpc(u, 'eth_blockNumber', []), 16)
        dep = deploy_block(c['state'][-1] if cid != 42161 else c['state'][0], pm, head) if cid not in (4663,) else 0
        o.update(initUrl=u, deployBlock=dep, toBlock=head)
        cur = o['currencies']
        def on(logs):
            for l in logs:
                if len(l['topics']) == 4:
                    for t in l['topics'][2:4]:
                        a = '0x' + t[-40:]; cur[a] = cur.get(a, 0) + 1
                    o['nInit'] += 1
        st = getlogs_range(u, {'address': pm, 'topics': [INIT]}, dep, head, c['initChunk'], workers=3, on_logs=on, label='init %d' % cid)
        o['stats'] = st
    json.dump(o, open(fn, 'w'))
    return cid, o.get('nInit'), len(o['currencies']), len(o.get('scout', [])), (o.get('stats') or {}).get('fail', [])[:3]
if __name__ == '__main__':
    ids = [int(x) for x in sys.argv[1:]] or list(CFG)
    with cf.ThreadPoolExecutor(21) as ex:
        for r in ex.map(run, ids): print(r, flush=True)
