"""L-1210: addresses of the uint256 instructions that cycle 30's vector mix leaves unreached in the Nitro b72783f
handler models, with the instruction text and a class: stack growth (morestack prologue/epilogue), panic call
(panicBounds, panicdivide, panicoverflow, panicshift), padding, or arithmetic. Same vector mix as cycle 30's
coverage.py (first 300 random vectors per op, c27 knuth vectors, 2,000 v4shapes vectors), plus the targeted set and
any extra vectors given in out/extra-<arch>.json. usage: python3 -I unreached.py <arch> <out.json> [extra]"""
import json, os, sys, re
C30 = '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/'
HERE = C30 + 'scripts'
sys.path.insert(0, HERE)
arch, OUT = sys.argv[1], sys.argv[2]
EXTRA = sys.argv[3] if len(sys.argv) > 3 else None
argv = sys.argv[:]
sys.argv = [argv[0], arch, 'random', '0', '1', '/dev/null']
os.environ['NRAND'] = '300'
src = open(os.path.join(HERE, 'drive.py')).read().split('\nGEN = ')[0]
g = {'__name__': 'cov', '__file__': os.path.join(HERE, 'drive.py')}
exec(src, g)
import models, goshim as G
m = models.Model(arch, C30 + 'dl/%s/usr/local/bin/nitro' % arch, C30 + 'dl/build/all-%s.txt' % arch)
V = list(g['rand']()) + [v for v in g['c27']() if not v[0].startswith('c27-poolmath')] + list(g['v4shapes']())[:2000] + list(g['targeted']())
if EXTRA:
    for op, a, b, c in json.load(open(EXTRA)):
        V.append(('extra', op, int(a, 16), int(b, 16), int(c, 16)))
errs = 0
for tag, op, a, b, c in V:
    try:
        r, _ = m.run_handler(op, a, b, c)
        if r != G.ref(op, a, b, c):
            errs += 1
    except Exception as e:
        errs += 1
byaddr = {v[0]: k for k, v in m.fns.items()}
FOCUS = ['udivrem', 'udivremBy1', 'udivremKnuth', '(*Int).Div', '(*Int).Mod', '(*Int).SMod', '(*Int).SDiv', '(*Int).SRsh',
         '(*Int).Exp', '(*Int).AddMod', '(*Int).MulMod', '(*Int).reduce4', 'Reciprocal']
ins = sorted(m.prog.ins)
txt = {}
for l in m.text.splitlines():
    mm = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
    if mm: txt[int(mm.group(1), 16)] = re.sub(r'\s+', ' ', mm.group(2)).strip()
out = {'arch': arch, 'vectors': len(V), 'mismatchesOrErrors': errs, 'functions': {}}
for f in FOCUS:
    name = G.U + f
    lo, hi = m.fns[name]
    tot = [a for a in ins if lo <= a < hi]
    un = [a for a in tot if a not in m.visited]
    # morestack block: from the prologue's jbe target to the end
    stackblk = set()
    for a in tot[:6]:
        t = txt.get(a, '')
        mm = re.match(r'^(jbe|b\.ls)\s+(?:0x)?([0-9a-f]+)', t)
        if mm:
            st = int(mm.group(2), 16)
            stackblk |= {x for x in tot if x >= st}
    rows = []
    for a in un:
        t = txt.get(a, '')
        tgt = re.search(r'(?:call|bl)\s+(?:0x)?([0-9a-f]+)', t)
        callee = byaddr.get(int(tgt.group(1), 16), '') if tgt else ''
        if a in stackblk or 'morestack' in callee:
            cls = 'stack growth'
        elif 'panic' in callee:
            cls = 'panic call'
        elif t.startswith(('int3', 'nop', 'udf', 'xchg ax,ax')) or t == '':
            cls = 'padding'
        else:
            cls = 'arithmetic'
        rows.append([hex(a), t + ((' ; ' + callee) if callee else ''), cls])
    out['functions'][f] = {'range': [hex(lo), hex(hi)], 'instructions': len(tot), 'unreached': rows,
                           'counts': {c: sum(1 for r in rows if r[2] == c) for c in ('stack growth', 'panic call', 'padding', 'arithmetic')}}
json.dump(out, open(OUT, 'w'), indent=1)
for f, v in out['functions'].items():
    print(arch, f, v['instructions'], v['counts'])
print('vectors', len(V), 'mismatches/errors', errs)
