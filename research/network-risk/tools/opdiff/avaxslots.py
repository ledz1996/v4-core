"""Avalanche C-Chain clears bit 248 of every storage slot index (finding F-040). This scans
contract bytecode on Avalanche for 32 byte constants that the rule would make collide:
two constants in one contract that differ only in bit 248, and constants with bit 248 set
that sit next to SLOAD or SSTORE. It reads the official v4 contracts from state/networks.json
and every hook that an Initialize event of the PoolManager names.

Usage: python3 avaxslots.py <out.json> [hook census json.gz from cycle 5]
"""
import sys, json, gzip, os, time
from evm import rpc

B = 1 << 248
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
HERE = os.path.dirname(os.path.abspath(__file__))


def consts(code):
    out = []; i = 0
    while i < len(code):
        op = code[i]
        if 0x60 <= op <= 0x7f:
            n = op - 0x5f
            if n == 32: out.append((i, int.from_bytes(code[i + 1:i + 33], 'big'), code[i + 33] if i + 33 < len(code) else None))
            i += 1 + n
        else: i += 1
    return out


def scan(code):
    cs = consts(code); vals = {v for _, v, _ in cs}
    pairs = sorted(hex(v) for v in vals if not (v >> 248) & 1 and (v ^ B) in vals)
    near = [[pc, hex(v)] for pc, v, nx in cs if (v >> 248) & 1 and nx in (0x54, 0x55)]
    return {'bytes': len(code), 'constants': len(vals), 'pairs': pairs, 'oddNextToStorage': near}


def get(url, method, params):
    for k in range(6):
        try: return rpc(url, method, params, timeout=60)
        except Exception as e:  # noqa
            err = e; time.sleep(2 * (k + 1))
    raise err


if __name__ == '__main__':
    out = sys.argv[1]
    nw = [x for x in json.load(open(os.path.join(HERE, '..', '..', 'state', 'networks.json')))['networks'] if x['chainId'] == 43114][0]
    url = nw['rpc']; res = {'official': {}, 'hooks': {}}
    for name, a in nw['contracts'].items():
        res['official'][name.replace('\xa0', ' ')] = dict(scan(bytes.fromhex(get(url, 'eth_getCode', [a, 'latest'])[2:])), address=a)
    hooks = set(); hi = 0
    if len(sys.argv) > 2:
        d = json.load(gzip.open(sys.argv[2])); hi = d['hi']
        for r in d['rows']:
            h = r[6]
            if h and int(h, 16): hooks.add(h.lower())
    # newer pools: Initialize logs after the census, from an endpoint that serves wide ranges
    logs_url = 'https://avalanche.gateway.tenderly.co'; head = int(get(url, 'eth_blockNumber', []), 16); lo = hi + 1 if hi else head - 2_000_000
    while lo <= head:
        to = min(lo + 99_999, head)
        for l in get(logs_url, 'eth_getLogs', [{'address': nw['poolManager'], 'fromBlock': hex(lo), 'toBlock': hex(to), 'topics': [INIT]}]):
            h = '0x' + l['data'][2 + 64 * 2 + 24:2 + 64 * 3]
            if int(h, 16): hooks.add(h.lower())
        lo = to + 1
    for h in sorted(hooks):
        code = bytes.fromhex(get(url, 'eth_getCode', [h, 'latest'])[2:])
        res['hooks'][h] = scan(code)
    hit = {h: r for h, r in res['hooks'].items() if r['pairs'] or r['oddNextToStorage']}
    res['summary'] = {'head': head, 'hooks': len(hooks), 'hooksWithCode': sum(1 for r in res['hooks'].values() if r['bytes']), 'hooksFlagged': len(hit),
                      'officialFlagged': sum(1 for r in res['official'].values() if r['pairs'] or r['oddNextToStorage'])}
    print(res['summary']); print(json.dumps(hit, indent=1)[:3000])
    json.dump(res, open(out, 'w'), indent=1)
