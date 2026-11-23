# Exit simulation on a network without a naturally blocked token: the code of one pool currency is replaced, in the eth_call only, by
# PUSH0 PUSH0 REVERT so that every call to it reverts, which is what a paused or frozen token does to PoolManager.take. Read-only.
import sys, json, os
import exit_sim
from lib import *
from abi2 import calldata, enc_tuple
from keccak import keccak256
from state import url
def find_position(cid, start=None, tries=400):
    n = net(cid); u = url(cid); posm = n['contracts']['PositionManager']
    nxt = int(rpc(u, 'eth_call', [{'to': posm, 'data': '0x75794a3c'}, 'latest']), 16)
    t = start or nxt - 1; found = []
    while t > 0 and tries > 0 and len(found) < 1:
        tries -= 1
        try:
            liq = int(rpc(u, 'eth_call', [{'to': posm, 'data': calldata('getPositionLiquidity(uint256)', [t])}, 'latest']), 16)
            if liq > 0:
                r = rpc(u, 'eth_call', [{'to': posm, 'data': calldata('getPoolAndPositionInfo(uint256)', [t])}, 'latest']); b = bytes.fromhex(r[2:])
                c0 = '0x' + b[12:32].hex(); c1 = '0x' + b[44:64].hex(); fee = int.from_bytes(b[64:96], 'big'); ts = int.from_bytes(b[96:128], 'big'); hooks = '0x' + b[140:160].hex()
                info = int.from_bytes(b[160:192], 'big'); tl = (info >> 8) & 0xffffff; tu = (info >> 32) & 0xffffff
                sg = lambda v: v - (1 << 24) if v >> 23 else v
                if int(hooks, 16) == 0 and int(c0, 16) != 0:
                    pid = '0x' + keccak256(b[0:160]).hex()
                    found.append((t, dict(id=pid, c0=c0, c1=c1, fee=fee, ts=ts, hooks=hooks, positions={str(t): dict(liq=liq, tl=sg(tl), tu=sg(tu))})))
        except Exception as e: pass
        t -= 1
    return found
if __name__ == '__main__':
    cid = int(sys.argv[1]); which = int(sys.argv[2]) if len(sys.argv) > 2 else 0; start = int(sys.argv[3]) if len(sys.argv) > 3 else None
    tid, key = find_position(cid, start)[0]
    blocked = key['c0'] if which == 0 else key['c1']
    ovr = {blocked: {'code': '0x5f5ffd'}}
    orig = exit_sim.call
    def call(u, frm, to, data, blk='latest'):
        try: return ('ok', rpc(u, 'eth_call', [{'from': frm, 'to': to, 'data': data}, blk, ovr], tries=3))
        except Exception as e: return ('revert', str(e)[:260])
    exit_sim.call = call
    o = exit_sim.run(cid, tid, blocked, key); o['override'] = ovr
    json.dump(o, open(os.path.join(HERE, 'raw', 'exitovr_%d_%d.json' % (cid, tid)), 'w'), indent=1)
    print(json.dumps({k: v for k, v in o.items() if k != 'results'}))
    for r in o['results']: print('  ', r)
