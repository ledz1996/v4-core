"""Cycle 30 op-stack-custom-gas: KECCAK256 vectors aimed at the global keccak cache that X Layer's reth build
enables (alloy-primitives 1.6.0 feature keccak-cache-global, fixed-cache 0.1.10, inputs of 1 to 87 bytes).
Uses the battery dispatcher record ('KECCAK', a, b, off | len << 8): memory holds a at 0, b at 32, zeros after.
Families: every length 1..96 at offsets 0..64 (cache boundary at 87/88); inputs that differ only by length
(trailing zero bytes); the same input repeated in one batch and across batches so later ones are cache hits;
64 byte mapping-slot shapes (key, slot) and 58 byte position-key shapes. Each eth_call is sent between two
web3_clientVersion calls in one JSON-RPC batch and kept only when both name the wanted build. Read-only.
Usage: python3 keccache.py <out.json> <url> <build substring> [rounds]"""
import sys, json, random, time, urllib.request, collections
R = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, R + '/tools/opdiff')
import evm, battery

def vectors(seed=3030):
    rnd = random.Random(seed); V = []
    r = lambda: rnd.getrandbits(256)
    for ln in range(1, 97):
        for off in (0, 1, 7, 31, 32, 33, 63, 64):
            V.append(('KECCAK', r(), r(), off | (ln << 8)))
    # length-only differences: same a, b, offset; lengths L and L+1..L+3 (extra bytes are zero or from b)
    for _ in range(600):
        a, b = r(), r(); off = rnd.randrange(0, 40); L = rnd.randrange(1, 88)
        for d in range(0, 4): V.append(('KECCAK', a, b, off | (min(L + d, 1023) << 8)))
    # zero-heavy inputs: all-zero and one-bit inputs of every cacheable length
    for ln in range(1, 89):
        V.append(('KECCAK', 0, 0, 0 | (ln << 8)))
        V.append(('KECCAK', 1 << rnd.randrange(256), 0, 0 | (ln << 8)))
    # 64-byte mapping slot shapes keccak(key . slot) with small slots, and 58-byte packed position keys
    for _ in range(1500):
        V.append(('KECCAK', r() >> 96, rnd.randrange(0, 16), 0 | (64 << 8)))
        V.append(('KECCAK', r(), r(), 0 | (58 << 8)))
    # repeats: the same 400 inputs again (cache hits in a warm process)
    base = list(V[:400]); V += base
    return V

def main():
    out, url, want = sys.argv[1], sys.argv[2], sys.argv[3]; rounds = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    V = vectors(); code = battery.dispatcher(); size = 500
    batches = [V[i:i + size] for i in range(0, len(V), size)]
    st = collections.Counter(); bad = []
    for rd in range(rounds):
        for bi, batch in enumerate(batches):
            data = battery.encode(batch)
            body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': evm.STUB, 'data': '0x' + data.hex()}, 'latest', {evm.STUB: {'code': '0x' + code.hex()}}]},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]).encode()
            for t in range(40):
                try:
                    req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
                    with urllib.request.urlopen(req, timeout=120, context=evm._ctx) as rr: j = {x['id']: x for x in json.load(rr)}
                except Exception:
                    st['transport'] += 1; time.sleep(2); continue
                v1, v3 = str(j.get(1, {}).get('result', '')), str(j.get(3, {}).get('result', ''))
                st['seen:' + v1] += 1
                if want not in v1 or want not in v3 or 'result' not in j.get(2, {}):
                    st['skip'] += 1; time.sleep(0.5); continue
                res = bytes.fromhex(j[2]['result'][2:]); exp = battery.expected(batch, data)
                for k, (tup, e) in enumerate(zip(batch, exp)):
                    g = int.from_bytes(res[32 * k:32 * k + 32], 'big')
                    if g != e: bad.append({'round': rd, 'a': hex(tup[1]), 'b': hex(tup[2]), 'c': hex(tup[3]), 'got': hex(g), 'want': hex(e)})
                st['pinned'] += 1; st['vectorsPinned'] += len(batch); break
            else: st['unpinned'] += 1
    r = {'url': url, 'build': want, 'vectors': len(V), 'rounds': rounds, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'stats': dict(st)}
    json.dump(r, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != 'mismatches'}, indent=1))

if __name__ == '__main__': main()
