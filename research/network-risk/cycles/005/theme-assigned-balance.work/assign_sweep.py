# For one representative token per family and every candidate function: read-only trial through eth_call with state overrides.
# The PoolManager address (code replaced by a measuring stub) hands amt tokens to an ordinary account A, A calls the function,
# then the stub reads balances and tries to send out the full balance and the balance minus amt. Each trial reverts.
import sys, json, gzip, os, re
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import MULTI, FWD
from abi import split_types, encode
A = '0x00000000000000000000000000000000000a11ce'; SINK = '0x00000000000000000000000000000000005111c0'
LOCKISH = re.compile(r'(?i)(lock|freez|frozen|vest|stak|bond|escrow|grant|hold|cooldown|restrict|allocat|reward|airdrop|distribut)')
def item(p):
    b = bytes.fromhex(p); return u256(len(b)) + b.ljust((len(b) + 31) // 32 * 32, b'\0').hex()
def variants(nm, pm, amt, now):
    types = split_types(nm)
    nuint = sum(1 for t in types if t.split('[')[0].startswith(('uint', 'int')))
    lock = bool(LOCKISH.search(nm.split('(')[0]))
    topts = [now + 3 * 365 * 86400, 400 * 86400, 1] if (lock and nuint >= 2) else [now + 3 * 365 * 86400]
    sopts = [False, True] if (lock and nuint >= 2) else [False]
    out = []; seen = set()
    for T in topts:
        for sw in sopts:
            vals = []; nu = 0; na = 0
            for t in types:
                base = t.split('[')[0]
                if base == 'address': v = pm if na == 0 else A; na += 1
                elif base.startswith(('uint', 'int')):
                    bits = int(base.lstrip('uint') or 256)
                    if nu == 0: v = T if sw else amt
                    elif nu == 1: v = amt if sw else T
                    else: v = T
                    if bits < 32 and v > 2 ** bits - 1: v = 1
                    nu += 1
                elif base == 'bool': v = True
                elif base == 'string': v = 'x'
                elif base == 'bytes': v = b''
                else: v = b'LOCK'
                if t.endswith('[]'): v = [v]
                elif t.endswith(']'): v = [v] * int(t[t.rindex('[') + 1:-1])
                vals.append(v)
            try: cd = sel(nm)[2:] + encode(types, vals)
            except Exception as e: continue
            if cd not in seen: seen.add(cd); out.append(cd)
    return out
def classify(base, w, amt):
    b0, okA, okC, b1, bA, full, part, fin = w
    if not okC: return None
    dPM = b1 - (b0 - amt); dA = bA - amt
    if dPM > 0 and full == 0 and base[5] == 1: return 'locked-assign'
    if dPM > 0 and dPM + dA > 0: return 'free-raise'
    if dPM < 0: return 'lowered'
    if dPM == 0 and full == 0 and base[5] == 1: return 'lock-only'
    if dA > 0: return 'A-gain'
    return None
def run(cid, per=25, workers=5, maxrep=1):
    fam = json.load(gzip.open(os.path.join(RAW, 'families_%d.json.gz' % cid)))
    xf = json.load(gzip.open(os.path.join(RAW, 'xfer_%d.json.gz' % cid))) if os.path.exists(os.path.join(RAW, 'xfer_%d.json.gz' % cid)) else {'bal': {}}
    d, rows = universe(cid); bal2 = {r['token']: int(r.get('bal2') or 0) for r in rows}
    pm = net(cid)['poolManager']
    now = int(time.time())
    jobs = []
    for key, f in fam.items():
        fns = f['fns'] + f['trig']
        if not fns: continue
        for t in f['reps'][:maxrep]:
            b = int(xf['bal'].get(t) or bal2.get(t) or 0)
            if b < 3: continue
            amt = max(1, b // 3)
            items = [('BASE', adr(t) + sel('balanceOf(address)')[2:] + adr(pm))]
            for nm in fns:
                for cd in variants(nm, pm, amt, now): items.append((nm, adr(t) + cd))
            for i in range(0, len(items), per):
                ch = items[i:i + per]
                if i > 0: ch = [items[0]] + ch
                jobs.append((key, t, amt, ch))
    print(cid, 'jobs', len(jobs), 'trials', sum(len(j[3]) for j in jobs), flush=True)
    hits = []; stats = dict(trials=0, okcall=0, failcalls=0, noxfer=0)
    def job(j):
        key, t, amt, ch = j
        data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + ''.join(item(p) for nm, p in ch)
        r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWD}}, gas=120_000_000 if cid not in (999,) else 2_900_000 * 10, rot=hash(t) % 7)
        if not isinstance(r, str) or len(r) != 2 + 512 * len(ch):
            return j, None, str(r)[:150]
        ws = [[int(r[2 + 512 * k + 64 * m: 66 + 512 * k + 64 * m], 16) for m in range(8)] for k in range(len(ch))]
        return j, ws, None
    with ThreadPoolExecutor(workers) as ex:
        for j, ws, err in ex.map(job, jobs):
            key, t, amt, ch = j
            if ws is None: stats['failcalls'] += 1; hits.append(dict(fam=key, token=t, cat='callfail', err=err, n=len(ch))); continue
            base = ws[0]
            if base[1] == 0: stats['noxfer'] += 1
            for (nm, p), w in zip(ch[1:], ws[1:]):
                stats['trials'] += 1
                if w[2]: stats['okcall'] += 1
                c = classify(base, w, amt)
                if c: hits.append(dict(fam=key, token=t, fn=nm, cat=c, amt=str(amt), w=[str(x) for x in w], base=[str(x) for x in base], data=p[40:]))
    json.dump(dict(chainId=cid, stats=stats, hits=hits), gzip.open(os.path.join(RAW, 'assign_%d.json.gz' % cid), 'wt'))
    import collections
    print(cid, net(cid)['name'], stats, collections.Counter(h['cat'] for h in hits), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
