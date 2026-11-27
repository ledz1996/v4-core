"""Line-for-line Python transcription of erigon main's per-frame SLOAD cache and the
journal-backed stamp it compares, as read on 2026-11-27 at commit
0ae25bfbdaee8653f1a97c8a4ad844fba24106d3 (the commit sourcegraph indexed for main;
raw.githubusercontent.com/erigontech/erigon/<that commit>/execution/vm/interpreter.go is
byte-identical to .../main/... fetched the same day).

  ReadStamp            execution/state/read_paths.go:1573-1587  {len(journal.entries), journal.epoch}
  journal.push/revert  execution/state/journal.go:116-157        push appends; revert truncates to the
                                                                   snapshot and epoch++; Reset epoch++
  frameSlots           execution/vm/interpreter.go:124-171       two entries keyed by the stack word,
                                                                   cleared when put() sees a new stamp
  opSload              execution/vm/instructions.go:859-880
  SSTORE gas phase     execution/vm/operations_acl.go:60-100     lookup, else GetState + put, then SetState
  SetState             execution/state/intra_block_state.go:1537-1561 journal entry unless prev == value
  transient Set        execution/state/transient_storage.go:52-64 journal entry unless unchanged
  getCallContext/putCallContext  execution/vm/interpreter.go:219-272  spare frame + pool, ok[] cleared on put
  run()                execution/vm/interpreter.go:577-578 and vm_run_gen.go:30-31  on = ReadStamp ok, misses = 0

The model keeps fewer journal entries than erigon (no access-list, refund, touch or nonce
entries). Every omitted entry would only move the stamp, so the model hits the cache at
least as often as erigon does: a stale word erigon could return, the model returns too.

Faults that can be planted (Task 5):
  nested      a storage write made while a lower frame of the same storage address is live
              does not push a journal entry (stamp not bumped on a nested write)
  revert      revert truncates but does not bump the epoch
  revshort    revert truncates the journal one entry short of the snapshot and does not bump the epoch
  revshort-epoch  the same short truncation with the epoch bumped as erigon does
  noaddr      one cache shared by all frames, keyed by slot word only (no address)
  reuse       putCallContext keeps ok[] (an entry survives frame reuse)
"""
MAX_MISSES = 8  # interpreter.go:122 maxFrameSlotMisses


class Slots:
    def __init__(self):
        self.on = False; self.misses = 0; self.stamp = None; self.next = 0
        self.ok = [False, False]; self.word = [None, None]; self.val = [0, 0]


class Ctx:
    def __init__(self):
        self.slots = Slots(); self.addr = None


class Core:
    def __init__(self, raw, fault=None):
        self.raw = raw  # the real storage dict {(addr, slot): value}
        self.n = 0; self.epoch = 0
        self.frames = []; self.spare = None; self.pool = []
        self.fault = fault; self.shared = Slots()
        self.hits = 0; self.fills = 0; self.reads = 0; self.stale = []; self.gas_stale = []

    # ReadStamp
    def stamp(self): return (self.n, self.epoch)
    def push(self): self.n += 1

    def revert_to(self, n):
        if self.fault in ('revshort', 'revshort-epoch'): n = max(0, n - 1)
        self.n = n
        if self.fault not in ('revert', 'revshort'): self.epoch += 1

    # getCallContext / run prologue
    def enter(self, addr):
        ctx = self.spare; self.spare = None
        if ctx is None: ctx = self.pool.pop() if self.pool else Ctx()
        ctx.addr = addr
        f = self.slots(ctx)
        f.on = True; f.misses = 0  # _, slots.on = ReadStamp(); slots.misses = 0
        self.frames.append(ctx)
        return ctx

    # putCallContext, called while evm.depth still counts the frame
    def leave(self):
        depth = len(self.frames); ctx = self.frames.pop()
        if self.fault != 'reuse':
            ctx.slots.ok = [False, False]; ctx.slots.word = [None, None]
        if depth > 1 and self.spare is None:
            self.spare = ctx; return
        self.pool.append(ctx)
        if depth == 1 and self.spare is not None:
            self.pool.append(self.spare); self.spare = None

    def slots(self, ctx): return self.shared if self.fault == 'noaddr' else ctx.slots

    # lookupSlot
    def lookup(self, ctx, word):
        f = self.slots(ctx)
        if f.stamp == self.stamp():
            for j in (0, 1):
                if f.ok[j] and f.word[j] == word:
                    f.misses = 0
                    return j
        return -1

    # frameSlots.put
    def put(self, ctx, word, v):
        f = self.slots(ctx)
        f.misses += 1
        if f.misses > MAX_MISSES:
            f.on = False; return
        if f.stamp != self.stamp():
            f.ok = [False, False]; f.stamp = self.stamp()
        i = f.next; f.next ^= 1
        f.ok[i], f.word[i], f.val[i] = True, word, v
        self.fills += 1

    # opSload
    def sload(self, addr, word, where=''):
        ctx = self.frames[-1]; assert ctx.addr == addr
        true = dict.get(self.raw, (addr, word), 0); self.reads += 1
        f = self.slots(ctx)
        if not f.on: return true
        j = self.lookup(ctx, word)
        if j >= 0:
            self.hits += 1; v = f.val[j]
            if v != true: self.stale.append({'addr': hex(addr), 'slot': hex(word), 'cached': hex(v), 'true': hex(true), 'depth': len(self.frames), 'where': where})
            return v
        self.put(ctx, word, true)
        return true

    # SSTORE: gas phase (operations_acl.go) then SetState
    def sstore(self, addr, word, v):
        ctx = self.frames[-1]; assert ctx.addr == addr
        true = dict.get(self.raw, (addr, word), 0)
        f = self.slots(ctx)
        if f.on:
            j = self.lookup(ctx, word)
            if j >= 0:
                if f.val[j] != true: self.gas_stale.append({'addr': hex(addr), 'slot': hex(word), 'cached': hex(f.val[j]), 'true': hex(true)})
            else:
                self.put(ctx, word, true)
        if true != v:
            reentrant = any(fr.addr == addr for fr in self.frames[:-1])
            if not (self.fault == 'nested' and reentrant): self.push()
            dict.__setitem__(self.raw, (addr, word), v)

    def journalled_set(self, d, k, v):  # transient storage and balances: an entry when the value changes
        if dict.get(d, k, 0) != v:
            self.push(); dict.__setitem__(d, k, v)
