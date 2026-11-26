"""For every pool of raw/census_<cid>.json (hook without code, or EIP-7702 delegated): flag bits, slot0 and active liquidity
(extsload), all ModifyLiquidity logs of those pools (topic OR list) from the first init block to head, live positions,
who added them (tx.from; PositionManager token owner), the pool creator (tx.from of the Initialize transaction),
amount estimates at the current price, nonce, balance and code of the hook address, and a direct eth_call from the
PoolManager to the hook with beforeRemoveLiquidity calldata. Read only. usage: detail.py <cid> <stateUrl> <logUrl> <chunk>"""
import sys, json, time, math, collections, concurrent.futures as cf
from ep import rpc, batch, NETS
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
cid, U, LU, CH = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
C = json.load(open('raw/census_%d.json' % cid)); N = NETS[cid]; PM = N['poolManager'].lower(); POSM = N['contracts'].get('PositionManager', '').lower()
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'; MODL = '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec'
import subprocess
def keccak(b): return subprocess.run(['build/kec', str(len(b))], input=b, capture_output=True).stdout
M = 1 << 256
def i256(x): return (x % M).to_bytes(32, 'big')
import os
blk = hex(int(rpc(U, 'eth_blockNumber', []), 16) - 30) if os.environ.get('FRESH') else hex(C['block']); cv0 = {U: rpc(U, 'web3_clientVersion', []), LU: rpc(LU, 'web3_clientVersion', [])}
def extsload(slots):
    out = []
    for i in range(0, len(slots), 1000):
        part = slots[i:i + 1000]
        data = 'dbd035ff' + (32).to_bytes(32, 'big').hex() + len(part).to_bytes(32, 'big').hex() + b''.join(part).hex()
        r = bytes.fromhex(rpc(U, 'eth_call', [{'to': PM, 'data': '0x' + data}, blk])[2:])
        out += [int.from_bytes(r[64 + 32 * k:96 + 32 * k], 'big') for k in range(len(part))]
    return out
NAMES = ['afterRemoveReturnsDelta', 'afterAddReturnsDelta', 'afterSwapReturnsDelta', 'beforeSwapReturnsDelta', 'afterDonate', 'beforeDonate', 'afterSwap', 'beforeSwap', 'afterRemove', 'beforeRemove', 'afterAdd', 'beforeAdd', 'afterInit', 'beforeInit']
def sqrt_at(t): return math.sqrt(1.0001 ** t)
def amounts(L, tl, tu, sp):
    a, b = sqrt_at(tl), sqrt_at(tu)
    if sp <= a: return L * (1 / a - 1 / b), 0.0
    if sp >= b: return 0.0, L * (b - a)
    return L * (1 / sp - 1 / b), L * (sp - a)
pools = C['hookPools']
def ticks_of(p):
    pid = bytes.fromhex(p['poolId'][2:]); st = int.from_bytes(keccak(pid + (6).to_bytes(32, 'big')), 'big'); ts = p['tickSpacing']
    lo_, hi_ = (-887272 // ts) >> 8, (887272 // ts) >> 8; words = list(range(lo_ - 1, hi_ + 2))
    base = (st + 5).to_bytes(32, 'big')
    kb = b''.join(i256(w) + base for w in words)
    hs = subprocess.run(['build/kec', '64'], input=kb, capture_output=True).stdout
    bm = extsload([hs[32 * i:32 * i + 32] for i in range(len(words))])
    return [((w << 8) + b) * ts for w, v in zip(words, bm) for b in range(256) if v >> b & 1]
skipped = []
if os.environ.get('SKIPEMPTY'):
    keep = []
    for p in pools:
        t = ticks_of(p); p['initializedTicks'] = t
        (keep if t else skipped).append(p)
    pools = keep
byid = {p['poolId']: p for p in pools}
res = {'chainId': cid, 'stateUrl': U, 'logUrl': LU, 'block': int(blk, 16), 'skippedNoTicks': [{'poolId': p['poolId'], 'hook': p['hook'], 'flagBits': int(p['hook'], 16) & 0x3fff, 'initBlock': p['block']} for p in skipped], 'clientVersionStart': cv0, 'pools': []}
if pools:
    # ModifyLiquidity logs for all pools at once
    lo = min(p['block'] for p in pools); hi = min(int(blk, 16), int(rpc(LU, 'eth_blockNumber', []), 16) - 50); FAILS = []; ids = [p['poolId'] for p in pools]; logs = []
    def get(a, b):
        for k in range(6):
            try: return rpc(LU, 'eth_getLogs', [{'address': PM, 'topics': [MODL, ids], 'fromBlock': hex(a), 'toBlock': hex(b)}], tries=3)
            except Exception as e:
                m = str(e).lower()
                if b > a and any(x in m for x in ('range', 'too many', 'exceed', 'too large', 'limit', 'max', 'timeout', 'size')) and 'rate' not in m:
                    mid = (a + b) // 2; return get(a, mid) + get(mid + 1, b)
                time.sleep(3 * (k + 1)); last = e
        FAILS.append([a, b, str(last)[:120]]); return []
    with cf.ThreadPoolExecutor(int(os.environ.get("W", "4"))) as ex:
        for L in ex.map(lambda a: get(a, min(hi, a + CH - 1)), range(lo, hi + 1, CH)): logs += L
    res['modifyLiquidityLogs'] = len(logs); res['logRange'] = [lo, hi]; res['logFailures'] = FAILS
    per = collections.defaultdict(list)
    for l in logs:
        d = l['data'][2:]
        def s(x): v = int(x, 16); return v - M if v >> 255 else v
        per[l['topics'][1]].append({'block': int(l['blockNumber'], 16), 'tx': l['transactionHash'], 'sender': '0x' + l['topics'][2][-40:], 'tickLower': s(d[0:64]), 'tickUpper': s(d[64:128]), 'liquidityDelta': s(d[128:192]), 'salt': '0x' + d[192:256]})
    hooks = sorted({p['hook'] for p in pools})
    hinfo = {}
    for h in hooks:
        nonce = int(rpc(U, 'eth_getTransactionCount', [h, blk]), 16); bal = int(rpc(U, 'eth_getBalance', [h, blk]), 16); code = rpc(U, 'eth_getCode', [h, blk])
        # direct call from the PoolManager with beforeRemoveLiquidity(address,PoolKey,ModifyLiquidityParams,bytes) shaped calldata
        cd = '0x21d0ee70' + '00' * 32 * 11
        try: r = rpc(U, 'eth_call', [{'from': PM, 'to': h, 'data': cd, 'gas': hex(1_000_000)}, blk], tries=2); call = {'ok': True, 'returndata': r}
        except Exception as e: call = {'ok': False, 'error': str(e)[:200]}
        hinfo[h] = {'nonce': nonce, 'balance': bal, 'code': code[:60], 'codeLen': (len(code) - 2) // 2, 'callFromPM': call}
    res['hooks'] = hinfo
    for p in pools:
        pid = bytes.fromhex(p['poolId'][2:]); st = int.from_bytes(keccak(pid + (6).to_bytes(32, 'big')), 'big')
        s0, liq = extsload([st.to_bytes(32, 'big'), (st + 3).to_bytes(32, 'big')])
        sp96 = s0 & ((1 << 160) - 1); tick = (s0 >> 160) & 0xffffff; tick = tick - (1 << 24) if tick >= 1 << 23 else tick
        hk = int(p['hook'], 16); flags = [NAMES[i] for i in range(14) if hk >> i & 1]
        # initialization tx
        L = rpc(LU, 'eth_getLogs', [{'address': PM, 'topics': [INIT, p['poolId']], 'fromBlock': hex(p['block']), 'toBlock': hex(p['block'])}])
        itx = L[0]['transactionHash'] if L else None
        creator = rpc(U, 'eth_getTransactionByHash', [itx])['from'].lower() if itx else None
        pos = collections.OrderedDict()
        for e in per.get(p['poolId'], []):
            k = (e['sender'], e['tickLower'], e['tickUpper'], e['salt'])
            q = pos.setdefault(k, {'sender': e['sender'], 'tickLower': e['tickLower'], 'tickUpper': e['tickUpper'], 'salt': e['salt'], 'liquidity': 0, 'adds': [], 'removes': 0})
            q['liquidity'] += e['liquidityDelta']
            if e['liquidityDelta'] > 0: q['adds'].append(e['tx'])
            elif e['liquidityDelta'] < 0: q['removes'] += 1
        live = []
        sp = sp96 / 2 ** 96 if sp96 else 0
        for q in pos.values():
            if q['liquidity'] <= 0: continue
            frm = sorted({rpc(U, 'eth_getTransactionByHash', [t])['from'].lower() for t in q['adds'][:5]})
            owner = None
            if q['sender'] == POSM and POSM:
                try: owner = '0x' + rpc(U, 'eth_call', [{'to': POSM, 'data': '0x6352211e' + q['salt'][2:]}, blk])[-40:]
                except Exception as e: owner = 'ownerOf failed: ' + str(e)[:80]
            a0, a1 = amounts(q['liquidity'], q['tickLower'], q['tickUpper'], sp) if sp else (None, None)
            third = any(x != creator for x in frm) or (owner is not None and owner.lower() != creator)
            live.append({**{k: v for k, v in q.items() if k != 'adds'}, 'addTxs': q['adds'][:5], 'addFrom': frm, 'tokenOwner': owner, 'amount0raw': a0, 'amount1raw': a1, 'thirdParty': third})
        exp = collections.Counter()
        for q in live: exp[q['tickLower']] += q['liquidity']; exp[q['tickUpper']] += q['liquidity']
        tks = sorted(exp); tk_base = (st + 4).to_bytes(32, 'big')
        got = extsload([keccak(i256(t) + tk_base) for t in tks]) if tks else []
        tickCheck = {'ticks': len(tks), 'mismatch': [[t, exp[t], g & ((1 << 128) - 1)] for t, g in zip(tks, got) if exp[t] != g & ((1 << 128) - 1)]}
        if 'initializedTicks' in p: tickCheck['bitmapTicks'] = len(p['initializedTicks']); tickCheck['bitmapNotInLogs'] = sorted(set(p['initializedTicks']) - set(tks))[:20]
        res['pools'].append({**p, 'tickCheck': tickCheck, 'flags': flags, 'flagBits': hk & 0x3fff, 'sqrtPriceX96': sp96, 'tick': tick, 'activeLiquidity': liq, 'initTx': itx, 'creator': creator,
                             'modifyLiquidityLogs': len(per.get(p['poolId'], [])), 'positionsEver': len(pos), 'livePositions': live,
                             'thirdPartyLive': any(x['thirdParty'] for x in live), 'removalGated': bool(hk & (1 << 9) or hk & (1 << 8)), 'donateGated': bool(hk & (1 << 5) or hk & (1 << 4))})
        print(cid, p['poolId'][:12], p['kind'], p['hook'], 'flags', flags, 'L', liq, 'logs', len(per.get(p['poolId'], [])), 'live', len(live), 'third', res['pools'][-1]['thirdPartyLive'], flush=True)
res['clientVersionEnd'] = {U: rpc(U, 'web3_clientVersion', []), LU: rpc(LU, 'web3_clientVersion', [])}
json.dump(res, open('raw/detail_%d.json' % cid, 'w'), indent=1)
print('done', cid, len(res['pools']), flush=True)
