"""Full exits of real PositionManager positions, measured with eth_estimateGas from the position's owner.
Read-only: nothing is signed or sent. For each network: sample token ids below nextTokenId, keep positions
with liquidity > 0 in pools without a hook, and estimate modifyLiquidities([BURN_POSITION, TAKE_PAIR]) from
ownerOf(tokenId) with the take to the owner. BURN_POSITION removes all liquidity and collects fees.
usage: python3 -I exits.py <out.json> [chainId ...]"""
import sys, json, random, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/020/theme-mined-gas-cap.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpc import call, NET
from evm import keccak

def sel(sig): return keccak(sig.encode())[:4].hex()
def w(x): return format(x % (1 << 256), '064x')
def wa(a): return w(int(a, 16))
S_NEXT = sel('nextTokenId()'); S_INFO = sel('getPoolAndPositionInfo(uint256)'); S_LIQ = sel('getPositionLiquidity(uint256)')
S_OWNER = sel('ownerOf(uint256)'); S_MOD = sel('modifyLiquidities(bytes,uint256)')

def ec(url, to, data, frm=None):
    tx = {'to': to, 'data': '0x' + data}
    if frm: tx['from'] = frm
    r = call(url, 'eth_call', [tx, 'latest'])
    return r.get('result') if isinstance(r, dict) else None

def enc_bytes(h):  # h: hex string without 0x
    n = len(h) // 2
    return w(n) + h + '0' * ((64 - len(h) % 64) % 64)

def unlock_data(token, c0, c1, rcpt):
    actions = '0311'
    burn = w(token) + w(0) + w(0) + w(0x80) + w(0)               # (tokenId, amount0Min, amount1Min, hookData='')
    take = wa(c0) + wa(c1) + wa(rcpt)                            # (currency0, currency1, recipient)
    elems = [burn, take]
    arr_heads = ''; arr_body = ''; off = 32 * len(elems)
    for e in elems:
        arr_heads += w(off); b = enc_bytes(e); arr_body += b; off += len(b) // 2
    arr = w(len(elems)) + arr_heads + arr_body
    act = enc_bytes(actions)
    head = w(0x40) + w(0x40 + len(act) // 2)
    return head + act + arr

def calldata(token, c0, c1, rcpt):
    ud = unlock_data(token, c0, c1, rcpt)
    return S_MOD + w(0x40) + w((1 << 255)) + enc_bytes(ud)

def run(n, want=20, tries=160, seed=20):
    url = n['rpc']; posm = n['contracts']['PositionManager']; cid = n['chainId']
    rnd = random.Random(seed + cid)
    out = {'chainId': cid, 'name': n['name'], 'positionManager': posm, 'rows': []}
    r = ec(url, posm, S_NEXT)
    if not r: out['error'] = 'nextTokenId failed'; return out
    nxt = int(r, 16); out['nextTokenId'] = nxt
    ids = list(range(nxt - 1, max(0, nxt - 40), -1)) + [rnd.randrange(1, nxt) for _ in range(tries)]
    seen = set(); got = 0
    for t in ids:
        if got >= want or t in seen or t <= 0: continue
        seen.add(t)
        info = ec(url, posm, S_INFO + w(t))
        if not info or len(info) < 2 + 64 * 6: continue
        words = [int(info[2 + 64 * i: 2 + 64 * (i + 1)], 16) for i in range(6)]
        c0, c1, fee, sp, hooks = words[:5]
        if hooks != 0 or (c0 == 0 and c1 == 0): continue
        liq = ec(url, posm, S_LIQ + w(t))
        if not liq or int(liq, 16) == 0: continue
        own = ec(url, posm, S_OWNER + w(t))
        if not own: continue
        owner = '0x' + own[-40:]
        c0h = '0x' + format(c0, '040x'); c1h = '0x' + format(c1, '040x')
        cd = calldata(t, c0h, c1h, owner)
        est = call(url, 'eth_estimateGas', [{'from': owner, 'to': posm, 'data': '0x' + cd}, 'latest'])
        row = {'tokenId': t, 'owner': owner, 'currency0': c0h, 'currency1': c1h, 'fee': fee, 'tickSpacing': sp,
               'liquidity': int(liq, 16)}
        if isinstance(est, dict) and isinstance(est.get('result'), str):
            row['estimate'] = int(est['result'], 16)
        else:
            row['error'] = (est or {}).get('error', est)
        out['rows'].append(row); got += 1
    ok = [r['estimate'] for r in out['rows'] if 'estimate' in r]
    out['n'] = len(out['rows']); out['nOk'] = len(ok)
    out['max'] = max(ok) if ok else None; out['median'] = sorted(ok)[len(ok) // 2] if ok else None
    return out

if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[2:]] or [n['chainId'] for n in NET]
    nets = [n for n in NET if n['chainId'] in ids]
    with cf.ThreadPoolExecutor(7) as ex:
        res = list(ex.map(run, nets))
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
    for r in res:
        errs = [str(x.get('error'))[:80] for x in r['rows'] if 'error' in x][:3]
        print(r['chainId'], r['name'], 'next', r.get('nextTokenId'), 'n', r.get('n'), 'ok', r.get('nOk'), 'max', r.get('max'), 'med', r.get('median'), errs)
