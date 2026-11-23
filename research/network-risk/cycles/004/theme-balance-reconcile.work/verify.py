# Second pass over every token that did not reconcile: re-read both balances with a direct eth_call on another endpoint,
# re-fetch the logs with an address filter, and count every event of the token that names the PoolManager in topic 1 or 2.
import sys, json, os
from lib import *
from config import CFG
from fetch import getlogs_range
DEPOSIT = '0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c'
WITHDRAWAL = '0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65'
def run(cid, only=None, chunk=None):
    fn = 'raw/mismatch_%d.json' % cid
    if not os.path.exists(fn): return
    o = json.load(open(fn)); c = CFG[cid]; pm = net(cid)['poolManager'].lower(); p = pad_addr(pm)
    su = c['state'][-1]; B1, B2 = o['B1'], o['B2']
    rows = [r for r in o['rows'] if r['status'] == 'mismatch' and (only is None or r['token'] in only)]
    for r in rows:
        t = r['token']; data = '0x70a08231' + pm[2:].rjust(64, '0')
        try:
            x1 = int(rpc(su, 'eth_call', [{'to': t, 'data': data}, hex(B1)]), 16); x2 = int(rpc(su, 'eth_call', [{'to': t, 'data': data}, hex(B2)]), 16)
        except Exception as e:
            r['verify'] = 'state read failed: ' + str(e)[:80]; continue
        ev = {}; tin = [0]; tout = [0]; dep = [0]; wd = [0]; seen = set()
        def on(logs):
            for l in logs:
                k = (l['transactionHash'], l['logIndex'])
                if k in seen: continue
                seen.add(k)
                t0 = l['topics'][0]; ev[t0] = ev.get(t0, 0) + 1
                d = l['data'][2:]
                if t0 == TRANSFER and len(l['topics']) == 3 and len(d) == 64:
                    v = int(d, 16)
                    if l['topics'][2] == p: tin[0] += v
                    if l['topics'][1] == p: tout[0] += v
                if t0 == DEPOSIT and len(l['topics']) == 2 and l['topics'][1] == p and len(d) == 64: dep[0] += int(d, 16)
                if t0 == WITHDRAWAL and len(l['topics']) == 2 and l['topics'][1] == p and len(d) == 64: wd[0] += int(d, 16)
        ch = chunk or c['chunk']
        s1 = getlogs_range(c['logs'], {'address': t, 'topics': [None, p]}, B1 + 1, B2, ch, on_logs=on)
        s2 = getlogs_range(c['logs'], {'address': t, 'topics': [None, None, p]}, B1 + 1, B2, ch, on_logs=on)
        r['v'] = dict(bal1=str(x1), bal2=str(x2), tin=str(tin[0]), tout=str(tout[0]), deposit=str(dep[0]), withdrawal=str(wd[0]), events=ev,
                      diff=str((x2 - x1) - (tin[0] - tout[0])), diffAfterWrap=str((x2 - x1) - (tin[0] - tout[0]) - dep[0] + wd[0]), fails=len(s1['fail']) + len(s2['fail']),
                      sameAsFirstPass=(str(x1) == r['bal1'] and str(x2) == r['bal2'] and str(tin[0]) == r['tin'] and str(tout[0]) == r['tout']))
        print(cid, t, r.get('symbol'), 'diff', r['v']['diff'], 'afterWrap', r['v']['diffAfterWrap'], 'same', r['v']['sameAsFirstPass'], 'events', {k[:10]: v for k, v in ev.items()}, flush=True)
    json.dump(o, open(fn, 'w'), indent=1)
if __name__ == '__main__':
    cid = int(sys.argv[1]); only = set(a.lower() for a in sys.argv[2:]) or None
    run(cid, only)
