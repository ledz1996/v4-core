"""Planted one-instruction faults, applied to the in-memory disassembly text before the model parses it.
The release binaries are not modified. Each fault names (address, old text, new text); a patch that does not
match exactly raises, so a fault cannot silently fail to apply."""
import re

FAULTS = {
    'amd64': {
        # umul (reached by MulMod): the carry of the first column becomes a plain add
        'carry': {'ops': ['MULMOD'], 'patch': [(0xc5ef05, 'adc    r8,0x0', 'add    r8,0x0')]},
        # Rsh, 64..127 path: limb 1 is read from limb 2
        'limb': {'ops': ['SHR', 'SAR'], 'patch': [(0xc61529, 'QWORD PTR [rbx+0x8]', 'QWORD PTR [rbx+0x10]')]},
        # Rsh: the 64 bound becomes 65, so a shift by exactly 64 takes the sub-64 path
        'shift': {'ops': ['SHR', 'SAR'], 'patch': [(0xc614ed, 'cmp    rcx,0x40', 'cmp    rcx,0x41')]},
    },
    'arm64': {
        'carry': {'ops': ['MULMOD'], 'patch': [(0xb5305c, 'adcs\tx9, x8, x9', 'adds\tx9, x8, x9')]},
        'limb': {'ops': ['SHR', 'SAR'], 'patch': [(0xb54f38, '[x1, #0x18]', '[x1, #0x10]')]},
        'shift': {'ops': ['SHR', 'SAR'], 'patch': [(0xb54f24, 'cmp\tx2, #0x40', 'cmp\tx2, #0x41')]},
    },
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


def get(arch, name):
    if name == 'none':
        return {}
    spec = FAULTS[arch][name]
    return {'ops': spec['ops'], 'text_patch': text_patcher(spec['patch']), 'stop_after': 0}
