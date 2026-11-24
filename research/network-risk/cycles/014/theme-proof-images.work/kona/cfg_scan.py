# Control-flow scan of the kona-client cannon64 text segment for the LLVM 235261 shape (lead L-709).
# From every `andi rX, rY, 0x40` site, follow fall-through, branch targets with their delay slots, j/jal
# targets and returns, tracking which registers (and stack slots stored through $sp/$fp) hold the
# 0-or-64 value, until it is dead on every path. Every read of a tainted value is recorded with its
# class. Usage: python3 -I cfg_scan.py text.bin out.json   (text.bin starts at vaddr 0x120000000)
import sys, struct, json, collections
data = open(sys.argv[1], 'rb').read() if __name__ == '__main__' else open(__import__('os').environ['TEXT'], 'rb').read()
BASE = 0x120000000
def word(pc):
    o = pc - BASE
    if o < 0 or o + 4 > len(data): return None
    return struct.unpack('>I', data[o:o + 4])[0]
HI, LO = 32, 33
ARGS = set(range(4, 12)); CALLEE_SAVED = set(range(16, 24)) | {28, 29, 30}
def dec(w):
    """returns (kind, uses, defs, extra). uses: list of (reg, role). kind in alu/branch/jump/call/ret/load/store/mov/sys"""
    op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31; sa = (w >> 6) & 31; fn = w & 63
    imm = w & 0xFFFF; simm = imm - 0x10000 if imm & 0x8000 else imm
    if op == 0:
        if fn in (0x00, 0x02, 0x03, 0x38, 0x3a, 0x3b, 0x3c, 0x3e, 0x3f):
            nm = {0: 'sll', 2: 'srl', 3: 'sra', 0x38: 'dsll', 0x3a: 'dsrl', 0x3b: 'dsra', 0x3c: 'dsll32', 0x3e: 'dsrl32', 0x3f: 'dsra32'}[fn]
            if w == 0: return ('nop', [], [], None)
            return ('alu', [(rt, nm + ' src sa=%d' % sa)], [rd], (nm, sa))
        if fn in (0x04, 0x06, 0x07, 0x14, 0x16, 0x17):
            nm = {4: 'sllv', 6: 'srlv', 7: 'srav', 0x14: 'dsllv', 0x16: 'dsrlv', 0x17: 'dsrav'}[fn]
            return ('alu', [(rt, nm + ' value'), (rs, nm + ' amount')], [rd], (nm,))
        if fn == 8: return ('jr', [(rs, 'jr target')], [], rs)
        if fn == 9: return ('jalr', [(rs, 'jalr target')], [rd], rs)
        if fn in (0x0a, 0x0b):
            nm = 'movz' if fn == 0x0a else 'movn'
            return ('mov', [(rt, nm + ' cond'), (rs, nm + ' value')], [], (nm, rs, rt, rd))
        if fn == 0x0c: return ('sys', [], [], None)
        if fn == 0x0f: return ('nop', [], [], None)
        if fn in (0x10, 0x12): return ('alu', [(HI if fn == 0x10 else LO, 'mfhi/lo')], [rd], ('mfhilo',))
        if fn in (0x11, 0x13): return ('alu', [(rs, 'mthi/lo')], [HI if fn == 0x11 else LO], ('mthilo',))
        if 0x18 <= fn <= 0x1f:
            nm = ['mult', 'multu', 'div', 'divu', 'dmult', 'dmultu', 'ddiv', 'ddivu'][fn - 0x18]
            return ('alu', [(rs, nm), (rt, nm)], [HI, LO], (nm,))
        nm = {0x20: 'add', 0x21: 'addu', 0x22: 'sub', 0x23: 'subu', 0x24: 'and', 0x25: 'or', 0x26: 'xor', 0x27: 'nor',
              0x2a: 'slt', 0x2b: 'sltu', 0x2c: 'dadd', 0x2d: 'daddu', 0x2e: 'dsub', 0x2f: 'dsubu', 0x34: 'teq', 0x36: 'tne'}.get(fn, 'r%x' % fn)
        if nm in ('teq', 'tne'): return ('alu', [(rs, nm), (rt, nm)], [], (nm,))
        return ('alu', [(rs, nm + ' rs'), (rt, nm + ' rt')], [rd], (nm, rs, rt))
    if op == 1:
        link = rt in (0x10, 0x11)
        return ('branch', [(rs, 'regimm%x vs zero' % rt)], [31] if link else [], simm)
    if op in (2, 3): return ('j' if op == 2 else 'jal', [], [31] if op == 3 else [], (w & 0x3FFFFFF) << 2)
    if op in (4, 5):
        nm = 'beq' if op == 4 else 'bne'
        if rs == rt: return ('branch', [], [], simm)
        return ('branch', [(rs, nm + (' vs zero' if rt == 0 else ' vs reg')), (rt, nm + (' vs zero' if rs == 0 else ' vs reg'))], [], simm)
    if op in (6, 7): return ('branch', [(rs, ('blez', 'bgtz')[op - 6] + ' vs zero')], [], simm)
    if 8 <= op <= 0x0f or op in (0x18, 0x19):
        nm = {8: 'addi', 9: 'addiu', 10: 'slti', 11: 'sltiu', 12: 'andi', 13: 'ori', 14: 'xori', 15: 'lui', 0x18: 'daddi', 0x19: 'daddiu'}[op]
        if op == 15: return ('alu', [], [rt], ('lui',))
        return ('alu', [(rs, '%s imm=0x%x' % (nm, imm))], [rt], (nm, imm))
    if op in (0x1a, 0x1b): return ('load', [(rs, 'load address'), (rt, 'ldl/ldr merge')], [rt], (rs, simm))
    if op == 0x1c:
        if fn == 2: return ('alu', [(rs, 'mul'), (rt, 'mul')], [rd], ('mul',))
        if fn in (0x20, 0x21, 0x24, 0x25): return ('alu', [(rs, {0x20: 'clz', 0x21: 'clo', 0x24: 'dclz', 0x25: 'dclo'}[fn])], [rd], ('clz',))
        return ('alu', [(rs, 's2_%x' % fn), (rt, 's2_%x' % fn)], [rd], ('s2',))
    if op in (0x22, 0x26): return ('load', [(rs, 'load address'), (rt, 'lwl/lwr merge')], [rt], (rs, simm))
    if 0x20 <= op <= 0x27 or op in (0x30, 0x34, 0x37): return ('load', [(rs, 'load address')], [rt], (rs, simm))
    if 0x28 <= op <= 0x2f or op in (0x38, 0x3c, 0x3f):
        return ('store', [(rs, 'store address'), (rt, 'STORED VALUE')], [rt] if op in (0x38, 0x3c) else [], (rs, simm, rt))
    return ('unk%x' % op, [(rs, 'unk'), (rt, 'unk')], [rt], None)

# classification of a read of a 0-or-64 value
SAFE = ('movz cond', 'movn cond', 'vs zero')
def classify(role, ex, w):
    if any(s in role for s in SAFE): return 'safe-zero-test'
    if role.startswith(('srl src', 'dsrl src')) and ex[1] == 6: return 'safe-normalise-to-0/1'
    if role.startswith(('sltu rt',)) and ex[1] == 0: return 'safe-nonzero-test'  # sltu rd, $0, rX
    if role.startswith('sltiu') and ex[1] == 1: return 'safe-zero-test'
    if role.startswith('andi') and ex[1] == 0x40: return 'propagate'
    if role.startswith('xori') and ex[1] == 0x40: return 'propagate'
    if ex and ex[0] in ('or', 'addu', 'daddu', 'xor') and (ex[1] == 0 or ex[2] == 0): return 'propagate'
    if role in ('movz value', 'movn value'): return 'propagate'
    return 'FLAG'

MAXSTEPS = 200000; MAXDEPTH = 8
def scan(site, r, start=None):
    flags = []; safe = collections.Counter(); events = collections.Counter()
    # state: pc, taint regs, taint slots, call depth, return stack
    work = [(site + 4, frozenset([r]), frozenset(), ())]
    if start is not None:
        work = [(start, frozenset([r]), frozenset(), ())]; pw = 0
    else: pw = word(site - 4)
    pk, _, _, pex = dec(pw)
    inslot = None
    if pk == 'branch':  # the site sits in a delay slot: successors are the branch target and the fall-through
        inslot = 'branch'; work.append((site + (pex << 2), frozenset([r]), frozenset(), ()))
    elif pk == 'j':
        inslot = 'j'; work = [((site & ~0x0FFFFFFF) | pex, frozenset([r]), frozenset(), ())]
    elif pk in ('jal', 'jalr', 'jr'):
        inslot = pk
        if pk == 'jal' and r in ARGS: work = [((site & ~0x0FFFFFFF) | pex, frozenset([r]), frozenset(), ((site + 4, frozenset(), frozenset()),))]
        elif pk == 'jr' and pex == 31 and r in (2, 3): pass
        else: work = []
    seen = set(); steps = 0
    while work and steps < MAXSTEPS:
        pc, T, S, rets = work.pop()
        key = (pc, T, S, rets)
        if key in seen: continue
        seen.add(key)
        if not T and not S: events['dead'] += 1; continue
        steps += 1
        w = word(pc)
        if w is None: events['out-of-text'] += 1; continue
        kind, uses, defs, ex = dec(w)
        newT = set(T); newS = set(S)
        for reg, role in uses:
            if reg and reg in T:
                c = classify(role, ex, w)
                if c == 'FLAG': flags.append({'pc': hex(pc), 'insn': '%08x' % w, 'role': role, 'tainted': sorted(T)})
                else: safe[c if c != 'propagate' else 'propagate:' + role.split()[0]] += 1
        # propagation
        prop = False
        if kind == 'alu':
            src_t = any(reg and reg in T for reg, _ in uses)
            cls = [classify(role, ex, w) for reg, role in uses if reg and reg in T]
            for d in defs: newT.discard(d)
            if src_t and 'propagate' in cls:
                for d in defs: newT.add(d)
            if src_t and 'FLAG' in cls:
                for d in defs: newT.add(d)  # keep following derived values too
        elif kind == 'mov':
            nm, rs_, rt_, rd_ = ex
            if rs_ in T and rd_: newT.add(rd_)
        elif kind == 'load':
            base, off, = ex
            for d in defs: newT.discard(d)
            if (base, off) in S and base in (29, 30):
                newT.add(defs[0]); events['reload-of-spill'] += 1
        elif kind == 'store':
            base, off, rt_ = ex
            if base in (29, 30):
                if rt_ in T: newS.add((base, off)); events['spill'] += 1
                else: newS.discard((base, off))
            for d in defs: newT.discard(d)
        elif kind == 'unk':
            for d in defs: newT.discard(d)
        newT.discard(0)
        def delay_then(target_list, T2, S2, rets2, link=False):
            # execute delay slot at pc+4 with the same rules, then go to each target
            w2 = word(pc + 4)
            k2, u2, d2, e2 = dec(w2)
            T3 = set(T2); S3 = set(S2)
            for reg, role in u2:
                if reg and reg in T3:
                    c = classify(role, e2, w2)
                    if c == 'FLAG': flags.append({'pc': hex(pc + 4), 'insn': '%08x' % w2, 'role': role + ' (delay slot)', 'tainted': sorted(T3)})
                    else: safe[c if c != 'propagate' else 'propagate:' + role.split()[0]] += 1
            if k2 == 'store' and e2[0] in (29, 30):
                if e2[2] in T3: S3.add((e2[0], e2[1]))
                else: S3.discard((e2[0], e2[1]))
            src_t = any(reg and reg in T3 for reg, _ in u2)
            if k2 == 'mov':
                if e2[1] in T3 and e2[3]: T3.add(e2[3])
            else:
                cls = [classify(role, e2, w2) for reg, role in u2 if reg and reg in T3]
                for d in d2: T3.discard(d)
                if src_t and any(c in ('propagate', 'FLAG') for c in cls) and k2 == 'alu':
                    for d in d2: T3.add(d)
            if link: T3.discard(31)
            T3.discard(0)
            return T3, S3
        if kind == 'branch':
            T3, S3 = delay_then(None, newT, newS, rets, link=bool(defs))
            work.append((pc + 4 + (ex << 2), frozenset(T3), frozenset(S3), rets))
            work.append((pc + 8, frozenset(T3), frozenset(S3), rets))
        elif kind == 'j':
            T3, S3 = delay_then(None, newT, newS, rets)
            work.append((((pc + 4) & ~0x0FFFFFFF) | ex, frozenset(T3), frozenset(S3), rets))
        elif kind in ('jal', 'jalr'):
            T3, S3 = delay_then(None, newT, newS, rets)
            argT = T3 & ARGS
            if argT: events['tainted-arg-to-call'] += 1
            after = frozenset(T3 & CALLEE_SAVED)
            if kind == 'jal' and len(rets) < MAXDEPTH and argT:
                tgt = ((pc + 4) & ~0x0FFFFFFF) | ex
                work.append((tgt, frozenset(argT), frozenset(), rets + ((pc + 8, after, frozenset(S3)),)))
            elif argT and kind == 'jalr':
                flags.append({'pc': hex(pc), 'insn': '%08x' % w, 'role': 'tainted arg to indirect call', 'tainted': sorted(argT)})
            elif argT:
                events['depth-limit'] += 1
            work.append((pc + 8, after, frozenset(S3), rets))
        elif kind == 'jr':
            T3, S3 = delay_then(None, newT, newS, rets)
            if ex == 31:
                retT = T3 & {2, 3}
                if rets:
                    rpc, cT, cS = rets[-1]
                    work.append((rpc, frozenset(cT | retT), cS, rets[:-1]))
                elif retT:
                    flags.append({'pc': hex(pc), 'insn': '%08x' % w, 'role': 'returned to unknown caller in v0/v1', 'tainted': sorted(retT)})
                else: events['return-dead'] += 1
            else:
                if T3 or S3: events['indirect-jump-live'] += 1; flags.append({'pc': hex(pc), 'insn': '%08x' % w, 'role': 'indirect jump while live', 'tainted': sorted(T3)})
        else:
            work.append((pc + 4, frozenset(newT), frozenset(newS), rets))
    if work: events['budget-exhausted'] += 1
    return {'site': hex(site), 'reg': r, 'inDelaySlotOf': inslot, 'steps': steps, 'flags': flags, 'safeReads': dict(safe), 'events': dict(events)}

def main():
  res = []
  for off in range(0, len(data) - 4, 4):
      w = struct.unpack('>I', data[off:off + 4])[0]
      if w >> 26 == 0x0C and (w & 0xFFFF) == 0x40 and (w >> 16) & 31:
          res.append(scan(BASE + off, (w >> 16) & 31))
  tot = collections.Counter(); nflag = 0
  for x in res:
      for k, v in x['safeReads'].items(): tot[k] += v
      nflag += len(x['flags'])
  summary = {'sites': len(res), 'sitesWithFlags': sum(1 for x in res if x['flags']), 'flags': nflag, 'safeReads': dict(tot),
             'budgetExhausted': sum(1 for x in res if x['events'].get('budget-exhausted')), 'maxSteps': max(x['steps'] for x in res)}
  print(json.dumps(summary, indent=1))
  json.dump({'summary': summary, 'sites': res}, open(sys.argv[2], 'w'), indent=1)

if __name__ == '__main__': main()
