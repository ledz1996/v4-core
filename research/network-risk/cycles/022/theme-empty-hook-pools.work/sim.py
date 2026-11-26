"""Read-only eth_call of a PositionManager owner's full decrease of a position in a pool whose hook has no code:
(a) state as is, (b) with the runtime that CREATE2 via 0x4e59b448 would place at the hook address (the Ethereum deployment's
runtime; the CREATE2 address commits to the init code, so a replay yields the same code), (c) with a stub hook that returns
its selector, to show the hook is the only obstacle. usage: sim.py <cid> <url> <tokenId> [<tokenId> ...]"""
import sys, json, subprocess
from ep import rpc, NETS
def kec(b): return subprocess.run(['build/kec', str(len(b))], input=b, capture_output=True).stdout
def sel(s): return kec(s.encode())[:4]
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
def eb(b): return w(len(b)) + b + b'\0' * ((-len(b)) % 32)
cid, U = int(sys.argv[1]), sys.argv[2]; toks = [int(x, 0) for x in sys.argv[3:]]
POSM = NETS[cid]['contracts']['PositionManager']
C2 = json.load(open('dl/create2_eth.json'))
blk = hex(int(rpc(U, 'eth_blockNumber', []), 16) - 30)
# stub: return the first 4 bytes of calldata left aligned in a 32 byte word, padded to 64 bytes (selector + zero delta)
STUB = '0x5f3560e01c60e01b5f5260405ff3'
res = {'chainId': cid, 'url': U, 'block': int(blk, 16), 'client': rpc(U, 'web3_clientVersion', []), 'runs': []}
for tid in toks:
    owner = '0x' + rpc(U, 'eth_call', [{'to': POSM, 'data': '0x' + (sel('ownerOf(uint256)') + w(tid)).hex()}, blk])[-40:]
    info = rpc(U, 'eth_call', [{'to': POSM, 'data': '0x' + (sel('getPoolAndPositionInfo(uint256)') + w(tid)).hex()}, blk])
    hook = '0x' + info[2 + 64 * 4 + 24:2 + 64 * 5]
    posliq = int(rpc(U, 'eth_call', [{'to': POSM, 'data': '0x' + (sel('getPositionLiquidity(uint256)') + w(tid)).hex()}, blk]), 16)
    p = w(tid) + w(posliq) + w(0) + w(0) + w(160) + w(0)
    c0 = int(info[2:66], 16); c1 = int(info[66:130], 16)
    tp = w(c0) + w(c1) + w(int(owner, 16))
    # actions DECREASE_LIQUIDITY (0x01), TAKE_PAIR (0x11); params is bytes[] of two entries
    e1, e2 = eb(p), eb(tp)
    arr = w(2) + w(64) + w(64 + len(e1)) + e1 + e2
    unlock = w(64) + w(64 + 32 + 32) + eb(bytes([0x01, 0x11])) + arr
    data = '0x' + (sel('modifyLiquidities(bytes,uint256)') + w(64) + w(2 ** 64) + eb(unlock)).hex()
    for name, ov in [('asIs', None), ('create2Replay', {hook: {'code': C2[hook]['runtime']}} if hook in C2 else None), ('selectorStub', {hook: {'code': STUB}})]:
        if name == 'create2Replay' and ov is None: continue
        args = [{'from': owner, 'to': POSM, 'data': data, 'gas': hex(5_000_000)}, blk] + ([ov] if ov else [])
        try: r = rpc(U, 'eth_call', args, tries=2); out = {'ok': True, 'ret': r[:130]}
        except Exception as e: out = {'ok': False, 'error': str(e)[:1400]}
        out.update({'tokenId': tid, 'owner': owner, 'hook': hook, 'positionLiquidity': posliq, 'case': name}); res['runs'].append(out)
        print(cid, tid, name, out['ok'], (out.get('error') or out.get('ret'))[:260], flush=True)
res['selectors'] = {n: '0x' + sel(n).hex() for n in ['InvalidHookResponse()', 'HookCallFailed()', 'WrappedError(address,bytes4,bytes,bytes)', 'NotPoolManager()', 'HookNotImplemented()']}
json.dump(res, open('raw/sim_%d.json' % cid, 'w'), indent=1)
