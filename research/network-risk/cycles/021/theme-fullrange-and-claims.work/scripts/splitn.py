"""Cycle 21, unit theme-fullrange-and-claims, task 1 (L-945). N-part split form of a set 2 script (pmdiff2.py, seed
11_2026_11_24), generalising cycle 18's split.py (set 1, two parts) to set 2 and to more than two parts.

The script's calls c[0..n) run as eth_calls over ranges [k0,k1), [k1,k2), ... Each part except the last appends two
reads to the same unlock: extsload(bytes32[]) of every PoolManager storage slot that the reference interpreter
(pyevm.py) writes while running c[0..k_j), and exttload(bytes32[]) of every PoolManager transient slot it writes plus
the driver's delta slots of currency0, the token double and native. Values come from the network; only the key lists
come from pyevm. The next part places the PoolManager code again (balance 1e19 as in the reference) with all slot values
as stateDiff, and a preamble rebuilds the driver's transient deltas by mint (negative) and burn from an operator-approved
dummy (positive), ending with exttload of the same slots so the rebuilt values can be compared. Preamble and read records
are dropped and the rest is concatenated and hashed (sha256), which equals the unsplit answer if the split is faithful.

The split is only faithful when the transient state at each cut is the unlock flag, the delta count and the driver's
deltas. The script records every other PoolManager transient slot that pyevm wrote (otherTransient) and also requires
the hook's deltas to be zero at the cut; cuts must be chosen where the token and hook doubles' own transient
configuration is set again before it is used (a cfg or tset item follows before any use).

Usage: python3 splitn.py <url> <gas> <out.json> <script> <k1,k2,...> [label]
"""
import sys, os, json, hashlib, time, random
TOOLS = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, TOOLS)
import pmdiff as P  # noqa
import pmdiff2 as Q  # noqa
from evm import rpc, keccak  # noqa
from pyevm import World  # noqa

URL, GAS, OUT, IDX, CUTS = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), [int(x) for x in sys.argv[5].split(',')]
LABEL = sys.argv[6] if len(sys.argv) > 6 else ''
rnd = random.Random(11_2026_11_24); SC = [Q.script(rnd, i) for i in range(300)]
CODE = bytes.fromhex(open('/home/user/v4-core/research/network-risk/cycles/018/theme-full-range-swaps.work/raw/pm-fresh-code.hex').read())
assert hashlib.sha256(CODE).hexdigest().startswith('a7aaa3ba')
PMI = int(P.PM, 16); DRVI = int(P.DRV, 16)
DRVB, TOKB, HOOKB = Q.driver(), Q.token(), Q.hook()
w = P.w
S_EXTS = P.sel('extsload(bytes32[])'); S_EXTT = P.sel('exttload(bytes32[])')
DUMMY_M = 0xD0D0000000000000000000000000000000000001; DUMMY_B = 0xD0D0000000000000000000000000000000000002
def slot_map(key, base): return int.from_bytes(keccak(w(key) + w(base)), 'big')
OPER = int.from_bytes(keccak(w(DRVI) + w(slot_map(DUMMY_B, 3))), 'big')
def bal_slot(owner, id_): return int.from_bytes(keccak(w(id_) + w(slot_map(owner, 4))), 'big')
CURS = [P.C0, Q.TOKEN, 0]
DSL = {c: P.delta_slot(DRVI, c) for c in CURS}


def items(data):
    out = []; i = 0
    while True:
        n = int.from_bytes(data[i + 20:i + 22], 'big')
        if n == 0: return out
        out.append(data[i:i + 22 + n]); i += 22 + n


def pmitem(cd): return Q.item(PMI, cd)
def pack(its): return b''.join(its) + b'\0' * 22
def arr(sel, slots): return sel + w(32) + w(len(slots)) + b''.join(w(x) for x in slots)


class RecWorld(World):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.seen_s = set(); self.seen_t = set()
    def restore(self, snap):
        self.seen_s |= {s for (a, s) in self.storage if a == PMI}; self.seen_t |= {s for (a, s) in self.transient if a == PMI}
        super().restore(snap)


def keys_after(its):
    codes = {PMI: CODE, DRVI: DRVB, Q.TOKEN: TOKB}
    for f in Q.HOOK_FLAGS: codes[Q.HOOK_BASE | f] = HOOKB
    wd = RecWorld(codes, {PMI: 10 ** 19}); wd.max_steps = 400_000_000
    ok, ret = wd.call(0, DRVI, 0, pack(its), False, 0)
    wd.restore(wd.snapshot())  # fold the final state into the seen sets
    return sorted(wd.seen_s), sorted(wd.seen_t), ret, wd.steps


def ask(data, ov):
    last = None
    for k in range(5):
        try: return bytes.fromhex(rpc(URL, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(GAS)}, 'latest', ov], timeout=300)[2:])
        except Exception as e: last = str(e)[:300]; time.sleep(4 * (k + 1))
    raise RuntimeError(last)


def s256(x): return x - (1 << 256) if x >> 255 else x
def dec(rb): n = int.from_bytes(rb[32:64], 'big'); return [int.from_bytes(rb[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]


def base_ov(sd=None):
    ov = {P.PM: {'code': '0x' + CODE.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + DRVB.hex()},
          '0x' + Q.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + TOKB.hex()}}
    for f in Q.HOOK_FLAGS: ov['0x' + (Q.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + HOOKB.hex()}
    if sd: ov[P.PM]['stateDiff'] = sd
    return ov


def run():
    data, kinds, meta = SC[IDX]; its = items(data); assert len(its) == len(kinds)
    hk = Q.HOOK_BASE | meta['flags']
    bounds = [0] + CUTS + [len(its)]
    recs = []; parts = []; svals = {}; tvals = {}
    for j in range(len(bounds) - 1):
        a, b = bounds[j], bounds[j + 1]; last = (b == len(its))
        pre = []
        if j > 0:
            for cur in CURS:
                d = s256(tvals.get(DSL[cur], 0)); lim = (1 << 127) - 1
                while d != 0:
                    ch = min(abs(d), lim)
                    if d < 0: pre.append(pmitem(P.S_MINT + w(DUMMY_M) + w(cur) + w(ch))); d += ch
                    else: pre.append(pmitem(P.S_BURN + w(DUMMY_B) + w(cur) + w(ch))); d -= ch
            pre.append(pmitem(arr(S_EXTT, tq)))
            sd = {'0x' + s.to_bytes(32, 'big').hex(): '0x' + v.to_bytes(32, 'big').hex() for s, v in svals.items()}
            sd['0x' + OPER.to_bytes(32, 'big').hex()] = '0x' + (1).to_bytes(32, 'big').hex()
            for cur in CURS:
                bs = bal_slot(DUMMY_B, cur); assert bs not in svals
                sd['0x' + bs.to_bytes(32, 'big').hex()] = '0x' + (1 << 255).to_bytes(32, 'big').hex()
            ov = base_ov(sd)
        else:
            ov = base_ov()
        prev_tq = tq if j > 0 else None
        if not last:
            sslots, tslots, _, steps = keys_after(its[:b])
            hkd = [P.delta_slot(hk, c) for c in CURS]
            tq = sorted(set(tslots) | set(DSL.values()) | set(hkd))
            body = pre + its[a:b] + [pmitem(arr(S_EXTS, sslots)), pmitem(arr(S_EXTT, tq))]
        else:
            sslots, tslots, steps = [], [], None
            body = pre + its[a:b]
        t0 = time.time(); r = P.parse(ask(pack(body), ov)); dt = time.time() - t0
        np_ = len(pre)
        part = {'range': [a, b], 'preambleCalls': np_, 'records': len(r), 'seconds': round(dt, 1), 'pyevmSteps': steps}
        if j > 0:
            assert all(ok == 1 for ok, _ in r[:np_]), 'preamble failed'
            tB = dict(zip(prev_tq, dec(r[np_ - 1][1])))
            part['transientRebuiltEqual'] = all(tB[s] == tvals.get(s, 0) for s in prev_tq)
        body_recs = r[np_:np_ + (b - a)]
        assert len(body_recs) == b - a, ('short', len(body_recs), b - a)
        recs += body_recs
        if not last:
            assert r[-2][0] == 1 and r[-1][0] == 1, 'reads failed'
            svals = dict(zip(sslots, dec(r[-2][1]))); tvals = dict(zip(tq, dec(r[-1][1])))
            known = set(DSL.values()) | set(hkd)
            part['storageSlots'] = len(sslots)
            part['transientWrittenByPyevm'] = [hex(x) for x in tslots]
            part['transientValues'] = {hex(s): hex(v) for s, v in tvals.items()}
            part['hookDeltasZero'] = all(tvals[s] == 0 for s in hkd)
            part['otherNonzeroTransient'] = {hex(s): hex(v) for s, v in tvals.items() if s not in known and v != 0}
        parts.append(part)
        print('part', j, part['range'], 'records', len(r), 'pre', np_, 'rebuilt', part.get('transientRebuiltEqual'), 'hookZero', part.get('hookDeltasZero'),
              'other', part.get('otherNonzeroTransient'), f'{dt:.1f}s', flush=True)
    buf = b''.join(w(ok) + w(len(x)) + x for ok, x in recs)
    h = hashlib.sha256(buf).hexdigest()
    return {'script': IDX, 'cuts': CUTS, 'calls': len(its), 'parts': parts, 'hash': h, 'output': '0x' + buf.hex()}


def q(m, pr):
    last = ''
    for _k in range(6):
        try: return rpc(URL, m, pr)
        except Exception as e: last = str(e)[:100]; time.sleep(8)
    return 'ERR ' + last


res = json.load(open(OUT)) if os.path.exists(OUT) else {'url': URL, 'gas': GAS, 'label': LABEL, 'batches': [], 'runs': []}
bt = {'clientVersionBefore': q('web3_clientVersion', []), 'blockBefore': q('eth_blockNumber', []), 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
try: r = run()
except Exception as e: r = {'script': IDX, 'cuts': CUTS, 'error': repr(e)[:500]}
bt['clientVersionAfter'] = q('web3_clientVersion', []); bt['blockAfter'] = q('eth_blockNumber', []); bt['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
r['batch'] = bt
res['runs'].append(r); res['batches'].append(bt)
json.dump(res, open(OUT, 'w'), indent=1)
print('hash', r.get('hash'), r.get('error', ''), bt['clientVersionBefore'], bt['clientVersionAfter'])
