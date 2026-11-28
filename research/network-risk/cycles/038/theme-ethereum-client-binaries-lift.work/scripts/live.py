"""Cycle 38, Task 5 second part: 2,000 of the model vectors by eth_call (state override, read-only) to one public
Ethereum endpoint per client release, each batch bracketed by web3_clientVersion. The vectors are drawn with seed
38_1128_05 from the sets the models ran (drive.py generators: targeted, v4shapes, ruint121, provevec, pow2, random),
restricted to the opcodes of the battery dispatcher.
usage: python3 -I live.py <out.json> <url> [<url> ...]"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery as B
OUT, OUTARGS = sys.argv[1], sys.argv[2:]
from evm import rpc
src = open(os.path.join(HERE, 'drive.py')).read(); src = src[:src.index('fspec = F.get')]
pool = []
for s in ('targeted', 'v4shapes', 'ruint121', 'provevec', 'pow2', 'random'):
    sys.argv[1:] = ['geth-amd64', s, '0', '1', '/dev/null']
    os.environ['NRAND'] = '2000'
    g = {'__name__': 'gen', '__file__': os.path.join(HERE, 'drive.py')}
    exec(compile(src, 'drive.py', 'exec'), g)
    pool += [(s, op, a, b, c) for tag, op, a, b, c in g['GEN'][s]() if op in B.ID]
rnd = random.Random(381128_05)
V = rnd.sample(pool, 2000)
out = {'seed': 381128_05, 'pool': len(pool), 'vectors': len(V), 'bySet': {}, 'results': []}
for s, *_ in V:
    out['bySet'][s] = out['bySet'].get(s, 0) + 1
code = B.dispatcher()
for url in OUTARGS:
    r = {'rpc': url, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    try:
        r['clientVersionBefore'] = rpc(url, 'web3_clientVersion', [], 30)
    except Exception as e:
        r['clientVersionBefore'] = 'ERR ' + str(e)[:200]
    done, bad, errors = B.run(url, code, [v[1:] for v in V], size=200)
    try:
        r['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [], 30)
    except Exception as e:
        r['clientVersionAfter'] = 'ERR ' + str(e)[:200]
    r.update({'ran': done, 'mismatchCount': len(bad), 'mismatches': bad, 'errors': errors})
    print(url, r['clientVersionBefore'], r['clientVersionAfter'], 'ran', done, 'mismatches', len(bad), 'errors', len(errors), errors[:2], flush=True)
    out['results'].append(r)
json.dump(out, open(OUT, 'w'), indent=1)
