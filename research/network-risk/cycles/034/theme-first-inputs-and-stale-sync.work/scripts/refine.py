"""Task 2 refinement: for every pool in out/pools-<label>.json, read the tick bitmap words the first swap step would search
(src/libraries/TickBitmap.sol:85-122: lte=false starts at compressed+1, lte=true at compressed), take the step target
exactly as nextInitializedTickWithinOneWord and Pool.swap (src/libraries/Pool.sol:347-364) do, and compute the
getAmount1Delta product liquidity * |sqrtP_target - sqrtP_current| with (a) the pool's in-range liquidity and (b) that plus
one position of maxLiquidityPerTick that an ordinary account adds around the current tick without creating a tick inside
the step. Then run the up step through v4math.compute_swap_step and pyevm-equivalent arithmetic for the top 50 by liquidity.
Usage: python3 refine.py <label> <url> <pm>"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak, rpc
import v4math as m
label, url, pm = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(f'out/pools-{label}.json'))
SEL = keccak(b'extsload(bytes32)')[:4]
def R(mth, p):
    for k in range(6):
        try: return rpc(url, mth, p, timeout=120)
        except Exception as e: err = e; time.sleep(1.5 * (k + 1))
    raise err
def ext(slot): return int(R('eth_call', [{'to': pm, 'data': '0x' + SEL.hex() + (slot % (1 << 256)).to_bytes(32, 'big').hex()}, 'latest']), 16)
def ml(ts):
    mn = -(887272 // ts) - (1 if 887272 % ts else 0); return ((1 << 128) - 1) // ((887272 // ts) - mn + 1)
def comp(t, ts): q = int(t / ts); return q - (1 if (t % ts != 0 and t < 0) else 0) if False else (t // ts)  # floor division == compress
def word(pid, wp):
    base = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big') + 5
    slot = int.from_bytes(keccak(int(wp).to_bytes(32, 'big', signed=True) + base.to_bytes(32, 'big')), 'big'); return ext(slot)
res = {'label': label, 'clientVersionBefore': R('web3_clientVersion', []), 'block': int(R('eth_blockNumber', []), 16), 'pools': {}}
TOP = 1 << 256
for pid, p in d['pools'].items():
    if not p.get('sqrtPriceX96') or 'tickSpacing' not in p: continue
    ts, t, P0, L = p['tickSpacing'], p['tick'], p['sqrtPriceX96'], p['liquidity']
    c = t // ts
    # up (lte = false)
    cu = c + 1; wpu, bpu = cu >> 8, cu & 0xff; wu = word(pid, wpu); mk = wu & ~((1 << bpu) - 1)
    nu = (cu + ((mk & -mk).bit_length() - 1 - bpu)) * ts if mk else (cu + 255 - bpu) * ts
    nu = min(nu, m.MAX_TICK)
    # down (lte = true)
    wpd, bpd = c >> 8, c & 0xff; wd = word(pid, wpd); mk = wd & ((1 << (bpd + 1)) - 1)
    nd = (c - (bpd - (mk.bit_length() - 1))) * ts if mk else (c - bpd) * ts
    nd = max(nd, m.MIN_TICK)
    du = max(0, m.get_sqrt_price_at_tick(nu) - P0); dd = max(0, P0 - m.get_sqrt_price_at_tick(nd))
    La = min((1 << 128) - 1, L + ml(ts))
    r = {'tick': t, 'tickSpacing': ts, 'liquidity': L, 'nextUp': nu, 'nextDown': nd,
         'log2ProdUp': (L * du).bit_length(), 'log2ProdDown': (L * dd).bit_length(),
         'log2ProdUpPlusOnePosition': (La * du).bit_length(), 'log2ProdDownPlusOnePosition': (La * dd).bit_length(),
         'hooks': p.get('hooks'), 'currency0': p.get('currency0'), 'currency1': p.get('currency1')}
    r['wideToday'] = L * max(du, dd) >= TOP
    r['wideWithOnePosition'] = La * max(du, dd) >= TOP
    if L:  # one step with a far limit: does the up step cross the 2^256 line? amount1 to the target in units
        sp_, ai, ao, fee = m.compute_swap_step(P0, m.get_sqrt_price_at_tick(nu) if nu > t else P0 + 1, L, -(1 << 127) + 1, p.get('fee', 0) & 0xffffff if p.get('fee', 0) < 1000000 else 0)
        r['upStepAmountInLog2'] = ai.bit_length()
    res['pools'][pid] = r
ps = res['pools']
res['counts'] = {'pools': len(ps), 'wideToday': sum(r['wideToday'] for r in ps.values()), 'wideWithOnePosition': sum(r['wideWithOnePosition'] for r in ps.values()),
                 'maxLog2ProdToday': max([max(r['log2ProdUp'], r['log2ProdDown']) for r in ps.values()] or [0]),
                 'maxLog2ProdWithOnePosition': max([max(r['log2ProdUpPlusOnePosition'], r['log2ProdDownPlusOnePosition']) for r in ps.values()] or [0])}
res['top50'] = sorted(([k, r['liquidity'], r['tick'], r['tickSpacing'], max(r['log2ProdUp'], r['log2ProdDown']), max(r['log2ProdUpPlusOnePosition'], r['log2ProdDownPlusOnePosition'])] for k, r in ps.items()), key=lambda x: -x[1])[:50]
res['wideWithOnePositionList'] = [[k, r['tick'], r['tickSpacing'], r['liquidity'], r['nextUp'], r['nextDown'], max(r['log2ProdUpPlusOnePosition'], r['log2ProdDownPlusOnePosition']), r['hooks']] for k, r in ps.items() if r['wideWithOnePosition']]
res['clientVersionAfter'] = R('web3_clientVersion', [])
json.dump(res, open(f'out/refined-{label}.json', 'w'), indent=1)
print(label, res['clientVersionBefore'], res['block'], res['counts'])
for x in res['wideWithOnePositionList'][:30]: print(x)
