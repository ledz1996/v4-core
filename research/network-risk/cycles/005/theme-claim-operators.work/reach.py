# Read-only reach test (debug_traceCall with callTracer, nothing is sent): from an unrelated account, call every dispatcher selector of an approved
# contract X with a few argument fillings and record which calls X makes to the PoolManager. A burn or transferFrom whose first argument is neither
# the caller nor X shows that the caller could name the account whose claims move.
import sys, json, os, time, threading, queue, requests
from collections import defaultdict
from lib import *
TR = {1: 'https://eth.drpc.org', 8453: 'https://base.api.pocket.network', 130: 'https://unichain.drpc.org', 42161: 'https://arbitrum.drpc.org', 4663: 'https://robinhood.drpc.org',
      137: 'https://polygon.drpc.org', 43114: 'https://avalanche.drpc.org', 999: 'https://hyperliquid.drpc.org', 143: 'https://rpc.monad.xyz', 56: 'https://bsc.api.pocket.network', 57073: 'https://rpc-qnd.inkonchain.com', 10: 'https://op.api.pocket.network', 42220: 'https://celo.api.pocket.network', 196: 'https://xlayer.drpc.org'}
ATT = '0x00000000000000000000000000000000a77ac4e5'
PMSEL = {'f5298aca': 'burn', 'fe99049a': 'transferFrom', '48c89491': 'unlock', '0b0d9c09': 'take', '095bcdb6': 'transfer', '156e29f6': 'mint', '11da60b4': 'settle', '3dd45adb': 'settleFor', 'a5841194': 'sync', '558a7297': 'setOperator', '426a8493': 'approve'}
def w(a): return a[2:].lower().rjust(64, '0')
def variants(o, i):
    z = '0' * 64; O = w(o); I = i[2:].rjust(64, '0'); A = w(ATT); one = '0' * 63 + '1'
    return {'zero': z * 24, 'owner': O * 24, 'owner,id': (O + I) * 12, 'id,owner': (I + O) * 12, 'owner,att,id,1': (O + A + I + one) * 6, 'id,1,owner,att': (I + one + O + A) * 6}
def walk(c, pm, out):
    if (c.get('to') or '').lower() == pm:
        inp = c.get('input', '0x'); s = inp[2:10]
        if s in PMSEL:
            a0 = '0x' + inp[10 + 24:10 + 64] if len(inp) >= 74 else None
            out.append([PMSEL[s], a0 if PMSEL[s] in ('burn', 'transferFrom') else None, (c.get('from') or '').lower(), 1 if c.get('error') else 0])
    for k in c.get('calls') or []: walk(k, pm, out)
def run(cid, only=None, nvar=6):
    u = TR[cid]; pm = net(cid)['poolManager'].lower()
    tri = json.load(open(os.path.join(HERE, 'raw', 'triage_%d.json' % cid))); st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid)))
    try: ex = {r['x']: r for r in json.load(open(os.path.join(HERE, 'raw', 'exposure_%d.json' % cid)))}
    except Exception: ex = {}
    owners = defaultdict(set)
    for ow, x, v in st['liveOp']:
        if v: owners[x].add(ow)
    for ow, x, i, v in st['liveAl']:
        if v: owners[x].add(ow)
    FN = os.path.join(HERE, 'raw', 'reach_%d.json' % cid)
    res = json.load(open(FN)) if os.path.exists(FN) else {}
    groups = {}
    for x, d in tri.items():
        if 'err' in d or d.get('isPM') or x in res: continue
        if only and x not in only: continue
        r = ex.get(x); items = (r or {}).get('items') or []
        if not items and len(owners[x]) < 2 and not only: continue
        k = (d['via'], d['target'] or d['h'])
        usd = sum(it[5] or 0 for it in items)
        if k not in groups or usd > groups[k][1]: groups[k] = (x, usd, items)
    todo = sorted(groups.values(), key=lambda g: -g[1])
    print(cid, 'contracts to trace', len(todo), 'already', len(res), flush=True)
    q = queue.Queue(); lock = threading.Lock()
    for g in todo: q.put(g)
    def work():
        s = requests.Session(); s.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'})
        while True:
            try: x, usd, items = q.get_nowait()
            except queue.Empty: return
            d = tri[x]
            if items: it = max(items, key=lambda it: (it[5] or 0, int(it[4]))); o, i = it[0], it[1]
            else: o = sorted(owners[x])[0]; i = '0x' + '0' * 40
            vs = list(variants(o, i).items())[:nvar]; rec = dict(owner=o, id=i, sels={}, errs=0)
            for sel in d['sels']:
                if sel in ('91dd7346',): continue
                for vn, args in vs:
                    j = None
                    for a in range(5):
                        try:
                            j = s.post(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceCall', 'params': [{'from': ATT, 'to': x, 'data': '0x' + sel + args, 'gas': hex(3000000)}, 'latest', {'tracer': 'callTracer'}]}), timeout=40).json()
                            if 'result' in j: break
                            time.sleep(1.5 * (a + 1))
                        except Exception: time.sleep(1.5 * (a + 1))
                    if not j or 'result' not in j: rec['errs'] += 1; continue
                    out = []; walk(j['result'], pm, out)
                    if out: rec['sels'].setdefault(sel, {})[vn] = out[:12]
            with lock:
                res[x] = rec
                json.dump(res, open(FN + '.tmp', 'w')); os.replace(FN + '.tmp', FN)
                print(cid, x, 'sels reaching PM', len(rec['sels']), 'errs', rec['errs'], flush=True)
    ths = [threading.Thread(target=work) for _ in range(3)]
    for t in ths: t.start()
    for t in ths: t.join()
if __name__ == '__main__':
    cid = int(sys.argv[1]); run(cid, only=set(a.lower() for a in sys.argv[2:]) or None)
