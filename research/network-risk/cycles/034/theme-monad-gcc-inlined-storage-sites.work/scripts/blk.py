"""Cycle 34, Task 3, whole blocks: the lock and reserves blocks of the 128 un-entered value blocks whose code-emitting
instructions all have an emit function in the model: 0xdbe and 0x275c (PUSH32 IS_UNLOCKED_SLOT, TLOAD, ISZERO, PUSH2,
JUMPI: src/libraries/Lock.sol:24 inside onlyWhenUnlocked) and 0xd1f (PUSH32 CURRENCY_SLOT, TLOAD, AND, EQ, JUMP:
src/libraries/CurrencyReserves.sol:16). Cycle 33 block.py is reused unchanged except: TLOAD is emitted by the call_runtime
instance 0x351f40 that compile_basic_blocks<MonadTraits<10>> calls with (Emitter, remaining_base_gas, 1, runtime::tload),
the runtime call is served by a Python transient store that also clobbers every caller-saved register, and the pyevm.py
reference runs with the same transient store preloaded. Lock words are drawn from 0, 1 and random words.
usage: python3 -I blk.py <outdir> <nsets> [fault]"""
import sys, os, json, random
OUTD = sys.argv[1]
C33 = '/home/user/v4-core/research/network-risk/cycles/033/theme-monad-gcc-terminators.work/scripts'
sys.path.insert(0, C33)
# load cycle 33 term.py as the module block.py imports, with its function-text cache redirected into this work
# directory so that nothing is written under cycle 33
import types
tsrc = open(C33 + '/term.py').read()
tsrc = tsrc.replace("MYFN = os.path.join(W, 'out', 'fn')", "MYFN = %r" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/out/fn'))
tsrc = tsrc.replace("os.path.join(HERE, 'faults33.json')", repr(C33 + '/faults33.json'))
assert 'out/fn' in tsrc.split('MYFN = ')[1].split('\n')[0]
_argv0 = list(sys.argv); sys.argv = [sys.argv[0], OUTD, '0']
_t = types.ModuleType('term'); _t.__file__ = C33 + '/term.py'
exec(compile(tsrc, 'term.py', 'exec'), _t.__dict__)
sys.modules['term'] = _t; sys.argv = _argv0
src = open(C33 + '/block.py').read()
assert src.rstrip().endswith('main()')
src = src.rstrip()[:-len('main()')]
src = src.replace("os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults33b.json')", "os.path.join(%r, 'faults33b.json')" % C33)
bm = {'__file__': C33 + '/block.py', '__name__': 'bm'}
exec(compile(src, 'block.py', 'exec'), bm)
term = bm['term']; helpers = bm['helpers']; pyevm = bm['pyevm']; Stop = bm['Stop']; ra = bm['ra']; g = bm['g']
HERE = os.path.dirname(os.path.abspath(__file__))
FAULTS34 = json.load(open(os.path.join(HERE, 'faults34.json')))
bm['FAULTS'].update(FAULTS34)
TLOAD_FN, CR_TLOAD = 0x340570, 0x351f40
bm['BLOCKS'][:] = [0xdbe, 0x275c, 0xd1f]
bm['EMIT']['TLOAD'] = CR_TLOAD
_orig_emit = bm['emit_site']
FAULT = sys.argv[3] if len(sys.argv) > 3 else None
def emit_site(kind, st, faults, table):
    if kind != 'TLOAD': return _orig_emit(kind, st, faults, table)
    ent = CR_TLOAD
    clos = term.closure_of([ent] + ra['clos'])
    g['ENTRY'][kind] = [ent] + [a for a in clos if a != ent]
    m, ids, info = ra['build'](kind, st, faults, table)
    term.Equip(m, st)
    bm['allocdrv'].TAB[:] = m.table(); m._ids, m._info, m._tabpre = ids, info, m.table()
    m.c.call(ent, [bm['E'], 0, 1, TLOAD_FN], maxsteps=5000000)
    return m
bm['emit_site'] = emit_site

TSTATE = {}
CALLS = []
_oc = helpers.CallCPU.i_call
def i_call(self, o, pc, n):
    s = o[0]
    if 'PTR' in s:
        t = self.get(self.opnd(s))
        if t == TLOAD_FN:
            key = self.read(self.r['rdx'], 32); CALLS.append(key)
            v = TSTATE.get(key, 0)
            if FAULT == 'stub-result-inverted': v ^= 1
            self.write(self.r['rsi'], 32, v)
            for r in ('rax', 'rcx', 'rdx', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11'): self.r[r] = RND.getrandbits(64)
            for i in range(16): self.y[i] = RND.getrandbits(256)
            for f in ('cf', 'zf', 'sf', 'of'): setattr(self, f, RND.getrandbits(1))
            return n
    return _oc(self, o, pc, n)
helpers.CallCPU.i_call = i_call
RND = random.Random(3435)
EQMODES = {}
SLOTS = [0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23, 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9]

_orig_run_ref = bm['run_ref']
def run_ref(pre, body, depth):
    # fresh lock and reserves words for this set, shared by the native stub and the reference
    TSTATE.clear(); del CALLS[:]
    for k in SLOTS: TSTATE[k] = RND.choice([0, 1, 1, RND.getrandbits(256), RND.getrandbits(160), 1 << 255])
    # reserves block 0xd1f compares and(tload(CURRENCY_SLOT), 2^160-1) with a copy of an entry word: make the synced
    # currency equal to an entry word (as stored, with dirty high bits, or one apart) in 40 per cent of the sets
    ents = [int.from_bytes(pre[i + 1:i + 33], 'big') for i in range(0, len(pre), 33)]
    if ents and RND.random() < 0.4:
        x = RND.choice(ents); mode = RND.choice(['same', 'dirty-high', 'plus1'])
        TSTATE[SLOTS[1]] = {'same': x, 'dirty-high': x | (RND.getrandbits(96) << 160), 'plus1': (x + 1) % (1 << 256)}[mode]
        EQMODES[mode] = EQMODES.get(mode, 0) + 1
    post = b''
    for k in range(depth): post += b'\x61' + (32 * k).to_bytes(2, 'big') + b'\x52'
    post += b'\x61' + (32 * depth).to_bytes(2, 'big') + b'\x5f\xf3'
    w = pyevm.World({0xaa: pre + body + post})
    for k, v in TSTATE.items(): w.transient[(0xaa, k)] = v
    ok, ret = w.call(1, 0xaa, 0, b'', False, 0)
    assert ok
    return [int.from_bytes(ret[32 * k:32 * k + 32], 'big') for k in range(depth)]
bm['run_ref'] = run_ref
bm['OUTD'] = OUTD
bm['main']()
print('reserves equal-word modes', EQMODES)
