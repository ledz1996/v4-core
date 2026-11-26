# Derive every PoolManager storage slot that the logs say was written, over the whole history.
# Layout from source: Owned.owner slot 0 (lib/solmate/src/auth/Owned.sol:17), protocolFeesAccrued 1 and
# protocolFeeController 2 (src/ProtocolFees.sol:21,24), isOperator 3, balanceOf 4, allowance 5 (src/ERC6909.sol:15-19),
# _pools 6 (src/PoolManager.sol:93); Pool.State fields +0..+6 (src/libraries/Pool.sol:83-91), TickInfo 3 words
# (Pool.sol:68-77), Position.State 3 words (src/libraries/Position.sol:19-25), position key (Position.sol:48-61),
# bitmap word key sar(8, compressed) (src/libraries/TickBitmap.sol:16-38,66-70).
import json, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
M = (1 << 256) - 1
def w(x): return (x & M).to_bytes(32, 'big')
def h(*parts): return int.from_bytes(keccak(b''.join(parts)), 'big')
def sx(hexword, bits):
    v = int(hexword, 16) & ((1 << bits) - 1)
    return v - (1 << bits) if v >> (bits - 1) else v
SIG = {}
for s in ['Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)', 'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)',
          'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)', 'Donate(bytes32,address,uint256,uint256)',
          'Transfer(address,address,address,uint256,uint256)', 'OperatorSet(address,address,bool)', 'Approval(address,address,uint256,uint256)']:
    SIG['0x' + keccak(s.encode()).hex()] = s.split('(')[0]
def addr(t): return int(t, 16) & ((1 << 160) - 1)
def compress(t, sp):
    c = abs(t) // sp
    if t < 0 and t % sp != 0: c += 1
    return -c if t < 0 else c
def derive(logs):
    slots = {0: 'owner', 1 << 300: None}; slots.pop(1 << 300)
    slots[2] = 'protocolFeeController'
    pools = {}; currencies = set()
    for l in logs:
        k = SIG.get(l['topics'][0]); d = l['data'][2:]; words = [d[i:i + 64] for i in range(0, len(d), 64)]
        if k == 'Initialize':
            pid = int(l['topics'][1], 16); c0, c1 = addr(l['topics'][2]), addr(l['topics'][3])
            pools[pid] = dict(c0=c0, c1=c1, fee=int(words[0], 16), sp=sx(words[1], 24), hooks=addr(words[2]))
            currencies |= {c0, c1}
    def pbase(pid):
        b = h(w(pid), w(6)); return b
    for pid in pools:
        b = pbase(pid)
        for i, n in enumerate(['slot0', 'feeGrowthGlobal0', 'feeGrowthGlobal1', 'liquidity']):
            slots[(b + i) & M] = f'pool {pid:#066x} {n}'
    def tick(pid, t):
        b = pbase(pid); s = h(w(t), w(b + 4))
        for i, n in enumerate(['gross|net', 'fgo0', 'fgo1']): slots[(s + i) & M] = f'pool {pid:#066x} tick {t} {n}'
        sp = pools[pid]['sp'] if pid in pools else 1
        wp = compress(t, sp) >> 8
        slots[h(w(wp), w(b + 5))] = f'pool {pid:#066x} bitmap word {wp}'
    for l in logs:
        k = SIG.get(l['topics'][0]); d = l['data'][2:]; words = [d[i:i + 64] for i in range(0, len(d), 64)]
        if k == 'ModifyLiquidity':
            pid = int(l['topics'][1], 16); owner = addr(l['topics'][2]); tl, tu = sx(words[0], 24), sx(words[1], 24); salt = int(words[3], 16)
            tick(pid, tl); tick(pid, tu)
            key = h(owner.to_bytes(20, 'big'), (tl & 0xffffff).to_bytes(3, 'big'), (tu & 0xffffff).to_bytes(3, 'big'), w(salt))
            s = h(w(key), w(pbase(pid) + 6))
            for i, n in enumerate(['liquidity', 'fgi0Last', 'fgi1Last']): slots[(s + i) & M] = f'pool {pid:#066x} position {owner:#042x} {tl} {tu} {salt:#x} {n}'
        elif k == 'Swap':
            pid = int(l['topics'][1], 16); t = sx(words[4], 24); b = pbase(pid)
            sp = pools[pid]['sp'] if pid in pools else 1
            wp = compress(t, sp) >> 8
            slots[h(w(wp), w(b + 5))] = f'pool {pid:#066x} bitmap word {wp}'
        elif k == 'Transfer':
            fr, to = addr(l['topics'][1]), addr(l['topics'][2]); cid = int(l['topics'][3], 16)
            currencies.add(cid & ((1 << 160) - 1))
            for o in (fr, to):
                if o: slots[h(w(cid), w(h(w(o), w(4))))] = f'balanceOf {o:#042x} id {cid:#x}'
        elif k == 'OperatorSet':
            o, op = addr(l['topics'][1]), addr(l['topics'][2])
            slots[h(w(op), w(h(w(o), w(3))))] = f'isOperator {o:#042x} {op:#042x}'
        elif k == 'Approval':
            o, sp_, cid = addr(l['topics'][1]), addr(l['topics'][2]), int(l['topics'][3], 16)
            slots[h(w(cid), w(h(w(sp_), w(h(w(o), w(5))))))] = f'allowance {o:#042x} {sp_:#042x} {cid:#x}'
    for c in currencies:
        slots[h(w(c), w(1))] = f'protocolFeesAccrued {c:#042x}'
    return slots, pools, currencies
if __name__ == '__main__':
    d = json.load(open(sys.argv[1]))
    slots, pools, cur = derive(d['logs'])
    json.dump({'source': sys.argv[1], 'toBlock': d['toBlock'], 'slots': {hex(k): v for k, v in slots.items()},
               'pools': {hex(k): v for k, v in pools.items()}, 'currencies': ['0x%040x' % c for c in sorted(cur)]}, open(sys.argv[2], 'w'), indent=0)
    import collections
    print(len(slots), 'slots', len(pools), 'pools', len(cur), 'currencies')
    print(collections.Counter(v.split()[2] if v.startswith('pool') else v.split()[0] for v in slots.values()))
