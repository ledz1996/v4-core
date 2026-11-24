"""State key differential: does a network treat two different storage slot indexes, or two different transient
slot indexes, as one slot?

A probe contract placed by state override writes CALLER into slot s and then reads a list of other slots. On
Ethereum every other slot of a fresh account reads zero. The masks tried against each base slot are every single
bit (256), every value of the top byte and of the low byte (255 each), the top 2 to 96 bits cleared, and the
low 1 to 64 bits cleared. The same is done with TSTORE and TLOAD.

Usage: python3 statekeys.py <out.json> [chainId ...]
"""
import sys, json, random, time, concurrent.futures as cf
from evm import rpc, networks, keccak

M = (1 << 256) - 1
PROBE = '0x00000000000000000000000000000000c0ffee0a'
CALLER = '0x00000000000000000000000000000000000a11ce'


def code(transient):
    st, ld = (0x5d, 0x5c) if transient else (0x55, 0x54)
    c = bytes([0x60, 0x00, 0x35, 0x33, 0x90, st, 0x60, 0x20,
               0x5b, 0x80, 0x36, 0x11, 0x15, 0x60, 0x1b, 0x57,
               0x80, 0x35, ld, 0x81, 0x52, 0x60, 0x20, 0x01, 0x60, 0x08, 0x56,
               0x5b, 0x50, 0x60, 0x00, 0x35, ld, 0x60, 0x00, 0x52, 0x36, 0x60, 0x00, 0xf3])
    assert c[0x1b] == 0x5b and c[0x08] == 0x5b
    return c


def masks():
    m = [1 << b for b in range(256)]
    m += [k << 248 for k in range(1, 256)] + list(range(1, 256))
    return list(dict.fromkeys(m))


def others(s):
    out = [(s ^ k, 'xor ' + hex(k)) for k in masks()]
    out += [(s & (M >> t), f'top {t} bits cleared') for t in (2, 4, 8, 16, 32, 64, 96)]
    out += [(s & (M << t) & M, f'low {t} bits cleared') for t in (1, 7, 8, 16, 32, 64)]
    return [(x, why) for x, why in out if x != s]


def bases():
    rnd = random.Random(40_2026_11_24)
    b = [rnd.getrandbits(256) | (1 << 255) | 1 for _ in range(4)]
    # slots the PoolManager really uses: a pool's state, a balance mapping entry, a transient delta slot
    b += [int.from_bytes(keccak(bytes(31) + b'\x07' + (6).to_bytes(32, 'big')), 'big'),
          int.from_bytes(keccak(bytes(12) + bytes.fromhex(CALLER[2:]) + (4).to_bytes(32, 'big')), 'big'),
          M, (1 << 248) | 5]
    return b


def run(nw):
    cid, name, url = nw; res = {}
    for transient in (False, True):
        c = code(transient); alias = {}; n = 0; err = None
        for s in bases():
            ot = others(s)
            data = b''.join(x.to_bytes(32, 'big') for x in [s] + [x for x, _ in ot])
            r = None
            for k in range(6):
                try:
                    r = bytes.fromhex(rpc(url, 'eth_call', [{'from': CALLER, 'to': PROBE, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest',
                                                            {PROBE: {'code': '0x' + c.hex()}}], timeout=90)[2:]); break
                except Exception as e:  # noqa
                    err = str(e)[:160]; time.sleep(4 * (k + 1))
            if r is None: break
            err = None
            if int.from_bytes(r[:32], 'big') != int(CALLER, 16): err = 'the written slot did not read back'; break
            for i, (x, why) in enumerate(ot):
                n += 1
                v = int.from_bytes(r[32 * (i + 1):32 * (i + 2)], 'big')
                if v: alias[why] = alias.get(why, 0) + 1
        res['transient' if transient else 'storage'] = {'reads': n, 'aliases': alias, 'error': err}
    return cid, name, res


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    nets = [n for n in networks() if not only or n[0] in only]; results = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, res in ex.map(run, nets):
            results[cid] = dict(name=name, **res)
            print(f'{cid:>8} {name:16} storage {res["storage"]["reads"]} reads, aliases {res["storage"]["aliases"]} {res["storage"]["error"] or ""}; '
                  f'transient {res["transient"]["reads"]} reads, aliases {res["transient"]["aliases"]} {res["transient"]["error"] or ""}', flush=True)
    json.dump({'bases': [hex(b) for b in bases()], 'masksPerBase': len(others(bases()[0])), 'results': results}, open(out, 'w'), indent=1)
