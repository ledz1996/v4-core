"""Cycle 30, lead L-1192: mined census of the unchecked subtractions of Pool.getFeeGrowthInside (src/libraries/Pool.sol:498-509)
and Position.update (src/libraries/Position.sol:91-96), extended from cycles/029/high-throughput.work/scripts/fgi_census.py:
absolute block range, ModifyLiquidity logs gathered with a topic filter, the one-log-per-pool-per-block rule checked by a
second getLogs on that block and pool, storage read at the parent block and at the block, and these words compared:
  feeGrowthInside0/1LastX128 of the position (reference: getFeeGrowthInside with v4math.sub),
  position liquidity (LiquidityMath.addDelta), tick word 0 of both ticks (Pool.updateTick packing, clearTick on a flip down),
  feeGrowthOutside of both ticks (updateTick initialisation rule).
It records which subtraction borrowed (getFeeGrowthInside below/above/inside, per token) and whether Position.update's
subtraction feeGrowthInside - feeGrowthInsideLast wrapped with nonzero liquidity (fees then computed with v4math.mul_div).
Read-only. Usage: python3 -I fgi30.py <out.json> <pm> <from> <to> <step> <threads> <maxCand> <url> [url ...]"""
import sys, os, json, time, random
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evm import keccak
import v4math as V
from rpc30 import R
M = (1 << 256) - 1; Q128 = 1 << 128
TOPIC = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
def w(x): return (x & M).to_bytes(32, 'big')
def s24(x): x &= 0xffffff; return x - (1 << 24) if x >> 23 else x
def s256(x): return x - (1 << 256) if x >> 255 else x
def s128(x): x &= (1 << 128) - 1; return x - (1 << 128) if x >> 127 else x
def add_delta(x, y):  # LiquidityMath.addDelta: reverts on overflow/underflow; None marks a revert
    z = x + y
    return z if 0 <= z < (1 << 128) else None

def make_one(pm, urls):
    def one(l):
        b = int(l['blockNumber'], 16); pid = int(l['topics'][1], 16); sender = int(l['topics'][2], 16)
        d = bytes.fromhex(l['data'][2:]); tl = s24(int.from_bytes(d[0:32], 'big')); tu = s24(int.from_bytes(d[32:64], 'big'))
        ld = s256(int.from_bytes(d[64:96], 'big')); salt = d[96:128]
        try:
            other, _ = R(urls, 'eth_getLogs', [{'address': pm, 'topics': [None, l['topics'][1]], 'fromBlock': hex(b), 'toBlock': hex(b)}])
            if len(other) != 1: return {'block': b, 'tx': l['transactionHash'], 'skip': f'{len(other)} logs of this pool in the block'}
            base = int.from_bytes(keccak(w(pid) + w(6)), 'big')
            def ts(t, j): return (int.from_bytes(keccak(w(t) + w(base + 4)), 'big') + j) & M
            pk = keccak(sender.to_bytes(20, 'big') + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + salt)
            ps = int.from_bytes(keccak(pk + w(base + 6)), 'big')
            g = lambda s, blk: int(R(urls, 'eth_getStorageAt', [pm, '0x%x' % s, hex(blk)])[0], 16)
            p = b - 1
            slot0 = g(base, p); cur = s24(slot0 >> 160); fg = [g(base + 1, p), g(base + 2, p)]
            lo = [g(ts(tl, j), p) for j in range(3)]; up = [g(ts(tu, j), p) for j in range(3)]
            pos0 = [g(ps + j, p) for j in range(3)]
            lo1 = [g(ts(tl, j), b) for j in range(3)]; up1 = [g(ts(tu, j), b) for j in range(3)]
            pos1 = [g(ps + j, b) for j in range(3)]
            # Pool.updateTick (Pool.sol:520-558) on both ticks when ld != 0
            ref_lo, ref_up = list(lo), list(up); flip = [False, False]
            if ld != 0:
                for k, (arr, t, upper) in enumerate(((ref_lo, tl, False), (ref_up, tu, True))):
                    gb = arr[0] & (Q128 - 1); nb = s128(arr[0] >> 128); ga = add_delta(gb, ld)
                    if ga is None: raise ValueError('addDelta would revert on tick')
                    flip[k] = (ga == 0) != (gb == 0)
                    if gb == 0 and t <= cur: arr[1], arr[2] = fg[0], fg[1]
                    na = nb - ld if upper else nb + ld
                    arr[0] = (ga & (Q128 - 1)) | ((na << 128) & M)
            ins = []; br = []
            for k in (0, 1):
                A, C = ref_lo[1 + k], ref_up[1 + k]
                if cur < tl: v = V.sub(A, C); br.append(('below', A < C))
                elif cur >= tu: v = V.sub(C, A); br.append(('above', C < A))
                else: v = V.sub(V.sub(fg[k], A), C); br.append(('inside', fg[k] < A or (fg[k] - A) < C))
                ins.append(v)
            liq0 = pos0[0] & (Q128 - 1)
            liq1 = liq0 if ld == 0 else add_delta(liq0, ld)
            pbor = [ins[k] < pos0[1 + k] for k in (0, 1)]
            fees = [V.mul_div(V.sub(ins[k], pos0[1 + k]), liq0, Q128) for k in (0, 1)]
            if ld < 0:  # clearTick (Pool.sol) deletes a tick that flipped to empty
                if flip[0]: ref_lo = [0, 0, 0]
                if flip[1]: ref_up = [0, 0, 0]
            ref_pos = [liq1, ins[0], ins[1]]
            cmp = {'pos': pos1 == ref_pos, 'tickLower': lo1 == ref_lo, 'tickUpper': up1 == ref_up}
            row = {'block': b, 'tx': l['transactionHash'], 'pool': l['topics'][1], 'tl': tl, 'tu': tu, 'cur': cur, 'ld': str(ld),
                   'branch': [x for x, _ in br], 'borrow': [y for _, y in br], 'posBorrow': pbor, 'liqBefore': str(liq0),
                   'fees': [str(x) for x in fees], 'equal': all(cmp.values()), 'cmp': cmp}
            if not row['equal']:
                row.update(ref={'pos': [hex(x) for x in ref_pos], 'lo': [hex(x) for x in ref_lo], 'up': [hex(x) for x in ref_up]},
                           got={'pos': [hex(x) for x in pos1], 'lo': [hex(x) for x in lo1], 'up': [hex(x) for x in up1]},
                           pre={'slot0': hex(slot0), 'fg': [hex(x) for x in fg], 'pos': [hex(x) for x in pos0], 'lo': [hex(x) for x in lo], 'up': [hex(x) for x in up]})
            return row
        except Exception as e:
            return {'block': b, 'tx': l['transactionHash'], 'error': str(e)[:300]}
    return one

def summarize(rows):
    stats = {'checked': 0, 'equal': 0, 'different': 0, 'error': 0, 'skipped': 0,
             'borrow': {'below': 0, 'above': 0, 'inside': 0}, 'posBorrow': 0, 'posBorrowWithLiquidity': 0}
    first = {}
    for r in rows:
        if 'error' in r: stats['error'] += 1; continue
        if 'skip' in r: stats['skipped'] += 1; continue
        stats['checked'] += 1; stats['equal' if r['equal'] else 'different'] += 1
        for k, (x, y) in enumerate(zip(r['branch'], r['borrow'])):
            if y:
                stats['borrow'][x] += 1; first.setdefault(f'{x}{k}', {'block': r['block'], 'tx': r['tx'], 'equal': r['equal']})
        for k in (0, 1):
            if r['posBorrow'][k]:
                stats['posBorrow'] += 1; first.setdefault(f'position{k}', {'block': r['block'], 'tx': r['tx'], 'equal': r['equal'], 'liqBefore': r['liqBefore']})
                if int(r['liqBefore']):
                    stats['posBorrowWithLiquidity'] += 1; first.setdefault(f'positionWithLiquidity{k}', {'block': r['block'], 'tx': r['tx'], 'equal': r['equal'], 'fees': r['fees'][k]})
    return stats, first

def main():
    out, pm = sys.argv[1], sys.argv[2]
    if sys.argv[3] == 'windows':
        return main_windows(out, pm, json.load(open(sys.argv[4])), int(sys.argv[5]), int(sys.argv[6]), sys.argv[8:])
    a, b, step, nth, maxc = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
    urls = sys.argv[8:]
    cv0 = {u: R(u, 'web3_clientVersion', [])[0] for u in urls}
    errs = []
    def chunk(lo):
        hi = min(lo + step - 1, b); got = []; f = lo; st = step
        while f <= hi:
            t = min(f + st - 1, hi)
            try:
                r, u = R(urls, 'eth_getLogs', [{'address': pm, 'topics': [TOPIC], 'fromBlock': hex(f), 'toBlock': hex(t)}])
            except Exception as e:
                errs.append([f, t, str(e)[:160]]); st = max(st // 2, 100)
                if len(errs) > 2000: return got, f - 1
                continue
            got += r; f = t + 1
        return got, hi
    starts = list(range(a, b + 1, step)); logs = []; reached = a - 1
    with ThreadPoolExecutor(nth) as ex:
        for k, (g, h) in enumerate(ex.map(chunk, starts)):
            logs += g
            if h == min(starts[k] + step - 1, b) and reached == starts[k] - 1: reached = h
            if k % 500 == 0: print('logs', h, len(logs), flush=True)
    print('ModifyLiquidity logs', len(logs), 'reached', reached, flush=True)
    per = {}
    for l in logs: per.setdefault((int(l['blockNumber'], 16), l['topics'][1]), []).append(l)
    single = [v[0] for v in per.values() if len(v) == 1]
    single.sort(key=lambda l: int(l['blockNumber'], 16))
    seed = 30030; rnd = random.Random(seed)
    if len(single) > maxc:
        # the first quarter of the budget goes to the oldest candidates (first occurrences), the rest is a uniform sample
        k0 = maxc // 4; chosen = single[:k0] + sorted(rnd.sample(single[k0:], maxc - k0), key=lambda l: int(l['blockNumber'], 16))
    else: chosen = single

    one = make_one(pm, urls)
    with ThreadPoolExecutor(nth) as ex: rows = list(ex.map(one, chosen))
    stats, first = summarize(rows)
    res = {'pm': pm, 'from': a, 'to': b, 'reached': reached, 'urls': urls, 'clientBefore': cv0,
           'clientAfter': {u: R(u, 'web3_clientVersion', [])[0] for u in urls}, 'getLogsErrors': errs, 'seed': seed,
           'modifyLiquidityLogs': len(logs), 'singleCandidates': len(single), 'chosen': len(chosen), 'stats': stats,
           'firstBorrow': first, 'rows': rows}
    json.dump(res, open(out, 'w'))
    print(json.dumps(stats), json.dumps(first)[:2000])
def main_windows(out, pm, wins, step, nth, urls):
    cv0 = {u: R(u, 'web3_clientVersion', [])[0] for u in urls}
    one = make_one(pm, urls); rnd = random.Random(30031); rows = []; winres = []
    for wdef in wins:
        logs = []; f = wdef['from']; reached = f - 1; errs = 0
        while f <= wdef['to']:
            t = min(f + step - 1, wdef['to'])
            try: r, _ = R(urls, 'eth_getLogs', [{'address': pm, 'topics': [TOPIC], 'fromBlock': hex(f), 'toBlock': hex(t)}])
            except Exception as e:
                errs += 1
                if errs > 50: break
                continue
            logs += r; reached = t; f = t + 1
            if wdef.get('chrono'):
                per = {}
                for l in logs: per.setdefault((int(l['blockNumber'], 16), l['topics'][1]), []).append(l)
                if sum(1 for v in per.values() if len(v) == 1) >= wdef['cap']: break
        per = {}
        for l in logs: per.setdefault((int(l['blockNumber'], 16), l['topics'][1]), []).append(l)
        single = sorted((v[0] for v in per.values() if len(v) == 1), key=lambda l: (int(l['blockNumber'], 16), int(l['logIndex'], 16)))
        ch = single[:wdef['cap']] if wdef.get('chrono') else sorted(rnd.sample(single, min(wdef['cap'], len(single))), key=lambda l: int(l['blockNumber'], 16))
        with ThreadPoolExecutor(nth) as ex: rr = list(ex.map(one, ch))
        rows += rr; winres.append({'from': wdef['from'], 'to': wdef['to'], 'reached': reached, 'logs': len(logs), 'single': len(single), 'chosen': len(ch), 'chrono': bool(wdef.get('chrono'))})
        print('window', winres[-1], flush=True)
    stats, first = summarize(rows)
    json.dump({'pm': pm, 'mode': 'windows', 'urls': urls, 'clientBefore': cv0, 'clientAfter': {u: R(u, 'web3_clientVersion', [])[0] for u in urls},
               'seed': 30031, 'windows': winres, 'stats': stats, 'firstBorrow': first, 'rows': rows}, open(out, 'w'))
    print(json.dumps(stats), json.dumps(first)[:3000])

main()
