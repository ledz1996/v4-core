"""L-821: for the 21 Ethereum pools whose hook is empty or delegated (cycle 17 census), read every
tick bitmap word and the TickInfo of every initialized tick through extsload(bytes32[]), and
report whether any liquidity sits outside the current tick, plus the hook permission bits that
gate removal. Read-only eth_call."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
PM = '0x000000000004444c5dc75cB358380D2e3dE08A90'
U = sys.argv[1] if len(sys.argv) > 1 else 'https://ethereum.public.blockpi.network/v1/rpc/public'
census = json.load(open('/home/user/v4-core/research/network-risk/cycles/017/ethereum-reference.work/hooks7702.json'))
M = 1 << 256
def i256(x): return (x % M).to_bytes(32, 'big')
def extsload(slots):
    out = []
    for i in range(0, len(slots), 2000):
        part = slots[i:i + 2000]
        data = bytes.fromhex('dbd035ff') + (32).to_bytes(32, 'big') + len(part).to_bytes(32, 'big') + b''.join(part)
        r = bytes.fromhex(rpc(U, 'eth_call', [{'to': PM, 'data': '0x' + data.hex()}, 'latest'])[2:])
        n = int.from_bytes(r[32:64], 'big'); assert n == len(part)
        out += [int.from_bytes(r[64 + 32 * k:96 + 32 * k], 'big') for k in range(n)]
    return out
FLAGS = {'beforeRemove': 1 << 9, 'afterRemove': 1 << 8, 'afterRemoveReturnsDelta': 1 << 0, 'beforeAdd': 1 << 11, 'afterAdd': 1 << 10, 'beforeSwap': 1 << 7, 'afterSwap': 1 << 6}
res = []
blk = rpc(U, 'eth_blockNumber', [])
for p in census['pools7702']:
    enc = b''.join(int(x, 16).to_bytes(32, 'big') for x in [p['currency0'], p['currency1']]) + p['fee'].to_bytes(32, 'big') + (p['tickSpacing'] % M).to_bytes(32, 'big') + int(p['hook'], 16).to_bytes(32, 'big')
    pid = keccak(enc); ts = p['tickSpacing']
    p['censusPoolId'] = p['poolId']; p['poolId'] = '0x' + pid.hex()
    state = int.from_bytes(keccak(pid + (6).to_bytes(32, 'big')), 'big')
    s0, liq = extsload([state.to_bytes(32, 'big'), (state + 3).to_bytes(32, 'big')])
    tick = (s0 >> 160) & 0xffffff; tick = tick - (1 << 24) if tick >= 1 << 23 else tick
    lo = (-887272 // ts) >> 8; hi = (887272 // ts) >> 8
    bm_base = (state + 5).to_bytes(32, 'big'); tk_base = (state + 4).to_bytes(32, 'big')
    words = list(range(lo - 1, hi + 2))
    bm = extsload([keccak(i256(w) + bm_base) for w in words])
    ticks = []
    for w, v in zip(words, bm):
        for bit in range(256):
            if v >> bit & 1: ticks.append(((w << 8) + bit) * ts)
    infos = extsload([keccak(i256(t) + tk_base) for t in ticks]) if ticks else []
    tl = []
    for t, v in zip(ticks, infos):
        gross = v & ((1 << 128) - 1); net = v >> 128; net = net - (1 << 128) if net >= 1 << 127 else net
        tl.append({'tick': t, 'liquidityGross': gross, 'liquidityNet': net})
    hook = int(p['hook'], 16)
    res.append({'poolId': p['poolId'], 'censusPoolId': p['censusPoolId'], 'hook': p['hook'], 'kind': p['kind'], 'currency0': p['currency0'], 'currency1': p['currency1'],
                'tickSpacing': ts, 'sqrtPriceX96': s0 & ((1 << 160) - 1), 'tick': tick, 'activeLiquidity': liq,
                'initializedTicks': tl, 'flags': {k: bool(hook & f) for k, f in FLAGS.items()}})
    print(p['poolId'][:12], p['kind'], 'ts', ts, 'tick', tick, 'L', liq, 'initTicks', len(tl), 'flags', [k for k, f in FLAGS.items() if hook & f])
json.dump({'rpc': U, 'block': int(blk, 16), 'pools': res}, open('l821.json', 'w'), indent=1)
