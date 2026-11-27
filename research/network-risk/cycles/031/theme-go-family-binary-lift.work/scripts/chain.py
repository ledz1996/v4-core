"""Cycle 31 copy of the cycle 30 chain.py. Task 5b: 2,000 of the model vectors sent to BNB Smart Chain, Polygon and
Avalanche by eth_call (read only), through the
battery dispatcher of tools/opdiff placed by state override, bracketed by web3_clientVersion. Each chunk is sent
twice. Sample seed 31_0731_05: 400 each from random, v4shapes, targeted, c27 and battery.
usage: python3 -I chain.py <out.json>"""
import json, os, random, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery as B
from evm import call_code, rpc

NETS = [(56, 'https://bsc-dataseed1.bnbchain.org'), (56, 'https://bsc-rpc.publicnode.com'), (137, 'https://polygon-bor-rpc.publicnode.com'),
        (43114, 'https://api.avax.network/ext/bc/C/rpc')]
OUT = sys.argv[1]
sys.argv = [sys.argv[0], 'bsc-amd64', 'random', '0', '1', '/dev/null']
os.environ.setdefault('NRAND', '2000')


def gen(setname):
    import importlib
    sys.argv[2] = setname
    g = {'__name__': 'drive_gen', '__file__': os.path.join(HERE, 'drive.py')}
    src = open(os.path.join(HERE, 'drive.py')).read().split('\nGEN = ')[0]
    src = src.replace('import models, goshim as G, targets\nimport faults as F\n', 'import goshim as G\n')
    exec(src, g)
    return g


g = gen('random')
rnd = random.Random(310731_05)
V = []
for name, fn in (('random', g['rand']), ('v4shapes', g['v4shapes']), ('targeted', g['targeted']), ('c27', g['c27']), ('battery', g['battery'])):
    allv = list(fn())
    pick = rnd.sample(allv, 400)
    V += [(t[1], t[2], t[3], t[4], name) for t in pick]


def cv(url):
    try:
        return rpc(url, 'web3_clientVersion', [])
    except Exception as e:
        return 'ERROR %s' % e


code = B.dispatcher()
res = {'vectors': len(V), 'seed': 310731_05, 'bySet': {}, 'results': []}
for t in V:
    res['bySet'][t[4]] = res['bySet'].get(t[4], 0) + 1
batch = [(o, a, b, c) for o, a, b, c, _ in V]
for cid, url in NETS:
    r = {'chainId': cid, 'rpc': url, 'passes': []}
    for p in range(2):
        before = cv(url); t0 = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        done, bad, errors = B.run(url, code, batch, size=200)
        after = cv(url)
        r['passes'].append({'time': t0, 'clientVersionBefore': before, 'clientVersionAfter': after, 'ran': done,
                            'mismatches': bad, 'errors': errors})
        print(cid, p, before, done, len(bad), errors[:1], after, flush=True)
    res['results'].append(r)
json.dump(res, open(OUT, 'w'), indent=1)
