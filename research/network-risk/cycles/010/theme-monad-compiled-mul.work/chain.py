"""Read-only facts from the Monad endpoint for this unit.
1. web3_clientVersion and the head block.
2. eth_getCode of the PoolManager: length, and whether the bytes around the MULMOD and MUL
   sites of sites.json equal the build (so the pcs hold on the deployed code).
3. Recent Swap events: the largest liquidity and the largest liquidity * |price step| seen,
   compared with 2^256 (the 512 bit branch of getAmount1Delta that reaches the MULMOD by 2^96
   at pc 22639) and with 2^160 (the 512 bit branch of getAmount0Delta).
Usage: SWAPS_WANT=20000 SWAPS_CALLS=200 python3 -I chain.py <repo>/research/network-risk <out.json>
"""
import sys, os, json
base = sys.argv[1]
sys.path.insert(0, os.path.join(base, 'tools', 'opdiff'))
import swaps as W
from evm import rpc

n = [x for x in json.load(open(os.path.join(base, 'state', 'networks.json')))['networks'] if x['chainId'] == 143][0]
url, pm = n['rpc'], n['poolManager']
out = {'rpc': url, 'poolManager': pm}
out['clientVersion'] = rpc(url, 'web3_clientVersion', [])
out['head'] = int(rpc(url, 'eth_blockNumber', []), 16)
code = bytes.fromhex(rpc(url, 'eth_getCode', [pm, 'latest'])[2:])
build = bytes.fromhex(json.load(open(os.path.join(base, 'build', 'PoolManager.json')))['runtime'].removeprefix('0x'))
out['deployedBytes'] = len(code); out['buildBytes'] = len(build)
diff = [i for i in range(min(len(code), len(build))) if code[i] != build[i]]
out['differingByteRanges'] = []
for i in diff:
    if out['differingByteRanges'] and out['differingByteRanges'][-1][1] == i - 1: out['differingByteRanges'][-1][1] = i
    else: out['differingByteRanges'].append([i, i])
sites = json.load(open(os.path.join(base, 'cycles', '010', 'theme-monad-compiled-mul.work', 'sites.json')))['sites']
out['siteBytesEqual'] = all(code[s['pc'] - 40:s['pc'] + 1] == build[s['pc'] - 40:s['pc'] + 1] for s in sites if s['pc'] < 24000)
out['opcodeAt'] = {str(p): hex(code[p]) for p in (22378, 22639, 23094, 22777, 22935, 18495, 16780)}
logs, lo, head = W.collect(url, pm)
mx_l = 0; mx_p1 = 0; mx_p0 = 0; nsw = 0; last = {}; wide0 = 0; bitc = {}
for lg in sorted(logs, key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16))):
    if lg['topics'][0] != W.SWAP: continue
    d = lg['data']; price = W.word(d, 2); liq = W.word(d, 3); pid = lg['topics'][1]; nsw += 1
    mx_l = max(mx_l, liq)
    tk = W.word(d, 4) & 0xffffff; tk = tk - (1 << 24) if tk >> 23 else tk
    for b in range(20):
        if abs(tk) >> b & 1: bitc[b] = bitc.get(b, 0) + 1
    if pid in last:
        p0 = last[pid]; step = abs(price - p0)
        mx_p1 = max(mx_p1, liq * step)
        mx_p0 = max(mx_p0, (liq << 96) * step)
        if (liq << 96) * max(p0, price) >= 1 << 256: wide0 += 1
    last[pid] = price
out['swaps'] = nsw; out['blocks'] = [lo, head]; out['pools'] = len(last)
out['maxLiquidity'] = mx_l; out['maxLiquidityBits'] = mx_l.bit_length()
out['maxLiquidityTimesStepBits'] = mx_p1.bit_length()
out['getAmount1Delta512Reached'] = mx_p1 >= 1 << 256
out['maxLiqShl96TimesStepBits'] = mx_p0.bit_length()
out['pairsWithLiqShl96TimesPriceAbove2e256'] = wide0
out['absTickBitCounts'] = {hex(1 << b): bitc.get(b, 0) for b in range(20)}
out['note'] = 'liquidity * |step| below 2^256 means the 512 bit branch of the Q96 mulDiv (pc 22544-22656) did not run for these consecutive pairs'
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'differingByteRanges'}, indent=1), out['differingByteRanges'][:10])
