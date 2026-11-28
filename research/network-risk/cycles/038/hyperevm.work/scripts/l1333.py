"""L-1333: a swap with an exact-input amount wide enough that SwapMath.sol:64-65 mulDiv(uint256(-amountRemaining), 1e6 - fee, 1e6)
has a 512 bit product, run by eth_call against EXISTING hookless pools of the DEPLOYED HyperEVM PoolManager. A driver placed by
state override calls unlock; in the callback it reads slot0 and liquidity, swaps, reads them again and the two currency deltas,
then reverts with the record, so nothing is settled or persisted. Answers are compared between the official endpoint and the two
nanoreth replicas and with v4math.compute_swap_step (single step check). Usage: python3 l1333.py <out.json>. Read-only."""
import sys, json, hashlib
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pmdiff as P, v4math as m
from evm import rpc, keccak
REALPM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
P.PM = REALPM
DRV = P.DRV
drv = P.driver()
EPS = [('official', 'https://rpc.hyperliquid.xyz/evm'), ('purroof', 'https://rpc.purroofgroup.com'), ('hyperlend', 'https://rpc.hyperlend.finance/archive')]
POOLS = [p for p in json.load(open(sys.argv[2] if len(sys.argv) > 2 else 'out/pools38.json'))['hookless']]
pick = ['0x10286777f517d918', '0x3c4a8680e5e1a582', '0x4bf2e188c58f4097']
POOLS = [p for p in POOLS if p['id'][:18] in pick]
def w(x): return P.w(x)
def kw(p): return w(int(p['c0'], 16)) + w(int(p['c1'], 16)) + w(p['fee']) + w(p['ts']) + w(0)
def item(cd): return len(cd).to_bytes(2, 'big') + cd
def slot(p, k): return (int.from_bytes(keccak(bytes.fromhex(p['id'][2:]) + w(6)), 'big') + k) & P.MASK
def dslot(cur): return int.from_bytes(keccak(w(int(DRV, 16)) + w(cur)), 'big')
out = {'cases': []}
for p in POOLS:
    for zfo in (True, False):
        for e in (236, 240, 250, 255):
            amt = -(1 << e) if e < 255 else -((1 << 255) - 1)
            calls = [P.c_ext(slot(p, 0)), P.c_ext(slot(p, 3))]
            # limit: about 2 ticks away from the current price, inside the current tick spacing range in most pools
            cur = p['sqrtPriceX96']
            lim = m.get_sqrt_price_at_tick(p['tick'] - 2) if zfo else m.get_sqrt_price_at_tick(p['tick'] + 3)
            calls.append(P.S_SWAP + kw(p) + w(int(zfo)) + w(amt) + w(lim) + w(0x120) + w(0))
            calls += [P.c_ext(slot(p, 0)), P.c_ext(slot(p, 3)), P.S_EXTTLOAD + w(dslot(int(p['c0'], 16))), P.S_EXTTLOAD + w(dslot(int(p['c1'], 16)))]
            data = b''.join(item(c) for c in calls) + b'\0\0'
            case = {'pool': p['id'], 'zeroForOne': zfo, 'amountSpecified': str(amt), 'log2': e, 'limit': lim, 'answers': {}}
            for name, url in EPS:
                try:
                    r = rpc(url, 'eth_call', [{'to': DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest', {DRV: {'code': '0x' + drv.hex()}}], timeout=90)
                    recs = P.parse(bytes.fromhex(r[2:]))
                    case['answers'][name] = {'sha': hashlib.sha256(bytes.fromhex(r[2:])).hexdigest()[:16], 'ok': [ok for ok, _ in recs], 'words': [d.hex() for _, d in recs]}
                except Exception as ex:
                    case['answers'][name] = {'err': str(ex)[:200]}
            a = case['answers']['official']
            if 'words' in a and all(a['ok']):
                s0b = int(a['words'][0], 16); Lb = int(a['words'][1], 16); sw = a['words'][2]
                d0 = int.from_bytes(bytes.fromhex(sw)[:16], 'big', signed=True); d1 = int.from_bytes(bytes.fromhex(sw)[16:32], 'big', signed=True)
                s0a = int(a['words'][3], 16); La = int(a['words'][4], 16)
                case['swapDelta'] = [d0, d1]; case['priceBefore'] = s0b & ((1 << 160) - 1); case['priceAfter'] = s0a & ((1 << 160) - 1)
                case['liquidityBefore'] = Lb; case['liquidityAfter'] = La
                case['driverDeltas'] = [int.from_bytes(bytes.fromhex(a['words'][5]), 'big', signed=True), int.from_bytes(bytes.fromhex(a['words'][6]), 'big', signed=True)]
                lpfee = (s0b >> 208) & 0xffffff
                case['wideProduct'] = ((-amt) * (10 ** 6 - lpfee)) >> 256 != 0
                if La == Lb and case['priceAfter'] == lim:
                    np_, ain, aout, fee = m.compute_swap_step(case['priceBefore'], lim, Lb, amt, lpfee)
                    exp = (-(ain + fee), aout) if zfo else (aout, -(ain + fee))
                    case['singleStepReference'] = list(exp); case['equalToReference'] = list(exp) == [d0, d1] and np_ == lim
            shas = {k: v.get('sha', v.get('err')) for k, v in case['answers'].items()}
            case['endpointsAgree'] = len(set(shas.values())) == 1
            print(p['id'][:18], zfo, e, shas, case.get('swapDelta'), case.get('wideProduct'), case.get('equalToReference'))
            out['cases'].append(case)
for name, url in EPS: out.setdefault('clientVersion', {})[name] = rpc(url, 'web3_clientVersion', [])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
