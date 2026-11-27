"""Debug helper: run one fixed sequence on a Nitro model and print the PC trail on the first stop."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stnitro as N
S2, SG, T = N.S2, N.SG, N.T
name = sys.argv[1]
m = N.NModel(name)
import x86emu
base = {(SG.PM, SG.SLOTS[0]): 5}
b = N.NBin(m, base, {SG.PM, SG.OTHER})
trail = []
c = b.c
steps = [('snap',), ('st', SG.PM, SG.SLOTS[0], 7), ('ld', SG.PM, SG.SLOTS[0]), ('rev',), ('ld', SG.PM, SG.SLOTS[0]),
         ('st', SG.NEWACCT, SG.SLOTS[0], 5), ('ld', SG.NEWACCT, SG.SLOTS[0])]
for st in steps:
    try:
        if st[0] == 'st': b.sst(*st[1:])
        elif st[0] == 'ld': print(st, hex(b.sld(*st[1:])))
        elif st[0] == 'snap': b.snap()
        else: b.rev()
    except Exception as e:
        print('STOP', st, e)
        v = sorted(x86emu.VISITED) if m.arch == 'amd64' else []
        pc = getattr(c, 'pc', None)
        print('pc', hex(pc) if pc else pc, 'last', getattr(c, 'last', None))
        rip = c.r.get('rip') if hasattr(c, 'r') else None
        for k in ('rip', 'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rsp'):
            if hasattr(c, 'r') and k in c.r: print(k, hex(c.r[k]))
        break
