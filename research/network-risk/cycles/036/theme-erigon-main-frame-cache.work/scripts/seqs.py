"""Task 2 sequences (a)-(h) and a random frame-tree sweep on the cache model, each run
with and without planted faults. A read is stale when the cache returns a word that is
not the value the storage holds at that moment (the uncached model's answer).
Usage: python3 -I seqs.py <out.json>"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cachemodel import Core

A, B = 0xA, 0xB
S, T, U = 1, 2, 3


class M:
    """Frames, calls with snapshot/revert, and SLOAD/SSTORE/TSTORE through the cache."""
    def __init__(self, fault=None):
        self.raw = {}; self.tr = {}; self.c = Core(self.raw, fault); self.static = False
    def frame(self, addr, body, revert=False, static=False):
        snap = (dict(self.raw), dict(self.tr), self.c.n)
        was = self.static; self.static = self.static or static
        self.c.enter(addr)
        try: body()
        finally: self.c.leave(); self.static = was
        if revert:
            self.raw.clear(); self.raw.update(snap[0]); self.tr.clear(); self.tr.update(snap[1]); self.c.revert_to(snap[2])
    def ld(self, w, where=''): return self.c.sload(self.c.frames[-1].addr, w, where)
    def st(self, w, v):
        assert not self.static
        self.c.sstore(self.c.frames[-1].addr, w, v)
    def tst(self, k, v): self.c.journalled_set(self.tr, (self.c.frames[-1].addr, k), v)


def seq_a(m):
    m.raw[(A, S)] = 5
    def nested(): m.st(S, 6)
    def outer(): m.ld(S, 'a1'); m.frame(A, nested); m.ld(S, 'a2')
    m.frame(A, outer)

def seq_b(m):
    m.raw[(A, S)] = 5
    def nested(): m.st(S, 6); m.ld(S, 'b-inner')
    def outer(): m.ld(S, 'b1'); m.frame(A, nested, revert=True); m.ld(S, 'b2')
    m.frame(A, outer)

def seq_c(m):
    m.raw[(A, S)] = 5
    def deeper(): m.st(S, 7); m.st(T, 1)
    def nested(): m.st(S, 6); m.ld(S, 'c-n1'); m.frame(A, deeper, revert=True); m.ld(S, 'c-n2')
    def outer(): m.ld(S, 'c1'); m.frame(A, nested); m.ld(S, 'c2')
    m.frame(A, outer)

def seq_c2(m):  # nested write that stands, a read, then a sibling that writes another slot and reverts
    m.raw[(A, S)] = 5
    def w1(): m.st(S, 6)
    def w2(): m.st(T, 1); m.st(U, 1)
    def outer(): m.ld(S, 'c2-1'); m.frame(A, w1); m.ld(S, 'c2-2'); m.frame(A, w2, revert=True); m.frame(A, lambda: m.st(S, 8)); m.frame(A, w2, revert=True); m.ld(S, 'c2-3')
    m.frame(A, outer)

def seq_c3(m):  # as c2, the sibling that reverts runs before the write that stands
    m.raw[(A, S)] = 5
    def w2(): m.st(T, 1); m.st(U, 1)
    def outer(): m.frame(A, w2, revert=True); m.ld(S, 'c3-1'); m.frame(A, lambda: m.st(S, 9)); m.frame(A, w2, revert=True); m.ld(S, 'c3-2')
    m.frame(A, outer)

def seq_d(m):  # write through DELEGATECALL: a frame with other code on A's storage
    m.raw[(A, S)] = 5
    def other_code(): m.st(S, 6)
    def outer(): m.ld(S, 'd1'); m.frame(A, other_code); m.ld(S, 'd2')  # storage address A, code B
    m.frame(A, outer)

def seq_e(m):
    m.raw[(A, S)] = 1; m.raw[(A, T)] = 2; m.raw[(A, U)] = 3
    def nested(): m.st(S, 11)
    def outer():
        m.ld(S, 'e1'); m.ld(T, 'e2'); m.ld(S, 'e3'); m.ld(T, 'e4')
        m.frame(A, nested)
        m.ld(S, 'e5'); m.ld(T, 'e6'); m.ld(U, 'e7'); m.ld(S, 'e8'); m.ld(T, 'e9'); m.ld(U, 'e10')
        m.frame(A, lambda: m.st(T, 22)); m.ld(T, 'e11'); m.ld(U, 'e12'); m.ld(T, 'e13')
    m.frame(A, outer)

def seq_f(m):  # written back to the original value
    m.raw[(A, S)] = 5
    def nested(): m.st(S, 7); m.st(S, 5)
    def nested2(): m.st(S, 7)
    def nested3(): m.st(S, 5)
    def outer(): m.ld(S, 'f1'); m.frame(A, nested); m.ld(S, 'f2'); m.frame(A, nested2); m.ld(S, 'f3'); m.frame(A, nested3); m.ld(S, 'f4')
    m.frame(A, outer)

def seq_g(m):  # a STATICCALL frame reads after the write
    m.raw[(A, S)] = 5
    def nested(): m.st(S, 6)
    def view(): m.ld(S, 'g-static')
    def outer(): m.ld(S, 'g1'); m.frame(A, view, static=True); m.frame(A, nested); m.frame(A, view, static=True); m.ld(S, 'g2')
    m.frame(A, outer)

def seq_h(m):  # frame reuse: siblings at the same depth on other storage addresses, no writes between
    m.raw[(A, S)] = 5; m.raw[(B, S)] = 9
    def outer():
        m.frame(A, lambda: m.ld(S, 'h-A'))
        m.frame(B, lambda: m.ld(S, 'h-B'))
        m.frame(A, lambda: (m.ld(S, 'h-A2'), m.frame(B, lambda: m.ld(S, 'h-B2'))))
        m.frame(B, lambda: m.ld(S, 'h-B3'))
    m.frame(A, outer)

def seq_t(m):  # transient storage write by a nested frame, then a read of storage
    m.raw[(A, S)] = 5
    def outer(): m.ld(S, 't1'); m.frame(A, lambda: m.tst(1, 1)); m.ld(S, 't2'); m.frame(A, lambda: (m.st(S, 6), m.tst(1, 0)), revert=True); m.ld(S, 't3')
    m.frame(A, outer)

SEQS = {'a': seq_a, 'b': seq_b, 'c': seq_c, 'c2': seq_c2, 'c3': seq_c3, 'd': seq_d, 'e': seq_e, 'f': seq_f, 'g': seq_g, 'h': seq_h, 't': seq_t}


def rand_tree(m, rnd, budget):
    """A random frame tree on two storage addresses and four slots."""
    def body(depth):
        for _ in range(rnd.randrange(1, 7)):
            if budget[0] <= 0: return
            budget[0] -= 1; r = rnd.random()
            if r < 0.4: m.ld(rnd.randrange(4), 'rnd')
            elif r < 0.65 and not m.static: m.st(rnd.randrange(4), rnd.choice([0, 1, 2, 3]))
            elif r < 0.7 and not m.static: m.tst(rnd.randrange(2), rnd.randrange(2))
            elif depth < 6:
                addr = rnd.choice([A, A, B]); m.frame(addr, lambda: body(depth + 1), revert=rnd.random() < 0.3, static=rnd.random() < 0.1)
    for (a, s) in [(A, 0), (A, 1), (B, 0), (B, 2)]: m.raw[(a, s)] = rnd.randrange(4)
    m.frame(A, lambda: body(1))


if __name__ == '__main__':
    out = sys.argv[1]; SEED = 36_2026_11_27; NTREE = 20000
    faults = [None, 'nested', 'revert', 'revshort', 'revshort-epoch', 'noaddr', 'reuse']
    res = {'seed': SEED, 'trees': NTREE, 'sequences': {}, 'random': {}}
    for fault in faults:
        fk = fault or 'none'; res['sequences'][fk] = {}
        for name, fn in SEQS.items():
            m = M(fault); fn(m)
            res['sequences'][fk][name] = {'reads': m.c.reads, 'hits': m.c.hits, 'stale': m.c.stale, 'gasStale': m.c.gas_stale}
        rnd = random.Random(SEED); tot = {'reads': 0, 'hits': 0, 'stale': 0, 'trees_with_stale': 0, 'first': None}
        for i in range(NTREE):
            m = M(fault); rand_tree(m, rnd, [60])
            tot['reads'] += m.c.reads; tot['hits'] += m.c.hits; tot['stale'] += len(m.c.stale)
            if m.c.stale:
                tot['trees_with_stale'] += 1
                if tot['first'] is None: tot['first'] = {'tree': i, 'stale': m.c.stale}
        res['random'][fk] = tot
        caught = sorted(k for k, v in res['sequences'][fk].items() if v['stale'])
        print(f'{fk:14s} sequences with a stale read: {caught}  random trees: {tot["trees_with_stale"]}/{NTREE} stale reads {tot["stale"]} of {tot["reads"]} reads, {tot["hits"]} hits')
    json.dump(res, open(out, 'w'), indent=1)
