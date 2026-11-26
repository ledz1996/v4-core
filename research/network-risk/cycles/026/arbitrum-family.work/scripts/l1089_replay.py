"""Lead L-1089. Replay the Swap at log index 0x10 of Arbitrum One transaction
0x06c45e81... (block 527,671,975) starting from the end state that the Swap at log
index 0x4 of transaction 0xa9ffc511... left in the same pool earlier in the same block,
instead of from parent-block state. Swaps do not change the tick bitmap or liquidityNet,
so those are read at the parent block once no ModifyLiquidity of the pool lies in the
block. Uses tools/opdiff/replay.py (Pool.swap transcription) unchanged.
"""
import sys, os, json
OPD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, OPD)
from evm import rpc, keccak
import replay as R

URL = 'https://arb-one.api.pocket.network'
PM = '0x360e68faccca8ca495c1b759fd9eee466db9fb32'
BLOCK = 527671975
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
MOD = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
POOL = '0x4dff5a7fe6e0acd5431237d7868824e2aaf86c1f748727cf7976b5f1a931281d'


def s(x, bits):
    return x - (1 << bits) if x >> (bits - 1) else x


def dec(lg):
    d = lg['data'][2:]; w = [int(d[64 * i:64 * i + 64], 16) for i in range(6)]
    return {'a0': s(w[0], 256), 'a1': s(w[1], 256), 'p': w[2], 'liq': w[3], 'tick': s(w[4], 256), 'fee': w[5], 'logIndex': int(lg['logIndex'], 16), 'tx': lg['transactionHash']}


out = {'clientVersion': rpc(URL, 'web3_clientVersion', [])}
logs = rpc(URL, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(BLOCK), 'toBlock': hex(BLOCK)}])
out['pmLogsInBlock'] = [{'logIndex': int(l['logIndex'], 16), 'topic0': l['topics'][0], 'pool': l['topics'][1] if len(l['topics']) > 1 else None, 'tx': l['transactionHash']} for l in logs]
mods = [l for l in logs if l['topics'][0] == MOD and l['topics'][1] == POOL]
swaps = sorted([dec(l) for l in logs if l['topics'][0] == SWAP and l['topics'][1] == POOL], key=lambda x: x['logIndex'])
out['modifyLiquidityOfPoolInBlock'] = len(mods)
out['swapsOfPool'] = swaps
prev = [x for x in swaps if x['logIndex'] == 0x4][0]
cur = [x for x in swaps if x['logIndex'] == 0x10][0]
smp = {'pool': POOL, 'p0': prev['p'], 'tick0': prev['tick'], 'liq': prev['liq'], 'p1': cur['p'], 'tick1': cur['tick'],
       'a0': cur['a0'], 'a1': cur['a1'], 'fee': cur['fee'], 'block': BLOCK - 1 + 1, 'tx': cur['tx']}
assert prev['liq'] == cur['liq']
ch = R.Chain(URL, PM)
# replay() tries block and block-1; pass BLOCK so it reads parent (BLOCK-1) state second; bitmap is the same at both if no ModifyLiquidity
out['replayFromInBlockState'] = R.replay(ch, smp)
# for contrast, the cycle 25 start: the pool's slot0 at the parent block
base = int.from_bytes(keccak(bytes.fromhex(POOL[2:]) + (6).to_bytes(32, 'big')), 'big')
slot0 = ch.sload(base, BLOCK - 1)
out['parentSlot0'] = {'sqrtPriceX96': slot0 & ((1 << 160) - 1), 'tick': s((slot0 >> 160) & 0xffffff, 24)}
out['logIndex4EndState'] = {'sqrtPriceX96': prev['p'], 'tick': prev['tick']}
out['clientVersionAfter'] = rpc(URL, 'web3_clientVersion', [])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('modifyLiquidityOfPoolInBlock', 'replayFromInBlockState', 'parentSlot0', 'logIndex4EndState', 'clientVersion')}, indent=1))
