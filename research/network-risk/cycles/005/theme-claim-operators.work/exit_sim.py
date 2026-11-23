# Read-only simulation (eth_call from the position owner) of ways to close a PositionManager position when one currency cannot leave the PoolManager.
import sys, json, os
from lib import *
from abi2 import calldata, enc_tuple
from keccak import keccak256
from state import url
MAXU = (1 << 256) - 1; M128 = (1 << 128) - 1
def call(u, frm, to, data, blk='latest'):
    try: return ('ok', rpc(u, 'eth_call', [{'from': frm, 'to': to, 'data': data}, blk], tries=3))
    except Exception as e: return ('revert', str(e)[:260])
def run(cid, token_id, blocked, key):
    n = net(cid); u = url(cid); pm = n['poolManager']; posm = n['contracts']['PositionManager']
    owner = '0x' + rpc(u, 'eth_call', [{'to': posm, 'data': '0x6352211e' + u256(token_id)}, 'latest'])[-40:]
    liq = int(rpc(u, 'eth_call', [{'to': posm, 'data': calldata('getPositionLiquidity(uint256)', [token_id])}, 'latest']), 16)
    nxt = int(rpc(u, 'eth_call', [{'to': posm, 'data': '0x75794a3c'}, 'latest']), 16)
    c0, c1 = key['c0'], key['c1']; other = c1 if blocked.lower() == c0.lower() else c0
    # slot0 of the pool through extsload: _pools is slot 6
    slot = keccak256(bytes.fromhex(key['id'][2:]) + (6).to_bytes(32, 'big')).hex()
    s0 = int(rpc(u, 'eth_call', [{'to': pm, 'data': '0x1e2eaeaf' + slot}, 'latest']), 16)
    tick = (s0 >> 160) & 0xffffff; tick = tick - (1 << 24) if tick >> 23 else tick
    ts = key['ts']; maxt = (887272 // ts) * ts
    if blocked.lower() == c0.lower(): tl = (tick // ts + 1) * ts; tu = maxt    # only currency0 above the price
    else: tl = -maxt; tu = (tick // ts) * ts                                    # only currency1 below the price
    P = lambda types, vals: enc_tuple(types, vals)
    dec = (1, P(['uint256', 'uint256', 'uint128', 'uint128', 'bytes'], [token_id, liq, 0, 0, b'']))
    burn = (3, P(['uint256', 'uint128', 'uint128', 'bytes'], [token_id, 0, 0, b'']))
    takepair = (0x11, P(['address', 'address', 'address'], [c0, c1, owner]))
    take_other = (0x0e, P(['address', 'address', 'uint256'], [other, owner, 0]))
    take_blocked = (0x0e, P(['address', 'address', 'uint256'], [blocked, owner, 0]))
    close_blocked = (0x12, P(['address'], [blocked]))
    clear_blocked = (0x13, P(['address', 'uint256'], [blocked, MAXU]))
    clear_small = (0x13, P(['address', 'uint256'], [blocked, 0]))
    mint6909 = (0x17, P(['address', 'address', 'uint256'], [blocked, owner, 0]))
    sweep = (0x14, P(['address', 'address'], [blocked, owner]))
    mfd = (0x05, P(['(address,address,uint24,int24,address)', 'int24', 'int24', 'uint128', 'uint128', 'address', 'bytes'], [(c0, c1, key['fee'], ts, key['hooks']), tl % (1 << 256), tu % (1 << 256), M128, M128, owner, b'']))
    def ml(acts):
        ud = P(['bytes', 'bytes[]'], [bytes(a for a, _ in acts), [p for _, p in acts]])
        return calldata('modifyLiquidities(bytes,uint256)', [ud, MAXU])
    seqs = [('decrease, take pair (what a removal normally does)', [dec, takepair]),
            ('decrease, take other, take blocked', [dec, take_other, take_blocked]),
            ('decrease, take other, close blocked', [dec, take_other, close_blocked]),
            ('decrease, take other, MINT_6909 for blocked', [dec, take_other, mint6909]),
            ('decrease, take other, sweep blocked', [dec, take_other, sweep]),
            ('decrease, take other, clear-or-take blocked with max 0', [dec, take_other, clear_small]),
            ('decrease, take other, clear-or-take blocked with max uint256 (forfeit)', [dec, take_other, clear_blocked]),
            ('burn position, take other, clear-or-take blocked with max uint256 (forfeit)', [burn, take_other, clear_blocked]),
            ('decrease, take other, mint one sided position from the blocked delta, clear dust', [dec, take_other, mfd, clear_blocked])]
    out = dict(chainId=cid, tokenId=token_id, owner=owner, liquidity=str(liq), pool=key, blocked=blocked, tick=tick, newRange=[tl, tu], nextTokenId=nxt, results=[])
    blk = rpc(u, 'eth_blockNumber', []); out['block'] = int(blk, 16)
    for name, acts in seqs:
        r = call(u, owner, posm, ml(acts), blk)
        out['results'].append([name, r[0], r[1][:200]])
    # the last sequence again inside PositionManager.multicall, followed by reads of the new token
    mc = calldata('multicall(bytes[])', [[bytes.fromhex(ml(seqs[-1][1])[2:]), bytes.fromhex(calldata('getPositionLiquidity(uint256)', [nxt])[2:]), bytes.fromhex('6352211e' + u256(nxt)), bytes.fromhex(calldata('getPositionLiquidity(uint256)', [token_id])[2:])]])
    r = call(u, owner, posm, mc, blk)
    if r[0] == 'ok':
        b = bytes.fromhex(r[1][2:]); 
        # decode bytes[]: offset, len, offsets...
        base = 32; nres = int.from_bytes(b[32:64], 'big'); vals = []
        for i in range(nres):
            off = int.from_bytes(b[64 + 32 * i:96 + 32 * i], 'big') + 64; ln = int.from_bytes(b[off:off + 32], 'big'); vals.append(b[off + 32:off + 32 + ln].hex())
        out['afterReinvest'] = dict(newTokenLiquidity=str(int(vals[1], 16)), newTokenOwner='0x' + vals[2][-40:], oldTokenLiquidity=str(int(vals[3], 16)))
    else: out['afterReinvest'] = r[1]
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1]); tok = sys.argv[2]; tid = int(sys.argv[3])
    pools = json.load(open(os.path.join(HERE, 'raw', 'positions_%d_%s.json' % (cid, tok.lower()))))
    key = [k for k in pools if str(tid) in k['positions']][0]
    o = run(cid, tid, tok, key)
    json.dump(o, open(os.path.join(HERE, 'raw', 'exit_%d_%d.json' % (cid, tid)), 'w'), indent=1)
    print(json.dumps({k: v for k, v in o.items() if k != 'results'})); 
    for r in o['results']: print('  ', r)
