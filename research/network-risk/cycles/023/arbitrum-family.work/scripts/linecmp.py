# Compare function start lines from the binary's pclntab with "func" lines of a source file.
import sys, re
funcs, src, fname = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(src).read().split('\n')
decl = {}
for i, l in enumerate(lines, 1):
    m = re.match(r'func (\([^)]*\) )?([A-Za-z0-9_]+)', l)
    if m:
        recv = m.group(1) or ''
        r = re.search(r'\*?([A-Za-z0-9_]+)\)', recv)
        name = (('(*' if '*' in recv else '(') + r.group(1) + ').' if r else '') + m.group(2)
        decl[name] = i
ok = bad = 0
for l in open(funcs):
    p = l.split()
    if not p[4].startswith('github.com/ethereum/go-ethereum@v1.16.2/core/vm/' + fname + ':'): continue
    name = p[0].split('core/vm.')[1]
    ln = int(p[4].rsplit(':', 1)[1])
    # pclntab line is the first instruction line, usually the func line itself
    d = decl.get(name)
    if d is None: print('MISSING-IN-SRC', name, ln); bad += 1; continue
    if d == ln: ok += 1
    else: print('LINE', name, 'bin', ln, 'src', d); bad += 1
print(fname, 'match', ok, 'differ', bad)
