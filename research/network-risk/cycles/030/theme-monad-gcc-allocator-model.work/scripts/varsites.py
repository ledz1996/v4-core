"""Cycle 30, Task 3. List the PoolManager sites of SHL, SHR, SAR, SIGNEXTEND and BYTE that cycle 28's site model
(sitearms.json) does not list as having a literal operand, with pc and the src/ line from the solc source map of
the same build (cycle 12 srcmap.py). These are the sites that reach the non-literal arms of Monad's emitter.
usage: python3 -I varsites.py <outdir>"""
import sys, os, json, collections, importlib.util
OUT = sys.argv[1]
R = '/home/user/v4-core/research/network-risk'
spec = importlib.util.spec_from_file_location('srcmap', R + '/cycles/012/theme-bytecode-coverage.work/srcmap.py')
sm = importlib.util.module_from_spec(spec); spec.loader.exec_module(sm)
code = bytes.fromhex(json.load(open(R + '/build/PoolManager.json'))['runtime'].removeprefix('0x'))
assert sm.code == code
lit = {r['pc'] for r in json.load(open(R + '/cycles/028/theme-monad-shipped-emitter.work/out/sitearms.json'))['rows']}
NAMES = {0x1b: 'SHL', 0x1c: 'SHR', 0x1d: 'SAR', 0x0b: 'SIGNEXTEND', 0x1a: 'BYTE'}
out = []; i = 0; tot = collections.Counter()
while i < len(code):
    op = code[i]
    if op in NAMES:
        tot[NAMES[op]] += 1
        if i not in lit:
            L = sm.loc(i)
            out.append({'pc': i, 'op': NAMES[op], 'src': '%s:%s' % (L['file'], L.get('line')), 'snippet': L.get('snippet', '')[:160]})
    i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
json.dump({'totals': tot, 'nonLiteralSites': out}, open(os.path.join(OUT, 'varsites.json'), 'w'), indent=1)
print(dict(tot)); print(collections.Counter(r['op'] for r in out))
for r in out: print(r['pc'], r['op'], r['src'], r['snippet'][:100].replace('\n', ' '))
