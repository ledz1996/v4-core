"""Cycle 29, Task 1. List the PoolManager sites (from cycle 28's sitearms.json) that take shift_by_literal, a literal
shifted by a run-time count, a literal SIGNEXTEND index or a BYTE literal arm, with pc, literal and the src/ line from
the solc source map of the same build (cycle 12 build-srcmap.json, whose runtime equals build/PoolManager.json).
usage: python3 -I sites.py <outdir>"""
import sys, os, json, collections, importlib.util
OUT = sys.argv[1]
R = '/home/user/v4-core/research/network-risk'
spec = importlib.util.spec_from_file_location('srcmap', R + '/cycles/012/theme-bytecode-coverage.work/srcmap.py')
sm = importlib.util.module_from_spec(spec); spec.loader.exec_module(sm)
assert sm.code.hex() == json.load(open(R + '/build/PoolManager.json'))['runtime'].removeprefix('0x')
rows = json.load(open(R + '/cycles/028/theme-monad-shipped-emitter.work/out/sitearms.json'))['rows']
out = []; cnt = collections.Counter(); pairs = collections.Counter(); per = collections.defaultdict(list)
for r in rows:
    op = r['op']; a = r['arm']
    if a.startswith('shift_by_literal'): k = 'shift_by_literal'; lit = int(r['values'][0], 16)
    elif a.startswith('shift_literal_by_non_literal'): k = 'shift_literal_by_non_literal'; lit = int(r['values'][1], 16)
    elif op == 'SIGNEXTEND' and r['values'][0]: k = 'signextend_literal_index'; lit = int(r['values'][0], 16)
    elif op == 'BYTE' and r['values'][0]: k = 'byte_literal_index'; lit = int(r['values'][0], 16)
    elif op == 'BYTE': k = 'byte_literal_value_runtime_index'; lit = int(r['values'][1], 16)
    else: continue
    if r['folded']: k += ' (both literal, folded)'
    L = sm.loc(r['pc'])
    src = '%s:%s' % (L['file'], L['line']) if L.get('line') else L['file']
    row = {'pc': r['pc'], 'op': op, 'arm': k, 'literal': hex(lit), 'src': src, 'snippet': L.get('snippet', '')[:120],
           'harnessMnemonics': r['harnessMnemonics']}
    out.append(row); cnt[(k, op)] += 1; pairs[(op, k, lit)] += 1; per[(op, k, hex(lit))].append(src)
summ = {'counts': {'%s %s' % (k[1], k[0]): v for k, v in sorted(cnt.items())},
        'distinct': [{'op': k[0], 'arm': k[1], 'literal': hex(k[2]), 'sites': v, 'srcLines': sorted(set(per[(k[0], k[1], hex(k[2]))]))} for k, v in sorted(pairs.items())]}
json.dump({'sites': out, 'summary': summ}, open(os.path.join(OUT, 'sites.json'), 'w'), indent=1)
for k, v in summ['counts'].items(): print(v, k)
for d in summ['distinct']: print(d['op'], d['arm'][:20], d['literal'][:20], d['sites'], d['srcLines'][:6])
