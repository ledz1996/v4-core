# For a token: list the pools that name it (Initialize logs), read StateView.getLiquidity and getSlot0 for each, and
# compare with balanceOf(PoolManager). A pool with active liquidity while the PoolManager holds none of the token is
# a pool whose recorded reserves are not backed.
# usage: python3 pool_state.py <chainId> <token> [fromBlock]
import sys, json
from lib import *
from config import CFG
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
def run(cid, tok, lo=None):
    n = net(cid); pm = n['poolManager']; sv = n.get('contracts', {}).get('StateView'); u = CFG[cid]['state'][0]; lu = CFG[cid].get('init') or CFG[cid]['logs']
    head = int(rpc(u, 'eth_blockNumber', []), 16) - 200; lu = u if cid == 42161 else lu; out = {'chainId': cid, 'token': tok, 'stateView': sv, 'pools': []}
    logs = []
    for tp in ([INIT, None, pad_addr(tok)], [INIT, None, None, pad_addr(tok)]):
        logs += rpc(lu, 'eth_getLogs', [{'address': pm, 'topics': tp, 'fromBlock': hex(lo or 0), 'toBlock': hex(head)}], timeout=90, tries=3)
    out['balanceNow'] = str(int(call(u, tok, 'balanceOf(address)', adr(pm)), 16))
    for l in logs:
        pid = l['topics'][1]; d = l['data'][2:]; p = dict(id=pid, c0='0x' + l['topics'][2][-40:], c1='0x' + l['topics'][3][-40:], fee=int(d[0:64], 16), hooks='0x' + d[128 + 24:192], block=int(l['blockNumber'], 16))
        if sv:
            try:
                p['liquidity'] = str(int(call(u, sv, 'getLiquidity(bytes32)', pid[2:]), 16)); s0 = call(u, sv, 'getSlot0(bytes32)', pid[2:])[2:]
                p['sqrtPriceX96'] = str(int(s0[0:64], 16)); t = int(s0[64:128], 16); p['tick'] = t - (1 << 256) if t >> 255 else t
            except Exception as e: p['err'] = str(e)[:100]
        out['pools'].append(p)
    print(json.dumps(out, indent=0)[:6000])
    json.dump(out, open('raw/pools_%d_%s.json' % (cid, tok[:10]), 'w'), indent=0)
    return out
if __name__ == '__main__': run(int(sys.argv[1]), sys.argv[2].lower(), int(sys.argv[3]) if len(sys.argv) > 3 else None)
