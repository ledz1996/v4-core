"""L-612: run the lane-exact transcription of the evm2 66687c18 jump destination kernels
(jd_sim.py, copied from the cycle 9 scratch transcription and re-read against
crates/evm2/src/bytecode/analysis.rs and analysis/x86.rs at 66687c18) on

  1. the 24,009 byte runtime of build/PoolManager.json, the deployed Tempo runtime (fetched by
     eth_getCode), and both shifted by 0..127 leading bytes (STOP), so that every byte of the
     runtime meets every lane of the 16, 32, 64 and 128 byte kernels;
  2. PUSH32 with JUMPDEST at each of its 32 data positions, the PUSH32 placed at every offset
     0..255 of a 0x01 filled buffer of several lengths, and PUSHn for every n with all data 0x5b,
     and chains of PUSH32 whose data is all 0x5b.

Each table is compared with the reference rule (one instruction at a time).
Usage: python3 -I jd_l612.py <out.json>
"""
import sys, json, os, urllib.request
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import jd_sim as S

base = here.rsplit('/', 3)[0]


def rpc_code(url, addr):
    req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getCode', 'params': [addr, 'latest']}).encode(),
                                 headers={'content-type': 'application/json'})
    return bytes.fromhex(json.load(urllib.request.urlopen(req, timeout=60))['result'][2:])


def check(code, kernels, bad, tag):
    ref = S.reference(code)
    for k in kernels:
        if S.run(code, k) != ref:
            bad.append({'case': tag, 'kernel': k, 'len': len(code)})
    return ref


if __name__ == '__main__':
    out = sys.argv[1]
    rt = bytes.fromhex(json.load(open(base + '/build/PoolManager.json'))['runtime'])
    nets = {n['chainId']: n for n in json.load(open(base + '/state/networks.json'))['networks']}
    dep = rpc_code(nets[4217]['rpc'], nets[4217]['poolManager'])
    res = {'buildLen': len(rt), 'deployedLen': len(dep)}
    bad = []; n = 0
    K = ['sse41', 'avx2', 'avx512', 'neon']
    for name, code in (('build', rt), ('deployedTempo', dep)):
        for shift in range(0, 128):
            ref = check(bytes(shift) + code, K, bad, f'{name}+{shift}'); n += 1
            if shift == 0:
                res[name + 'JumpdestCount'] = sum(bin(b).count('1') for b in ref)
        print(name, 'done', len(bad), flush=True)
    # PUSH32 lane set
    m = 0
    for L in (80, 160, 300):
        for at in range(0, min(256, L - 33)):
            for j in range(32):
                c = bytearray([0x01] * L); c[at] = 0x7f; c[at + 1 + j] = 0x5b
                if at + 33 < L: c[at + 33] = 0x5b
                check(bytes(c), K, bad, f'push32 L{L} at{at} j{j}'); m += 1
            c = bytearray([0x5b] * L); c[at] = 0x7f
            check(bytes(c), K, bad, f'push32all L{L} at{at}'); m += 1
            for p in range(0x60, 0x80):
                c = bytearray([0x5b] * L); c[at] = p
                check(bytes(c), K, bad, f'pushn L{L} at{at} p{p:x}'); m += 1
    for lead in range(0, 64):
        c = bytes([0x01] * lead) + (bytes([0x7f]) + bytes([0x5b] * 32)) * 8 + bytes([0x5b] * 40)
        check(c, K, bad, f'chain lead{lead}'); m += 1
    res.update({'runtimeCases': n, 'push32Cases': m, 'kernels': K, 'mismatches': bad[:50], 'mismatchCount': len(bad)})
    print(res['runtimeCases'], res['push32Cases'], res['mismatchCount'])
    json.dump(res, open(out, 'w'), indent=1)
