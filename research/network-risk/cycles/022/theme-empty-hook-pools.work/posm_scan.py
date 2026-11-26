"""Fallback for BNB Smart Chain where log history is unreliable: read positionInfo(tokenId) of every PositionManager token
through Multicall3 aggregate3 (eth_call), keep tokens whose 25 byte pool id prefix is one of the pools on empty or delegated
hooks that have initialized ticks (raw/ticks_56.json), then ownerOf, getPositionLiquidity, the Initialize transaction sender,
and compare the PositionManager liquidity per tick with TickInfo.liquidityGross. Read only. usage: posm_scan.py <cid> <url>"""
import sys, json, subprocess, concurrent.futures as cf, collections, math
from ep import rpc, NETS
cid, U = int(sys.argv[1]), sys.argv[2]; LU = sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
P = NETS[cid]['contracts']['PositionManager'].lower(); PM = NETS[cid]['poolManager']; MC = '0xcA11bde05977b3631167028862bE2a173976CA11'
def kec(b, n=None): return subprocess.run(['build/kec', str(n or len(b))], input=b, capture_output=True).stdout
def sel(s): return kec(s.encode())[:4]
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
TK = json.load(open('raw/ticks_%d.json' % cid)); pools = [p for p in TK['pools'] if p['ticks']]
pref = {bytes.fromhex(p['poolId'][2:])[:25]: p for p in pools}
headAtStart = int(rpc(U, 'eth_blockNumber', []), 16); blk = 'latest'; cv0 = rpc(U, 'web3_clientVersion', [])
N = int(rpc(U, 'eth_call', [{'to': P, 'data': '0x' + sel('nextTokenId()').hex()}, blk]), 16)
SI = sel('positionInfo(uint256)'); A3 = sel('aggregate3((address,bool,bytes)[])')
def agg(calls):
    # aggregate3(Call3[] calls) with Call3 = (address target, bool allowFailure, bytes callData)
    head = w(32) + w(len(calls)); offs = []; body = b''
    enc = []
    for tgt, data in calls:
        e = w(int(tgt, 16)) + w(1) + w(96) + w(len(data)) + data + b'\0' * ((-len(data)) % 32); enc.append(e)
    off = 32 * len(calls)
    for e in enc: offs.append(w(off)); off += len(e)
    payload = '0x' + (A3 + head + b''.join(offs) + b''.join(enc)).hex()
    r = bytes.fromhex(rpc(U, 'eth_call', [{'to': MC, 'data': payload, 'gas': hex(40_000_000)}, blk], tries=6)[2:])
    n = int.from_bytes(r[32:64], 'big'); out = []
    for i in range(n):
        o = 64 + int.from_bytes(r[64 + 32 * i:96 + 32 * i], 'big'); ok = int.from_bytes(r[o:o + 32], 'big')
        lo = o + int.from_bytes(r[o + 32:o + 64], 'big'); ln = int.from_bytes(r[lo:lo + 32], 'big')
        out.append((ok, r[lo + 32:lo + 32 + ln]))
    return out
STEP = 400; hits = []
def chunk(a):
    res = agg([(P, SI + w(t)) for t in range(a, min(N, a + STEP))])
    return [(a + i, d) for i, (ok, d) in enumerate(res) if ok and len(d) == 32 and d[:25] in pref]
import os
HF = 'raw/posm_%d_hits.json' % cid
if os.path.exists(HF): hits = [(t, bytes.fromhex(d)) for t, d in json.load(open(HF))]
else:
    with cf.ThreadPoolExecutor(10) as ex:
        for h in ex.map(chunk, range(1, N, STEP)): hits += h
    json.dump([(t, d.hex()) for t, d in hits], open(HF, 'w'))
print(cid, 'tokens', N - 1, 'hits', len(hits), flush=True)
rows = []
for t, d in hits:
    p = pref[d[:25]]
    owner = '0x' + rpc(U, 'eth_call', [{'to': P, 'data': '0x' + (sel('ownerOf(uint256)') + w(t)).hex()}, blk])[-40:]
    liq = int(rpc(U, 'eth_call', [{'to': P, 'data': '0x' + (sel('getPositionLiquidity(uint256)') + w(t)).hex()}, blk]), 16)
    v = int.from_bytes(d, 'big'); tl = (v >> 8) & 0xffffff; tu = (v >> 32) & 0xffffff
    tl = tl - (1 << 24) if tl >> 23 else tl; tu = tu - (1 << 24) if tu >> 23 else tu
    rows.append({'tokenId': t, 'poolId': p['poolId'], 'owner': owner, 'liquidity': liq, 'tickLower': tl, 'tickUpper': tu})
out = {'chainId': cid, 'url': U, 'block': 'latest', 'headAtStart': headAtStart, 'clientStart': cv0, 'positionManager': P, 'tokensScanned': N - 1, 'pools': []}
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
for p in pools:
    L = rpc(LU, 'eth_getLogs', [{'address': PM, 'topics': [INIT, p['poolId']], 'fromBlock': hex(p['initBlock']), 'toBlock': hex(p['initBlock'])}], tries=8)
    itx = L[0]['transactionHash'] if L else None; creator = None
    for k in range(8):
        if not itx: break
        b = rpc(LU, 'eth_getBlockByNumber', [hex(p['initBlock']), True], tries=4)
        if b: creator = [t for t in b['transactions'] if t['hash'] == itx][0]['from'].lower(); break
    mine = [r for r in rows if r['poolId'] == p['poolId'] and r['liquidity'] > 0]
    exp = collections.Counter()
    for r in mine: exp[r['tickLower']] += r['liquidity']; exp[r['tickUpper']] += r['liquidity']
    st = int.from_bytes(kec(bytes.fromhex(p['poolId'][2:]) + w(6)), 'big')
    got = {}
    for t in p['ticks']:
        slot = kec(w(t) + w(st + 4))
        got[t] = int(rpc(U, 'eth_call', [{'to': PM, 'data': '0x1e2eaeaf' + slot.hex()}, blk]), 16) & ((1 << 128) - 1)
    sp = p['sqrtPriceX96'] / 2 ** 96
    def amt(L_, a, b):
        sa, sb = math.sqrt(1.0001 ** a), math.sqrt(1.0001 ** b)
        if sp <= sa: return L_ * (1 / sa - 1 / sb), 0.0
        if sp >= sb: return 0.0, L_ * (sb - sa)
        return L_ * (1 / sp - 1 / sb), L_ * (sp - sa)
    for r in mine: r['amount0raw'], r['amount1raw'] = amt(r['liquidity'], r['tickLower'], r['tickUpper']); r['thirdParty'] = r['owner'].lower() != creator
    out['pools'].append({**{k: p[k] for k in ('poolId', 'hook', 'flagBits', 'kind', 'initBlock', 'liquidity', 'currency0', 'currency1')}, 'initTx': itx, 'creator': creator, 'positions': mine,
                         'tickCheck': {'ticks': p['ticks'], 'posmLiquidityGross': {str(t): exp[t] for t in p['ticks']}, 'tickInfoLiquidityGross': {str(t): got[t] for t in p['ticks']},
                                       'allLiquidityInPositionManager': all(exp[t] == got[t] for t in p['ticks'])}, 'thirdPartyLive': any(r['thirdParty'] for r in mine)})
    print(cid, p['poolId'][:12], p['hook'][:10], hex(p['flagBits']), 'creator', (creator or '')[:10], 'posm positions', len(mine), 'third', out['pools'][-1]['thirdPartyLive'], 'all in posm', out['pools'][-1]['tickCheck']['allLiquidityInPositionManager'], flush=True)
out['clientEnd'] = rpc(U, 'web3_clientVersion', [])
json.dump(out, open('raw/posm_%d.json' % cid, 'w'), indent=1)
