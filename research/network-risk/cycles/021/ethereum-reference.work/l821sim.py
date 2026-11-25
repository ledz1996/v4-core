"""L-821: read-only eth_call of the NFT owner's own full decrease of PositionManager token 264099
(pool 0x462175db..., hook without code, beforeRemoveLiquidity flag) and of token 292697 (pool
0xf6aaf9bd..., hook without code, only afterSwap). Reports the revert selector."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
U = sys.argv[1] if len(sys.argv) > 1 else 'https://ethereum.public.blockpi.network/v1/rpc/public'
POSM = '0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e'
def sel(s): return keccak(s.encode())[:4]
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
def enc_bytes(b): return w(len(b)) + b + b'\0' * ((-len(b)) % 32)
res = {}
for tid, liq in ((0x40ba3, 150557992383766460021), (0x47759, 849560478854846)):
    owner = '0x' + rpc(U, 'eth_call', [{'to': POSM, 'data': '0x' + (sel('ownerOf(uint256)') + w(tid)).hex()}, 'latest'])[-40:]
    posliq = int(rpc(U, 'eth_call', [{'to': POSM, 'data': '0x' + (sel('getPositionLiquidity(uint256)') + w(tid)).hex()}, 'latest']), 16)
    # params for DECREASE_LIQUIDITY: (tokenId, liquidity, amount0Min, amount1Min, hookData)
    p = w(tid) + w(posliq) + w(0) + w(0) + w(160) + w(0)
    actions = bytes([0x01])
    # unlockData = abi.encode(bytes actions, bytes[] params)
    params_arr = w(1) + w(32) + enc_bytes(p)
    unlock = w(64) + w(64 + 32 + 32) + enc_bytes(actions) + params_arr
    data = sel('modifyLiquidities(bytes,uint256)') + w(64) + w(2 ** 64) + enc_bytes(unlock)
    r = None
    try:
        r = rpc(U, 'eth_call', [{'from': owner, 'to': POSM, 'data': '0x' + data.hex()}, 'latest'])
        out = {'ok': True, 'ret': r[:200]}
    except Exception as e:
        out = {'ok': False, 'error': str(e)[:600]}
    out.update({'tokenId': tid, 'owner': owner, 'positionLiquidity': posliq})
    res[hex(tid)] = out; print(out)
names = {n: '0x' + sel(n).hex() for n in ['InvalidHookResponse()', 'CurrencyNotSettled()', 'HookCallFailed()', 'WrappedError(address,bytes4,bytes,bytes)', 'NotApproved(address)', 'DeltaNotNegative(address)']}
print(names); res['selectors'] = names
json.dump(res, open('l821sim.json', 'w'), indent=1)
