"""Task 3 on chain (L-1176): does a write to storage slot s read back at s xor 2^248, and does TSTORE alias?
Uses the probe of tools/opdiff/statekeys.py (writes CALLER into slot s, then reads the listed slots), placed by
state override and run with eth_call, so nothing is sent. Slots tried: fixed slots 0 to 6 of the PoolManager, real
PoolManager-shaped keccak slots of a pool (slot0, feeGrowth, liquidity, a tick, a bitmap word, a position) and an
ERC-6909 balance slot, each with its bit-248 partner and with other bit-248..255 partners as controls.
Each network batch is bracketed by web3_clientVersion. Usage: python3 avaxalias.py <out.json> [chainId ...]
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
NR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import rpc, networks, keccak
import statekeys as SK

def w(x): return x.to_bytes(32, 'big')
def k(*parts): return int.from_bytes(keccak(b''.join(p if isinstance(p, bytes) else w(p) for p in parts)), 'big')
pid = keccak(w(0) + w(0xabcdef) + w(3000) + w(60) + w(0))
base = k(pid, w(6))
slots = {f'fixed {i}': i for i in range(7)}
slots.update({'pool slot0': base, 'pool feeGrowthGlobal0': base + 1, 'pool liquidity': base + 3,
              'tick 60': k(w(60), w(base + 4)), 'bitmap word -1': k(w((1 << 256) - 1), w(base + 5)),
              'position': k(keccak(b'\x11' * 20 + (0).to_bytes(3, 'big') + (60).to_bytes(3, 'big') + w(0)), w(base + 6)),
              'erc6909 balance': k(w(0xabcdef), k(w(0x1234), w(4)))})
masks = [1 << 248, 1 << 249, 1 << 255, 0xff << 248, 1 << 247, 1]
only = set(map(int, sys.argv[2:])) or {43114, 137, 56}
out = {'probe': 'tools/opdiff/statekeys.py code()', 'slots': {n: hex(s) for n, s in slots.items()}, 'masks': [hex(m) for m in masks], 'networks': []}
for cid, name, url in networks():
    if cid not in only: continue
    rec = {'chainId': cid, 'name': name, 'rpc': url, 'before': rpc(url, 'web3_clientVersion', []), 'storage': {}, 'transient': {}}
    for kind, tr in (('storage', False), ('transient', True)):
        code = SK.code(tr)
        for n, s in slots.items():
            reads = [s] + [s ^ m for m in masks]
            data = b''.join(w(x) for x in reads)
            tx = {'from': SK.CALLER, 'to': SK.PROBE, 'data': '0x' + data.hex()}
            r = bytes.fromhex(rpc(url, 'eth_call', [tx, 'latest', {SK.PROBE: {'code': '0x' + code.hex()}}])[2:])
            words = [int.from_bytes(r[i:i + 32], 'big') for i in range(0, len(r), 32)]
            rec[kind][n] = {'self': hex(words[0]) if words else None, **{hex(m): hex(v) for m, v in zip(masks, words[1:])}}
    rec['after'] = rpc(url, 'web3_clientVersion', [])
    al = {kind: sorted({m for d in rec[kind].values() for m, v in d.items() if m != 'self' and v != '0x0'}) for kind in ('storage', 'transient')}
    rec['aliasedMasks'] = al
    print(cid, name, rec['before'], al, flush=True)
    out['networks'].append(rec)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
