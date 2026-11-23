# For currencies whose full balance transfer was rejected: symbol, revert reason, and whether smaller amounts pass.
import sys, json, gzip, os
from common import *
SINK = '0x00000000000000000000000000000000005111c0'
def dec(r):
    if not isinstance(r, str): 
        e = r.get('error') or {}
        d = e.get('data'); m = e.get('message', '')
        if isinstance(d, str) and d.startswith('0x08c379a0'):
            try:
                ln = int(d[74:138], 16); return 'REVERT:' + bytes.fromhex(d[138:138 + 2 * ln]).decode('utf8', 'replace')
            except Exception: pass
        return 'REVERT:' + (m + ' ' + (d if isinstance(d, str) else ''))[:90]
    return r
def sym(r):
    if not isinstance(r, str) or len(r) < 4: return '?'
    b = bytes.fromhex(r[2:])
    try:
        if len(b) >= 96: 
            ln = int.from_bytes(b[32:64], 'big'); return b[64:64 + ln].decode('utf8', 'replace')
        return b.rstrip(b'\0').decode('utf8', 'replace')
    except Exception: return '?'
def run(cid, limit=400):
    x = json.load(gzip.open(os.path.join(RAW, 'xfer_%d.json.gz' % cid)))
    pm = net(cid)['poolManager']
    us = urls(cid)
    if cid == 196: us = ['https://xlayerrpc.okx.com']
    us = list(reversed(us))
    rows = []
    odd = [(t, w) for t, w in x['odd'].items()]
    for t, w in odd[:limit]:
        if w[0] == 'callfail': rows.append((t, 'callfail', w[1])); continue
        bal = w[0]
        calls = [('eth_call', [{'to': t, 'data': sel('symbol()')}, 'latest']),
                 ('eth_call', [{'to': t, 'data': sel('decimals()')}, 'latest'])]
        for amt in (bal, bal - 1 if bal else 0, bal // 2, 1, 0):
            calls.append(('eth_call', [{'from': pm, 'to': t, 'data': sel('transfer(address,uint256)') + adr(SINK) + u256(amt)}, 'latest']))
        res = None
        for k in range(6):
            uu = us[k % len(us)]
            try:
                res = batch(uu, calls, timeout=60)
                if any('capacity' in json.dumps(r) or 'rate' in json.dumps(r).lower() and 'limit' in json.dumps(r).lower() for r in res if not isinstance(r, str)): raise Exception('rate')
                break
            except Exception as e:
                res = None; time.sleep(1 + k)
        if res is None:
            res = [rpc_safe(us[-1], c) for c in calls]
        s = sym(res[0]); 
        try: d = int(res[1], 16) if isinstance(res[1], str) and len(res[1]) > 2 else -1
        except Exception: d = -1
        outs = []
        for r in res[2:]:
            r = dec(r)
            outs.append('ok' if (isinstance(r, str) and not r.startswith('REVERT') and (r == '0x' or r.endswith('1'))) else (r[:70] if r.startswith('REVERT') else 'ret:' + r[:20]))
        rows.append((t, s, d, bal, w[1], w[2], w[3], outs))
    json.dump(rows, open(os.path.join(RAW, 'why_%d.json' % cid), 'w'), indent=0)
    return rows
def rpc_safe(u, c):
    try: return rpc(u, c[0], c[1])
    except Exception as e: return {'error': {'message': str(e)}}
if __name__ == '__main__':
    for c in sys.argv[1:]:
        for r in run(int(c)):
            print(c, r)
