"""Task 2: Arc, per-request build pinning. On each endpoint, ROUNDS rounds of: arc_getVersion, TokenRollbackProbe on the
USDC ERC-20 face (mode 0), arc_getVersion, TokenRollbackProbe on native value with the face read (mode 1), arc_getVersion.
A probe answer is attributed to a build only when the versions read just before and just after it name the same commit.
Read-only eth_call with a code override at the PoolManager address. usage: python3 -I arcpin.py <out.json> <rounds> <url>..."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc
from evm import keccak
B = json.load(open('/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/build/TokenRollbackProbe.json'))
PM = '0x8366a39CC670B4001A1121B8F6A443A643e40951'; USDC = '0x3600000000000000000000000000000000000000'; TO = '0x000000000000000000000000000000000dead032'
def w(x): return x.to_bytes(32, 'big').hex()
SEL = keccak(b'run(address,address,uint256,uint256)')[:4].hex()
def ver(u):
    r = rpc(u, 'arc_getVersion', [], 30); return (r.get('result') or {}).get('git_short_hash', 'ERR:' + json.dumps(r)[:80])
def probe(u, mode):
    data = '0x' + SEL + w(int(USDC, 16)) + w(int(TO, 16)) + w(1) + w(mode)
    r = rpc(u, 'eth_call', [{'from': '0x00000000000000000000000000000000000a11ce', 'to': PM, 'data': data, 'gas': hex(20_000_000)}, 'latest', {PM: {'code': '0x' + B['runtime']}}], 120)
    if 'result' not in r: return {'err': r}
    b = bytes.fromhex(r['result'][2:]); ws = [int.from_bytes(b[i:i + 32], 'big') for i in range(64, len(b), 32)]
    rows = [ws[i:i + 10] for i in range(0, len(ws), 10)]
    return {'leaks': [x[0] for x in rows if x[0] != 0 and x[2:6] != x[6:10]], 'controlMoved': [x for x in rows if x[0] == 0][0][2:6] != [x for x in rows if x[0] == 0][0][6:10],
            'staticRefused': [x for x in rows if x[0] == 9][0][1] == 0, 'rows': [[str(v) for v in x] for x in rows]}
out = {'rounds': int(sys.argv[2]), 'endpoints': {}}
for u in sys.argv[3:]:
    recs = []; per = {}
    for i in range(int(sys.argv[2])):
        v0 = ver(u); a = probe(u, 0); v1 = ver(u); b = probe(u, 1); v2 = ver(u)
        for p, (x, y) in ((a, (v0, v1)), (b, (v1, v2))):
            key = x if x == y else f'unpinned {x}/{y}'
            d = per.setdefault(key, {'runs': 0, 'ok': 0, 'err': 0})
            d['runs'] += 1
            if 'err' in p: d['err'] += 1
            elif not p['leaks'] and p['controlMoved'] and p['staticRefused']: d['ok'] += 1
        recs.append({'v': [v0, v1, v2], 'face': a, 'native': b})
    out['endpoints'][u] = {'byBuild': per, 'records': recs}
    print(u, per)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
