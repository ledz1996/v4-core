"""Task 2: pools on MegaETH, HyperEVM and Monad, their tick, tick spacing and in-range liquidity (extsload of
StateLibrary slots: pools mapping at slot 6, slot0 at +0, liquidity at +3), and whether an ordinary account can make a
swap step there see a getAmount1Delta product >= 2^256 (src/libraries/SqrtPriceMath.sol:250-252).
Usage: python3 pools.py <label> <url> <pm> <logRange> <fromBlock|-N> [topic: init|swap]   Read-only (eth_getLogs, eth_call)."""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak, rpc
import v4math as m
label, url, pm, rng, frm = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
kind = sys.argv[6] if len(sys.argv) > 6 else 'init'
TI = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
TS = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
def R(mth, p):
    for k in range(6):
        try: return rpc(url, mth, p, timeout=120)
        except Exception as e:
            err = e; time.sleep(1.5 * (k + 1))
    raise err
log = {'label': label, 'url': url, 'clientVersionBefore': R('web3_clientVersion', [])}
head = int(R('eth_blockNumber', []), 16); b0 = frm if frm >= 0 else max(0, head + frm)
log.update({'head': head, 'from': b0, 'kind': kind})
pools = {}
b = b0; nq = 0
while b <= head:
    e = min(head, b + rng - 1)
    for l in R('eth_getLogs', [{'address': pm, 'topics': [TI if kind == 'init' else TS], 'fromBlock': hex(b), 'toBlock': hex(e)}]):
        pid = l['topics'][1]
        if kind == 'init':
            d = bytes.fromhex(l['data'][2:]); ts = int.from_bytes(d[32:64], 'big', signed=True)
            pools[pid] = {'currency0': '0x' + l['topics'][2][-40:], 'currency1': '0x' + l['topics'][3][-40:], 'fee': int.from_bytes(d[0:32], 'big'),
                          'tickSpacing': ts, 'hooks': '0x' + d[64:96].hex()[-40:], 'block': int(l['blockNumber'], 16)}
        else:
            pools.setdefault(pid, {'swaps': 0}); pools[pid]['swaps'] = pools[pid].get('swaps', 0) + 1
    b = e + 1; nq += 1
log['logQueries'] = nq
SEL = keccak(b'extsload(bytes32)')[:4]
def ext(slot):
    return int(R('eth_call', [{'to': pm, 'data': '0x' + SEL.hex() + slot.to_bytes(32, 'big').hex()}, 'latest']), 16)
def ml(ts):
    mn = -(887272 // ts) - (1 if 887272 % ts else 0); return ((1 << 128) - 1) // ((887272 // ts) - mn + 1)
TOP = 1 << 256
for pid, p in pools.items():
    base = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big')
    s0 = ext(base); liq = ext(base + 3) & ((1 << 128) - 1)
    price = s0 & ((1 << 160) - 1); tick = (s0 >> 160) & 0xffffff
    if tick >= 1 << 23: tick -= 1 << 24
    p.update({'sqrtPriceX96': price, 'tick': tick, 'liquidity': liq})
    if 'tickSpacing' not in p or price == 0: continue
    ts = p['tickSpacing']
    # widest one-word step upward from the current price: to the end of the current bitmap word, capped at MAX_TICK
    comp = tick // ts if tick >= 0 or tick % ts == 0 else tick // ts
    wordEnd = (((comp + 1) >> 8) + 1) * 256 * ts  # boundary after the word of compressed tick + 1
    tgtUp = m.get_sqrt_price_at_tick(min(m.MAX_TICK, wordEnd))
    diffUp = max(0, tgtUp - price)
    Lavail = min((1 << 128) - 1, liq + ml(ts))  # existing in-range liquidity plus one position an ordinary account can add
    p['log2ProductUpExisting'] = (liq * diffUp).bit_length()
    p['log2ProductUpWithOnePosition'] = (Lavail * diffUp).bit_length()
    p['wideUpExisting'] = liq * diffUp >= TOP
    p['wideUpWithOnePosition'] = Lavail * diffUp >= TOP
    p['wideUpWithMaxPoolLiquidity'] = ((1 << 128) - 1) * diffUp >= TOP
log['pools'] = pools
log['counts'] = {'pools': len(pools), 'withPrice': sum(1 for p in pools.values() if p.get('sqrtPriceX96')),
                 'wideUpExisting': sum(1 for p in pools.values() if p.get('wideUpExisting')),
                 'wideUpWithOnePosition': sum(1 for p in pools.values() if p.get('wideUpWithOnePosition')),
                 'wideUpWithMaxPoolLiquidity': sum(1 for p in pools.values() if p.get('wideUpWithMaxPoolLiquidity'))}
top = sorted(pools.items(), key=lambda kv: -kv[1].get('liquidity', 0))[:50]
log['top50ByLiquidity'] = [[k, v.get('liquidity'), v.get('tick'), v.get('tickSpacing'), v.get('log2ProductUpExisting'), v.get('log2ProductUpWithOnePosition')] for k, v in top]
hi = sorted(pools.items(), key=lambda kv: -(kv[1].get('tick') if kv[1].get('sqrtPriceX96') else -10**9))[:20]
log['highestTicks'] = [[k, v.get('tick'), v.get('tickSpacing'), v.get('liquidity'), v.get('log2ProductUpWithOnePosition'), v.get('currency0'), v.get('currency1'), v.get('hooks')] for k, v in hi]
log['clientVersionAfter'] = R('web3_clientVersion', [])
json.dump(log, open(f'out/pools-{label}.json', 'w'), indent=1)
print(label, log['clientVersionBefore'], head, log['counts'])
for r in log['highestTicks'][:10]: print(r)
