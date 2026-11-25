# Task 3 (L-938): battery.py, targeted.py and pmdiff2.py on Arbitrum One and Robinhood Chain, every chunk sent as the
# batch [web3_clientVersion, eth_call, web3_clientVersion]. A chunk is "kept" for an architecture only when both
# bracket strings name it. Every answer, kept or not, is also checked against the specification (battery, targeted)
# or the Ethereum reference hash of cycle 20 (pmdiff2), so a fault on either architecture shows up in the full count.
# Vector sets are the tools' own: battery seed 20261124, targeted seed 681, pmdiff2 seed 11_2026_11_24 with 300 scripts.
# MINANS=<k> keeps sending until a job has at least k answers (second Robinhood pass: independent per-element routing).
# Usage: pinned.py <chainId> <url> <maxAttempts> <out.json>
import sys, os, json, time, threading, hashlib, random, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('PM_FROM', '42161')
import battery as B, targeted as T, pmdiff as P, pmdiff2 as P2
from evm import STUB
from rpcp import rpcb, arch
cid, url, maxatt, outp = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4]
ARCHS = ('linux-arm64', 'linux-amd64')
jobs = []
code = B.dispatcher()
for name, mod in (('battery', B), ('targeted', T)):
    V = mod.vectors()
    for i in range(0, len(V), 600):
        b = V[i:i + 600]; d = B.encode(b)
        jobs.append({'set': name, 'idx': i, 'n': len(b), 'tx': {'to': STUB, 'data': '0x' + d.hex()}, 'ov': {STUB: {'code': '0x' + code.hex()}},
                     'check': ('vec', b, B.expected(b, d))})
rnd = random.Random(11_2026_11_24)
scripts = [P2.script(rnd, i) for i in range(300)]
pmcode = P.fetch_code(); drv = P2.driver(); tok = P2.token(); hk = P2.hook()
ov2 = {P.PM: {'code': '0x' + pmcode.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + drv.hex()},
       '0x' + P2.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + tok.hex()}}
for f in P2.HOOK_FLAGS: ov2['0x' + (P2.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + hk.hex()}
ref = json.load(open('/home/user/v4-core/research/network-risk/cycles/020/arbitrum-family.work/raw/pmdiff2.json'))['referenceHashes']
for k, (data, kinds, meta) in enumerate(scripts):
    jobs.append({'set': 'pmdiff2', 'idx': k, 'n': 1, 'tx': {'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'ov': ov2, 'check': ('hash', ref[k])})
lock = threading.Lock(); stats = {'requests': 0, 'errors': 0, 'errorSamples': [], 'bracketPairs': {}, 'clientStrings': {}}
recs = {}  # (set, idx) -> list of attempts
def check(job, res):
    kind = job['check'][0]
    if kind == 'vec':
        _, b, e = job['check']; got = bytes.fromhex(res[2:])
        if len(got) != 32 * len(b): return [{'short': len(got)}]
        bad = []
        for k, (t, w) in enumerate(zip(b, e)):
            g = int.from_bytes(got[32 * k:32 * k + 32], 'big')
            if g != w: bad.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(g), 'want': hex(w)})
        return bad
    h = hashlib.sha256(bytes.fromhex(res[2:])).hexdigest()
    return [] if h == job['check'][1] else [{'hash': h, 'ref': job['check'][1], 'answer': res}]
def attempt(job):
    r = rpcb(url, [('web3_clientVersion', []), ('eth_call', [job['tx'], 'latest', job['ov']]), ('web3_clientVersion', [])])
    with lock: stats['requests'] += 1
    if not isinstance(r, list) or len(r) != 3 or not isinstance(r[1], str):
        with lock:
            stats['errors'] += 1
            if len(stats['errorSamples']) < 30: stats['errorSamples'].append(str(r)[:300])
        return None
    a0, a2 = arch(r[0]), arch(r[2])
    with lock:
        k = f'{a0}|{a2}'; stats['bracketPairs'][k] = stats['bracketPairs'].get(k, 0) + 1
        for s in (r[0], r[2]): stats['clientStrings'][s] = stats['clientStrings'].get(s, 0) + 1
    return {'c0': a0, 'c2': a2, 'kept': a0 if a0 == a2 else None, 'bad': check(job, r[1]), 't': time.strftime('%H:%M:%S', time.gmtime())}
def worker(job):
    key = (job['set'], job['idx']); got = set(); n = 0; fails = 0
    while n < maxatt and fails < 6:
        a = attempt(job)
        if a is None: fails += 1; time.sleep(2 * fails); continue
        n += 1
        with lock: recs.setdefault(key, []).append(a)
        if a['kept']: got.add(a['kept'])
        if all(x in got for x in ARCHS) and n >= int(os.environ.get('MINANS', '0')): break
        if cid == 42161 and 'linux-arm64' in got and n >= 2: break  # Arbitrum One answers arm64 only (cvtriple); two tries
        time.sleep(0.2)
t0 = time.time()
with cf.ThreadPoolExecutor(6) as ex: list(ex.map(worker, jobs))
per = {}
for job in jobs:
    L = recs.get((job['set'], job['idx']), [])
    for a in ARCHS:
        p = per.setdefault(f"{job['set']}|{a}", {'jobsKept': 0, 'vectorsKept': 0, 'mismatchesKept': 0})
        kept = [x for x in L if x['kept'] == a]
        if kept:
            p['jobsKept'] += 1; p['vectorsKept'] += job['n']; p['mismatchesKept'] += len(kept[0]['bad'])
    q = per.setdefault(f"{job['set']}|all-answers", {'answers': 0, 'vectorAnswers': 0, 'mismatches': 0, 'jobsAnswered': 0})
    q['answers'] += len(L); q['vectorAnswers'] += job['n'] * len(L); q['mismatches'] += sum(len(x['bad']) for x in L); q['jobsAnswered'] += 1 if L else 0
missing = {a: [f"{j['set']}:{j['idx']}" for j in jobs if not any(x['kept'] == a for x in recs.get((j['set'], j['idx']), []))] for a in ARCHS}
allbad = [[s, i, x] for (s, i), L in recs.items() for x in L if x['bad']]
out = {'chainId': cid, 'url': url, 'maxAttempts': maxatt, 'jobs': len(jobs), 'jobsPerSet': {s: sum(1 for j in jobs if j['set'] == s) for s in ('battery', 'targeted', 'pmdiff2')},
       'vectorsPerSet': {s: sum(j['n'] for j in jobs if j['set'] == s) for s in ('battery', 'targeted', 'pmdiff2')},
       'seconds': round(time.time() - t0), 'stats': stats, 'perSetArch': per, 'missingKeptCount': {a: len(v) for a, v in missing.items()}, 'missingKept': missing,
       'mismatchRecords': allbad, 'attempts': {f'{s}:{i}': [{k: v for k, v in x.items() if k != 'bad'} | {'nbad': len(x['bad'])} for x in L] for (s, i), L in recs.items()}}
json.dump(out, open(outp, 'w'), indent=0)
print(json.dumps({k: v for k, v in out.items() if k not in ('attempts', 'missingKept', 'mismatchRecords')}, indent=1)[:4000]); print('mismatch records', len(allbad))
