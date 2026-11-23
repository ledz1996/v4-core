# For each hook: pair every currency of its real pools with a codeless foreign currency, mark that pool initialized by state override,
# and run both swap directions through the Quoter inside an unlock. Report what the hook did: PoolManager take, mint, burn, settle,
# token transfers and value sends that originate from the hook. Read-only (debug_traceCall).
import sys, collections
from common import *
import qtr, qsum
os.chdir(C5)
from summ import census, load
os.chdir(HERE)
W = '0x1111111111111111111111111111111111111112'
PMSEL = {'0b0d9c09': 'take', '156e29f6': 'mint', 'f5298aca': 'burn', '11da60b4': 'settle', '3dd45adb': 'settleFor', 'a5841194': 'sync', 'f3cd914c': 'swap', '5a6bcfda': 'modifyLiquidity', '234266d7': 'donate', '48c89491': 'unlock', '80f0b44c': 'clear'}
TSEL = {'a9059cbb': 'transfer', '23b872dd': 'transferFrom', '095ea7b3': 'approve'}
def acts(c, hook, pm, out, inhook=False):
    frm = c.get('from', '').lower(); to = c.get('to', '').lower(); inp = c.get('input', '0x'); s = inp[2:10]
    val = int(c.get('value', '0x0'), 16) if c.get('value') else 0
    a = [inp[10 + 64 * i:10 + 64 * (i + 1)] for i in range(4)]
    err = ' ERR' if c.get('error') else ''
    if frm == hook and c.get('type') in ('CALL',):
        if to == pm.lower() and s in PMSEL:
            n = PMSEL[s]
            if n in ('take',): out.append('PM.take(cur=0x%s,to=0x%s,amt=%d)%s' % (a[0][24:], a[1][24:], int(a[2] or '0', 16), err))
            elif n in ('mint', 'burn'): out.append('PM.%s(who=0x%s,id=0x%s,amt=%d)%s' % (n, a[0][24:], a[1][24:], int(a[2] or '0', 16), err))
            elif n == 'sync': out.append('PM.sync(0x%s)%s' % (a[0][24:], err))
            elif n == 'settle': out.append('PM.settle(value=%d)%s' % (val, err))
            else: out.append('PM.%s%s' % (n, err))
        elif s in TSEL:
            if s == 'a9059cbb': out.append('token 0x%s.transfer(to=0x%s,amt=%d)%s' % (to[2:10], a[0][24:], int(a[1] or '0', 16), err))
            elif s == '23b872dd': out.append('token 0x%s.transferFrom(0x%s,0x%s,%d)%s' % (to[2:10], a[0][24:32], a[1][24:32], int(a[2] or '0', 16), err))
        elif val: out.append('send %d wei to %s%s' % (val, to, err))
        elif to != pm.lower() and s: out.append('call %s.%s%s' % (to[:12], qsum.nm(s), err))
    for x in c.get('calls') or []: acts(x, hook, pm, out)
def test(cid, hook, maxtok=3, amount=10 ** 15, extra_keys=None):
    n = net(cid); pm = n['poolManager']; hook = hook.lower()
    os.chdir(C5); rows = [r for r in load(cid) if r[6] == hook]; os.chdir(HERE)
    cur = collections.Counter()
    for r in rows: cur[r[2]] += 1; cur[r[3]] += 1
    toks = [c for c, _ in cur.most_common()][:maxtok]
    fees = collections.Counter((r[4], r[5]) for r in rows).most_common(1)
    fee, ts = fees[0][0] if fees else (3000, 60)
    print('== %d %s pools %d currencies %s fee/ts %s' % (cid, hook, len(rows), toks, (fee, ts)))
    keys = [(min(W, t, key=lambda x: int(x, 16)), max(W, t, key=lambda x: int(x, 16)), fee, ts) for t in toks] + [(W, '0x2222222222222222222222222222222222222223', fee, ts)] + (extra_keys or [])
    for c0, c1, f, t in keys:
        for zfo in (1, 0):
            for exact in ('in',):
                r = qtr.run(cid, hook, c0, c1, f, t, zfo, amount, exact, True, quiet=True)
                if not r: print('   trace failed'); continue
                out = []; acts(r, hook, pm, out)
                sw = qsum.find_swap(r) or {}
                hookerr = ''
                for x in sw.get('calls') or []:
                    if x.get('to', '').lower() == hook and x.get('error'): hookerr = ' hookRevert[%s]=%s' % (qsum.nm(x['input'][2:10]), (x.get('output') or '')[:74])
                print('   key(%s,%s) zfo=%d: %s%s | top=%s' % (c0[:8], c1[:8], zfo, '; '.join(out)[:700] or 'no value calls by hook', hookerr, (r.get('output') or '')[:10]))
if __name__ == '__main__':
    cid = int(sys.argv[1])
    for h in sys.argv[2:]: test(cid, h)
