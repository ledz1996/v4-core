# Fetch harness dependencies from raw.githubusercontent.com into dl/<name>, using the path lists of the cycle 16 copies,
# and report which fetched files differ from the cycle 16 copies. Usage: fetchsrc.py
import os, sys, hashlib, urllib.request, concurrent.futures as cf, json
W16 = '/home/user/v4-core/research/network-risk/cycles/016/theme-monad-harness-exact.work/dl/'
OUT = '/home/user/v4-core/research/network-risk/cycles/023/theme-monad-compiled-coverage.work/dl/'
JOBS = [  # (local dir, cycle16 dir, repo, ref, path prefix inside repo)
    ('monad-0.16.7', 'monad', 'category-labs/monad', 'v0.16.7', ''),
    ('monad-0.16.5', 'monad-0.16.5', 'category-labs/monad', 'v0.16.5', ''),
    ('asmjit', 'asmjit', 'asmjit/asmjit', 'e8c8e2e48a1a38154c8e8864eb3bc61db80a1e31', ''),
    ('evmc-f6b7c57e', 'evmc', 'category-labs/evmc', 'f6b7c57e071d4eb0020d2cda3aee51e05ad8c726', ''),
    ('evmc-34795f4e', 'evmc165', 'category-labs/evmc', '34795f4eb4fd43cf8212d2b525a359236bad891c', ''),
    ('third', 'third', 'category-labs/monad', 'v0.16.7', 'third_party/'),
    ('openssl', 'openssl', 'category-labs/monad', 'v0.16.7', 'third_party/openssl/'),
]
res = {}
def get(job, rel):
    loc, c16, repo, ref, pre = job
    url = f'https://raw.githubusercontent.com/{repo}/{ref}/{pre}{rel}'
    p = OUT + loc + '/' + rel
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        for i in range(3):
            try:
                data = urllib.request.urlopen(url, timeout=60).read(); open(p, 'wb').write(data); break
            except Exception as e:
                err = str(e)
        else:
            return (loc, rel, 'FAIL ' + err, url)
    a = open(p, 'rb').read(); b = open(W16 + c16 + '/' + rel, 'rb').read()
    return (loc, rel, 'same' if a == b else 'differs', url)
tasks = []
for job in JOBS:
    base = W16 + job[1]
    for d, _, fs in os.walk(base):
        for f in fs:
            tasks.append((job, os.path.relpath(os.path.join(d, f), base)))
with cf.ThreadPoolExecutor(16) as ex:
    out = list(ex.map(lambda t: get(*t), tasks))
summ = {}
for loc, rel, st, url in out:
    summ.setdefault(loc, {}).setdefault(st.split()[0], 0); summ[loc][st.split()[0]] += 1
json.dump({'summary': summ, 'files': out}, open(OUT + 'fetch-report.json', 'w'), indent=0)
print(summ)
for o in out:
    if o[2] != 'same': print(o)
