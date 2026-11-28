"""Task 3 (c): scan for the window in which the CallFrom child (PoolManager.unlock) succeeds and the completion step runs out
of gas, and read the PoolManager storage and transient words after the precompile returns. Uses the harness of live.py.
For each N: s = gas the child spends (direct call, ample gas, minus the driver's calibration), Lmin = smallest child gas limit
at which the direct call succeeds, e = CallFrom encode gas = 100 + 3*ceil(len(output)/32), o = decode gas 100+3*ceil(132/32)=115
plus the warm target access 100. Then scan the driver gas X for the Multicall3From call in steps of STEP over a range that
covers both bounds. usage: python3 -I window.py <out.json> <url> <N> [<N> ...]"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv_saved = list(sys.argv); sys.argv = ['live.py', 'none']
import live as L
sys.argv = sys.argv_saved
STEP = 20
def run(url, ns):
    out = {'url': url, 'before': L.ver(url), 'blk': L.rpc(url, 'eth_blockNumber', [], 30).get('result'), 'byN': {}}
    cal = L.call(url, 2, 1_000_000, 0, 0); base = cal['g0'] - cal['g1']
    for n in ns:
        a = L.call(url, 0, 20_000_000, n, 0); s = a['g0'] - a['g1'] - base
        lmin = L.search(url, 0, n, hi=20_000_000)[0]
        e = 100 + 3 * -(-(n + 64) // 32); o = 115 + 100
        # predicted precompile gas G bounds: child success needs (G-o) - (G-o)//64 >= lmin ; completion needs G >= o + s + e
        g_child = next(G for G in range(lmin + o, 2 * lmin + o + 100) if (G - o) - (G - o) // 64 >= lmin)
        g_compl = o + s + e
        rec = {'s': s, 'Lmin': lmin, 'e': e, 'o': o, 'G_childOk': g_child, 'G_completionOk': g_compl, 'windowPredicted': g_compl > g_child, 'scan': []}
        # X ~ G*64/63 + c ; c unknown (few thousand); scan generously
        lo = int(g_child * 64 / 63) - 1500; hi = int(g_compl * 64 / 63) + 6000
        for X in range(lo, hi, STEP):
            p = L.call(url, 1, X, n, 0)
            if 'err' in p: rec['scan'].append({'X': X, 'err': p['err']}); continue
            rec['scan'].append({'X': X, 'used': p['g0'] - p['g1'], 'ok': p['ok'], 'entry': p.get('entrySuccess'), 'isOp': p['isOperator'],
                                'tCur': p['tCurrency'], 'tLock': p['tLock'], 'tCount': p['tCount'], 'rds': p['rds'], 'ret': p['ret_head'][:640]})
        out['byN'][n] = rec
        print(url, n, {k: v for k, v in rec.items() if k != 'scan'}, flush=True)
    out['after'] = L.ver(url)
    return out
if __name__ == '__main__':
    url = sys.argv[2]; ns = [int(x) for x in sys.argv[3:]]
    res = {'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'step': STEP, 'result': run(url, ns)}
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
