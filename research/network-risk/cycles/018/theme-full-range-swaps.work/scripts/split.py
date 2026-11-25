"""Split form of a set 1 script (pmdiff.py), for endpoints whose eth_call gas cap is below what the whole script needs.

The script's calls c[0..n) run in two eth_calls. Part A runs c[0..k) and then two reads appended to the same unlock:
extsload(bytes32[]) of every PoolManager storage slot that the reference interpreter (pyevm.py) writes while running
c[0..k), and exttload(bytes32[]) of every PoolManager transient slot it writes. The values come from the network, only
the list of slot keys comes from pyevm. Part B places the PoolManager code again with the slot values of part A as a
stateDiff, and runs a preamble that rebuilds the driver's transient currency deltas through mint (negative delta) and
burn from an operator-approved dummy (positive delta) in chunks of at most 2^127-1, then c[k..n). Its first records,
those of the preamble, are dropped. The records of part A before the reads and those of part B after the preamble are
concatenated and hashed, which gives the answer of the unsplit script if the split is faithful. The transient slots of
part A must be exactly the unlock flag, the delta count and the driver's deltas of the two currencies, which the
script checks; part B's preamble ends with exttload of those slots so the rebuilt values are compared with part A's.

Usage: python3 split.py <url> <gas> <out.json> <idx:k,idx:k,...>   (k = 'auto' splits after the heaviest-looking swap:
       the call after the first swap whose limit is a price edge)"""
import sys, os, json, hashlib, time, random
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
import pmdiff as P  # noqa
from evm import rpc, keccak, MASK  # noqa
from pyevm import World  # noqa

URL, GAS, OUT, SPEC = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
rnd = random.Random(7_2026_11_24); SC = [P.script(rnd) for _ in range(250)]
REF = json.load(open(os.path.join(TOOLS, '..', '..', 'opcodes', 'pmdiff.json')))['referenceHashes']
_CF = os.path.join(HERE, '..', 'raw', 'pm-fresh-code.hex')
if not os.path.exists(_CF):
    for _k in range(6):
        try: open(_CF, 'w').write(P.fetch_code().hex()); break
        except Exception: time.sleep(10)
CODE = bytes.fromhex(open(_CF).read()); DRVB = P.driver(); PMI = int(P.PM, 16); DRVI = int(P.DRV, 16)
w = P.w
S_EXTS = P.sel('extsload(bytes32[])'); S_EXTT = P.sel('exttload(bytes32[])')
DUMMY_M = 0xD0D0000000000000000000000000000000000001; DUMMY_B = 0xD0D0000000000000000000000000000000000002
def slot_map(key, base): return int.from_bytes(keccak(w(key) + w(base)), 'big')
OPER = int.from_bytes(keccak(w(DRVI) + w(slot_map(DUMMY_B, 3))), 'big')
def bal_slot(owner, id_): return int.from_bytes(keccak(w(id_) + w(slot_map(owner, 4))), 'big')


def items(data):
    out = []; i = 0
    while True:
        n = int.from_bytes(data[i:i + 2], 'big')
        if n == 0: return out
        out.append(data[i + 2:i + 2 + n]); i += 2 + n


def pack(calls): return b''.join(len(c).to_bytes(2, 'big') + c for c in calls) + b'\0\0'
def arr(sel, slots): return sel + w(32) + w(len(slots)) + b''.join(w(x) for x in slots)


class RecWorld(World):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.seen_s = set(); self.seen_t = set()
    def restore(self, snap):
        self.seen_s |= {s for (a, s) in self.storage if a == PMI}; self.seen_t |= {s for (a, s) in self.transient if a == PMI}
        super().restore(snap)


def keys_after(calls):
    wd = RecWorld({PMI: CODE, DRVI: DRVB}); wd.max_steps = 400_000_000
    ok, ret = wd.call(0, DRVI, 0, pack(calls), False, 0)
    return sorted(wd.seen_s), sorted(wd.seen_t), ret


def ask(data, ov):
    last = None
    for k in range(5):
        try: return bytes.fromhex(rpc(URL, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(GAS)}, 'latest', ov], timeout=200)[2:])
        except Exception as e: last = str(e)[:300]; time.sleep(4 * (k + 1))
    raise RuntimeError(last)


def s256(x): return x - (1 << 256) if x >> 255 else x


def run(idx, k):
    data, kinds, meta = SC[idx]; calls = items(data); assert len(calls) == len(kinds)
    if k == 'auto':
        k = None
        for j, (kd, c) in enumerate(zip(kinds, calls)):
            if kd == 'swap':
                lim = int.from_bytes(c[4 + 32 * 7:4 + 32 * 8], 'big')
                if lim in (P.m.MIN_SQRT_PRICE + 1, P.m.MAX_SQRT_PRICE - 1): k = j + 1; break
        assert k is not None
    k = int(k)
    sslots, tslots, _ = keys_after(calls[:k])
    dC0 = P.delta_slot(DRVI, P.C0); dC1 = P.delta_slot(DRVI, P.C1)
    lock_slot = int.from_bytes(keccak(b'Unlocked'), 'big') - 1 if False else None
    # part A
    ovA = {P.PM: {'code': '0x' + CODE.hex()}, P.DRV: {'code': '0x' + DRVB.hex()}}
    tq = sorted(set(tslots) | {dC0, dC1})
    a = P.parse(ask(pack(calls[:k] + [arr(S_EXTS, sslots), arr(S_EXTT, tq)]), ovA))
    assert len(a) == k + 2 and a[k][0] == 1 and a[k + 1][0] == 1, 'part A reads failed'
    def dec(rb): n = int.from_bytes(rb[32:64], 'big'); return [int.from_bytes(rb[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]
    svals = dict(zip(sslots, dec(a[k][1]))); tvals = dict(zip(tq, dec(a[k + 1][1])))
    other_t = {hex(s): v for s, v in tvals.items() if s not in (dC0, dC1)}
    # part B
    pre = []
    for cur, sl in ((P.C0, dC0), (P.C1, dC1)):
        d = s256(tvals[sl]); lim = (1 << 127) - 1
        while d != 0:
            ch = min(abs(d), lim)
            if d < 0: pre.append(P.S_MINT + w(DUMMY_M) + w(cur) + w(ch)); d += ch
            else: pre.append(P.S_BURN + w(DUMMY_B) + w(cur) + w(ch)); d -= ch
    pre.append(arr(S_EXTT, tq))
    sd = {'0x' + s.to_bytes(32, 'big').hex(): '0x' + v.to_bytes(32, 'big').hex() for s, v in svals.items()}
    sd['0x' + OPER.to_bytes(32, 'big').hex()] = '0x' + (1).to_bytes(32, 'big').hex()
    for cur in (P.C0, P.C1):
        bs = bal_slot(DUMMY_B, cur); assert bs not in svals
        sd['0x' + bs.to_bytes(32, 'big').hex()] = '0x' + (1 << 255).to_bytes(32, 'big').hex()
    ovB = {P.PM: {'code': '0x' + CODE.hex(), 'stateDiff': sd}, P.DRV: {'code': '0x' + DRVB.hex()}}
    b = P.parse(ask(pack(pre + calls[k:]), ovB))
    np_ = len(pre)
    assert all(ok == 1 for ok, _ in b[:np_]), 'preamble failed'
    tB = dict(zip(tq, dec(b[np_ - 1][1])))
    rebuilt = {hex(s): [tvals[s], tB[s]] for s in tq}
    recs = a[:k] + b[np_:]
    buf = b''.join(w(ok) + w(len(r)) + r for ok, r in recs)
    return {'k': k, 'calls': len(calls), 'storageSlots': len(sslots), 'transientSlotsA': [hex(x) for x in tslots],
            'transientA': {hex(s): hex(v) for s, v in tvals.items()}, 'transientRebuiltEqual': all(x == y for x, y in rebuilt.values()),
            'preambleCalls': np_, 'hash': hashlib.sha256(buf).hexdigest(), 'equalsStored25M': hashlib.sha256(buf).hexdigest() == REF[idx],
            'output': '0x' + buf.hex(), 'otherTransient': other_t}


def q(m, pr):
    for _k in range(6):
        try: return rpc(URL, m, pr)
        except Exception as e: last = str(e)[:100]; time.sleep(8)
    return 'ERR ' + last


res = json.load(open(OUT)) if os.path.exists(OUT) else {'url': URL, 'gas': GAS, 'batches': [], 'scripts': {}}
bt = {'clientVersionBefore': q('web3_clientVersion', []), 'blockBefore': q('eth_blockNumber', []), 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'spec': SPEC}
for part in SPEC.split(','):
    i, k = part.split(':'); i = int(i)
    try: r = run(i, k)
    except Exception as e: r = {'error': str(e)[:400]}
    res['scripts'][str(i)] = r
    print(i, 'k', r.get('k'), 'of', r.get('calls'), 'slots', r.get('storageSlots'), 'tA', len(r.get('transientSlotsA', [])), 'rebuilt', r.get('transientRebuiltEqual'), 'hash', r.get('hash', '')[:16], 'stored25M', r.get('equalsStored25M'), r.get('error', ''), flush=True)
bt['clientVersionAfter'] = q('web3_clientVersion', []); bt['blockAfter'] = q('eth_blockNumber', []); bt['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
res['batches'].append(bt)
json.dump(res, open(OUT, 'w'), indent=1)
