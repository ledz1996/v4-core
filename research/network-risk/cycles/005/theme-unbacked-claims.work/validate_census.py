# For census rows of class U with a real outflow (out > in): did balanceOf(PoolManager) fall in that block, or is the
# log a spoof (a token that emits Transfer logs naming the PoolManager without moving its balance)?
# usage: python3 validate_census.py <chainId>
import sys, json, gzip, collections, concurrent.futures as cf
from lib import *
from config import CFG
from validate_burns import txt, bal
def run(cid):
    d = json.load(gzip.open('raw/census_%d.json.gz' % cid, 'rt')); pm = net(cid)['poolManager']; urls = CFG[cid]['state']
    if cid == 56: urls = ['https://bsc-mainnet.public.blastapi.io', 'https://bsc-dataseed1.bnbchain.org']
    by = collections.defaultdict(list)
    for u in d['unexplained']:
        if int(u['out']) > int(u['in']): by[u['token']].append(u)
    def one(t):
        v = by[t]; e = v[-1]; r = dict(token=t, rows=len(v), egTx=e['tx'], block=e['block'], out=e['out'])
        r['symbol'] = txt(urls[0], t, 'symbol()')
        b0 = bal(urls, t, pm, e['block'] - 1); b1 = bal(urls, t, pm, e['block'])
        r['balBefore'] = None if b0 is None else str(b0); r['balAfter'] = None if b1 is None else str(b1)
        r['real'] = None if b0 is None or b1 is None else (b1 < b0)
        try:
            x = rpc(urls[-1], 'eth_getTransactionByHash', [e['tx']]); r['sender'] = x['from']; r['txTo'] = x['to']; r['selector'] = x['input'][:10]
        except Exception as ex: pass
        return r
    with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(one, list(by)))
    json.dump(dict(chainId=cid, rows=res), open('raw/census_%d_U_validated.json' % cid, 'w'), indent=0)
    c = collections.Counter('real' if r['real'] else 'spoof' if r['real'] is False else 'unknown' for r in res)
    print(cid, 'U tokens with outflow', len(res), dict(c), 'selectors', collections.Counter(r.get('selector') for r in res).most_common(5))
    for r in res:
        if r['real'] is not False: print('   ', r['token'], r.get('symbol'), 'rows', r['rows'], 'bal', r['balBefore'], '->', r['balAfter'], 'out', r['out'], 'sender', r.get('sender'), 'to', r.get('txTo'), r.get('selector'), r['egTx'])
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
