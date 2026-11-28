"""Classify every site that scan.py found, by reading the decoded instructions of its function (objdump text, the
binary read as data only).
Checkpoint site: the three lengths (J+0x10, J+0x28, J+0x40) loaded from the journal base, stored as a contiguous
checkpoint record (+0, +8, +0x10 in that order, the layout the out-of-line copy writes and checkpoint_revert reads),
and the depth word J+0x118 raised by exactly one.
Decrement site: run on its own in a tiny interpreter of the instructions it uses, for depth inputs 0, 1, 2, 3, 1023,
1024, 1025, 2^63 and 2^64-1; it must give max(d-1, 0) and store it back to the same word.
Calls to checkpoint_revert in a function that holds a checkpoint site: rdi must be the journal base and rsi the
record. usage: python3 -I classify.py <profile> <scan.json> <out.json>"""
import json, re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bins import BINS
prof, scanf, outp = sys.argv[1:4]
P = BINS[prof]; S = json.load(open(scanf))
M64 = (1 << 64) - 1
_cache = {}


def dis(lo, hi):
    k = (lo, hi)
    if k not in _cache:
        out = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % lo,
                              '--stop-address=%#x' % hi, P['bin']], capture_output=True, text=True).stdout
        L = []
        for l in out.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)
            if m:
                body = re.sub(r'\s*<[^>]*>', '', m.group(2)).split('#')[0].strip()
                L.append((int(m.group(1), 16), body))
        _cache[k] = L
    return _cache[k]


R32 = {'eax': 'rax', 'ebx': 'rbx', 'ecx': 'rcx', 'edx': 'rdx', 'esi': 'rsi', 'edi': 'rdi', 'ebp': 'rbp', 'esp': 'rsp',
       **{'r%dd' % i: 'r%d' % i for i in range(8, 16)}}


def mem(s):
    m = re.match(r'^QWORD PTR \[(\w+)([+-]0x[0-9a-f]+)?\]$', s)
    return (m.group(1), int(m.group(2) or '0', 16)) if m else None


def classify_checkpoint(c):
    a = int(c['addr'], 16); fr = [int(x, 16) for x in c['fn']]; J = int(c['J'], 16)
    L = dis(fr[0], fr[1]); idx = [i for i, (x, _) in enumerate(L) if x == a][0]
    inc = L[idx][1]
    m = re.match(r'^inc\s+(QWORD PTR \[.*\])$', inc) or re.match(r'^add\s+(QWORD PTR \[.*\]),0x1$', inc)
    base_inc, off = mem(m.group(1))
    if off != J + 0x118: return dict(ok=False, why='inc offset')
    # copies of the base register in the 40 instructions before (mov rX,rY / lea rX,[rY+J] seen as base+J)
    win = L[max(0, idx - 40): idx + 30]
    loads = {}; dst = {}
    # provenance of each register: the text of its last definition (a reload of the host pointer from the same
    # stack slot, or a register copy, counts as the same base)
    prov = {}
    def pv(r):
        return prov.get(r, r)
    for x, b in L[max(0, idx - 80):idx + 1]:
        mm = re.match(r'^mov\s+(\w+),(QWORD PTR \[(rsp|rbp)[+-]0x[0-9a-f]+\])$', b)
        if mm: prov[mm.group(1)] = mm.group(2); continue
        mm = re.match(r'^mov\s+(r\w+),(r\w+)$', b)
        if mm: prov[mm.group(1)] = pv(mm.group(2)); continue
        mm = re.match(r'^(mov|lea|xor|add|sub|imul|movzx|pop|cmov\w+|shl|shr|and|or)\s+(\w+),', b)
        if mm:
            r = R32.get(mm.group(2), mm.group(2)); prov[r] = '%s@%x' % (r, x)
    inc_prov = pv(base_inc)
    prov = {}
    for x, b in L[max(0, idx - 80):idx + 30]:
        mm = re.match(r'^mov\s+(\w+),(QWORD PTR \[.*\])$', b)
        if mm and mem(mm.group(2)) and idx - 40 <= [i for i, (y, _) in enumerate(L) if y == x][0]:
            r, o = mem(mm.group(2))
            for f in (0x10, 0x28, 0x40):
                if (pv(r) == inc_prov or r == base_inc) and o == J + f:
                    loads[f] = (x, mm.group(1)); dst[mm.group(1)] = f
        mm2 = re.match(r'^mov\s+(\w+),(QWORD PTR \[(rsp|rbp)[+-]0x[0-9a-f]+\])$', b)
        if mm2: prov[mm2.group(1)] = mm2.group(2); continue
        mm2 = re.match(r'^mov\s+(r\w+),(r\w+)$', b)
        if mm2: prov[mm2.group(1)] = pv(mm2.group(2)); continue
        mm2 = re.match(r'^(mov|lea|xor|add|sub|imul|movzx|pop|cmov\w+|shl|shr|and|or)\s+(\w+),', b)
        if mm2:
            r = R32.get(mm2.group(2), mm2.group(2)); prov[r] = '%s@%x' % (r, x)
        mm = re.match(r'^lea\s+(\w+),\[(\w+)\+(0x[0-9a-f]+)\]$', b)
    if len(loads) != 3: return dict(ok=False, why='loads %s' % sorted(loads))
    # stores of the loaded registers (before being overwritten) to a memory record
    stores = {}
    live = dict(dst)
    for x, b in win:
        if x <= min(v[0] for v in loads.values()): continue
        mm = re.match(r'^mov\s+(QWORD PTR \[.*\]),(\w+)$', b)
        if mm and mem(mm.group(1)) and mm.group(2) in live:
            stores.setdefault(live[mm.group(2)], []).append(mem(mm.group(1)))
        mm = re.match(r'^(mov|lea|xor|add|sub|imul|movzx|pop|cmov\w+|shl|shr)\s+(\w+),', b)
        if mm and x not in [v[0] for v in loads.values()]:
            r = R32.get(mm.group(2), mm.group(2))
            if r in live: del live[r]
    # one level of copy: mov rax,[slot] ; mov [slot2],rax in the function moves a stored length to a second slot
    for i, (x, b) in enumerate(L):
        mm = re.match(r'^mov\s+(\w+),(QWORD PTR \[(rsp|rbp)[+-]0x[0-9a-f]+\])$', b)
        if mm and i + 1 < len(L):
            m2 = re.match(r'^mov\s+(QWORD PTR \[(rsp|rbp)[+-]0x[0-9a-f]+\]),(\w+)$', L[i + 1][1])
            if m2 and m2.group(3) == mm.group(1):
                for f in list(stores):
                    if mem(mm.group(2)) in stores[f]: stores[f].append(mem(m2.group(1)))
    recs = []
    for s10 in stores.get(0x10, []):
        if (s10[0], s10[1] + 8) in stores.get(0x28, []) and (s10[0], s10[1] + 16) in stores.get(0x40, []):
            recs.append(s10)
    if not recs: return dict(ok=False, why='no contiguous record %s' % stores)
    # calls to checkpoint_revert in the same function and the record they pass
    rev = []
    for i, (x, b) in enumerate(L):
        mm = re.match(r'^call\s+([0-9a-f]+)$', b)
        if mm and int(mm.group(1), 16) in P['reverts']:
            prev = [bb for _, bb in L[max(0, i - 6):i]]
            rsi = [bb for bb in prev if re.match(r'^lea\s+rsi,', bb) or re.match(r'^mov\s+rsi,', bb)]
            rev.append(dict(at='%#x' % x, target='%#x' % int(mm.group(1), 16), rsi=rsi[-1] if rsi else None))
    rec_txt = ['lea    rsi,[%s%s0x%x]' % (r, '-' if o < 0 else '+', abs(o)) for r, o in recs]
    rev_ok = all(r['rsi'] is None or any(r['rsi'].replace(' ', '') == t.replace(' ', '') for t in rec_txt) for r in rev)
    calls_other = sorted({'%#x' % int(mm.group(1), 16) for _, b in L for mm in [re.match(r'^call\s+([0-9a-f]+)$', b)] if mm})
    return dict(ok=True, inc=inc, base=base_inc, record=['%s%+#x' % r for r in recs], loads={'%#x' % k: '%#x' % v[0] for k, v in loads.items()},
                revert_calls=rev, revert_calls_pass_record=rev_ok, n_calls=len(calls_other))


def run_dec(text, D, d):
    """tiny interpreter: the instructions scan.py captured, from the load of [r+D] to the store back"""
    regs = {}; cf = 0; mem_ = {}
    for ins in text.split(' ; '):
        ins = ins.strip()
        op, _, args = ins.partition(' '); args = [s.strip() for s in args.split(',')] if args.strip() else []
        def val(s):
            if s in regs: return regs[s]
            if s in R32: return regs.get(R32[s], 0) & 0xffffffff
            if re.match(r'^-?0x[0-9a-f]+$', s): return int(s, 16) & M64
            mm = mem(s)
            if mm and mm[1] == D: return d
            if mm: return mem_.get(mm, 0)
            if re.match(r'^r[a-z0-9]+$', s): return 0    # a register the snippet copies but does not use for the result
            raise ValueError(s)
        def setr(s, v):
            if s in R32: regs[R32[s]] = v & 0xffffffff
            elif mem(s): mem_[mem(s)] = v & M64
            else: regs[s] = v & M64
        if op == 'mov': setr(args[0], val(args[1]))
        elif op == 'xor':
            setr(args[0], val(args[0]) ^ val(args[1])); cf = 0
        elif op == 'sub':
            a, b = val(args[0]), val(args[1]); cf = int(a < b); setr(args[0], a - b)
        elif op == 'cmp':
            a, b = val(args[0]), val(args[1]); cf = int(a < b)
        elif op == 'adc':
            a, b = val(args[0]), val(args[1]); r = a + b + cf; cf = int(r > M64); setr(args[0], r)
        elif op == 'inc':
            setr(args[0], val(args[0]) + 1)
        elif op == 'cmovae':
            if not cf: setr(args[0], val(args[1]))
        elif op == 'cmovb':
            if cf: setr(args[0], val(args[1]))
        else:
            raise ValueError('op ' + ins)
    st = [v for k, v in mem_.items() if k[1] == D]
    return st[-1] if st else None


out = dict(profile=prof, checkpoints=[], decrements=[])
for c in S['checkpoints']:
    if c['fn'] is None or not c['three_loads']:
        out['checkpoints'].append(dict(c, cls=dict(ok=False, why='not a three-load site'))); continue
    out['checkpoints'].append(dict(addr=c['addr'], J=c['J'], fn=c['fn'], cls=classify_checkpoint(c)))
for d in S['decrements']:
    D = int(d['D'], 16); res = {}
    try:
        ok = True
        for x in (0, 1, 2, 3, 1023, 1024, 1025, 1 << 63, M64):
            r = run_dec(d['text'], D, x); res[str(x)] = r
            merged = re.search(r'^mov\s+(\w+),QWORD PTR \[\w+\+%s\] ; inc\s+\1 ;' % d['D'], d['text'])
            if r != (max(((x + 1) & M64) - 1, 0) if merged else max(x - 1, 0)): ok = False
        out['decrements'].append(dict(addr=d['addr'], D=d['D'], fn=d['fn'], ok=ok, text=d['text'], results=res))
    except ValueError as e:
        out['decrements'].append(dict(addr=d['addr'], D=d['D'], fn=d['fn'], ok=None, text=d['text'], err=str(e)))
json.dump(out, open(outp, 'w'), indent=1)
cps = out['checkpoints']; ds = out['decrements']
print(prof, 'checkpoints', len(cps), 'ok', sum(1 for c in cps if c['cls'].get('ok')),
      'not ok', [(c['addr'], c['cls'].get('why')) for c in cps if not c['cls'].get('ok')],
      '| revert calls not passing the record', [(c['addr'], r) for c in cps if c['cls'].get('ok') for r in c['cls']['revert_calls'] if not c['cls']['revert_calls_pass_record']][:4],
      '| decrements', len(ds), 'ok', sum(1 for d in ds if d['ok']), 'bad', [(d['addr'], d.get('results') or d.get('err')) for d in ds if d['ok'] is False],
      'uninterpreted', [(d['addr'], d.get('err')) for d in ds if d['ok'] is None])
