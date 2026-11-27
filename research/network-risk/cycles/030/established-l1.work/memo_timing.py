"""Timing probe for bor's MULMOD reciprocal memo (L-1076, L-1191). Read-only eth_call.
Two loops of the same length run 16 MULMODs per iteration with full-width moduli:
'same' uses one modulus for all of them, 'alt' alternates 2^256-189 and 2^256-1 (the
FullMath.mulDiv pattern). A memo that keeps one reciprocal makes 'same' cheaper than 'alt';
stock MulMod costs the same for both. The words are not checked here (battery does that);
the loop's last MULMOD result is returned for a spot check.
Usage: python3 memo_timing.py <out.json> <label=rpc> ...
"""
import sys, json, time, urllib.request

M1, M2 = (1 << 256) - 189, (1 << 256) - 1
A, B = (1 << 255) + 0x1234567, (1 << 254) + 0x89abcdef
ITERS = 110_000
STUB = '0x00000000000000000000000000000000c0ffee31'


def code(alt):
    c = '7f%064x' % M2 + '7f%064x' % M1 + '7f%064x' % B + '7f%064x' % A + '62%06x' % ITERS
    body = ''
    for k in range(16):
        dm = '84' if (alt and k % 2) else '83'  # DUP5 -> m2, DUP4 -> m1
        body += dm + '83' + '83' + '09' + '50'  # m, b, a ; MULMOD ; POP
    head = len(c) // 2
    c += '5b' + body + '600190' + '03' + '80' + '61%04x' % head + '57'
    # result: mulmod(a, b, m_last) stored and returned
    c += '83' + '83' + '83' + '09' + '5f52' + '60205ff3'
    return '0x' + c


def call(url, bc):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call',
                       'params': [{'to': STUB, 'gas': hex(45_000_000)}, 'latest', {STUB: {'code': bc}}]}).encode()
    t = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, data=body, headers={'content-type': 'application/json'}), timeout=60))
    return time.time() - t, r


def ver(url):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=body, headers={'content-type': 'application/json'}), timeout=30)).get('result')


def main():
    out = {'iters': ITERS, 'mulmodsPerCall': ITERS * 16, 'runs': []}
    codes = {'same': code(False), 'alt': code(True)}
    for spec in sys.argv[2:]:
        label, url = spec.split('=', 1)
        for rep in range(6):
            for kind in ('same', 'alt'):
                v1 = ver(url)
                dt, r = call(url, codes[kind])
                v2 = ver(url)
                ok = 'result' in r and int(r['result'], 16) == (A * B) % M1
                rec = {'label': label, 'kind': kind, 'rep': rep, 'seconds': round(dt, 4), 'ok': ok,
                       'err': r.get('error'), 'clientBefore': v1, 'clientAfter': v2}
                out['runs'].append(rec)
                print(json.dumps(rec)[:300], flush=True)
    json.dump(out, open(sys.argv[1], 'w'), indent=1)


main()
