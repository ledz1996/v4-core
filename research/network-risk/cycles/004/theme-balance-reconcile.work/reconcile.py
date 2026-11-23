# For one network: read balanceOf(PoolManager) for every candidate currency at blocks B1 and B2,
# sum the ERC-20 Transfer logs that name the PoolManager in (B1, B2], and list the tokens that do not reconcile.
# Read-only: eth_call (Multicall3 aggregate3), eth_getLogs, eth_getBlockByNumber.
import sys, json, os, threading, concurrent.futures as cf
from lib import *
from config import CFG
from fetch import getlogs_range
def enc_aggregate3(calls):
    n = len(calls); head = '82ad56cb' + (32).to_bytes(32, 'big').hex() + n.to_bytes(32, 'big').hex()
    offs = ''; body = ''; off = n * 32
    for target, data in calls:
        d = bytes.fromhex(data[2:]); pad = (32 - len(d) % 32) % 32
        el = target[2:].lower().rjust(64, '0') + (1).to_bytes(32, 'big').hex() + (0x60).to_bytes(32, 'big').hex() + len(d).to_bytes(32, 'big').hex() + d.hex() + '00' * pad
        offs += off.to_bytes(32, 'big').hex(); off += len(el) // 2; body += el
    return '0x' + head + offs + body
def dec_aggregate3(ret):
    b = bytes.fromhex(ret[2:]); base = int.from_bytes(b[0:32], 'big'); n = int.from_bytes(b[base:base + 32], 'big'); out = []
    start = base + 32
    for i in range(n):
        o = start + int.from_bytes(b[start + 32 * i:start + 32 * i + 32], 'big')
        ok = int.from_bytes(b[o:o + 32], 'big'); bo = o + int.from_bytes(b[o + 32:o + 64], 'big'); ln = int.from_bytes(b[bo:bo + 32], 'big')
        out.append((bool(ok), b[bo + 32:bo + 32 + ln]))
    return out
def mc(urls, calls, block, size=400, ts=None):
    """calls: list of (target, data). Returns list of (ok, bytes) or None when the token could not be read.
    Each group starts with Multicall3.getCurrentBlockTimestamp(); a reply whose timestamp is not the timestamp of the
    requested block is discarded, because some load balanced endpoints answer old-state calls from the latest state."""
    res = [None] * len(calls); bad = {'wrongBlock': 0}
    def do(idx):
        sub = [(MC3, '0x0f28c97d')] + [calls[i] for i in idx]
        for u in urls * 3:
            try:
                r = rpc(u, 'eth_call', [{'to': MC3, 'data': enc_aggregate3(sub)}, hex(block)], timeout=60, tries=3)
                d = dec_aggregate3(r)
                if ts is not None and int.from_bytes(d[0][1][:32], 'big') != ts:
                    bad['wrongBlock'] += 1; continue
                for i, x in zip(idx, d[1:]): res[i] = x
                return
            except Exception as e:
                err = str(e)
        if len(idx) > 1:
            m = len(idx) // 2; do(idx[:m]); do(idx[m:])
    groups = [list(range(i, min(i + size, len(calls)))) for i in range(0, len(calls), size)]
    with cf.ThreadPoolExecutor(4) as ex: list(ex.map(do, groups))
    if bad['wrongBlock']: print('replies from the wrong block discarded:', bad['wrongBlock'], flush=True)
    return res
def balances(urls, tokens, pm, block, ts=None):
    data = '0x70a08231' + pm[2:].lower().rjust(64, '0')
    r = mc(urls, [(t, data) for t in tokens], block, ts=ts)
    out = {}
    for t, x in zip(tokens, r):
        if x is not None and x[0] and len(x[1]) == 0: out[t] = 'nocode'  # success with empty return data: no code at this block
        elif x is None or not x[0] or len(x[1]) < 32: out[t] = None
        else: out[t] = int.from_bytes(x[1][:32], 'big')
    return out
def run(cid, days=1.0, tag=''):
    n = net(cid); c = CFG[cid]; pm = n['poolManager'].lower(); su = c['state']
    head = int(rpc(su[0], 'eth_blockNumber', []), 16)
    B2 = head - 200
    t2 = int(rpc(su[0], 'eth_getBlockByNumber', [hex(B2), False])['timestamp'], 16)
    tprev = int(rpc(su[0], 'eth_getBlockByNumber', [hex(B2 - 20000), False])['timestamp'], 16)
    bt = (t2 - tprev) / 20000
    B1 = B2 - int(days * 86400 / bt)
    t1 = int(rpc(su[0], 'eth_getBlockByNumber', [hex(B1), False])['timestamp'], 16)
    print(cid, n['name'], 'B1', B1, 'B2', B2, 'seconds', t2 - t1, flush=True)
    agg = {}  # token -> [in, out, nlogs, odd]
    def on(logs):
        for l in logs:
            tp = l['topics']
            if len(tp) != 3 or tp[0] != TRANSFER: continue
            d = l['data'][2:]
            a = l['address'].lower(); e = agg.setdefault(a, [0, 0, 0, 0])
            if len(d) != 64: e[3] += 1; continue
            v = int(d, 16); frm = '0x' + tp[1][-40:]; to = '0x' + tp[2][-40:]
            if to == pm: e[0] += v
            if frm == pm: e[1] += v
            e[2] += 1
    p = pad_addr(pm)
    s_out = getlogs_range(c['logs'], {'topics': [TRANSFER, p]}, B1 + 1, B2, c['chunk'], workers=c.get('workers', 4), on_logs=on, label='%d out' % cid)
    s_in = getlogs_range(c['logs'], {'topics': [TRANSFER, None, p]}, B1 + 1, B2, c['chunk'], workers=c.get('workers', 4), on_logs=on, label='%d in' % cid)
    # self transfers appear in both queries; count them once
    uni = set(agg)
    fn = 'raw/currencies_%d.json' % cid
    src = {}
    if os.path.exists(fn) or os.path.exists(fn + '.gz'):
        cu = jl(fn)
        for a in cu.get('currencies', {}): uni.add(a.lower())
        for s in cu.get('scout', []): uni.add(s['address']); src[s['address']] = s
    uni.discard('0x' + '0' * 40)
    toks = sorted(uni)
    b1 = balances(su, toks, pm, B1, t1); b2 = balances(su, toks, pm, B2, t2)
    rows = []; mism = []
    for t in toks:
        i, o, k, odd = agg.get(t, [0, 0, 0, 0])
        x1, x2 = b1[t], b2[t]
        row = dict(token=t, bal1=x1, bal2=x2, tin=i, tout=o, nlogs=k, odd=odd)
        if x1 == 'nocode': x1 = 0; row['bal1'] = 0; row['nocodeAtB1'] = True
        if x2 == 'nocode': x2 = 0; row['bal2'] = 0; row['nocodeAtB2'] = True
        if x1 is None or x2 is None: row['status'] = 'unreadable'
        elif x1 == 0 and x2 == 0 and i == o: row['status'] = 'zero'
        elif x2 - x1 == i - o: row['status'] = 'ok'
        else: row['status'] = 'mismatch'; row['diff'] = (x2 - x1) - (i - o); mism.append(row)
        if t in src: row['symbol'] = src[t]['symbol']; row['rate'] = src[t]['rate']; row['decimals'] = src[t]['decimals']
        rows.append({k2: (str(v) if isinstance(v, int) and k2 not in ('nlogs', 'odd') else v) for k2, v in row.items()})
    out = dict(chainId=cid, name=n['name'], poolManager=pm, stateUrl=su, logsUrl=c['logs'], B1=B1, B2=B2, t1=t1, t2=t2, seconds=t2 - t1,
               logStats=dict(out=s_out, **{'in': s_in}), universe=len(toks),
               counts={s: sum(1 for r in rows if r['status'] == s) for s in ('ok', 'zero', 'mismatch', 'unreadable')}, rows=rows)
    json.dump(out, open('raw/reconcile_%d%s.json' % (cid, tag), 'w'))
    print(cid, n['name'], 'universe', len(toks), out['counts'], 'logs', s_out['logs'], s_in['logs'], 'fails', len(s_out['fail']), len(s_in['fail']), flush=True)
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1]); days = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    run(cid, days, sys.argv[3] if len(sys.argv) > 3 else '')
