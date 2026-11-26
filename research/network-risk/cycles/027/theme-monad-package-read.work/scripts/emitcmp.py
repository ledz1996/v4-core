"""Compare what the x86 emitter functions of the package and of the cycle 23 harness pass to asmjit.

Input: objdump -d -C (and -r for objects) text of both builds. For every emitter function the script follows
calls and address references to other functions of monad::vm::compiler (the closure, so that different inlining
by gcc and clang does not matter) and collects:
  ids     asmjit instruction ids passed in esi to BaseEmitter::_emitI/_emit/emit, plus the ids of the
          EmitterExplicitT wrappers it references (each wrapper's own id is read from its body)
  wrappers names of the asmjit EmitterExplicitT methods referenced (instruction mnemonics)
  runtime  runtime routines referenced (monad::vm::runtime::*, monad_vm_runtime_*, monad:: math)
  consts   immediate operands of 16 bits or more that are not stack or structure offsets
usage: python3 -I emitcmp.py <package.s> <harness.s> <out.json>
"""
import sys, re, json

ROOTS = ['shl', 'shr', 'sar', 'mul', 'mulmod', 'addmod', 'udiv', 'sdiv', 'umod', 'smod', 'exp', 'signextend', 'byte',
         'lt', 'gt', 'slt', 'sgt', 'eq', 'iszero', 'jumpi', 'mload', 'mstore', 'call', 'returndatacopy', 'tload', 'tstore',
         'mstore8', 'jump', 'and_', 'or_', 'xor_', 'not_', 'add', 'sub']

def strip_templates(s):
    out, d = [], 0
    for ch in s:
        if ch == '<': d += 1; continue
        if ch == '>': d = max(0, d - 1); continue
        if d == 0: out.append(ch)
    return ''.join(out)

def norm(name):
    name = re.sub(r'\s*\[clone [^\]]*\]', '', name)
    name = re.sub(r'[+-]0x[0-9a-f]+$', '', name.strip())
    name = strip_templates(name).strip()
    if name.endswith('}'):
        base = name
    else:
        d = 0; base = name
        for i in range(len(name) - 1, -1, -1):
            if name[i] == ')': d += 1
            elif name[i] == '(':
                d -= 1
                if d == 0:
                    base = name[:i]; break
    # drop a leading return type: last space outside parentheses and braces
    d = 0; cut = -1
    for i, ch in enumerate(base):
        if ch in '({': d += 1
        elif ch in ')}': d -= 1
        elif ch == ' ' and d == 0 and 'operator' not in base[:i + 9][-9:]:
            cut = i
    if cut >= 0 and 'operator' not in base: base = base[cut + 1:]
    return base.replace('(anonymous namespace)::', '').strip()

def parse(path):
    funcs = {}
    cur = None
    last_esi = None
    for line in open(path, errors='replace'):
        m = re.match(r'^[0-9a-f]+ <(.*)>:\s*$', line)
        if m:
            cur = norm(m.group(1)); f = funcs.setdefault(cur, {'ids': set(), 'refs': set(), 'consts': set(), 'n': 0, 'esi_unknown': 0})
            last_esi = None; continue
        if cur is None: continue
        f = funcs[cur]
        m = re.match(r'^\s+[0-9a-f]+:\s+(\S+)\s*(.*)$', line)
        r = re.match(r'^\s+[0-9a-f]+: (R_X86_64_\S+)\s+(.*)$', line)
        targets = []
        if r:
            targets.append(r.group(2))
        elif m:
            mn, ops = m.group(1), m.group(2)
            f['n'] += 1
            for t in re.findall(r'<([^>]*(?:<[^>]*>[^>]*)*)>', ops):
                pass
            mm = re.search(r'\s<(.*)>\s*$', ops)
            if mm and (mn in ('call', 'jmp', 'lea') or mn.startswith('j')):
                targets.append(mm.group(1))
            mi = re.match(r'^esi,(0x[0-9a-f]+)$', ops)
            if mn == 'mov' and mi: last_esi = int(mi.group(1), 16)
            elif mn == 'xor' and ops == 'esi,esi': last_esi = 0
            elif re.match(r'^(esi|rsi|sil|si),', ops): last_esi = None
            for imm in re.findall(r'(?<![\[+\-])\b0x([0-9a-f]+)\b(?!\])', ops):
                v = int(imm, 16)
                if v >= 0x10000 and not re.search(r'\[[^\]]*0x' + imm, ops) and mn not in ('call', 'jmp') and not mn.startswith('j') and '<' not in ops:
                    f['consts'].add(v)
            if mn == 'call':
                tgt = mm.group(1) if mm else ''
                f.setdefault('_pending', []).append(last_esi)
        for t in targets:
            tn = norm(t)
            if tn == cur: continue
            f['refs'].add(tn)
            if re.search(r'BaseEmitter::(_emitI|_emit|emit)$', tn):
                if last_esi is not None: f['ids'].add(last_esi)
                else: f['esi_unknown'] += 1
    for f in funcs.values(): f.pop('_pending', None)
    return funcs

def closure(funcs, root):
    seen, stack = set(), [root]
    while stack:
        x = stack.pop()
        if x in seen or x not in funcs: continue
        seen.add(x)
        for r in funcs[x]['refs']:
            if r.startswith('monad::vm::compiler::') or r.startswith('std::') and 'monad::vm::compiler' in r:
                stack.append(r)
    return seen

def features(funcs, root):
    cl = closure(funcs, root)
    ids, wr, rt, consts, unk = set(), set(), set(), set(), 0
    for x in cl:
        f = funcs[x]
        ids |= f['ids']; consts |= f['consts']; unk += f['esi_unknown']
        for r in f['refs']:
            if 'EmitterExplicitT' in r or r.startswith('asmjit::v1_14::x86::Assembler::'):
                wr.add(r.split('::')[-1])
                if r in funcs: ids |= funcs[r]['ids']
            if r.startswith('monad::vm::runtime::') or r.startswith('monad_vm_runtime') or re.match(r'^monad::(mulmod|addmod|exp|udivrem|sdivrem|signextend|byte|shl|shr|sar|knuth_div)$', r):
                rt.add(r)
    return {'closure': len(cl), 'ids': sorted(ids), 'wrappers': sorted(wr), 'runtime': sorted(rt), 'consts': sorted(consts), 'esiUnknown': unk}

if __name__ == '__main__':
    pk, hv, out = sys.argv[1], sys.argv[2], sys.argv[3]
    P, H = parse(pk), parse(hv)
    res = {}
    for r in ROOTS + sys.argv[4:]:
        key = 'monad::vm::compiler::native::Emitter::' + r
        if key not in P and key not in H:
            res[r] = {'present': False}; continue
        a, b = features(P, key), features(H, key)
        d = {'package': a, 'harness': b}
        for k in ('ids', 'wrappers', 'runtime', 'consts'):
            d[k + 'Equal'] = a[k] == b[k]
            if a[k] != b[k]:
                d[k + 'OnlyPackage'] = sorted(set(a[k]) - set(b[k]))
                d[k + 'OnlyHarness'] = sorted(set(b[k]) - set(a[k]))
        res[r] = d
        print('%-15s closure %4d/%4d ids %s(%d/%d) wrappers %s runtime %s consts %s(%d/%d) unk %d/%d' % (
            r, a['closure'], b['closure'], d['idsEqual'], len(a['ids']), len(b['ids']), d['wrappersEqual'], d['runtimeEqual'],
            d['constsEqual'], len(a['consts']), len(b['consts']), a['esiUnknown'], b['esiUnknown']))
    json.dump(res, open(out, 'w'), indent=1, default=list)
