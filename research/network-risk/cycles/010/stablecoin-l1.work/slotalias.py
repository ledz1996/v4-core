"""Slot aliasing probe for lead L-576 (and L-587 on MegaETH), by eth_call with a code override.

The probe at an unused address writes CALLER into slot s (first calldata word), then SLOADs every further
calldata word and ORs the results, and returns (or of the reads, value read back from s). With empty storage
every other slot must read 0 and s must read the caller. Slots tried: s XOR k for every k in 1..255 (all
multi-bit masks inside one MIP-8 page, offsets 0..127, and across the bit 7 page boundary), s +- 1..4 across
a 128 boundary, slots that differ from s only in bits 249..255 or in the page index high bits, and slots
equal to s with the page index truncated to 249, 248, 160 and 64 bits.

Usage: python3 slotalias.py <out.json> <chainId> [...]
"""
import sys, json, random
sys.path.insert(0, __file__.rsplit('/', 4)[0] + '/tools/opdiff')
from evm import rpc

M = (1 << 256) - 1
nets = {n['chainId']: n for n in json.load(open(__file__.rsplit('/', 4)[0] + '/state/networks.json'))['networks']}
PROBE = '0x00000000000000000000000000000000c0ffee09'
CALLER = '0x00000000000000000000000000000000000a11ce'


def code():
    c = bytearray()
    c += bytes([0x60, 0x00, 0x35, 0x33, 0x90, 0x55])          # sstore(calldataload(0), caller)
    c += bytes([0x60, 0x00, 0x60, 0x20])                      # acc=0, i=32
    loop = len(c)
    c += bytes([0x5b, 0x80, 0x36, 0x11, 0x15, 0x60, 0x00, 0x57])  # jumpdest; if iszero(gt(cds, i)) jump end (patched)
    jpos = len(c) - 2
    c += bytes([0x80, 0x35, 0x54, 0x82, 0x17, 0x91, 0x50])    # acc |= sload(calldataload(i))
    c += bytes([0x60, 0x20, 0x01, 0x60, loop, 0x56])          # i += 32; jump loop
    end = len(c)
    c += bytes([0x5b, 0x50, 0x60, 0x00, 0x52, 0x60, 0x00, 0x35, 0x54, 0x60, 0x20, 0x52, 0x60, 0x40, 0x60, 0x00, 0xf3])
    c[jpos] = end
    return bytes(c)


def slots_for(s):
    out = [s ^ k for k in range(1, 256)]
    out += [(s + d) & M for d in (-4, -3, -2, -1, 1, 2, 3, 4)]
    out += [s ^ (1 << b) for b in range(249, 256)] + [s ^ (0x7f << 249)]
    for keep in (249, 248, 160, 64):
        page = s >> 7; tp = page & ((1 << keep) - 1)
        out.append(((tp << 7) | (s & 0x7f)) & M)
    return [x for x in dict.fromkeys(out) if x != s]


if __name__ == '__main__':
    out = sys.argv[1]; cids = [int(x) for x in sys.argv[2:]]
    rnd = random.Random(576)
    bases = [rnd.getrandbits(256) for _ in range(12)]
    bases += [(rnd.getrandbits(249) << 7) | o for o in (0, 1, 126, 127)]
    bases += [((1 << 249) - 1) << 7 | 127, ((1 << 249) - 1) << 7, 127, 128, 0, 1 << 255]
    c = code(); res = {}
    for cid in cids:
        url = nets[cid]['rpc']; bad = []; n = 0
        for s in bases:
            sl = slots_for(s)
            data = b''.join(x.to_bytes(32, 'big') for x in [s] + sl)
            r = rpc(url, 'eth_call', [{'from': CALLER, 'to': PROBE, 'data': '0x' + data.hex(), 'gas': hex(30_000_000)}, 'latest',
                                      {PROBE: {'code': '0x' + c.hex()}}], timeout=90)
            b = bytes.fromhex(r[2:]); acc = int.from_bytes(b[:32], 'big'); back = int.from_bytes(b[32:64], 'big')
            n += len(sl)
            if acc != 0 or back != int(CALLER, 16): bad.append({'s': hex(s), 'or': hex(acc), 'readBack': hex(back)})
        res[cid] = {'bases': len(bases), 'aliasReads': n, 'bad': bad}
        print(cid, res[cid], flush=True)
    json.dump({'probeCodeHex': c.hex(), 'results': res}, open(out, 'w'), indent=1)
