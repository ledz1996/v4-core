# Re-read rows marked unreadable with direct eth_call at both blocks and settle their status. Writes raw/unreadable_<cid>.json.
import sys, json, concurrent.futures as cf
from lib import *
from config import CFG
def run(cid):
    o = jl('raw/reconcile_%d.json' % cid); pm = o['poolManager']; data = '0x70a08231' + adr(pm)
    un = [r for r in o['rows'] if r['status'] == 'unreadable']; urls = CFG[cid]['state']
    def rd(t, b):
        last = None
        for u in (urls[::-1] + urls) * 6:
            try:
                j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': t, 'data': data}, hex(b)]}, tries=2)
            except Exception as e:
                last = 'transport: ' + str(e)[:60]; continue
            if 'result' in j:
                r = j['result']
                if r in ('0x', '0x0'): return 'nocode-or-empty'
                return int(r[:66], 16)
            last = 'revert: ' + json.dumps(j['error'])[:80]
            if 'unknown state' in last.lower() or 'rate' in last.lower(): time.sleep(0.3); continue
            if 'revert' in last.lower() or 'execution' in last.lower(): return last
        return last
    def one(r):
        x1 = rd(r['token'], o['B1']); x2 = rd(r['token'], o['B2']); net_ = int(r['tin']) - int(r['tout'])
        if isinstance(x1, int) and isinstance(x2, int): st = 'ok' if x2 - x1 == net_ else 'mismatch'
        elif not isinstance(x1, int) and isinstance(x2, int): st = 'new-in-window-ok' if x2 == net_ else 'new-in-window-mismatch'
        elif not isinstance(x2, int) and not isinstance(x1, int): st = 'never-readable'
        else: st = 'unreadable-at-B2'
        return dict(token=r['token'], bal1=str(x1), bal2=str(x2), tin=r['tin'], tout=r['tout'], nlogs=r['nlogs'], status=st)
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(one, un))
    cnt = {}
    for r in res: cnt[r['status']] = cnt.get(r['status'], 0) + 1
    json.dump(dict(chainId=cid, counts=cnt, rows=res), open('raw/unreadable_%d.json' % cid, 'w'), indent=1)
    print(cid, cnt)
    for r in res:
        if r['status'] not in ('ok', 'new-in-window-ok'): print('  ', r)
if __name__ == '__main__':
    for a in sys.argv[1:]: run(int(a))
