"""L-1317: the 20 reentry scenarios of cycle 36 (theme-erigon-main-frame-cache scripts/rpcshapes.py,
same seed) sent R rounds through one rotating gateway, with a separate web3_clientVersion sample
after every call to measure which backends were in rotation. A gateway splits batches per element,
so a single answer cannot be tied to a backend; the result is statistical. Read-only calls only.
usage: PM_BUILD=... python3 -I rpcshapes_rounds.py out.json n rounds url"""
import sys, os, json, random, hashlib, time, collections
S36 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '036', 'theme-erigon-main-frame-cache.work', 'scripts')
sys.path.insert(0, S36)
sys.path.insert(1, os.path.join(S36, '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc
import pmdiff as P
import pmshapes as X
import rpcshapes as R

out, n, rounds, url = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
pm = P.fetch_code(); rnd = random.Random(36_2026_11_27 + 1)
scen = [X.scenario(rnd, i) for i in range(n)]
refs = []
for desc, data, hook in scen:
    rw, ok, ret = X.run(X.RefWorld, pm, hook, data); refs.append((ok, ret))
res = {'seed': 36_2026_11_27 + 1, 'n': n, 'rounds': rounds, 'url': url, 'pmCodeSha256': hashlib.sha256(pm).hexdigest(),
       'startedUtc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'agree': 0, 'differ': 0, 'noAnswer': 0,
       'rotation': collections.Counter(), 'records': []}
for rd in range(rounds):
    for (desc, data, hook), (ok, ref) in zip(scen, refs):
        kind, got, msg = R.ask(url, data, R.overrides(pm, hook))
        try: cv = rpc(url, 'web3_clientVersion', [])
        except Exception as ex: cv = 'ERR ' + str(ex)[:100]
        res['rotation'][cv] += 1
        r = {'round': rd, 'desc': desc, 'kind': kind, 'msg': msg, 'cvAfter': cv,
             'refSha256': hashlib.sha256(ref).hexdigest(), 'gotSha256': hashlib.sha256(got).hexdigest() if got is not None else None}
        if got is None: res['noAnswer'] += 1
        elif got == ref and kind == ('ok' if ok else 'revert'): res['agree'] += 1
        else: res['differ'] += 1; r['got'] = got.hex()
        res['records'].append(r)
        time.sleep(0.3)
    print('round', rd, 'agree', res['agree'], 'differ', res['differ'], 'noAnswer', res['noAnswer'], dict(res['rotation']), flush=True)
res['endedUtc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(res, open(out, 'w'), indent=1)
