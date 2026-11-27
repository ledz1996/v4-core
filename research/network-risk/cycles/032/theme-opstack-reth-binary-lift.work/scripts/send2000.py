"""Send 2,000 of the model vectors (seeded sample, seed 3205, from the battery, targeted, fault-shape and v4math sets
that ran in the binary models) by eth_call to one endpoint per OP Stack chain with the battery dispatcher, bracketed by
web3_clientVersion. usage: python3 -I send2000.py <out.json>"""
import json, random, sys, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/scripts')
import battery, targeted, v4shapes
M = (1 << 256) - 1
V = [t for t in battery.vectors() if t[0] in battery.ID] + [t for t in targeted.vectors() if t[0] in battery.ID]
base = '/home/user/v4-core/research/network-risk/cycles/025/stablecoin-l1.work/'
for name in ('maxmod', 'maxmod2'):
    g = {'__file__': base + name + '.py', '__name__': name + '_v'}; exec(open(base + name + '.py').read().split("\nif __name__")[0], g)
    V += [('MULMOD', a, b, n) for a, b, n in g['vecs']()] + [('ADDMOD', a, b, n) for a, b, n in g['vecs']()]
V += [(op, a, b, c) for tag, op, a, b, c in v4shapes.vectors() if op in battery.ID]
rnd = random.Random(3205); S = rnd.sample(V, 2000)
code = battery.dispatcher()
EP = {10: 'https://mainnet.optimism.io', 8453: 'https://mainnet.base.org', 130: 'https://mainnet.unichain.org', 7777777: 'https://rpc.zora.energy/',
      480: 'https://worldchain-mainnet.g.alchemy.com/public', 57073: 'https://rpc-gel.inkonchain.com', 1868: 'https://rpc.soneium.org'}
def cv(url):
    r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}).encode(), {'Content-Type': 'application/json', 'User-Agent': 'curl/8'})
    try: return json.load(urllib.request.urlopen(r, timeout=60)).get('result')
    except Exception as e: return 'error ' + str(e)[:100]
out = {'seed': 3205, 'pool': len(V), 'sample': 2000, 'byOp': {}, 'chains': {}}
for t in S: out['byOp'][t[0]] = out['byOp'].get(t[0], 0) + 1
for cid, url in EP.items():
    before = cv(url); done, bad, errors = battery.run(url, code, S, size=200); after = cv(url)
    out['chains'][cid] = {'url': url, 'clientVersionBefore': before, 'clientVersionAfter': after, 'done': done, 'mismatches': bad, 'errors': errors}
    print(cid, before, after, 'done', done, 'mismatch', len(bad), 'errors', len(errors)); sys.stdout.flush()
json.dump(out, open(sys.argv[1], 'w'), indent=1)
