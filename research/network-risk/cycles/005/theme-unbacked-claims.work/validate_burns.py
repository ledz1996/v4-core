# For each token flagged by classify_burns.py: is the log real (did balanceOf(PoolManager) fall in that block), who
# sent the transaction, what did it call, and how many pools name the token (Initialize topics 2 and 3).
# usage: python3 validate_burns.py <chainId> [maxTokens]
import sys, json, concurrent.futures as cf
from lib import *
from config import CFG
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
def txt(u, t, sig):
    try:
        b = bytes.fromhex(call(u, t, sig)[2:])
        if len(b) >= 96 and int.from_bytes(b[:32], 'big') == 32: return b[64:64 + int.from_bytes(b[32:64], 'big')].decode(errors='replace')
        return b[:32].rstrip(b'\0').decode(errors='replace')
    except Exception as e: return None
def bal(urls, t, pm, blk):
    for u in urls:
        try: return int(call(u, t, 'balanceOf(address)', adr(pm), block=hex(blk) if isinstance(blk, int) else blk), 16)
        except Exception as e: last = str(e)[:80]
    return None
def run(cid, maxn=60):
    d = json.load(open('raw/burns_%d_classified.json' % cid)); pm = net(cid)['poolManager']; c = CFG[cid]; urls = c['state']; lu = c.get('init') or c['logs']
    def one(o):
        t = o['token']; u = urls[0]; r = dict(token=t, hits=o['hits'], noPM=o['noPM'], sumNoPM=o['sumNoPM'], egTx=o['egTx'], first=o['first'], last=o['last'], recipients=o['recipients'][:4])
        r['name'] = txt(u, t, 'name()'); r['symbol'] = txt(u, t, 'symbol()')
        try:
            x = rpc(u, 'eth_getTransactionByHash', [o['egTx']]); r['sender'] = x['from']; r['txTo'] = x['to']; r['selector'] = x['input'][:10]; b = int(x['blockNumber'], 16)
            r['balBefore'] = bal(urls, t, pm, b - 1); r['balAfter'] = bal(urls, t, pm, b); r['balNow'] = bal(urls, t, pm, 'latest')
            r['real'] = None if r['balBefore'] is None or r['balAfter'] is None else r['balAfter'] < r['balBefore']
        except Exception as e: r['err'] = str(e)[:120]
        try:
            n = 0; hooks = set()
            for tp in ([INIT, None, pad_addr(t)], [INIT, None, None, pad_addr(t)]):
                lg = rpc(lu, 'eth_getLogs', [{'address': pm, 'topics': tp, 'fromBlock': hex(max(0, o['first'] - 3000000)), 'toBlock': hex(o['last'])}], timeout=60, tries=2)
                n += len(lg)
                for l in lg: hooks.add('0x' + l['data'][2:][64 * 2 + 24:64 * 3])
            r['pools'] = n; r['hooks'] = sorted(hooks)[:4]
        except Exception as e: r['poolsErr'] = str(e)[:100]
        for k in ('balBefore', 'balAfter', 'balNow'):
            if isinstance(r.get(k), int): r[k] = str(r[k])
        return r
    with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(one, d['flagged'][:maxn]))
    json.dump(dict(chainId=cid, rows=res), open('raw/burns_%d_validated.json' % cid, 'w'), indent=0)
    print(cid, 'flagged', len(d['flagged']), 'validated', len(res), 'real', sum(1 for r in res if r.get('real')), 'spoof(log only)', sum(1 for r in res if r.get('real') is False), 'unknown', sum(1 for r in res if r.get('real') is None))
    for r in res:
        if r.get('real') is not False: print('  ', r['token'], r.get('symbol'), 'noPM', r['noPM'], 'sum', r['sumNoPM'], 'bal', r.get('balBefore'), '->', r.get('balAfter'), 'now', r.get('balNow'), 'pools', r.get('pools'), 'hooks', r.get('hooks'), 'sender', r.get('sender'), 'to', r.get('txTo'), r.get('selector'), 'eg', r['egTx'], r.get('err', ''), r.get('poolsErr', ''))
if __name__ == '__main__': run(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 60)
