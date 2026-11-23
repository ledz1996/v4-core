# For the burn-address hits of scan_burns.py: sample receipts per token and mark those where the PoolManager emitted
# no event in the transaction (noPM). For tokens with a noPM sample, fetch every hit.
# usage: python3 classify_burns.py <chainId>
import sys, json, gzip, collections
from lib import *
from sample_receipts import RCPT, T6909, SWAP, MODL, DON
import concurrent.futures as cf
def pmsum(cid, txs, workers=6):
    pm = net(cid)['poolManager'].lower(); out = {}
    def one(a):
        k, tx = a
        for at in range(4):
            try:
                r = rpc(RCPT[cid][(k + at) % len(RCPT[cid])], 'eth_getTransactionReceipt', [tx], timeout=40, tries=2)
                if r:
                    ev = [l['topics'][0] for l in r['logs'] if l['address'].lower() == pm and l['topics']]
                    out[tx] = dict(frm=r['from'], to=r.get('to'), pmEvents=len(ev), pool=sum(1 for e in ev if e in (SWAP, MODL, DON)), c6909=sum(1 for e in ev if e == T6909), nLogs=len(r['logs'])); return
            except Exception: time.sleep(1 + at)
        out[tx] = None
    with cf.ThreadPoolExecutor(workers) as ex: list(ex.map(one, list(enumerate(txs))))
    return out
def run(cid):
    d = json.load(gzip.open('raw/burns_%d.json.gz' % cid, 'rt')); by = collections.defaultdict(list)
    for r in d['rows']: by[r[2]].append(r)
    pick = []
    for t, v in by.items():
        v.sort(); n = len(v); idx = sorted(set([0, n - 1] + [round(j * (n - 1) / 5) for j in range(6)])) if n > 6 else range(n)
        pick += [v[j][1] for j in idx]
    s = pmsum(cid, list(dict.fromkeys(pick)))
    flagged = [t for t, v in by.items() if any(s.get(r[1]) and s[r[1]]['pmEvents'] == 0 for r in v)]
    more = [r[1] for t in flagged for r in by[t] if r[1] not in s][:6000]
    s.update(pmsum(cid, list(dict.fromkeys(more))))
    out = []
    for t in flagged:
        rows = [r for r in by[t] if s.get(r[1]) and s[r[1]]['pmEvents'] == 0]
        out.append(dict(token=t, hits=len(by[t]), noPM=len(rows), sumNoPM=str(sum(int(r[4]) for r in rows)), first=rows[0][0], last=rows[-1][0], egTx=rows[-1][1], egTo=s[rows[-1][1]]['to'], recipients=sorted(set(r[3] for r in rows)), rows=[[r[0], r[1], r[4]] for r in rows][:400]))
    out.sort(key=lambda o: -o['noPM'])
    json.dump(dict(chainId=cid, tokens=len(by), sampledTxs=len(s), flagged=out), open('raw/burns_%d_classified.json' % cid, 'w'), indent=0)
    print(cid, 'tokens', len(by), 'sampled txs', len(s), 'tokens with a burn in a tx without PoolManager events:', len(out))
    for o in out[:40]: print('  ', o['token'], 'hits', o['hits'], 'noPM', o['noPM'], 'sum', o['sumNoPM'], 'blocks', o['first'], o['last'], 'eg', o['egTx'], 'to', o['egTo'])
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
