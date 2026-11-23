# Claim mints of the native id (0) in transactions without a pool event leave no Transfer log to compare with.
# For each sampled one: compare the mint with the transaction value, then with Withdrawal logs of wrappers in the
# receipt, and trace the rest where an endpoint serves debug_traceTransaction (value sent into the PoolManager,
# native takes out of it and their recipients).
# usage: python3 native_check.py <chainId> [maxTraces]
import sys, json, gzip, collections, concurrent.futures as cf
from lib import *
from sample_receipts import RCPT
from txinfo import trace
def flat(c, out):
    out.append(c)
    for x in c.get('calls', []) or []: flat(x, out)
    return out
def run(cid, maxtr=25):
    pm = net(cid)['poolManager'].lower()
    S = json.load(gzip.open('raw/sample_%d.json.gz' % cid, 'rt'))
    nat = [d for d in S['digests'] if 'err' not in d and d['ids'].get('0' * 40, {}).get('cls') == 'native']
    res = []; cnt = collections.Counter()
    def one(a):
        k, d = a; m = int(d['ids']['0' * 40]['mint']) - int(d['ids']['0' * 40]['burn'])
        v = None
        for u in RCPT[cid] * 2:
            try: v = int(rpc(u, 'eth_getTransactionByHash', [d['tx']], timeout=30, tries=2)['value'], 16); break
            except Exception: pass
        un = int(d.get('unwrap', '0')); nl = 0
        if cid == 5042:  # Arc logs every native transfer as Transfer(from, to, amount) at 0xff..fe
            for u in RCPT[cid] * 2:
                try:
                    rc = rpc(u, 'eth_getTransactionReceipt', [d['tx']], timeout=30, tries=2)
                    nl = sum(int(l['data'], 16) for l in rc['logs'] if l['address'].lower() == '0x' + 'f' * 39 + 'e' and len(l['topics']) == 3 and l['topics'][2] == pad_addr(pm)); break
                except Exception: pass
        cls = 'value' if v is not None and v >= m else 'native-log' if nl >= m else 'unwrap' if v is not None and v + un >= m else 'open'
        if cls == 'open':  # wrappers of the Arbitrum bridge design log a withdraw as Transfer(holder, 0, amount)
            for u in RCPT[cid] * 2:
                try:
                    rc = rpc(u, 'eth_getTransactionReceipt', [d['tx']], timeout=30, tries=2); bz = {}
                    for l in rc['logs']:
                        if len(l['topics']) == 3 and l['topics'][0] == TRANSFER and l['topics'][2] == '0x' + '0' * 64 and len(l['data']) == 66: bz[l['address']] = bz.get(l['address'], 0) + int(l['data'], 16)
                    hit = [a for a, x in bz.items() if x + (v or 0) >= m]
                    if hit: cls = 'unwrap-burn'; un = bz[hit[0]]
                    break
                except Exception: pass
        return dict(tx=d['tx'], block=d['block'], sender=d['from'], to=d['to'], mint=str(m), value=None if v is None else str(v), unwrap=str(un), cls=cls)
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(one, list(enumerate(nat))))
    opens = [r for r in res if r['cls'] == 'open']
    # one trace per distinct "to" contract first, then more up to maxtr
    seen = set(); order = []
    for r in opens:
        if r['to'] not in seen: seen.add(r['to']); order.append(r)
    order += [r for r in opens if r not in order]
    for r in order[:maxtr]:
        tu, tr = trace(cid, r['tx'])
        if not tr:
            r['trace'] = 'not served'
            try:  # fallback: did the called contract's own native balance fall by at least the mint in that block
                from config import CFG
                su = CFG[cid]['state']; b0 = b1 = None
                for u in su:
                    try: b0 = int(rpc(u, 'eth_getBalance', [r['to'], hex(r['block'] - 1)], tries=2), 16); b1 = int(rpc(u, 'eth_getBalance', [r['to'], hex(r['block'])], tries=2), 16); break
                    except Exception: pass
                if b0 is not None: r['payerBalance'] = [str(b0), str(b1)]; r['cls'] = 'payer-balance-fell' if b0 - b1 >= int(r['mint']) else 'open'
            except Exception: pass
            continue
        calls = flat(tr, [])
        vin = sum(int(c.get('value', '0x0') or '0x0', 16) for c in calls if (c.get('to') or '').lower() == pm and c.get('type') == 'CALL' and not c.get('error'))
        outs = [((c.get('to') or '').lower(), int(c.get('value', '0x0') or '0x0', 16)) for c in calls if (c.get('from') or '').lower() == pm and c.get('type') == 'CALL' and int(c.get('value', '0x0') or '0x0', 16) > 0 and not c.get('error')]
        r['trace'] = dict(url=tu, valueIntoPM=str(vin), nativeOut=[(a, str(x)) for a, x in outs][:8])
        r['cls'] = 'traced-value' if vin >= int(r['mint']) else 'traced-short'
    for r in res: cnt[r['cls']] += 1
    json.dump({'chainId': cid, 'nativeOnlySampled': len(nat), 'counts': dict(cnt), 'rows': res}, open('raw/native_%d.json' % cid, 'w'), indent=0)
    print(cid, 'native-only sampled', len(nat), dict(cnt))
    for r in res:
        if r['cls'] in ('traced-short',) or (r['cls'] == 'open'): print('   ', json.dumps(r)[:420])
if __name__ == '__main__': run(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 25)
