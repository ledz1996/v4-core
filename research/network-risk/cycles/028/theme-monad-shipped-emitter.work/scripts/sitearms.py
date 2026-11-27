"""Cycle 28, Task 1. Join the literal sites of litsites.json with the harness listing pm-asm-0.16.7.txt (cycle 27, clang
build of v0.16.7) and name the emitter arm each site takes by the v0.16.7 source (emitter.cpp). The arm is decided by
the source rules below from the literal values; the listing is used to confirm that the harness took it (a runtime call
where the rule says the general path, inline code where it says a literal arm). usage: python3 -I sitearms.py <outdir> <pm-asm>"""
import sys, json, os, re, collections
OUT = sys.argv[1]; ASM = sys.argv[2]
M = (1 << 256) - 1
S = json.load(open(os.path.join(OUT, 'litsites.json')))['sites']
lines = open(ASM).read().splitlines()
seg = {}; cur = None
for ln in lines:
    m = re.match(r'^//\s+0x([0-9a-f]+): (\w+)', ln)
    if m:
        cur = int(m.group(1), 16); seg[cur] = []; continue
    if ln.startswith('//'): cur = None; continue
    if cur is not None: seg[cur].append(ln)
def pc1(v): return int(v, 16) if v else None
def arm(s):
    op = s['op']; v = [pc1(x) for x in s['values']]; lit = [x is not None for x in v]
    if s['folded']: return 'folded to a literal'
    if op == 'MULMOD' or op == 'ADDMOD':
        m = v[2]
        if m is None: return 'general (modulus not literal): runtime %s' % op.lower()
        if m in (0, 1): return 'modop_optimized trivial group'
        if bin(m).count('1') != 1: return 'general (modulus literal, not a power of two): runtime %s' % op.lower()
        exp = m.bit_length() - 1
        return 'modop_optimized -> mul_mod2 exp=%d last_ix=%d inline mul_with_bit_size' % (exp, (exp - 1) >> 6)
    if op in ('DIV', 'SDIV', 'MOD', 'SMOD'):
        a, b = v[0], v[1]
        if a is not None and b is None: return 'div/mod_optimized: literal numerator %s, no arm (general)' % ('zero' if a == 0 else 'nonzero')
        if b is not None:
            bb = b
            if op in ('SDIV', 'SMOD') and b >> 255: bb = (-b) & M
            if bb == 0 or (op.endswith('MOD') and bb <= 1): return 'literal divisor 0 or 1: folded'
            if bin(bb).count('1') == 1: return 'literal divisor power of two: shift or mask arm'
            return 'literal divisor not a power of two: general runtime %s' % op.lower()
    if op == 'MUL':
        a = v[0] if v[0] is not None else v[1]
        ash = (-a) & M if a >> 255 else a
        if a == 0: return 'mul_optimized zero'
        if bin(ash).count('1') == 1: return 'mul_optimized -> shift_by_literal SHL %d' % ((ash & -ash).bit_length() - 1)
        limbs = [(a >> (64 * i)) & ((1 << 64) - 1) for i in range(4)]
        if 0 in limbs: return 'mul_optimized -> mul_with_bit_size(256) inline, zero limbs %s' % [i for i, l in enumerate(limbs) if l == 0]
        return 'mul_optimized general (runtime mul)'
    if op in ('SHL', 'SHR', 'SAR'):
        if lit[0]: return 'shift_by_literal count=%d' % v[0]
        return 'shift_literal_by_non_literal value=%s' % hex(v[1])
    if op == 'SIGNEXTEND': return 'signextend literal index %d' % v[0] if lit[0] else 'signextend literal value'
    if op == 'BYTE': return 'byte literal index %d' % v[0] if lit[0] else 'byte literal value, non-literal index'
    return '%s with literal operand %s' % (op, s['literal'])
rows = []; cnt = collections.Counter(); disagree = []
for s in S:
    a = arm(s); body = seg.get(s['pc'], [])
    calls = [l for l in body if l.startswith('call')]
    mn = sorted(set(l.split()[0] for l in body if l and not l.startswith('L') and ':' not in l.split()[0]))
    r = dict(s, arm=a, harnessCall=bool(calls), harnessMnemonics=mn, harnessLines=len(body))
    rows.append(r); cnt[(s['op'], a.split(':')[0].split(' ->')[0] if s['op'] not in ('MULMOD', 'SHL', 'SHR', 'SAR', 'SIGNEXTEND', 'BYTE') else a)] += 1
    general = 'general' in a
    if s['op'] in ('MULMOD', 'DIV', 'SDIV', 'MOD', 'SMOD', 'MUL') and not s['folded']:
        if general != bool(calls): disagree.append({'pc': s['pc'], 'op': s['op'], 'arm': a, 'harnessCall': bool(calls), 'lines': body[:12]})
json.dump({'rows': rows, 'armCounts': [[k[0], k[1], v] for k, v in sorted(cnt.items())], 'callDisagreements': disagree},
          open(os.path.join(OUT, 'sitearms.json'), 'w'), indent=1)
for k, v in sorted(cnt.items()):
    if k[0] in ('MULMOD', 'DIV', 'SDIV', 'MOD', 'SMOD', 'MUL', 'SIGNEXTEND', 'BYTE') or v < 6: print(v, k)
print('shift arms', sum(v for k, v in cnt.items() if k[0] in ('SHL', 'SHR', 'SAR')))
print('disagreements', len(disagree))
for d in disagree: print(d['pc'], d['op'], d['arm'], d['harnessCall'], d['lines'][:6])
