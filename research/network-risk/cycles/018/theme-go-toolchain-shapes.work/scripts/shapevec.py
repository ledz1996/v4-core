#!/usr/bin/env python3
"""Vectors for the opcode paths that hold a candidate site of the shape search:
 - SIGNEXTEND (uint256 ExtendSign: int8 sign extension of the sign byte, v1.3.2 lines 1260-1300; v1.2.4 mask form)
 - ADDMOD (uint256 AddMod: x = &tmpX / y = &tmpY branch when an operand is >= the modulus)
 - SIGNEXT_CHAIN (the int128 / int24 extraction the PoolManager does)
Each is run through the battery dispatcher (tools/opdiff/battery.py) at a state-override address with
eth_call. Every JSON-RPC request is a batch [web3_clientVersion, eth_call, web3_clientVersion]; a batch is
counted only when both clientVersion answers are the same build (for Celo: only when that build is Geth).
Usage: shapevec.py <out.json> <chainId>...   Seed 20261125."""
import sys, os, json, random, time, hashlib, urllib.request, ssl
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../tools/opdiff'))
from evm import networks, STUB, MASK
import battery
SEED = 20261125
rng = random.Random(SEED)
V = []
# SIGNEXTEND: a = byte index (top), b = value
idx = list(range(0, 34)) + [2**64, 2**64 + 1, 2**255, MASK]
for b_i in idx:
    for sb in (0x00, 0x01, 0x7f, 0x80, 0x81, 0xfe, 0xff):
        for k in range(4):
            x = rng.getrandbits(256)
            if b_i < 32:
                x &= ~(0xff << (8 * b_i)) & MASK; x |= sb << (8 * b_i)
            if k == 0: x &= (1 << (8 * min(b_i, 31) + 8)) - 1  # clean upper bytes
            if k == 1: x |= MASK ^ ((1 << (8 * min(b_i, 31) + 8)) - 1)  # all upper bytes set
            V.append(('SIGNEXTEND', b_i, x & MASK, 0))
# ADDMOD: a, b, c=modulus; operand >= modulus forces the tmpX / tmpY branch
mods = [1, 2, 3, 2**64 - 1, 2**64, 2**64 + 1, 2**128 - 1, 2**128, 2**192 - 1, 2**192, 2**255, MASK - 1, MASK]
mods += [rng.getrandbits(rng.choice((8, 63, 64, 65, 127, 128, 129, 191, 192, 193, 255, 256))) | 1 for _ in range(60)]
for m in mods:
    for _ in range(12):
        def pick():
            r = rng.randrange(6)
            if r == 0: return m
            if r == 1: return m - 1
            if r == 2: return min(MASK, m + rng.getrandbits(8))
            if r == 3: return MASK - rng.getrandbits(8)
            if r == 4: return rng.randrange(m)
            return rng.getrandbits(256)
        V.append(('ADDMOD', pick() & MASK, pick() & MASK, m))
for _ in range(400):
    a = rng.getrandbits(256); sh = rng.choice((0, 8, 24, 160, 184, 208, 232, rng.randrange(256)))
    V.append(('SIGNEXT_CHAIN', a, sh, 0))
code = battery.dispatcher()
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
        return json.load(r)

def run(cid, url, size=300):
    bad, builds, errors, done, skipped = [], {}, [], 0, 0
    i = 0
    while i < len(V):
        batch = V[i:i + size]; data = battery.encode(batch)
        body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': STUB, 'data': '0x' + data.hex()}, 'latest', {STUB: {'code': '0x' + code.hex()}}]},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
        ok = False
        for attempt in range(int(os.environ.get('ATTEMPTS', 8))):
            try:
                r = {x['id']: x for x in post(url, body)}
                v1, v2 = r[1].get('result'), r[3].get('result')
                if v1 != v2 or 'result' not in r[2]:
                    errors.append((i, 'unbracketed or error', v1, v2, str(r[2].get('error'))[:120])); time.sleep(1); continue
                if cid == 42220 and not str(v1).startswith('Geth'):
                    skipped += 1; time.sleep(0.3); continue
                res = bytes.fromhex(r[2]['result'][2:]); ok = True; break
            except Exception as e:  # noqa
                errors.append((i, str(e)[:160])); time.sleep(2)
        if not ok:
            i += size; continue
        builds[v1] = builds.get(v1, 0) + len(batch)
        exp = battery.expected(batch, data)
        for k, (t, e) in enumerate(zip(batch, exp)):
            got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
            if got != e:
                bad.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e), 'build': v1})
        done += len(batch); i += size
    return {'chainId': cid, 'rpc': url, 'vectors': len(V), 'ran': done, 'builds': builds, 'mismatchCount': len(bad), 'mismatches': bad,
            'celoNonGethAnswersSkipped': skipped, 'errors': errors[:30]}

if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    per = {}
    for t in V: per[t[0]] = per.get(t[0], 0) + 1
    print('vectors', len(V), per, 'dispatcher sha256', hashlib.sha256(code).hexdigest())
    res = []
    for cid, name, url in networks():
        if cid in only:
            r = run(cid, url); r['name'] = name; res.append(r)
            print(cid, name, 'ran', r['ran'], '/', r['vectors'], 'mismatches', r['mismatchCount'], 'builds', r['builds'], 'skipped', r['celoNonGethAnswersSkipped'], 'errors', len(r['errors']), r['errors'][:2])
    json.dump({'seed': SEED, 'vectors': len(V), 'perOp': per, 'dispatcherSha256': hashlib.sha256(code).hexdigest(),
               'date': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'results': res}, open(out, 'w'), indent=1)
