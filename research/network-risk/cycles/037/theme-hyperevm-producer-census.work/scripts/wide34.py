"""Tasks 1 and 3: scripts that reach the wide (product >= 2^256) MULMOD sites of the getAmount1Delta and fee copies of
mulDiv, run in pyevm.py (this checkout's build, research/network-risk/build/PoolManager.json) with a MULMOD operand log,
then by eth_call (state override, nothing deployed, the driver reverts with its record) on the given endpoints.
Usage: python3 wide.py ref            -> out/wide-ref.json
       python3 wide.py net <label> <url> -> out/wide-<label>.json  (brackets the batch with web3_clientVersion)
Deterministic: no random sampling (seed not used)."""
import sys, os, json, hashlib, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
os.environ['PM_BUILD'] = '/home/user/v4-core/research/network-risk/build/PoolManager.json'
import pmdiff as P, v4math as m
from pyevm import World
from evm import rpc
sp = m.get_sqrt_price_at_tick
def ml(ts):
    mn = -(887272 // ts) - (1 if 887272 % ts else 0); return ((1 << 128) - 1) // ((887272 // ts) - mn + 1)
def item(cd): return len(cd).to_bytes(2, 'big') + cd
CASES = []
def case(name, fee, ts, t0, pos, swaps, price=None):
    calls = [P.c_init(fee, ts, price if price is not None else sp(t0))]
    for lo, hi, L in pos: calls.append(P.c_mod(fee, ts, lo, hi, L))
    for zfo, amt, lim in swaps:
        calls.append(P.c_swap(fee, ts, zfo, amt, lim))
        for k in (0, 1, 2, 3): calls.append(P.c_ext(P.pool_slot(fee, ts, k)))
        calls.append(P.S_EXTTLOAD + P.w(P.delta_slot(int(P.DRV, 16), P.C0))); calls.append(P.S_EXTTLOAD + P.w(P.delta_slot(int(P.DRV, 16), P.C1)))
    CASES.append({'name': name, 'fee': fee, 'ts': ts, 'data': b''.join(item(c) for c in calls) + b'\0\0', 'pos': pos, 'swaps': swaps})
W = 819200  # a word start for tick spacing 1 (3200 * 256)
L1 = ml(1)
# A: one position of maxLiquidityPerTick(1) inside one bitmap word near the top; oneForZero exact input with a far limit:
#    getAmount1Delta(cur, target) at SwapMath.sol:68 sees L1 * (sp(W+255) - sp(W)) >= 2^256, amountRemaining is small
CASES_SPEC = [
 ('A-oneForZero-exactIn-small', 3000, 1, W, [(W, W + 255, L1)], [(False, -(10 ** 18), m.MAX_SQRT_PRICE - 1)]),
 ('B-oneForZero-exactOut-small', 3000, 1, W, [(W, W + 255, L1)], [(False, 10 ** 15, m.MAX_SQRT_PRICE - 1)]),
 ('C-zeroForOne-exactIn-from-top', 3000, 1, W + 254, [(W, W + 255, L1)], [(True, -(10 ** 18), sp(W))]),
 ('C0-gasbound-zeroForOne-exactIn-no-liquidity-walk', 3000, 1, W + 255, [(W, W + 255, L1)], [(True, -(10 ** 18), m.MIN_SQRT_PRICE + 1)]),
 ('D-zeroForOne-exactOut-from-top', 3000, 1, W + 254, [(W, W + 255, L1)], [(True, 10 ** 30, sp(W))]),
 ('D2-zeroForOne-exactOut-small', 3000, 1, W + 254, [(W, W + 255, L1)], [(True, 10 ** 6, sp(W))]),
 ('E-fee-copy-amountSpecified-2^250', 3000, 60, 0, [(-600, 600, 10 ** 18)], [(True, -(1 << 250), m.get_sqrt_price_at_tick(-60))]),
 ('F-fee-copy-int256-min', 500, 10, 0, [(-100, 100, 10 ** 18)], [(False, -(1 << 255), m.get_sqrt_price_at_tick(50))]),
 ('G-spacing-60-top-word', 3000, 60, 15360 * 43, [(15360 * 43, 15360 * 43 + 60 * 255, ml(60))], [(False, -(10 ** 20), m.MAX_SQRT_PRICE - 1)]),
 ('H-spacing-32767-whole-range', 10000, 32767, -884709, [(-884709, 884709, ml(32767))], [(False, -(10 ** 20), m.MAX_SQRT_PRICE - 1), (True, -(10 ** 20), m.MIN_SQRT_PRICE + 1)]),
 ('I-oneForZero-exactIn-reaches-target-int128-bound', 3000, 1, W, [(W, W + 255, L1)], [(False, -((1 << 127) - 1), m.MAX_SQRT_PRICE - 1)]),
]
for s in CASES_SPEC: case(*s)
def ref():
    code = P.fetch_code(); drv = P.driver(); pm = int(P.PM, 16); out = []
    for c in CASES:
        w = World({pm: code, int(P.DRV, 16): drv}); w.trace = []; w.trace_stack = 3; w.max_steps = 20_000_000
        ok, ret = w.call(0, int(P.DRV, 16), 0, c['data'], False, 0)
        mm = {}
        for depth, pc, op, stk in w.trace:
            if op == 0x09 and depth >= 1 and stk and len(stk) == 3:
                c_, b_, a_ = stk  # stack top is a
                prod = a_ * b_
                r = mm.setdefault(pc, {'n': 0, 'wide': 0, 'maxLog2Product': 0, 'moduli': set(), 'example': None})
                r['n'] += 1
                if prod >> 256:
                    r['wide'] += 1
                    if r['example'] is None: r['example'] = [hex(a_), hex(b_), hex(c_), hex(prod % c_ if c_ else 0)]
                r['maxLog2Product'] = max(r['maxLog2Product'], prod.bit_length())
                r['moduli'].add('2^256-1' if c_ == (1 << 256) - 1 else ('2^96' if c_ == 1 << 96 else ('1e6' if c_ == 10 ** 6 else 'other')))
        recs = P.parse(ret)
        res = {'name': c['name'], 'steps': w.steps, 'okFlags': [r[0] for r in recs], 'returnSha256': hashlib.sha256(ret).hexdigest(),
               'returnHex': ret.hex(), 'mulmod': {str(k): dict(v, moduli=sorted(v['moduli'])) for k, v in sorted(mm.items())},
               'calldata': '0x' + c['data'].hex()}
        out.append(res)
        print(c['name'], 'steps', w.steps, 'ok', res['okFlags'], {k: (v['n'], v['wide'], v['maxLog2Product'], v['moduli']) for k, v in res['mulmod'].items() if v['wide']})
    json.dump(out, open('out/wide-ref.json', 'w'), indent=1)
def net(label, url):
    code = P.fetch_code(); drv = P.driver(); ref = {r['name']: r for r in json.load(open('out/wide-ref.json'))}
    ov = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + drv.hex()}}
    log = {'label': label, 'url': url, 'clientVersionBefore': None, 'clientVersionAfter': None, 'results': []}
    try: log['clientVersionBefore'] = rpc(url, 'web3_clientVersion', [])
    except Exception as e: log['clientVersionBefore'] = 'ERR ' + str(e)[:200]
    try: log['blockBefore'] = int(rpc(url, 'eth_blockNumber', []), 16)
    except Exception as e: log['blockBefore'] = 'ERR ' + str(e)[:200]
    for c in CASES:
        r = None
        for k in range(3):
            try:
                r = rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + c['data'].hex(), 'gas': hex(25_000_000)}, 'latest', ov], timeout=90); break
            except Exception as e:
                r = 'ERR ' + str(e)[:300]; time.sleep(2 * (k + 1))
        eq = isinstance(r, str) and r.startswith('0x') and r[2:] == ref[c['name']]['returnHex']
        rec = {'name': c['name'], 'equalToReference': eq}
        if not eq: rec['answer'] = r; rec['reference'] = ref[c['name']]['returnHex']
        log['results'].append(rec); print(label, c['name'], eq if eq else (r[:200] if isinstance(r, str) else r))
        time.sleep(0.3)
    try: log['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [])
    except Exception as e: log['clientVersionAfter'] = 'ERR ' + str(e)[:200]
    json.dump(log, open(f'out/wide-{label}.json', 'w'), indent=1)
if __name__ == '__main__':
    if sys.argv[1] == 'ref': ref()
    else: net(sys.argv[2], sys.argv[3])
