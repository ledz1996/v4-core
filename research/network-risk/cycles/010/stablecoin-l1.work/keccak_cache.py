"""KECCAK256 vectors aimed at the process-global keccak cache that Tempo (alloy-primitives 1.7.3,
fixed-cache 0.1.10, feature keccak-cache-global in the default features of bin/tempo) and Arc
(alloy-primitives 1.5.7 with keccak-cache-global, fixed-cache 0.1.8) put in front of the KECCAK256
opcode. The cache holds inputs of 1 to 87 bytes keyed by length and content.

Vectors use the battery dispatcher (tools/opdiff/battery.py): mstore(0,a), mstore(32,b),
keccak256(off, len) over memory whose rest is zero.
  - every length 1..96 at offsets 0, 1, 31, 32, 33 with random words (both sides of the 87 byte limit)
  - inputs that equal another input except for length (trailing zero bytes): (0, n) and (0, n+1)
    with b = 0 so byte n is zero for n >= 32
  - all-zero inputs of every length 1..96 (memory past 64 bytes)
  - the whole set sent three times, in three eth_call requests, so later rounds meet cache hits
Usage: python3 keccak_cache.py <out.json> <chainId> [...]
"""
import sys, os, json, random
base = os.path.dirname(os.path.abspath(__file__)).rsplit('/', 3)[0]
sys.path.insert(0, base + '/tools/opdiff')
import battery as B

nets = {n['chainId']: n for n in json.load(open(base + '/state/networks.json'))['networks']}

if __name__ == '__main__':
    out = sys.argv[1]; cids = [int(x) for x in sys.argv[2:]]
    rnd = random.Random(1010)
    V = []
    for ln in range(1, 97):
        for off in (0, 1, 31, 32, 33):
            if off + ln > 0xff + 0x3ff: continue
            V.append(('KECCAK', rnd.getrandbits(256), rnd.getrandbits(256), off | (ln << 8)))
    a = rnd.getrandbits(256)
    for ln in range(1, 96):
        V.append(('KECCAK', a, 0, 0 | (ln << 8)))
        V.append(('KECCAK', a, 0, 0 | ((ln + 1) << 8)))
    for ln in range(1, 97):
        V.append(('KECCAK', 0, 0, 64 | (ln << 8)))
    code = B.dispatcher(); res = {}
    for cid in cids:
        url = nets[cid]['rpc']; rounds = []
        for r in range(3):
            done, bad, errors = B.run(url, code, V, size=300)
            rounds.append({'ran': done, 'mismatches': bad[:20], 'mismatchCount': len(bad), 'errors': errors[:5]})
        res[cid] = {'vectors': len(V), 'rounds': rounds}
        print(cid, len(V), [(x['ran'], x['mismatchCount'], len(x['errors'])) for x in rounds], flush=True)
    json.dump(res, open(out, 'w'), indent=1)
