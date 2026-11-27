"""Send 2,000 KECCAK256 vectors of the shapes run in the binary models by eth_call (state override, no transaction)
to one endpoint per network, each batch bracketed by web3_clientVersion. Seed 3535.
A small contract copies each record's bytes from calldata to memory at 0x100 + offset and hashes them there.
usage: python3 -I send2000.py <out.json> [chainId=url ...]"""
import json, random, sys, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import assemble, call_code, rpc, keccak

code = assemble([('PUSH', 0x8000), ('PUSH', 0),
                 ('LABEL', 'loop'), 'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'end'), 'JUMPI',
                 'DUP1', 'CALLDATALOAD', 'DUP1', ('PUSH', 0xffff), 'AND',
                 'SWAP1', ('PUSH', 16), 'SHR', ('PUSH', 0xff), 'AND', ('PUSH', 0x100), 'ADD',
                 'DUP2', 'DUP4', ('PUSH', 32), 'ADD', 'DUP3', 'CALLDATACOPY',
                 'DUP2', 'SWAP1', 'KECCAK256', 'DUP4', 'MSTORE',
                 ('PUSH', 31), 'ADD', ('PUSH', 5), 'SHR', ('PUSH', 5), 'SHL', ('PUSH', 32), 'ADD', 'ADD',
                 'SWAP1', ('PUSH', 32), 'ADD', 'SWAP1', ('REF', 'loop'), 'JUMP',
                 ('LABEL', 'end'), 'POP', ('PUSH', 0x8000), 'SWAP1', 'SUB', ('PUSH', 0x8000), 'RETURN'])
rnd = random.Random(3535)
def rb(n): return bytes(rnd.getrandbits(8) for _ in range(n))
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
A = [0, 1, (1 << 160) - 1, 0x4200000000000000000000000000000000000006] + [rnd.getrandbits(160) for _ in range(30)]
V = []
for n in list(range(0, 1101, 3)) + [135, 136, 137, 271, 272, 273, 407, 408, 409, 1100]:
    V.append(('len', rnd.randrange(0, 256), rb(n)))
for off in range(32):
    for n in (1, 32, 58, 64, 87, 88, 136, 160):
        V.append(('unaligned', off + 32 * rnd.randrange(0, 7), rb(n)))
while len(V) < 2000:
    k = rnd.randrange(5)
    if k == 0:
        c0, c1 = sorted((rnd.choice(A), rnd.choice(A)))
        V.append(('poolId160', 32 * rnd.randrange(0, 7), w(c0) + w(c1) + w(rnd.choice([100, 500, 3000, 10000, 0x800000])) + w(rnd.choice([1, 10, 60, 200])) + w(rnd.choice(A))))
    elif k == 1:
        lo, hi = rnd.randrange(-887272, 0), rnd.randrange(0, 887273)
        V.append(('positionKey58', 12 + 32 * rnd.randrange(0, 7), rnd.choice(A).to_bytes(20, 'big') + (lo % (1 << 24)).to_bytes(3, 'big') + (hi % (1 << 24)).to_bytes(3, 'big') + rb(32)))
    elif k == 2:
        V.append(('currencyDelta64', 0, w(rnd.choice(A)) + w(rnd.choice(A))))
    elif k == 3:
        V.append(('mappingSmallSlot64', 0, rb(32) + w(rnd.choice([0, 1, 4, 5, 6]))))
    else:
        V.append(('rand1to88', rnd.randrange(0, 64), rb(rnd.randrange(1, 89))))
V = V[:2000]
EP = {196: 'https://rpc.xlayer.tech', 42220: 'https://forno.celo.org', 4326: 'https://mainnet.megaeth.com/rpc',
      56: 'https://bsc-rpc.publicnode.com'}
for a in sys.argv[2:]:
    c, u = a.split('=', 1); EP[int(c)] = u
def cv(url):
    try: return rpc(url, 'web3_clientVersion', [])
    except Exception as e: return 'error ' + str(e)[:120]
def enc(batch):
    out = b''
    for tag, off, d in batch:
        out += ((off << 16) | len(d)).to_bytes(32, 'big') + d + bytes((-len(d)) % 32)
    return out
res = {'seed': 3535, 'vectors': len(V), 'byShape': {}, 'contractHex': code.hex(), 'chains': {}}
for t in V: res['byShape'][t[0]] = res['byShape'].get(t[0], 0) + 1
B = 100
for cid, url in EP.items():
    ch = {'url': url, 'batches': [], 'mismatches': [], 'errors': [], 'done': 0}
    for i in range(0, len(V), B):
        batch = V[i:i + B]
        before = cv(url)
        try:
            r = call_code(url, code, enc(batch), gas=200_000_000 if cid != 4326 else None)
        except Exception as e:
            r = None; ch['errors'].append({'batch': i // B, 'error': str(e)[:200]})
        after = cv(url)
        ch['batches'].append({'batch': i // B, 'before': before, 'after': after})
        if r is None: continue
        if len(r) != 32 * len(batch):
            ch['errors'].append({'batch': i // B, 'error': 'answer %d bytes' % len(r)}); continue
        for k, (tag, off, d) in enumerate(batch):
            got = r[32 * k:32 * k + 32]
            if got != keccak(d):
                ch['mismatches'].append({'shape': tag, 'offset': off, 'input': d.hex(), 'got': got.hex(), 'want': keccak(d).hex()})
        ch['done'] += len(batch)
        time.sleep(0.3)
    ch['clientVersions'] = sorted(set(b['before'] for b in ch['batches']) | set(b['after'] for b in ch['batches']))
    res['chains'][cid] = ch
    print(cid, url, 'done', ch['done'], 'mismatches', len(ch['mismatches']), 'errors', len(ch['errors']), ch['clientVersions']); sys.stdout.flush()
json.dump(res, open(sys.argv[1], 'w'), indent=1)
