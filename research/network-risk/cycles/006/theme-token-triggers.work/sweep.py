# Step 2. For every token worth more than 1,000 USD at the PoolManager: call from an ordinary account A every selector of the
# token, of its implementation and of the contracts that balanceOf(PoolManager) touches, with the PoolManager as address
# argument. Each trial runs in eth_call with a measuring stub at the PoolManager address (state override): the stub hands one
# third of the balance to A, A makes the call, the stub reads balances and tries to send out the full balance. Trials are
# repeated with the block time moved forward by 8 hours, 91 days and 400 days (block override). Nothing is sent on chain.
import sys, json, gzip, os, re, collections
from concurrent.futures import ThreadPoolExecutor
from base import *
SIG = jz(os.path.join(RAW5, 'signatures.json.gz'))
if os.path.exists(os.path.join(RAW6, 'signatures_more.json.gz')): SIG.update(jz(os.path.join(RAW6, 'signatures_more.json.gz')))
DTS = [0, 8 * 3600, 91 * 86400, 400 * 86400]
JUNK = {'ffffffff', '4e487b71', '08c379a0', '00000000', '01ffc9a7'}
LOCKISH = re.compile(r'(?i)(lock|freez|frozen|vest|stak|bond|escrow|grant|hold|cooldown|restrict|allocat|reward|airdrop|distribut)')
TRIG = re.compile(r'(?i)(sweep|idle|inactiv|reflect|rebase|claim|process|distribut|harvest|accrue|update|poke|drip|sync|skim|expire|decay|burn|liquidat|collect|checkpoint|release|unlock|settle|epoch|trigger|execute|compound|tax|fee|swap)')
def item(p):
    b = bytes.fromhex(p); return u256(len(b)) + b.ljust((len(b) + 31) // 32 * 32, b'\0').hex()
def words(*ws): return ''.join(u256(int(w, 16) if isinstance(w, str) else w) for w in ws)
def generic(s, pm, amt, far):
    """Calldata shapes for a selector without a known signature."""
    return [s + words(pm, amt, far, far, 0, 0), s + words(pm, A, amt, far, 0, 0), s + words(A, pm, amt, far, 0, 0), s + words(amt, pm, far, 0, 0, 0),
            s + words(pm, 1, 1, 1, 1, 1), s + words(0x20, 1, pm, 0, 0, 0), s + words(0x40, 0x80, 1, pm, 1, amt), s + words(pm, 0, 0, 0, 0, 0)]
def named(nm, pm, amt, far):
    try: types = split_types(nm)
    except Exception: return None
    if not supported(types): return None
    apos = [i for i, t in enumerate(types) if t.split('[')[0] == 'address']
    if not apos: return []
    nuint = sum(1 for t in types if t.split('[')[0].startswith(('uint', 'int')))
    lock = bool(LOCKISH.search(nm.split('(')[0]))
    combos = [(k, far, False) for k in apos[:3]]
    if len(apos) >= 2: combos.append((-1, far, False))
    if lock and nuint >= 2: combos += [(apos[0], far, True), (apos[0], 400 * 86400, False), (apos[0], 400 * 86400, True), (apos[0], 1, False)]
    out = []; seen = set()
    for k, T, sw in combos:
        vals = []; nu = 0
        for i, t in enumerate(types):
            base = t.split('[')[0]
            if base == 'address': v = pm if (k == -1 or i == k) else A
            elif base.startswith(('uint', 'int')):
                bits = int(base.lstrip('uint') or 256)
                if nu == 0: v = T if sw else amt
                elif nu == 1: v = amt if sw else T
                else: v = T
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
def plan(t, o, pm, amt, far):
    """list of (label, target, calldata)"""
    out = []; seen = set()
    def add(target, s, src):
        if s in JUNK: return
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
            if (target, c) in seen: continue
            seen.add((target, c)); out.append((nm, target, c))
    for s in o.get('sels') or []: add(t, s, 'own')
    for a, r in (o.get('rel') or {}).items():
        k = r['kind']
        for s in r['sels']:
            if k == 'impl' or o.get('deleg'): add(t, s, 'impl')
            if k == 'acl': add(a, s, 'rel')
            if k.startswith('impl-of:'): add(k[8:], s, 'rel')
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
GASCAP = {999: 29_000_000}
# Mode B: the PoolManager sends nothing before the call, so its inactivity timers stay as they are on chain. A holds a
# balance written by state override (slot from slots.py). Same eight result words; word 1 is always 0.
from asm import _bal, _xfer
_TRIAL_B = (_bal('ADDRESS', '0x200') + '0 0x220 MSTORE' + '''
0x80 CALLDATASIZE SUB 0x80 0x400 CALLDATACOPY
0 0x1e0 MSTORE
0x20 0x1e0 0x80 CALLDATASIZE SUB 0x400 0 0x20 CALLDATALOAD GAS CALL
0x1e0 MLOAD AND 0x240 MSTORE
''' + _bal('ADDRESS', '0x260') + _bal('0x20 CALLDATALOAD', '0x280') + _xfer('0x60 CALLDATALOAD', '0x260 MLOAD', '0x2a0') + '0 0x2c0 MSTORE' + _bal('ADDRESS', '0x2e0'))
MULTI_B = assemble('''
CALLER ADDRESS EQ @trial JUMPI
0x80 0 0x1000 CALLDATACOPY
0x80 0x8000
loop:
DUP2 CALLDATASIZE GT ISZERO @end JUMPI
DUP2 CALLDATALOAD
DUP1 DUP4 0x20 ADD 0x1080 CALLDATACOPY
0x100 DUP3 DUP3 0x80 ADD 0x1000 0 ADDRESS 0x3d0900 CALL POP
0x1f ADD 0x1f NOT AND 0x20 ADD
SWAP2 DUP3 ADD SWAP2 POP
0x100 ADD
@loop JUMP
end:
0x8000 DUP2 SUB 0x8000 RETURN
trial:
''' + _TRIAL_B + '0x100 0x200 REVERT')
def run(cid, per=40, workers=6, only=None, dts=None, mode='A'):
    fn = os.path.join(RAW6, 'discover_%d.json.gz' % cid)
    disc = jz(fn); pm = net(cid)['poolManager'].lower()
    us = urls2(cid)
    tov = jz(os.path.join(RAW6, 'time_override.json')) if False else json.load(open(os.path.join(RAW6, 'time_override.json')))
    okus = [u for u in us if (tov.get(str(cid)) or {}).get(u, {}).get('ok')]
    dts = dts or (DTS if okus else [0])
    if not okus: okus = us
    now = int(time.time()); far = now + 5 * 365 * 86400
    jobs = []
    meta = {}
    slots = jz(os.path.join(RAW6, 'slots_%d.json.gz' % cid)) if mode in ('B', 'C') and os.path.exists(os.path.join(RAW6, 'slots_%d.json.gz' % cid)) else {}
    ovx = {}
    for t, o in disc.items():
        if only and t not in only: continue
        if 'err' in o: continue
        b = int(o['bal'])
        if b < 3: continue
        amt = b // 3
        if mode == 'C' and t in slots: continue
        if mode == 'B':
            if t not in slots: continue
            x = min(max(int(slots[t]['totalSupply']) // 10, b), 2 ** 95)
            ovx[t] = {slots[t]['holder']: {'stateDiff': {slots[t]['slot']: '0x' + u256(x)}}}
        pl = plan(t, o, pm, amt, far)
        meta[t] = dict(n=len(pl))
        base = ('BASE', t, sel('balanceOf(address)')[2:] + adr(pm))
        for dt in dts:
            for i in range(0, max(1, len(pl)), per):
                jobs.append((t, amt, dt, [base] + pl[i:i + per]))
    print(cid, net(cid)['name'], 'tokens', len(meta), 'trials per time', sum(m['n'] for m in meta.values()), 'calls', len(jobs), 'times', dts, 'urls', okus, flush=True)
    res = collections.defaultdict(lambda: dict(base={}, hits=[], trials=0, ok=0, fail=0))
    def job(j):
        t, amt, dt, ch = j
        data = '0x' + adr(t) + adr(A) + u256(amt if mode == 'A' else 0) + adr(SINK) + ''.join(item(adr(tg) + cd) for nm, tg, cd in ch)
        ov = {pm: {'code': MULTI if mode == 'A' else MULTI_B}, A: {'code': FWD}}
        for hd, v in ovx.get(t, {}).items(): ov[hd] = dict(ov.get(hd, {}), **v)
        last = None
        for k in range(7):
            u = okus[(hash(t) + k) % len(okus)]
            try:
                r = ecall_t(cid, u, pm, data, ov, gas=GASCAP.get(cid, 200_000_000 if k < 3 else 45_000_000), dt=dt, now=now, timeout=120)
            except Exception as e: last = str(e)[:150]; time.sleep(0.6 * (k + 1)); continue
            if isinstance(r, str) and len(r) == 2 + 512 * len(ch):
                return j, [[int(r[2 + 512 * q + 64 * m: 66 + 512 * q + 64 * m], 16) for m in range(8)] for q in range(len(ch))], None
            last = str(r)[:150]; time.sleep(0.5 * (k + 1))
        return j, None, last
    done = 0
    with ThreadPoolExecutor(workers) as ex:
        for j, ws, err in ex.map(job, jobs):
            t, amt, dt, ch = j; R = res[t]; done += 1
            if done % 500 == 0: print(cid, 'calls done', done, len(jobs), flush=True)
            if ws is None: R['fail'] += 1; R.setdefault('errs', []).append([dt, err]); continue
            base = ws[0]; R['base'].setdefault(str(dt), base)
            for (nm, tg, cd), w in zip(ch[1:], ws[1:]):
                R['trials'] += 1
                if w[2]: R['ok'] += 1
                c = classify(base, w)
                if c: R['hits'].append(dict(dt=dt, fn=nm, target=tg, cat=c, amt=str(amt), w=[str(x) for x in w], base=[str(x) for x in base], data=cd))
    out = {t: dict(sym=disc[t].get('sym'), usd=disc[t].get('usd'), n=meta[t]['n'], **{k: (v if k != 'base' else {a: [str(x) for x in b] for a, b in v.items()}) for k, v in res[t].items()}) for t in meta}
    sfx = '' if not only else '_part'
    json.dump(dict(chainId=cid, now=now, dts=dts, mode=mode, tokens=out), gzip.open(os.path.join(RAW6, 'sweep%s_%d%s.json.gz' % ('' if mode == 'A' else mode, cid, sfx), ), 'wt'))
    cats = collections.Counter(h['cat'] for o in out.values() for h in o['hits'])
    print(cid, net(cid)['name'], 'tokens', len(out), 'trials', sum(o['trials'] for o in out.values()), 'accepted', sum(o['ok'] for o in out.values()), 'failed calls', sum(o['fail'] for o in out.values()), dict(cats), flush=True)
if __name__ == '__main__':
    md = sys.argv[1] if sys.argv[1] in ('B', 'C') else 'A'
    for c in sys.argv[1:]:
        if c not in ('B', 'C'): run(int(c), mode=md)
