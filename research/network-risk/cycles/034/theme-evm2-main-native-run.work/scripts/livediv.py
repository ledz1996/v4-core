#!/usr/bin/env python3
"""Read-only eth_call on Ethereum (1) and Tempo (4217): a stub placed by state override
computes DIV and MOD at a zero divisor and at full-width divisors and returns the words,
compared with the reference of tools/opdiff/evm.py. Each batch is bracketed with
web3_clientVersion. No transaction is sent. Usage: python3 -I livediv.py <outdir>"""
import sys, os, json, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')))
from evm import assemble, rpc, REF, MASK  # noqa: E402

STUB = '0x00000000000000000000000000000000c0de0034'


def stub(cases):
    p = []
    for i, (op, a, b) in enumerate(cases):
        p += [('PUSH', b), ('PUSH', a), op, ('PUSH', 32 * i), 'MSTORE']
    p += [('PUSH', 32 * len(cases)), ('PUSH', 0), 'RETURN']
    return assemble(p)


if __name__ == '__main__':
    out = sys.argv[1]; rnd = random.Random(4217_1)
    cases = []
    for a in (0, 1, 2, MASK, MASK - 1, 1 << 255, (1 << 192) - 1, 1 << 192):
        cases += [('DIV', a, 0), ('MOD', a, 0)]
    for _ in range(40):
        b = rnd.getrandbits(256) | (1 << rnd.randrange(192, 256)); a = rnd.choice([rnd.getrandbits(256), MASK, b, b - 1, (2 * b) & MASK])
        cases += [('DIV', a & MASK, b), ('MOD', a & MASK, b)]
    code = stub(cases)
    want = [REF[op](a, b, 0) for op, a, b in cases]
    nets = {1: 'https://ethereum-rpc.publicnode.com', 4217: 'https://rpc.mainnet.tempo.xyz'}
    res = {'seed': 4217_1, 'cases': len(cases), 'networks': {}}
    for cid, url in nets.items():
        r = {'url': url}
        try:
            r['clientBefore'] = rpc(url, 'web3_clientVersion', [])
            ret = rpc(url, 'eth_call', [{'to': STUB, 'data': '0x', 'gas': hex(5_000_000)}, 'latest', {STUB: {'code': '0x' + code.hex()}}])
            r['clientAfter'] = rpc(url, 'web3_clientVersion', [])
            r['block'] = int(rpc(url, 'eth_blockNumber', []), 16)
            got = bytes.fromhex(ret[2:])
            words = [int.from_bytes(got[32 * i:32 * i + 32], 'big') for i in range(len(cases))]
            r['mismatches'] = [{'op': c[0], 'a': hex(c[1]), 'b': hex(c[2]), 'got': hex(g), 'want': hex(w)} for c, g, w in zip(cases, words, want) if g != w]
            r['ok'] = len(words) == len(cases)
        except Exception as e:  # noqa
            r['error'] = str(e)[:300]
        r['time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        res['networks'][cid] = r
        print(cid, {k: v for k, v in r.items()})
    json.dump(res, open(os.path.join(out, 'livediv.json'), 'w'), indent=1)
