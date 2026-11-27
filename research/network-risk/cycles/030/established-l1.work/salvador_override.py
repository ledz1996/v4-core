"""L-1191: eth_call on Polygon with blockOverrides number at, before and after Salvador.
A probe placed by state override returns NUMBER, the EXTCODESIZE and EXTCODEHASH of the five
Salvador targets, CLZ(0x1e) and a MULMOD word. Read-only. Usage: python3 salvador_override.py <out.json> [rpc]
"""
import sys, json, time, urllib.request

RPC = sys.argv[2] if len(sys.argv) > 2 else 'https://polygon-bor-rpc.publicnode.com'
TARGETS = ['e4C4C39C1733e1C7c06B79f97ED442B68Df41EC6', '5392587814Ce8c6af6789764f88e5e9AB0b9962C',
           'c91ee0574a14446DE200923729c349B9CAE19b60', '3f7019221a925537dC20767C38e80A7127fb1Ffa',
           '5227f603C1eE34CE3C06eFe6477003BDfCCB2f8c']
PROBE = '0x00000000000000000000000000000000c0ffee30'


def code():
    c = '43' + '5f' + '52'  # NUMBER PUSH0 MSTORE
    off = 32
    for t in TARGETS:
        c += '73' + t.lower() + '3b' + '61%04x' % off + '52'; off += 32  # EXTCODESIZE
        c += '73' + t.lower() + '3f' + '61%04x' % off + '52'; off += 32  # EXTCODEHASH
    c += '601e' + '1e' + '61%04x' % off + '52'; off += 32  # CLZ(0x1e)
    # MULMOD(a, b, m) with a full width modulus, then with 2^256-1
    a, b, m = (1 << 255) + 12345, (1 << 254) + 999, (1 << 256) - 189
    c += '7f%064x' % m + '7f%064x' % b + '7f%064x' % a + '09' + '61%04x' % off + '52'; off += 32
    c += '5f19' + '7f%064x' % b + '7f%064x' % a + '09' + '61%04x' % off + '52'; off += 32
    c += '61%04x' % off + '5f' + 'f3'
    return '0x' + c, off, (a * b) % m, (a * b) % ((1 << 256) - 1)


def rpc(method, params):
    req = urllib.request.Request(RPC, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 headers={'content-type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    out = sys.argv[1]
    bc, n, mm1, mm2 = code()
    res = []
    head = int(rpc('eth_blockNumber', [])['result'], 16)
    for num in [None, 98688599, 98688600, 98688601, 99000000]:
        v1 = rpc('web3_clientVersion', [])['result']
        bo = {} if num is None else {'number': hex(num)}
        r = rpc('eth_call', [{'to': PROBE, 'data': '0x', 'gas': hex(5_000_000)}, 'latest', {PROBE: {'code': bc}}, bo])
        v2 = rpc('web3_clientVersion', [])['result']
        rec = {'override': num, 'head': head, 'clientBefore': v1, 'clientAfter': v2}
        if 'result' in r:
            w = [int(r['result'][2 + 64 * i: 66 + 64 * i], 16) for i in range(n // 32)]
            rec['number'] = w[0]
            rec['targets'] = [{'addr': t, 'codesize': w[1 + 2 * i], 'codehash': '%064x' % w[2 + 2 * i]} for i, t in enumerate(TARGETS)]
            rec['clz_0x1e'] = w[11]
            rec['mulmod_fullwidth_ok'] = w[12] == mm1
            rec['mulmod_allones_ok'] = w[13] == mm2
        else:
            rec['error'] = r.get('error')
        res.append(rec)
        print(json.dumps(rec))
        time.sleep(0.3)
    json.dump({'rpc': RPC, 'probe': bc, 'records': res}, open(out, 'w'), indent=1)


main()
