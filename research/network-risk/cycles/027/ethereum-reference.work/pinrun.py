"""Run the battery, targeted and extra vectors on one gateway, keeping only batches whose
eth_call is bracketed by the same web3_clientVersion string before and after, and that string
is the wanted build. Each batch is retried until it is pinned to the build or tries run out.
Read-only: eth_call with a state override only.
Usage: python3 pinrun.py <out.json> <url> <build substring> <sets comma list> [batch size] [tries]"""
import sys, json, random, threading, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm, battery, targeted
from evm import MASK, SIGN

def extra(seed=1027):
    r = random.Random(seed); V = []
    hi = [1 << 64, 1 << 128, 1 << 192, (1 << 64) | (1 << 128), MASK ^ ((1 << 64) - 1)]
    vals = [0, 1, 0x7f, 0x80, 0xff, 0x7fff, 0x8000, 0x800000, 0x7fffff, SIGN, MASK, MASK - 1] + [r.getrandbits(256) for _ in range(30)]
    # SIGNEXTEND, BYTE, shifts with a small low limb and nonzero high limbs (spec: index >= 31/32/256)
    for small in (0, 1, 2, 14, 15, 30, 31, 32, 255):
        for h in hi:
            for v in vals:
                V.append(('SIGNEXTEND', small + h, v, 0)); V.append(('BYTE', small + h, v, 0))
                V.append(('SHL', small + h, v, 0)); V.append(('SHR', small + h, v, 0)); V.append(('SAR', small + h, v, 0))
    # SIGNEXTEND and BYTE at every index with sign patterns
    for k in range(0, 40):
        for v in vals: V.append(('SIGNEXTEND', k, v, 0)); V.append(('BYTE', k, v, 0))
    # JUMPI condition only in one high bit
    for b in range(256): V.append(('JUMPI', 1 << b, 0, 0))
    # EXP edges
    for a in (0, 1, 2, 3, MASK, SIGN, 10, 1 << 128):
        for e in (0, 1, 2, 255, 256, 257, MASK, 1 << 64, (1 << 64) + 1, r.getrandbits(256)):
            V.append(('EXP', a, e, 0))
    # SDIV / SMOD at INT_MIN and -1 and the tick range
    for a in (SIGN, SIGN + 1, MASK, 1, 887272, (-887272) & MASK, (-887273) & MASK):
        for b in (MASK, 1, 2, 60, 200, (-60) & MASK, SIGN, 887272, 0):
            V.append(('SDIV', a, b, 0)); V.append(('SMOD', a, b, 0)); V.append(('MOD', a, b, 0)); V.append(('DIV', a, b, 0))
    # MULMOD and ADDMOD with modulus 2^256-1 and full-width operands
    for _ in range(400):
        a, b = r.getrandbits(256), r.getrandbits(256)
        V.append(('MULMOD', a, b, MASK)); V.append(('ADDMOD', a, b, MASK)); V.append(('MULMOD', a, b, r.getrandbits(256) | SIGN))
    return V

def main():
    out, url, want, sets = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
    size = int(sys.argv[5]) if len(sys.argv) > 5 else 600
    tries = int(sys.argv[6]) if len(sys.argv) > 6 else 60
    code = battery.dispatcher(); V = []
    if 'battery' in sets: V += battery.vectors()
    if 'targeted' in sets: V += targeted.vectors()
    if 'extra' in sets: V += extra()
    batches = [V[i:i + size] for i in range(0, len(V), size)]
    stats = {'pinned': 0, 'attempts': 0, 'versions': {}, 'unpinned': 0}
    lock = threading.Lock(); bad = []

    def cv():
        try: return evm.rpc(url, 'web3_clientVersion', [], 20)
        except Exception as e: return 'ERR ' + str(e)[:50]

    def work(bi):
        batch = batches[bi]; data = battery.encode(batch)
        for t in range(tries):
            b = cv()
            with lock: stats['attempts'] += 1
            if want not in b: continue
            try: res = bytes.fromhex(evm.rpc(url, 'eth_call', [{'to': evm.STUB, 'data': '0x' + data.hex()}, 'latest', {evm.STUB: {'code': '0x' + code.hex()}}], 90)[2:])
            except Exception as e: time.sleep(1); continue
            a = cv()
            with lock: stats['versions'][a] = stats['versions'].get(a, 0) + 1
            if a != b: continue
            exp = battery.expected(batch, data)
            if len(res) != 32 * len(batch): continue
            mm = []
            for k, (tup, e) in enumerate(zip(batch, exp)):
                g = int.from_bytes(res[32 * k:32 * k + 32], 'big')
                if g != e: mm.append({'op': tup[0], 'a': hex(tup[1]), 'b': hex(tup[2]), 'c': hex(tup[3]), 'got': hex(g), 'want': hex(e)})
            with lock: stats['pinned'] += 1; bad.extend(mm)
            return len(batch)
        with lock: stats['unpinned'] += 1
        return 0

    with cf.ThreadPoolExecutor(6) as ex: ran = sum(ex.map(work, range(len(batches))))
    r = {'url': url, 'build': want, 'sets': sets, 'vectors': len(V), 'batches': len(batches), 'ranPinned': ran, 'mismatchCount': len(bad), 'mismatches': bad[:200], **stats}
    json.dump(r, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != 'mismatches'}, indent=1))

if __name__ == '__main__': main()
