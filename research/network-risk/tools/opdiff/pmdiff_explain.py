"""For the scripts where a network's answer differs from Ethereum's in pmdiff.py:
fetch both answers again and say, call by call, what differs."""
import sys, json, random, hashlib
from evm import rpc, networks
import pmdiff as P

out = json.load(open(sys.argv[1])); n_scripts = out['scripts']
rnd = random.Random(7_2026_11_24); scripts = [P.script(rnd) for _ in range(n_scripts)]
code = P.fetch_code(); drv = P.driver()
ov = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + drv.hex()}}
urls = {n[0]: n[2] for n in networks()}
gas = int(sys.argv[2]) if len(sys.argv) > 2 else 25_000_000


def call(cid, data, g):
    return bytes.fromhex(rpc(urls[cid], 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(g)}, 'latest', ov], timeout=90)[2:])


for r in out['results']:
    if not r['different']: continue
    kinds_diff = {}; fixed = 0; still = []
    for i in r['different']:
        data, kinds, meta = scripts[i]
        ref = P.parse(call(1, data, 25_000_000)); got = P.parse(call(r['chainId'], data, 25_000_000))
        first = next((k for k, (a, b) in enumerate(zip(ref, got)) if a != b), None)
        if first is None and len(ref) != len(got): first = min(len(ref), len(got))
        why = 'identical on retry' if first is None else f"{kinds[first] if first < len(kinds) else '?'}: ref ok={ref[first][0] if first < len(ref) else None} len={len(ref[first][1]) if first < len(ref) else None} / got ok={got[first][0] if first < len(got) else None} data={got[first][1][:36].hex() if first < len(got) else None}"
        kinds_diff[why[:90]] = kinds_diff.get(why[:90], 0) + 1
        # the same script with a much larger gas allowance
        try:
            big = P.parse(call(r['chainId'], data, gas * 20))
            if big == ref: fixed += 1
            else: still.append(i)
        except Exception as e:  # noqa
            still.append((i, str(e)[:80]))
    print(r['chainId'], r['name'], 'different', len(r['different']), '| identical to Ethereum with 20x gas:', fixed, '| still different:', still[:10])
    for k, v in sorted(kinds_diff.items(), key=lambda x: -x[1])[:6]: print('    ', v, k)
