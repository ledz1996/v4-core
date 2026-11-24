"""Fourth script set: malformed input. It takes the scripts of pmdiff3.py and damages
the calldata of the PoolManager calls: truncation, junk appended, single words with
their high bits set (dirty addresses, booleans, int24 and uint24 values), flipped
bytes, a wrong offset for a bytes argument, and another function's selector on the
same arguments. This reaches the reverting side of the checks that well-formed
calls always pass (the ABI decoder, SafeCast, range checks). All scripts end by
reverting with the record. Every network's answer is compared with the reference
interpreter's. Usage: python3 pmdiff4.py <out.json> [nScripts] [chainId ...]
"""
import sys, json, random, hashlib, time, concurrent.futures as cf
from evm import rpc, networks, MASK
import pmdiff as P, pmdiff3 as R
from pyevm import NAMES


def split(blob):
    items = []; i = 0
    while True:
        addr = blob[i:i + 20]; n = int.from_bytes(blob[i + 20:i + 22], 'big')
        if n == 0: return items
        items.append([addr, bytearray(blob[i + 22:i + 22 + n])]); i += 22 + n


def damage(rnd, data, selectors):
    k = rnd.randrange(8); d = bytearray(data); words = (len(d) - 4) // 32
    if k == 0 and len(d) > 4: d = d[:rnd.randrange(0, len(d))]
    elif k == 1: d += rnd.randbytes(rnd.choice([1, 31, 32, 64]))
    elif k == 2 and words:
        j = 4 + 32 * rnd.randrange(words); d[j:j + rnd.choice([1, 8, 12, 29, 31])] = b'\xff' * rnd.choice([1, 8, 12, 29, 31])
    elif k == 3 and words:
        j = 4 + 32 * rnd.randrange(words); d[j] |= 0x80
    elif k == 4:
        for _ in range(rnd.randrange(1, 4)): d[rnd.randrange(len(d))] ^= 1 << rnd.randrange(8)
    elif k == 5 and words:
        j = 4 + 32 * rnd.randrange(words); d[j:j + 32] = rnd.choice([0x20, 0x1000, MASK, len(d), len(d) - 4, 1 << 64]).to_bytes(32, 'big')
    elif k == 6: d[:4] = rnd.choice(selectors)
    else:
        if words: j = 4 + 32 * rnd.randrange(words); d[j:j + 32] = rnd.choice([0, 1, MASK, 1 << 255, (1 << 127), (1 << 128) - 1, (1 << 160), 0x800000, 0x7fffff, 0xffffff, 1 << 24]).to_bytes(32, 'big')
    return bytes(d[:0x1800])


if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 300; only = set(map(int, sys.argv[3:]))
    code = P.fetch_code(); rnd = random.Random(3_2026_11_24); base = [R.build(rnd, i, code) for i in range(n)]
    rnd = random.Random(4_2026_11_24); selectors = list(R.S.values()) + [P.S_INIT, P.S_MOD, P.S_SWAP, P.S_DONATE, P.S_MINT, P.S_BURN, P.S_TAKE, P.S_SETTLE, P.S_CLEAR, P.S_EXTSLOAD, P.S_UNLOCK]
    scripts = []
    for blob, kinds, meta in base:
        items = split(blob)
        for it in items:
            if int.from_bytes(it[0], 'big') == R.PMI and rnd.random() < 0.35: it[1] = bytearray(damage(rnd, bytes(it[1]), selectors))
        scripts.append(b''.join(a + len(d).to_bytes(2, 'big') + bytes(d) for a, d in items if len(d)) + b'\0' * 22)
    ref = []; cover = set(); branches = {}; ops = {}; calls = 0; failed = 0
    for data in scripts:
        wd = R.world(code); wd.max_steps = 20_000_000
        try:
            ok, ret = wd.call(0, R.DRV, 0, data, False, 0)
        except TimeoutError:
            ret = b'heavy'
        ref.append(ret)
        cover |= wd.cover.get(R.PMI, set())
        for (a, pc), o in wd.branches.items():
            if a == R.PMI: branches.setdefault(pc, set()).update(o)
        for o, c in wd.ops.items(): ops[o] = ops.get(o, 0) + c
        if ret != b'heavy':
            for k, r in P.parse(ret): calls += 1; failed += 1 - k
    json.dump({'cover': sorted(cover), 'branches': {str(k): sorted(v) for k, v in branches.items()}, 'ops': {NAMES.get(o, hex(o)): c for o, c in ops.items()}},
              open(out.replace('.json', '-coverage.json'), 'w'))
    print(n, 'scripts,', calls, 'calls,', failed, 'failed in the reference')
    refh = [hashlib.sha256(r).hexdigest() if r != b'heavy' else 'heavy' for r in ref]; ov = R.overrides(code)
    print(sum(1 for h in refh if h == 'heavy'), 'scripts left out as too long for the reference')

    def ask(url, data, gas):
        last = None
        for k in range(5):
            try:
                return hashlib.sha256(bytes.fromhex(rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(gas)}, 'latest', ov], timeout=120)[2:])).hexdigest()
            except Exception as e:  # noqa
                last = str(e)[:120]
                if 'gas' in last.lower() and 'limit' in last.lower(): break
                time.sleep(3 * (k + 1))
        return 'ERR ' + last

    def run_net(nw):
        cid, name, url = nw; res = []
        for i, data in enumerate(scripts):
            if refh[i] == 'heavy': res.append('heavy'); continue
            h = ask(url, data, 25_000_000)
            if h != refh[i] and not h.startswith('ERR'):
                for gas in (2_000_000_000, 150_000_000):
                    h2 = ask(url, data, gas)
                    if not h2.startswith('ERR'): h = h2 if h2 == refh[i] else h; break
            res.append(h)
        return cid, name, res

    summary = []
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, res in ex.map(run_net, [x for x in networks() if not only or x[0] in only]):
            diff = [i for i, (a, b) in enumerate(zip(res, refh)) if a != b and not a.startswith('ERR')]; err = [a for a in res if a.startswith('ERR')]
            print(f'{cid:>8} {name:16} equal to the reference {sum(1 for a, b in zip(res, refh) if a == b)}/{n} different {len(diff)} errors {len(err)} {err[:1]}', flush=True)
            summary.append({'chainId': cid, 'name': name, 'identical': sum(1 for a, b in zip(res, refh) if a == b), 'different': diff, 'errors': len(err)})
    json.dump({'scripts': n, 'calls': calls, 'failedInReference': failed, 'results': summary, 'referenceHashes': refh}, open(out, 'w'), indent=1)
