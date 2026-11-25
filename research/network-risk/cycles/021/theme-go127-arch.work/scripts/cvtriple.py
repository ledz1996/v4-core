# Does the middle element of a three element batch share the backend architecture of the two bracket elements?
# Sends [web3_clientVersion]*n batches and records the architecture of every position. Output: raw/cvtriple-<chain>.json
import sys, json, time, collections
sys.path.insert(0, '.')
from rpcp import rpcb, arch
url, tag, n, width = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
rows = []
for i in range(n):
    r = rpcb(url, [('web3_clientVersion', [])] * width)
    rows.append([arch(x) for x in r] if isinstance(r, list) else {'err': str(r)[:200]})
    time.sleep(0.15)
ok = [r for r in rows if isinstance(r, list)]
c = collections.Counter(); m = collections.Counter()
for r in ok:
    if width == 3:
        c[(r[0], r[1], r[2])] += 1
        if r[0] == r[2]: m['brackets agree, middle same' if r[1] == r[0] else 'brackets agree, middle differs'] += 1
pos = [collections.Counter(r[k] for r in ok) for k in range(width)]
out = {'url': url, 'batches': n, 'answered': len(ok), 'width': width, 'patterns': {str(k): v for k, v in c.items()}, 'middleVsBrackets': dict(m), 'perPosition': [dict(p) for p in pos], 'rows': rows, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
json.dump(out, open(f'../raw/cvtriple-{tag}.json', 'w'), indent=0)
print(json.dumps({k: v for k, v in out.items() if k != 'rows'}))
