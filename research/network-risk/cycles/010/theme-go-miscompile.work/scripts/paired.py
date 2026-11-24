"""Runs the opdiff battery, the targeted vectors and a set aimed at the branch-selected
pointer in uint256 AddMod (x = &tmpX, y = &tmpY) and the sign branches of SDIV and SMOD,
on the endpoints whose node reports an affected Go toolchain. Every eth_call is sent in one
JSON-RPC batch with web3_clientVersion, so the build that answered each chunk is recorded.
Usage: python3 -I paired.py <out.json> [chainId ...]"""
import sys, json, random, subprocess, collections, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery, targeted
from evm import STUB, MASK
EPS = {42161: 'https://arb1.arbitrum.io/rpc', 4663: 'https://rpc.mainnet.chain.robinhood.com',
       137: 'https://polygon-bor-rpc.publicnode.com', 56: 'https://bsc-dataseed1.bnbchain.org',
       43114: 'https://api.avax.network/ext/bc/C/rpc'}
SIGN = 1 << 255
def u(x): return x & MASK
def shape_vectors(seed=81863):
    r = random.Random(seed); V = []
    for _ in range(6000):
        m = (r.getrandbits(64) | 1) << 192 | r.getrandbits(192)
        if r.random() < 0.2: m = MASK - r.getrandbits(r.choice((1, 8, 64)))
        def pick():
            k = r.random()
            if k < 0.25: return m + r.getrandbits(r.choice((1, 8, 64, 190))) if m + (1 << 190) < (1 << 256) else m
            if k < 0.5: return max(0, m - 1 - r.getrandbits(r.choice((1, 8, 64, 190))))
            if k < 0.6: return m
            if k < 0.7: return (m >> 192) << 192 | ((1 << 192) - 1)
            return ((m >> 192) - r.randrange(0, 2)) << 192 | r.getrandbits(192) if (m >> 192) else r.getrandbits(256)
        V.append(('ADDMOD', u(pick()), u(pick()), m))
    for _ in range(3000):
        for op in ('SDIV', 'SMOD'):
            a = r.getrandbits(r.choice((8, 64, 128, 255, 256))); b = r.getrandbits(r.choice((1, 8, 64, 128, 255, 256)))
            if r.random() < 0.5: a = u(-a)
            if r.random() < 0.5: b = u(-b)
            V.append((op, a, b, 0))
    for a in (0, 1, SIGN, SIGN + 1, MASK, MASK - 1, SIGN - 1):
        for b in (0, 1, 2, SIGN, MASK, MASK - 1, SIGN - 1, SIGN + 1):
            V += [('SDIV', a, b, 0), ('SMOD', a, b, 0)]
    return V
def call(url, code, data):
    body = json.dumps([{"jsonrpc": "2.0", "id": 1, "method": "web3_clientVersion", "params": []},
                       {"jsonrpc": "2.0", "id": 2, "method": "eth_call", "params": [{"to": STUB, "data": "0x" + data.hex()}, "latest", {STUB: {"code": "0x" + code.hex()}}]}])
    p = subprocess.run(['curl', '-s', '-m', '60', '-H', 'Content-Type: application/json', '--data-binary', '@-', url], input=body, capture_output=True, text=True)
    j = json.loads(p.stdout); d = {x['id']: x for x in j}
    if 'result' not in d[2]: raise Exception(json.dumps(d[2].get('error'))[:150])
    return d[1].get('result'), bytes.fromhex(d[2]['result'][2:])
def run(cid, sets, code, size=500, want_builds=1):
    url = EPS[cid]; builds = collections.Counter(); bad = []; done = 0; errors = []; perchunk = collections.Counter()
    for name, V in sets:
        for i in range(0, len(V), size):
            batch = V[i:i + size]; data = battery.encode(batch); exp = battery.expected(batch, data); seen = set(); tries = 0
            while len(seen) < want_builds and tries < (8 if want_builds > 1 else 3):
                tries += 1
                try: cv, res = call(url, code, data)
                except Exception as e:
                    if tries >= 3 and not seen: errors.append((name, i, str(e)[:150])); break
                    continue
                if len(res) != 32 * len(batch): errors.append((name, i, 'short')); continue
                if cv in seen: continue
                seen.add(cv); builds[cv] += 1
                for k, (t, e) in enumerate(zip(batch, exp)):
                    g = int.from_bytes(res[32 * k:32 * k + 32], 'big')
                    if g != e: bad.append({'set': name, 'build': cv, 'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(g), 'want': hex(e)})
                done += len(batch)
            perchunk[len(seen)] += 1
    return {'chainId': cid, 'rpc': url, 'vectorsRun': done, 'builds': dict(builds), 'chunksByBuildCount': dict(perchunk), 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:20]}
if __name__ == '__main__':
    out = sys.argv[1]; only = [int(x) for x in sys.argv[2:]] or list(EPS)
    code = battery.dispatcher()
    assert targeted.dispatcher() == code if hasattr(targeted, 'dispatcher') and targeted.dispatcher is not battery.dispatcher else True
    sets = [('shape', shape_vectors()), ('battery', battery.vectors()), ('targeted', targeted.vectors())]
    print({n: len(v) for n, v in sets}, flush=True)
    with cf.ThreadPoolExecutor(5) as ex:
        res = list(ex.map(lambda c: run(c, sets, code, want_builds=2 if c == 4663 else 1), only))
    for r in res: print(r['chainId'], r['vectorsRun'], r['builds'], r['chunksByBuildCount'], 'mismatches', r['mismatchCount'], 'errors', len(r['errors']), r['errors'][:2], flush=True)
    json.dump({'sets': {n: len(v) for n, v in sets}, 'results': res}, open(out, 'w'), indent=1)
