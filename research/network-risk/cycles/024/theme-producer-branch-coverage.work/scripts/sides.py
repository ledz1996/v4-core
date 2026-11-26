"""Static guess of what each side of a JUMPI leads to: 'revert' when straight-line code (following PUSH-JUMP) reaches REVERT
or INVALID before another JUMPI, else 'continues'. Then list the library and settlement JUMPIs with a side the producers never took.
usage: sides.py   writes ../out/library-sides.json"""
import sys, json, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap as S
code = S.code; I = S.PC2I
def nxt(p): op = code[p]; return p + (op - 0x5e if 0x60 <= op <= 0x7f else 1)
def push_val(p): op = code[p]; return int.from_bytes(code[p + 1:p + op - 0x5e], 'big') if 0x60 <= op <= 0x7f else None
def walk(p, lim=80):
    prev = None
    for _ in range(lim):
        if p >= len(code): return 'end'
        op = code[p]
        if op in (0xfd, 0xfe): return 'revert'
        if op in (0x00, 0xf3): return 'return'
        if op == 0x57: return 'continues'
        if op == 0x56:
            t = push_val(prev) if prev is not None else None
            if t is None: return 'continues'
            prev = None; p = t; continue
        prev = p; p = nxt(p)
    return 'continues'
def sides(p):
    k = I[p]; t = push_val(S.starts[k - 1]); return {'taken': walk(t) if t is not None else '?', 'fallthrough': walk(nxt(p))}
LIBS = ('TickMath', 'BitMath', 'FullMath', 'UnsafeMath', 'SqrtPriceMath', 'SwapMath', 'TickBitmap', 'Position', 'LiquidityMath', 'Pool', 'BalanceDelta', 'SafeCast', 'ProtocolFeeLibrary', 'LPFeeLibrary', 'CurrencyDelta', 'Currency', 'NonzeroDeltaCount', 'CurrencyReserves', 'SwapMath')
if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    D = {c: json.load(open('%s/../out/%d/branches.json' % (HERE, c))) for c in (143, 4326, 999, 8453)}
    out = []
    for i, r in enumerate(D[143]['rows']):
        f = r['file']; base = f.split('/')[-1].replace('.sol', '')
        pmline = f == 'src/PoolManager.sol' and r['line'] not in (80,)
        if base not in LIBS and not pmline: continue
        sd = sides(r['pc'])
        e = {'pc': r['pc'], 'file': f, 'line': r['line'], 'snippet': r['snippet'], 'sideLeadsTo': sd, 'cycle12': r['cycle12'],
             'counts': {str(c): [D[c]['rows'][i]['taken'], D[c]['rows'][i]['fallthrough']] for c in D}}
        miss = {}
        for c in (143, 4326, 999):
            t, fl = e['counts'][str(c)]
            m = [s for s, n in (('taken', t), ('fallthrough', fl)) if n == 0]
            if m: miss[str(c)] = m
        e['neverOnProducer'] = miss
        # a missing side that does not revert is a computing side
        e['computingSideMissing'] = sorted({s for c, ms in miss.items() for s in ms if sd[s] != 'revert'})
        out.append(e)
    json.dump(out, open('%s/../out/library-sides.json' % HERE, 'w'), indent=1)
    for e in out:
        if e['computingSideMissing']:
            print(e['pc'], e['file'].split('/')[-1], e['line'], e['sideLeadsTo'], {c: v for c, v in e['counts'].items()}, e['snippet'][:70])
