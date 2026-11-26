"""Task 4 (L-1040): rerun the one-unit mutations of cycle 23 (theme-state-replay.work/scripts/mutate.py) and four new ones
on the replayed transactions that take a given branch, selected from the branch keys that replaycov.py recorded per
transaction. Categories: flip (TickBitmap.flipTick ran: JUMPI 16669 fell through), wordEdge (nextInitializedTickWithinOneWord
returned an uninitialized word edge: JUMPI 19371 or 21204 taken), roundUp (FullMath.mulDivRoundingUp incremented: JUMPI 23682
taken, reached from SqrtPriceMath getAmount0Delta(roundUp) and getNextSqrtPriceFromAmount0RoundingUp).
Sampling: random.Random(SEED + cid) picks up to N transactions per category. usage: mutate_subset.py <cid> [N] [comma-separated mutation indices]
writes ../out/<cid>/mutation-subset.json"""
import sys, os, json, gzip, random, collections
HERE = os.path.dirname(os.path.abspath(__file__))
C23 = '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work'
sys.path.insert(0, C23 + '/scripts')
import model as M, v4math as V
from eps import NETS
from aggregate import load
SEED = 2026_11_26
cid = int(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 300
PM = NETS[cid]['poolManager'].lower()
_, _, _, _, pertx = load(cid)
CAT = {'flip': lambda k: 16669 * 2 in k, 'wordEdge': lambda k: 19371 * 2 + 1 in k or 21204 * 2 + 1 in k, 'roundUp': lambda k: 23682 * 2 + 1 in k,
       'wordCross': lambda k: 19903 * 2 in k}  # Pool.sol:415 not initialized: the step ended on an uninitialized word edge (or the MIN/MAX clamp) and the swap moved past it
if os.environ.get('CATS'): CAT = {k: v for k, v in CAT.items() if k in os.environ['CATS'].split(',')}
sel = {}; pop = {}
for name, f in CAT.items():
    hs = sorted(h for h, k in pertx.items() if f(set(k))); pop[name] = len(hs)
    rnd = random.Random(SEED + cid); sel[name] = sorted(rnd.sample(hs, min(N, len(hs))))
orig_step = V.compute_swap_step; orig_flip = M.Model.flip; orig_a0 = V.amount0_delta; orig_tick = V.get_tick_at_sqrt_price
orig_mdru = V.mul_div_rounding_up; orig_np0 = V.next_price_amount0_rounding_up; orig_a1 = V.amount1_delta; orig_next = M.Model.next_init
def m_step(*a): p, i, o, f = orig_step(*a); return p, i, o + 1, f
def m_stepfee(*a): p, i, o, f = orig_step(*a); return p, i, o, f + 1 if f else f
def m_flip(self, b, t, ts): s = self.word_slot(b, (t // ts) >> 8); self.sstore(s, self.sload(s) ^ 2)
def m_a0(pa, pb, l, r): return orig_a0(pa, pb, l, r) + (1 if r else 0)
def m_tick(p): return orig_tick(p) + (1 if p % 7 == 0 else 0)
def m_mdru(a, b, d): return V.mul_div(a, b, d)  # round-up increment dropped
def m_np0(p, l, a, add_):
    r = orig_np0(p, l, a, add_); return r - 1 if r != p else r
def m_a1(pa, pb, l, r): return orig_a1(pa, pb, l, False)
def m_next(self, b, tick, ts, lte):
    n, init = orig_next(self, b, tick, ts, lte)
    if not init: n = n + ts if lte else n - ts  # uninitialized word edge one spacing inside the word
    return n, init
MUT = {'none': {}, 'swap amountOut +1': {'step': m_step}, 'swap fee +1': {'step': m_stepfee}, 'flipTick wrong bit': {'flip': m_flip},
       'getAmount0Delta round-up +1': {'a0': m_a0}, 'getTickAtSqrtPrice +1 on 1/7 of prices': {'tick': m_tick},
       'new: mulDivRoundingUp without increment': {'mdru': m_mdru}, 'new: getNextSqrtPriceFromAmount0RoundingUp -1': {'np0': m_np0},
       'new: getAmount1Delta round-up dropped': {'a1': m_a1}, 'new: uninitialized word edge one spacing inside': {'next': m_next}}
raws = {}
for name in sel:
    for h in sel[name]:
        if h not in raws: raws[h] = gzip.open('%s/raw/%d/tx/%s.json.gz' % (C23, cid, h)).read()
res = {'chainId': cid, 'seed': SEED + cid, 'N': N, 'population': pop, 'selected': {k: len(v) for k, v in sel.items()}, 'selectedHashes': sel, 'mutations': {}}
ONLY = [list(MUT)[int(x)] for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else list(MUT)
for mname, pat in MUT.items():
    if mname not in ONLY: continue
    V.compute_swap_step = pat.get('step', orig_step); M.Model.flip = pat.get('flip', orig_flip); V.amount0_delta = pat.get('a0', orig_a0)
    V.get_tick_at_sqrt_price = pat.get('tick', orig_tick); V.mul_div_rounding_up = pat.get('mdru', orig_mdru)
    V.next_price_amount0_rounding_up = pat.get('np0', orig_np0); V.amount1_delta = pat.get('a1', orig_a1); M.Model.next_init = pat.get('next', orig_next)
    hit = {}
    for h, raw in raws.items():
        rec = json.loads(raw)
        pre = next((v for k, v in rec['pre'].items() if k.lower() == PM), {})
        dpre = next((v for k, v in rec['diff']['pre'].items() if k.lower() == PM), {})
        dpost = next((v for k, v in rec['diff']['post'].items() if k.lower() == PM), {})
        m = M.Model(PM, pre.get('storage'), M.I(pre.get('balance')))
        try:
            m.frame(rec['call']); m.finish(dpre, dpost); hit[h] = bool(m.mm)
        except Exception:
            hit[h] = True
    res['mutations'][mname] = {cat: {'txs': len(hs), 'detected': sum(hit[h] for h in hs)} for cat, hs in sel.items()}
    print(mname, res['mutations'][mname], flush=True)
json.dump(res, open('%s/../out/%d/mutation-subset%s%s.json' % (HERE, cid, os.environ.get('CATS', '').replace(',', '_'), '-' + sys.argv[3].replace(',', '_') if len(sys.argv) > 3 else ''), 'w'), indent=1)
