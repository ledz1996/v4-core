"""Cycle 38, theme-frame-checkpoint-and-commit-lift: family 'F' of the cycle 37 journal machines, in which the
checkpoint, the commit and the revert are the code the call frame itself runs, lifted from the frame functions of
the shipped binary (objdump text interpreted in the cycle 27-37 x86-64 model; nothing is executed or loaded):

  checkpoint : the inlined block of make_call_frame (EthFrame::init_with_context) that reads the three lengths of
               the journal (logs J+0x10, entries J+0x28, third list J+0x40), stores them as the frame's record and
               raises the depth word J+0x118, run between its first and its last instruction with the frame
               function's own base register and stack frame;
  commit     : the inlined saturating decrement of the depth word, taken alternately from the frame return
               (process_next_action / frame_return_result) and from make_call_frame (precompile or empty code);
  revert     : the checkpoint_revert routine that the frame functions call (rdi = journal, rsi = the record the
               inlined checkpoint wrote).
In family F every frame also emits 0 to 3 logs (records in the logs vector with a no-op data drop) and 0 to 2
entries of the third list after its checkpoint, so that the log and list truncation of the revert is checked:
after every revert the log count and the list length must equal the record's values, after every commit they must
be unchanged.
"""
import random

M64 = (1 << 64) - 1

FRAME = {
    'celo': dict(base='A', cp=(0x1d6b299, 0x1d6b2d8), cp_regs={'r15': 'HOST'}, frame_reg='rbp', rec=-0x200,
                 commits=[(0x1d6fd39, 0x1d6fd51, 'rdx'), (0x1d6b944, 0x1d6b95c, 'r15')], revert=0x1d61dd0),
    'xlayer': dict(base='A', cp=(0x3cecfff, 0x3ced047), cp_regs={'r12': 'HOST'}, frame_reg='rsp', rec=0xd0,
                   commits=[(0x3cf063e, 0x3cf0656, 'rdx'), (0x3ced542, 0x3ced55c, 'r12')], revert=0x3ce8080),
    'arc': dict(base='A', cp=(0x1a0c117, 0x1a0c15c), cp_regs={'r12': 'HOST'}, frame_reg='rsp', rec=0x480,
                commits=[(0x1a26f7b, 0x1a26f93, 'rdx'), (0x1a0ca9a, 0x1a0cab2, 'rsi')], revert=0x19ffce0),
    'opreth': dict(base='A', cp=(0x456e2a4, 0x456e2ec), cp_regs={}, host_at_rsp8=True, frame_reg='rsp', rec=0x238,
                   commits=[(0x4571114, 0x457112a, 'rdx'), (0x456618c, 0x45661a2, 'rbp')], revert=0x44daef0),
}
NOOP = 0x16f00000          # model-only address of the no-op data drop of the fake logs


class FrameMismatch(Exception):
    pass


def install(MOD, prof, mode='frame'):
    P = MOD.PROFILES[prof]; spec = FRAME[prof]
    fam = dict(P['families'][spec['base']]); fam['revert'] = spec['revert']; P['families']['F'] = fam
    Machine = MOD.Machine
    HOST = MOD.HOST if hasattr(MOD, 'HOST') else __import__('rethj').HOST
    SP0 = MOD.SP0 if hasattr(MOD, 'SP0') else __import__('rethj').SP0
    J_of = lambda mc: getattr(mc, 'J', None) or mc.INNER
    orig_init = Machine.__init__

    def __init__(self, *a, **k):
        orig_init(self, *a, **k)
        if self.fam != 'F': return
        J = J_of(self)
        self.cpu.externs[NOOP] = lambda cpu: None
        self._vt = self._alloc(0x40, 16); self.wr(self._vt + 0x20, 8, NOOP)
        # logs vector (cap J+0, ptr J+8, len J+0x10) and third list (cap J+0x30, ptr J+0x38, len J+0x40) with room
        buf = self._alloc(0x50 * 512, 16); self.wr(J + 0x0, 8, 512); self.wr(J + 0x8, 8, buf); self.wr(J + 0x10, 8, 0)
        sd = self._alloc(0x20 * 512, 16); self.wr(J + 0x30, 8, 512); self.wr(J + 0x38, 8, sd); self.wr(J + 0x40, 8, 0)
        self._frnd = random.Random(self.rnd.getrandbits(64)); self._ncommit = 0
        self.fstats = {'cp_runs': 0, 'commit_ret': 0, 'commit_make': 0, 'logs_emitted': 0, 'list_pushed': 0}

    def _emit(self):
        J = J_of(self); r = self._frnd
        for _ in range(r.randint(0, 3)):
            n = self.rd(J + 0x10, 8)
            if n >= 500: break
            e = self.rd(J + 0x8, 8) + 0x50 * n
            self.wr(e, 0x50, 0); self.wr(e + 0x18, 8, self._vt); self.wr(e + 0x20, 8, 0xabc0 + n)
            self.wr(J + 0x10, 8, n + 1); self.fstats['logs_emitted'] += 1
        for _ in range(r.randint(0, 2)):
            n = self.rd(J + 0x40, 8)
            if n >= 500: break
            self.wr(self.rd(J + 0x38, 8) + 0x20 * n, 20, 0xdd00 + n); self.wr(J + 0x40, 8, n + 1)
            self.fstats['list_pushed'] += 1

    def checkpoint(self):
        if self.fam != 'F': return Machine._orig_checkpoint(self)
        J = J_of(self); a, b = spec['cp']
        regs = {k: (HOST if v == 'HOST' else v) for k, v in spec['cp_regs'].items()}
        if spec['frame_reg'] == 'rbp':
            fr = SP0 - 0x20000 - 0x1000 * self.depth(); regs['rbp'] = fr; rec = fr + spec['rec']
        else:
            rec = SP0 - 0x8 + spec['rec']
        if spec.get('host_at_rsp8'): self.wr(SP0, 8, HOST)
        d0 = self.depth(); before = (self.rd(J + 0x10, 8), self.rd(J + 0x28, 8), self.rd(J + 0x40, 8))
        self.run(a, [], stop=b, regs=regs)
        cp = tuple(self.rd(rec + 8 * i, 8) for i in range(3))
        self.fstats['cp_runs'] += 1
        if cp != before: raise FrameMismatch('inlined checkpoint record %s, journal lengths %s' % (cp, before))
        if self.depth() != (d0 + 1) & M64: raise FrameMismatch('inlined checkpoint depth %d after %d' % (self.depth(), d0))
        self._emit()
        self._after = (self.rd(J + 0x10, 8), self.rd(J + 0x40, 8))
        return cp

    def commit(self):
        if self.fam != 'F': return Machine._orig_commit(self)
        J = J_of(self); i = self._ncommit % len(spec['commits']); self._ncommit += 1
        a, b, reg = spec['commits'][i]
        logs, lst = self.rd(J + 0x10, 8), self.rd(J + 0x40, 8); d0 = self.depth(); jl = self.jlen()
        self.run(a, [], stop=b, regs={reg: HOST})
        self.fstats['commit_ret' if i == 0 else 'commit_make'] += 1
        if self.depth() != max(d0 - 1, 0): raise FrameMismatch('inlined commit depth %d after %d' % (self.depth(), d0))
        if (self.rd(J + 0x10, 8), self.rd(J + 0x40, 8), self.jlen()) != (logs, lst, jl):
            raise FrameMismatch('inlined commit changed lengths')

    def revert(self, cp):
        if self.fam != 'F': return Machine._orig_revert(self, cp)
        J = J_of(self); rec = SP0 - 0x30000 - 0x100 * (self.depth() & 0xff)
        for i, v in enumerate(cp): self.wr(rec + 8 * i, 8, v)
        logs0 = self.rd(J + 0x10, 8); lst0 = self.rd(J + 0x40, 8)
        self.run(self.F['revert'], [J, rec])
        exp_logs = min(cp[0], logs0); exp_lst = min(cp[2], lst0)
        if self.rd(J + 0x10, 8) != exp_logs:
            raise FrameMismatch('revert left %d logs, record %d (had %d)' % (self.rd(J + 0x10, 8), cp[0], logs0))
        if self.rd(J + 0x40, 8) != exp_lst:
            raise FrameMismatch('revert left third list length %d, record %d (had %d)' % (self.rd(J + 0x40, 8), cp[2], lst0))
        if self.jlen() != cp[1]:
            raise FrameMismatch('revert left journal length %d, record %d' % (self.jlen(), cp[1]))
        # the surviving logs are the ones emitted before the checkpoint, unchanged
        for n in range(exp_logs):
            e = self.rd(J + 0x8, 8) + 0x50 * n
            if self.rd(e + 0x20, 8) != 0xabc0 + n: raise FrameMismatch('log %d damaged by revert' % n)

    if not hasattr(Machine, '_orig_checkpoint'):
        Machine._orig_checkpoint = Machine.checkpoint; Machine._orig_commit = Machine.commit; Machine._orig_revert = Machine.revert
    Machine.__init__ = __init__; Machine._emit = _emit
    Machine.checkpoint = checkpoint; Machine.commit = commit; Machine.revert = revert
