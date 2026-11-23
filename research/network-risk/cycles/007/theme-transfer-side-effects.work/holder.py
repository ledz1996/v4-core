# Part two. For every priced currency worth more than MINUSD at the PoolManager that the cycle 6 sweep did not cover: an ordinary
# account A calls every selector of the token and of its implementation with the PoolManager as address argument. Each trial runs
# in eth_call with the measuring stub MULTI at the PoolManager address (state override): the stub hands one third of the balance
# to A, A makes the call through a forwarder, the stub reads balances and tries to send out the full balance. Nothing is sent on chain.
import sys, json, os, re, collections
from concurrent.futures import ThreadPoolExecutor
from base import *
SIG = jz(os.path.join(RAW5, 'signatures.json.gz'))
if os.path.exists(os.path.join(RAW6T, 'signatures_more.json.gz')): SIG.update(jz(os.path.join(RAW6T, 'signatures_more.json.gz')))
if os.path.exists(os.path.join(RAW6C, 'signatures.json.gz')):
    for k, v in jz(os.path.join(RAW6C, 'signatures.json.gz')).items():
        if v and not SIG.get(k): SIG[k] = v
JUNK = {'ffffffff', '4e487b71', '08c379a0', '00000000', '01ffc9a7', '06fdde03', '18160ddd', '313ce567', '70a08231', '95d89b41', 'dd62ed3e', '3644e515', '7ecebe00'}
LOCKISH = re.compile(r'(?i)(lock|freez|frozen|vest|stak|bond|escrow|grant|hold|cooldown|restrict|allocat|reward|airdrop|distribut)')
TRIG = re.compile(r'(?i)(sweep|idle|inactiv|reflect|rebase|claim|process|distribut|harvest|accrue|update|poke|drip|sync|skim|expire|decay|burn|liquidat|collect|checkpoint|release|unlock|settle|epoch|trigger|execute|compound|tax|fee|swap|migrat|convert|upgrade|redeem|exit|wrap)')
def item(p):
    b = bytes.fromhex(p); return u256(len(b)) + b.ljust((len(b) + 31) // 32 * 32, b'\0').hex()
def words(*ws): return ''.join(u256(int(w, 16) if isinstance(w, str) else w) for w in ws)
def generic(s, pm, amt, far):
    return [s + words(pm, amt, far, far, 0, 0), s + words(pm, A, amt, far, 0, 0), s + words(A, pm, amt, far, 0, 0), s + words(amt, pm, far, 0, 0, 0), s + words(pm, 0, 0, 0, 0, 0), s + words(0x20, 1, pm, 0, 0, 0)]
def named(nm, pm, amt, far):
    try: types = split_types(nm)
    except Exception: return None
    if not supported(types): return None
    apos = [i for i, t in enumerate(types) if t.split('[')[0] == 'address']
    if not apos: return []
    combos = [(k, far, False) for k in apos[:3]]
    if len(apos) >= 2: combos.append((-1, far, False))
    out = []; seen = set()
    for k, T, sw in combos:
        vals = []; nu = 0
        for i, t in enumerate(types):
            base = t.split('[')[0]
            if base == 'address': v = pm if (k == -1 or i == k) else A
            elif base.startswith(('uint', 'int')):
                bits = int(base.lstrip('uint') or 256)
                v = amt if nu == 0 else T
                if v > 2 ** (bits - 1) - 1: v = 1
                nu += 1
            elif base == 'bool': v = True
            elif base == 'string': v = 'x'
            elif base == 'bytes': v = b''
            else: v = b''
            if t.endswith('[]'): v = [v]
            elif t.endswith(']'): v = [v] * int(t[t.rindex('[') + 1:-1])
            vals.append(v)
        try: cd = sel(nm)[2:] + encode(types, vals)
        except Exception: continue
        if cd not in seen: seen.add(cd); out.append(cd)
    return out
def trigger(nm, amt):
    try: types = split_types(nm)
    except Exception: return []
    if len(types) > 2 or not all(t.startswith(('uint', 'int', 'bool')) and '[' not in t for t in types): return []
    if not TRIG.search(nm.split('(')[0]): return []
    return [sel(nm)[2:] + ''.join(u256(amt if t.startswith(('u', 'i')) and int(t.lstrip('uint') or 256) >= 128 else 1) for t in types)]
def plan(t, sels, pm, amt, far):
    out = []; seen = set()
    for s in sels:
        if s in JUNK: continue
        nms = SIG.get(s) or []
        cds = []
        if nms:
            got = False
            for nm in nms[:3]:
                v = named(nm, pm, amt, far)
                if v is None: cds += [(nm + '~g', c) for c in generic(s, pm, amt, far)]; got = True
                elif v: cds += [(nm, c) for c in v]; got = True
            if not got:
                for nm in nms[:2]: cds += [(nm, c) for c in trigger(nm, amt)]
        else: cds = [('?' + s, c) for c in generic(s, pm, amt, far)]
        for nm, c in cds:
            if c in seen: continue
            seen.add(c); out.append((nm, t, c))
    return out
def classify(base, w):
    if not w[2]: return None
    dPM = w[3] - base[3]; dA = w[4] - base[4]
    if dPM < 0: return 'lowered'
    if dPM > 0 and base[5] == 1 and w[5] == 0: return 'locked-assign'
    if dPM > 0 and dPM + dA > 0: return 'free-raise'
    if dPM > 0: return 'raise-paid'
    if base[5] == 1 and w[5] == 0: return 'lock-only'
    if base[5] == 0 and w[5] == 1: return 'unlock'
    if dA > 0: return 'A-gain'
    if w[7] != base[7]: return 'final-differs'
    return None
def run(cid, minusd=1.0, per=40, workers=6):
    pm = net(cid)['poolManager'].lower()
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']; S = jz(os.path.join(RAW7, 'sels_%d.json.gz' % cid))
    prev = set()
    fn = os.path.join(RAW6T, 'sweep_%d.json.gz' % cid)
    if os.path.exists(fn): prev = set(jz(fn)['tokens'])
    now = int(time.time()); far = now + 5 * 365 * 86400
    jobs = []; meta = {}
    for t, L in live.items():
        b = int(L['bal'] or 0)
        if t in prev or L['usd'] <= minusd or b < 3 or not (S.get(t) or {}).get('sels'): continue
        amt = b // 3
        pl = plan(t, S[t]['sels'][:400], pm, amt, far)
        meta[t] = dict(n=len(pl))
        base = ('BASE', t, sel('balanceOf(address)')[2:] + adr(pm))
        for i in range(0, max(1, len(pl)), per): jobs.append((t, amt, [base] + pl[i:i + per]))
    print(cid, net(cid)['name'], 'tokens', len(meta), 'covered in cycle 6', len(prev), 'trials', sum(m['n'] for m in meta.values()), 'calls', len(jobs), flush=True)
    res = collections.defaultdict(lambda: dict(base=None, hits=[], trials=0, ok=0, fail=0))
    gcap = 29_000_000 if cid == 999 else None
    def job(j):
        t, amt, ch = j
        data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + ''.join(item(adr(tg) + cd) for nm, tg, cd in ch)
        ov = {pm: {'code': MULTI}, A: {'code': FWD}}
        last = None
        for k in range(6):
            r = ecall(cid, pm, data, ov, gas=gcap or (200_000_000 if k < 2 else 45_000_000), rot=hash(t) + k, tries=1, timeout=120)
            if isinstance(r, str) and len(r) == 2 + 512 * len(ch):
                return j, [[int(r[2 + 512 * q + 64 * m: 66 + 512 * q + 64 * m], 16) for m in range(8)] for q in range(len(ch))], None
            last = str(r)[:150]; time.sleep(0.4 * (k + 1))
        return j, None, last
    done = 0
    with ThreadPoolExecutor(workers) as ex:
        for j, ws, err in ex.map(job, jobs):
            t, amt, ch = j; R = res[t]; done += 1
            if done % 500 == 0: print(cid, 'calls done', done, len(jobs), flush=True)
            if ws is None: R['fail'] += 1; R.setdefault('errs', []).append(err); continue
            base = ws[0]; R['base'] = [str(x) for x in base]
            for (nm, tg, cd), w in zip(ch[1:], ws[1:]):
                R['trials'] += 1
                if w[2]: R['ok'] += 1
                c = classify(base, w)
                if c: R['hits'].append(dict(fn=nm, cat=c, amt=str(amt), w=[str(x) for x in w], data=cd))
    out = {t: dict(sym=live[t]['sym'], usd=live[t]['usd'], n=meta[t]['n'], **res[t]) for t in meta}
    wz(os.path.join(RAW7, 'holder_%d.json.gz' % cid), dict(chainId=cid, now=now, minusd=minusd, tokens=out))
    cats = collections.Counter(h['cat'] for o in out.values() for h in o['hits'])
    print(cid, net(cid)['name'], 'tokens', len(out), 'trials', sum(o['trials'] for o in out.values()), 'accepted', sum(o['ok'] for o in out.values()), 'failed calls', sum(o['fail'] for o in out.values()), dict(cats), flush=True)
if __name__ == '__main__':
    mu = 1.0
    for c in sys.argv[1:]:
        if c.startswith('minusd='): mu = float(c[7:]); continue
        run(int(c), minusd=mu)
