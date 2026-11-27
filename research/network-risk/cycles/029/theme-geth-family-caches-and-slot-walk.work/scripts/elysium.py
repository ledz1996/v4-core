"""Task 2 (L-1173): a vector set for Elysium (chain 99901), the only network whose node reports go1.25.12.
Sent through the dispatcher of tools/opdiff/battery.py by eth_call with a state override (read-only).
Vectors: the edge and Knuth-boundary families of u256vectors.py (seed 29_2026_11_27) mapped to battery ops,
weighted towards the code shapes that the go1.25.13 to go1.27.4 compiler fixes concern and that occur in
holiman/uint256 v1.3.2: signed int division and remainder on loop indices (WriteToSlice, uint256.go:143), the
arithmetic shift in ExtendSign (uint256.go:1284), and 64 bit shifts by variable counts (Lsh, Rsh, SRsh).
Each batch is bracketed by web3_clientVersion before and after.
Usage: python3 elysium.py <out.json> [nVectors] [rpcUrl]
"""
import sys, os, json, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
NR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff')); sys.path.insert(1, HERE)
from evm import rpc
import battery as B
import u256vectors as UV

out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 40000
url = sys.argv[3] if len(sys.argv) > 3 else 'https://rpc.elysium.kinetiq.xyz'
rnd = random.Random(29_99901)
V0 = UV.gen(60000, random.Random(29_2026_11_27)) + UV.maxmod_vectors()
keep = []
for op, a, b, c in V0:
    if op == 'MULDIV': keep.append(('MULDIV512', a, b, c))
    elif op in B.OPS: keep.append((op, a, b, c))
# weight: all SIGNEXTEND, SAR, SHL, SHR, BYTE, SDIV, SMOD vectors with small indices; sample the rest
pri = [v for v in keep if v[0] in ('SIGNEXTEND', 'SAR', 'SHL', 'SHR', 'BYTE') or (v[0] in ('SDIV', 'SMOD') and rnd.random() < 0.3)]
rest = [v for v in keep if v not in pri] if False else [v for v in keep if v[0] not in ('SIGNEXTEND', 'SAR', 'SHL', 'SHR', 'BYTE', 'SDIV', 'SMOD')]
rnd.shuffle(pri); rnd.shuffle(rest)
V = pri[:n // 3] + rest[:n - min(len(pri), n // 3)]
code = B.dispatcher()
res = {'url': url, 'seed': [29_2026_11_27, 29_99901], 'vectors': len(V), 'byOp': {}, 'batches': [], 'mismatches': [], 'errors': []}
for v in V: res['byOp'][v[0]] = res['byOp'].get(v[0], 0) + 1
size = 400
for i in range(0, len(V), size):
    batch = V[i:i + size]
    try: before = rpc(url, 'web3_clientVersion', [])
    except Exception as e: before = 'ERR ' + str(e)[:100]
    done, bad, errors = B.run(url, code, batch, size=size)
    try: after = rpc(url, 'web3_clientVersion', [])
    except Exception as e: after = 'ERR ' + str(e)[:100]
    res['batches'].append({'start': i, 'n': len(batch), 'ran': done, 'before': before, 'after': after, 'mismatches': len(bad), 'errors': errors})
    res['mismatches'] += bad
    print(i, done, len(bad), errors[:1], before, after, flush=True)
    time.sleep(0.3)
res['ran'] = sum(b['ran'] for b in res['batches']); res['mismatchCount'] = len(res['mismatches'])
res['clientVersions'] = sorted({b['before'] for b in res['batches']} | {b['after'] for b in res['batches']})
json.dump(res, open(out, 'w'), indent=1)
print('ran', res['ran'], 'of', len(V), 'mismatches', res['mismatchCount'], res['clientVersions'])
