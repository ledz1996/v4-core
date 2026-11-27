"""For each named handler, disassembles it (objdump, read only) and lists every direct and indirect call/branch target
outside the function, plus every RIP/ADRP-relative data reference, resolved against the pclntab list.
usage: python3 -I calls.py <binary> <all-fn list> <arch amd64|arm64> <out.json> <name regex>..."""
import bisect, json, re, subprocess, sys
B, L, A, OUT = sys.argv[1:5]; pats = [re.compile(p) for p in sys.argv[5:]]
fns = []
for l in open(L):
    p = l.split()
    fns.append((int(p[-4], 16), int(p[-3], 16), ' '.join(p[:-4])))
fns.sort(); st = [f[0] for f in fns]
def name(a):
    k = bisect.bisect_right(st, a) - 1
    if k >= 0 and fns[k][0] <= a < fns[k][1]: return fns[k][2] + ('' if a == fns[k][0] else '+%#x' % (a - fns[k][0]))
    return None
res = {}
for lo, hi, n in fns:
    if not any(p.search(n) for p in pats): continue
    d = subprocess.run([('objdump' if A == 'amd64' else 'llvm-objdump-18'), '-d', '--no-show-raw-insn', '--start-address=%#x' % lo, '--stop-address=%#x' % hi, B],
                       capture_output=True, text=True).stdout.splitlines()
    calls, data, ind = [], [], []
    adrp = {}
    for l in d:
        m = re.match(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$', l)
        if not m: continue
        pc = int(m.group(1), 16); op = m.group(2); args = m.group(3)
        if A == 'amd64':
            if op.startswith('call') or op.startswith('jmp'):
                t = re.match(r'([0-9a-f]+)', args)
                if t and not args.startswith('*'):
                    ta = int(t.group(1), 16)
                    if not (lo <= ta < hi): calls.append((hex(pc), op, name(ta) or hex(ta)))
                elif args.startswith('*'):
                    ind.append((hex(pc), op + ' ' + args))
            r = re.search(r'#\s*([0-9a-f]+)', args)
            if r and 'rip' in args: data.append((hex(pc), op, hex(int(r.group(1), 16)), name(int(r.group(1), 16))))
        else:
            if op in ('bl', 'b') or op.startswith('b.') or op in ('cbz', 'cbnz', 'tbz', 'tbnz'):
                t = re.search(r'0x([0-9a-f]{5,})\b', args)
                if t:
                    ta = int(t.group(1), 16)
                    if not (lo <= ta < hi): calls.append((hex(pc), op, name(ta) or hex(ta)))
            if op in ('blr', 'br'): ind.append((hex(pc), op + ' ' + args))
            if op == 'adrp':
                r = re.match(r'(x\d+),\s*0x([0-9a-f]+)', args) or re.match(r'(x\d+),\s*([0-9a-f]+)', args)
                if r: adrp[r.group(1)] = int(r.group(2), 16)
            elif op in ('add', 'ldr', 'ldrb', 'ldrh', 'ldrsw', 'str'):
                r = re.match(r'(\w+),\s*\[?(x\d+),\s*#(0x[0-9a-f]+|\d+)', args)
                if r and r.group(2) in adrp:
                    data.append((hex(pc), op, hex(adrp[r.group(2)] + int(r.group(3), 0)), None))
    res[n] = {'range': [hex(lo), hex(hi)], 'calls': calls, 'indirect': ind, 'dataRefs': data}
json.dump(res, open(OUT, 'w'), indent=1)
for n, r in res.items():
    print(n.split('.')[-1] if 'core/vm' in n else n.replace('github.com/holiman/', ''), sorted(set(c[2] for c in r['calls'])), 'ind', len(r['indirect']), 'data', sorted(set(x[2] for x in r['dataRefs'])))
