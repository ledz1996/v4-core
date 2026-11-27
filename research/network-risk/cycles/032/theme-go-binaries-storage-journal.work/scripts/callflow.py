"""Task 4: the order of calls in (*EVM).Call, DelegateCall and StaticCall of each shipped binary (amd64), with
indirect calls through the EVM's StateDB interface (evm+X itab) named by reading the vm.StateDB itab of the
StateDB type from the file. Read only; nothing runs.
usage: python3 -I callflow.py <bsc|bor|avax> <out.txt>"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tsgo as T, fn
kind, out = sys.argv[1], sys.argv[2]
m = T.Model(kind + '-amd64')
itab = m.itab_sdb
meth = {}
for i in range(120):
    a = m.img.read(itab + 0x18 + 8 * i, 8)
    if a in m.byaddr:
        meth[0x18 + 8 * i] = m.byaddr[a].split('.')[-1]
res = []
for f in ('(*EVM).Call', '(*EVM).DelegateCall', '(*EVM).StaticCall'):
    lo, hi = m.fns[m.V + f]
    txt = T.G.disasm(m.bin, 'amd64', [(lo, hi)])
    res.append('== ' + f)
    lines = txt.splitlines()
    for i, l in enumerate(lines):
        mm = re.search(r'call\s+([0-9a-f]+)\s*<([^>]+)>', l)
        if mm:
            n = mm.group(2).split('/')[-1]
            if not n.startswith('runtime.'):
                res.append('  ' + l.split(':')[0].strip() + ' ' + n)
            continue
        if re.search(r'\scall\s+r[a-z0-9]+$', l):
            # look back for the itab slot load: mov rX,QWORD PTR [rY+0xNN]
            for j in range(i - 1, max(i - 12, 0), -1):
                q = re.search(r'mov\s+r\w+,QWORD PTR \[r\w+\+(0x[0-9a-f]+)\]', lines[j])
                if q:
                    off = int(q.group(1), 16)
                    res.append('  ' + l.split(':')[0].strip() + ' icall slot %#x %s' % (off, meth.get(off, '?')))
                    break
open(out, 'w').write('\n'.join(res) + '\n')
print('\n'.join(res))
