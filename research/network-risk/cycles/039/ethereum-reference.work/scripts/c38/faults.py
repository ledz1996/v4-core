"""Cycle 31 planted faults, applied to the in-memory disassembly text before the model parses it. The release
binaries are not modified. Each fault is found by searching the text of one function for the first instruction that
matches a pattern, and a patch that does not match exactly raises, so a fault cannot silently fail to apply.
  carry   uint256.umul: the first add-with-carry becomes a plain add (MULMOD, MUL); in bor, whose PGO build inlines
          umul, the first add-with-carry of uint256.(*Int).MulMod
  limb    uint256.(*Int).Rsh: the first load of limb 2 reads limb 1 instead (SHR, SAR)
  shift   uint256.(*Int).Rsh: the 64 bound becomes 65 (SHR, SAR); the first compare with 64 that is followed by an
          unsigned below test, since uint256 v1.2.4 first compares 64 for equality in a switch
  cmpskip core/vm.opLt (amd64): the load of limb 2 of the second operand reads limb 1, so the comparison skips a limb
The memo compare fault the plan names cannot be planted: the tagged bor binary has no MULMOD memo (see symcmp)."""
import re
import goshim as G
import targets

SPEC = {
    'carry': ('github.com/holiman/uint256.umul', {'amd64': (r'\tadc +', 'adc ', 'add '), 'arm64': (r'\tadcs\t', 'adcs', 'adds')}, ['MULMOD', 'MUL']),
    'limb': ('github.com/holiman/uint256.(*Int).Rsh', {'amd64': (r'QWORD PTR \[rbx\+0x10\]', '[rbx+0x10]', '[rbx+0x8]'), 'arm64': (r'\[x1, #0x10\]', '[x1, #0x10]', '[x1, #0x8]')}, ['SHR', 'SAR']),
    'shift': ('github.com/holiman/uint256.(*Int).Rsh', {'amd64': (r'cmp +rcx,0x40$', 'rcx,0x40', 'rcx,0x41'), 'arm64': (r'cmp\tx2, #0x40$', '#0x40', '#0x41')}, ['SHR', 'SAR']),
    'cmpskip': ('VM:opLt', {'amd64': (r'mov +r1[0-5],QWORD PTR \[r[a-z0-9]+\+r[a-z0-9]+\*1\+0x(10|18)\]', None, None)}, ['LT']),
}


def text_patcher(patch):
    def f(text):
        lines = text.split('\n')
        for addr, old, new in patch:
            pat = re.compile(r'^\s*%x:' % addr)
            hit = [i for i, l in enumerate(lines) if pat.match(l)]
            if len(hit) != 1 or old not in lines[hit[0]]:
                raise SystemExit('fault patch at %x did not match: %r' % (addr, [lines[i] for i in hit]))
            lines[hit[0]] = lines[hit[0]].replace(old, new, 1)
        return '\n'.join(lines)
    return f


def find(tgt, name):
    fn, pats, ops = SPEC[name]
    t = targets.get(tgt)
    G.VM = t['vm']
    fn = fn.replace('VM:', t['vm'])
    if name == 'carry' and tgt.startswith('bor-'):
        fn = 'github.com/holiman/uint256.(*Int).MulMod'
    if t['arch'] not in pats:
        raise SystemExit('fault %s not defined for %s' % (name, t['arch']))
    rx, old, new = pats[t['arch']]
    fns = G.fnlist(t['fns'])
    text = G.disasm(t['bin'], t['arch'], [fns[fn]])
    L = text.splitlines()
    for i, l in enumerate(L):
        m = re.search(rx, l)
        if name == 'shift' and m and not re.search(r'\t(jb|jbe|b\.lo|b\.ls|b\.cc)\b', L[i + 1] if i + 1 < len(L) else ''):
            continue
        if m and re.match(r'^\s*[0-9a-f]+:', l):
            addr = int(l.split(':')[0], 16)
            if old is None:  # cmpskip: lower the displacement by one limb
                disp = m.group(1)
                old = '+0x%s]' % disp
                new = '+0x%x]' % (int(disp, 16) - 8)
            return addr, l.strip(), old, new, ops
    raise SystemExit('no match for fault %s in %s' % (name, fn))


def get(tgt, name):
    if name == 'none':
        return {}
    addr, line, old, new, ops = find(tgt, name)
    return {'ops': ops, 'text_patch': text_patcher([(addr, old, new)]), 'stop_after': 20,
            'where': {'addr': hex(addr), 'line': line, 'old': old, 'new': new}}
