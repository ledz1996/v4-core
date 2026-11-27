"""Cycle 30, Task 2 for the non-literal shift sites. For each of the 22 PoolManager sites of SHL and SHR whose two
operands are both non-literal (varsites.py), take the instruction stream of the clang-built harness listing
(cycles/027/theme-monad-engine-agreement.work/out/pm-asm-0.16.7.txt) and look for a Stack state under which the gcc
build's Emitter::shl()/shr(), run in the x86 model (shiftfull.py), emits the same stream up to a consistent renaming
of registers other than rax, rcx, rbx, rbp and rsp, of stack slots, and of read-only data labels. The gcc streams come
from random Stack states (seed fixed) plus a systematic grid of operand locations; the register table rows are
permuted in half of them, as earlier blocks can leave it.
usage: python3 -I cmpclang.py <outdir> <nstates>"""
import sys, os, json, random, re
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = sys.argv[1]; NS = int(sys.argv[2])
sys.argv = [sys.argv[0], OUTD, '0', '0', '-', 'perm']
src = open(os.path.join(HERE, 'shiftfull.py')).read().replace('\nmain()\n', '\n')
g = {'__file__': os.path.join(HERE, 'shiftfull.py'), '__name__': 'sf'}
exec(compile(src, 'shiftfull.py', 'exec'), g)
x86emu = g['x86emu']; ALIAS = x86emu.ALIAS
FIXED = {'rax', 'rcx', 'rbx', 'rbp', 'rsp'}


def canon(lines):
    reg = {}; vec = {}; slot = {}; rod = {}
    out = []
    for l in lines:
        l = re.sub(r'^\s*[0-9a-f]+:\s*', '', l).strip().lower()
        if not l or l == 'ret': continue
        mn, _, rest = l.partition(' ')
        ops = [o.strip() for o in rest.split(',')] if rest else []
        co = []
        for o in ops:
            o = re.sub(r'^(byte|word|dword|qword|xmmword|ymmword) ptr ', '', o)
            m = re.match(r'^\[(.*)\]$', o)
            if m:
                inner = m.group(1).replace(' ', '')
                mm = re.match(r'^rod(?:\+(\d+))?$', inner)
                m2 = re.match(r'^0x7000000*([0-9a-f]*)$', inner) if inner.startswith('0x7') else None
                if mm or m2:
                    off = int(mm.group(1) or 0) if mm else int(m2.group(1) or '0', 16)
                    rod.setdefault(off, len(rod)); co.append('[rod%d]' % rod[off]); continue
                m3 = re.match(r'^rbp([+-])(0x[0-9a-f]+|\d+)$', inner)
                if m3:
                    x = int(m3.group(2), 0) * (1 if m3.group(1) == '+' else -1)
                    s = x >> 5; slot.setdefault(s, len(slot)); co.append('[slot%d+%d]' % (slot[s], x & 31)); continue
                if inner == 'rbp': slot.setdefault(0, len(slot)); co.append('[slot%d+0]' % slot[0]); continue
                co.append('[' + inner + ']'); continue
            if o in ALIAS:
                base, bits = ALIAS[o]
                if base in FIXED: co.append('%s/%d' % (base, bits)); continue
                reg.setdefault(base, len(reg)); co.append('g%d/%d' % (reg[base], bits)); continue
            mv = re.match(r'^([xy])mm(\d+)$', o)
            if mv:
                vec.setdefault(mv.group(2), len(vec)); co.append('%sv%d' % (mv.group(1), vec[mv.group(2)])); continue
            try: co.append(str(int(o, 0)))
            except ValueError: co.append(o)
        out.append(mn + ' ' + ','.join(co))
    return tuple(out)


def main():
    clang = json.load(open(os.path.join(OUTD, 'clang-sites.json')))
    sites = {s['pc']: s for s in json.load(open(os.path.join(OUTD, 'varsites.json')))['nonLiteralSites']}
    want = {}
    for pc, bodies in clang.items():
        for b in bodies: want.setdefault(canon(b), []).append(int(pc))
    rnd = random.Random(4030)
    found = {}; states = 0; distinct = set()
    kinds = sorted({sites[int(pc)]['op'] for pc in clang})
    grid = []
    locs = [{'stack': None}, {'gen': 0}, {'gen': 1}, {'gen': 2}, {'avx': 1}, {'gen': 1, 'stack': None}]
    for kind in kinds:
        for v in locs:
            for sh in locs + ['same']:
                if sh != 'same' and set(v.items()) & set(sh.items()) - {('stack', None)}: continue
                for dv in (False, True):
                    for ds in (False, True):
                        for occ in ([], [0], [1], [2], [0, 1], [0, 2], [1, 2], [0, 1, 2]):
                            held = {d.get('gen') for d in (v, sh) if isinstance(d, dict)}
                            if set(occ) & held: continue
                            sc = {'value': dict(v), 'same': sh == 'same', 'shift': None if sh == 'same' else dict(sh),
                                  'deep': [{'gen': r} for r in occ], 'dup_value': dv, 'dup_shift': ds and sh != 'same'}
                            grid.append((kind, sc))
    print('grid states', len(grid))
    for n in range(NS + len(grid)):
        if n < len(grid): kind, sc = grid[n]
        else:
            kind = kinds[n % len(kinds)]
            sc = g['scenario'](rnd)
        m, blocks, dicts, order = g['build'](kind, sc, rnd, None)
        try: m.c.call(g['ENTRY'][kind][0], [g['E']], maxsteps=2000000)
        except g['Stop']: continue
        states += 1
        cs = canon(g['seqtext'](m.emitted).splitlines())
        distinct.add(cs)
        if cs in want:
            for pc in want[cs]:
                found.setdefault(pc, {'kind': kind, 'state': repr(sc), 'gccStream': g['seqtext'](m.emitted)})
    rows = []
    for pc in sorted(int(p) for p in clang):
        rows.append({'pc': pc, 'op': sites[pc]['op'], 'src': sites[pc]['src'], 'clangStream': clang[str(pc)][0],
                     'matched': pc in found, 'gcc': found.get(pc)})
    out = {'seed': 4030, 'gccStates': states, 'distinctGccStreams': len(distinct), 'distinctClangStreams': len(want),
           'sitesMatched': sum(r['matched'] for r in rows), 'sites': len(rows), 'rows': rows}
    json.dump(out, open(os.path.join(OUTD, 'cmpclang.json'), 'w'), indent=1)
    print({k: v for k, v in out.items() if k != 'rows'})
    for r in rows:
        if not r['matched']: print('UNMATCHED', r['pc'], r['op'], r['src']); print('\n'.join(r['clangStream']))
main()
