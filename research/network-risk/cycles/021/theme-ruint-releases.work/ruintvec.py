"""Vectors aimed at the ruint functions found faulty in some release (cycle 21, theme-ruint-releases).

Uses the battery dispatcher of tools/opdiff/battery.py unchanged, plus single probes for jump
targets and memory offsets whose high limbs are set. Read-only eth_call with a code override at
an unused address. Every batch per network is bracketed by web3_clientVersion.

Usage: python3 ruintvec.py <out.json> [chainId ...]
"""
import sys, os, json, random, hashlib, time, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import *  # noqa
import battery

SEED = 2102101
M64 = (1 << 64) - 1


def vectors():
    r = random.Random(SEED)
    V = []
    big_amounts = []
    for base in (1 << 32, 1 << 33, 1 << 64, (1 << 32) * 3, 1 << 63, 1 << 128, 1 << 192):
        for k in list(range(0, 260, 7)) + [255, 256, 257]:
            big_amounts.append((base + k) & MASK)
    big_amounts += [M64 - k for k in (0, 1, 255, 256)] + [(1 << 32) - 1, (1 << 32) - 256, MASK, SIGN]
    vals = [1, 0x80, MASK, SIGN, SIGN - 1, (1 << 128) - 1, 0x0706060506020500060203020504000106050205030304010505030400000000]
    for op in ('SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND'):
        for a in big_amounts:
            for v in vals + [r.getrandbits(256) for _ in range(3)]:
                V.append((op, a, v, 0))
    # EXP with power of two bases (the 1.21 fast path) and with large exponents
    for k in list(range(0, 64)) + [64, 127, 128, 255]:
        for e in list(range(0, 40)) + [63, 64, 85, 127, 128, 255, 256, 257, 1 << 32, (1 << 32) + 1, 1 << 64, (1 << 64) + 3, MASK]:
            V.append(('EXP', 1 << k, e, 0))
    # MULMOD / ADDMOD / MULDIV512 in the shape of the mul_mod quotient-skip fault
    for _ in range(1500):
        m = r.getrandbits(256 - r.randrange(0, 64)) | (1 << 192)
        a = (m + r.randrange(-1000, 1000)) & MASK
        if a >> 192 == 0:
            a |= 1 << 192
        b = MASK - r.randrange(0, 1 << r.randrange(1, 64))
        if r.random() < 0.5:
            a, b = b, a
        V.append(('MULMOD', a, b, m))
        V.append(('MULDIV512', a, b, m))
    for _ in range(500):
        m = r.getrandbits(256) | (1 << 192)
        a = r.randrange(0, min(2 * m, MASK + 1)); b = r.randrange(0, min(2 * m, MASK + 1))
        V.append(('ADDMOD', a, b, m))
        V.append(('ADDMOD', (m - r.randrange(0, 3)) & MASK, (m + r.randrange(-3, 3)) & MASK, m))
    # comparisons at limb edges (1.19 rewrote Ord::cmp through subtraction)
    for _ in range(400):
        a = r.getrandbits(256)
        lim = r.randrange(4)
        b = a ^ (1 << (64 * lim + r.randrange(64)))
        for op in ('LT', 'GT', 'SLT', 'SGT', 'EQ'):
            V.append((op, a, b, 0))
    # calldata offsets with high bits
    V += [('CDLOAD', a, 0, 0) for a in big_amounts[::5]]
    return V


def jump_mem_code(kind, x):
    """Single probes. Expected: success returning word 1 only for the plain target / in-range offset."""
    if kind == 'jump':
        # PUSH32 x; JUMP; then at fixed offset 0x30: JUMPDEST PUSH1 1 PUSH1 0 MSTORE PUSH1 32 PUSH1 0 RETURN
        code = bytes([0x7f]) + x.to_bytes(32, 'big') + bytes([0x56])
        code = code.ljust(0x30, b'\xfe') + bytes([0x5b, 0x60, 1, 0x60, 0, 0x52, 0x60, 32, 0x60, 0, 0xf3])
        return code
    if kind == 'jumpi':
        code = bytes([0x60, 1, 0x7f]) + x.to_bytes(32, 'big') + bytes([0x57, 0x00])
        code = code.ljust(0x30, b'\xfe') + bytes([0x5b, 0x60, 1, 0x60, 0, 0x52, 0x60, 32, 0x60, 0, 0xf3])
        return code
    if kind == 'mload':
        # PUSH32 x; MLOAD; POP; PUSH1 1 ... return 1 (only reachable when the offset is affordable)
        return bytes([0x7f]) + x.to_bytes(32, 'big') + bytes([0x51, 0x50, 0x60, 1, 0x60, 0, 0x52, 0x60, 32, 0x60, 0, 0xf3])
    if kind == 'return_len':
        # RETURN(offset 0, len x)
        return bytes([0x7f]) + x.to_bytes(32, 'big') + bytes([0x60, 0, 0xf3])
    raise KeyError(kind)


def probes():
    P = []
    for t in (0x30, (1 << 32) + 0x30, (1 << 64) + 0x30, (1 << 128) + 0x30, (1 << 192) + 0x30, (1 << 255) + 0x30, ((1 << 32) * 7) + 0x30, M64 + 0x31):
        P.append(('jump', t & MASK, t == 0x30))
        P.append(('jumpi', t & MASK, t == 0x30))
    for x in (0, 64, (1 << 32), (1 << 32) + 32, (1 << 64), (1 << 64) + 32, (1 << 128), (1 << 255)):
        P.append(('mload', x, x == 0 or x == 64))
    for x in ((1 << 64), (1 << 64) + 32, (1 << 128) + 32, (1 << 192) + 32):
        P.append(('return_len', x, False))
    return P


def client_version(url):
    try:
        return rpc(url, 'web3_clientVersion', [])
    except Exception as e:  # noqa
        return 'ERROR ' + str(e)[:160]


def run_probes(url):
    out = []
    for kind, x, ok in probes():
        code = jump_mem_code(kind, x)
        try:
            res = bytes.fromhex(rpc(url, 'eth_call', [{'to': STUB, 'data': '0x', 'gas': hex(5_000_000)}, 'latest', {STUB: {'code': '0x' + code.hex()}}])[2:])
            got = 'ok:' + res.hex()
            good = ok and int.from_bytes(res, 'big') == 1
        except Exception as e:  # noqa
            got = 'error:' + str(e)[:120]
            good = not ok
        out.append({'kind': kind, 'x': hex(x), 'expectSuccess': ok, 'got': got, 'asSpecified': good})
    return out


if __name__ == '__main__':
    outp = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = battery.dispatcher(); V = vectors()
    per_op = {}
    for t in V: per_op[t[0]] = per_op.get(t[0], 0) + 1
    print('dispatcher', len(code), 'bytes', hashlib.sha256(code).hexdigest()[:16], len(V), 'vectors', per_op, flush=True)
    nets = [n for n in networks() if not only or n[0] in only]

    def work(n):
        cid, name, url = n
        v0 = client_version(url); t0 = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        done, bad, errors = battery.run(url, code, V, size=300)
        if errors and done < len(V):
            retry = [t for i, _ in errors for t in V[i:i + 300]]
            d2, b2, e2 = battery.run(url, code, retry, size=75)
            done += d2; bad += b2; errors = e2
        pr = run_probes(url)
        v1 = client_version(url)
        return {'chainId': cid, 'name': name, 'rpc': url, 'clientVersionBefore': v0, 'clientVersionAfter': v1, 'startedUtc': t0,
                'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad, 'errors': errors[:20],
                'probes': pr, 'probesAsSpecified': sum(p['asSpecified'] for p in pr), 'probeCount': len(pr)}

    res = []
    with cf.ThreadPoolExecutor(7) as ex:
        for rr in ex.map(work, nets):
            print(f"{rr['chainId']:>8} {rr['name']:16} ran {rr['ran']}/{rr['vectors']} mism {rr['mismatchCount']} err {len(rr['errors'])} probes {rr['probesAsSpecified']}/{rr['probeCount']} | {rr['clientVersionBefore'][:60]} | {rr['clientVersionAfter'][:40]}", flush=True)
            res.append(rr)
    json.dump({'seed': SEED, 'vectors': len(V), 'perOp': per_op, 'dispatcherSha256': hashlib.sha256(code).hexdigest(), 'results': res}, open(outp, 'w'), indent=1)
