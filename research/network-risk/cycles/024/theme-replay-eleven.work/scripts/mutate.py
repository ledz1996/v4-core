"""Sensitivity check of the replay: apply one deliberate one-unit change to the model at a time and count how many
transactions then show a mismatch. A replay that cannot see a one-unit change in these places would prove nothing.
usage: mutate.py <chainId> <n_files>"""
import json, sys, gzip, glob, collections
import model as M, v4math as V
from eps import NETS
cid = int(sys.argv[1]); n = int(sys.argv[2]); PM = NETS[cid]['poolManager'].lower()
files = sorted(glob.glob('../raw/%d/tx/*.json.gz' % cid))[:n]
raws = [gzip.open(f).read() for f in files]
orig_step = V.compute_swap_step; orig_md = V.mul_div; orig_flip = M.Model.flip; orig_a0 = V.amount0_delta; orig_tick = V.get_tick_at_sqrt_price
def m_step(*a):
    p, i, o, f = orig_step(*a); return p, i, o + 1, f
def m_stepfee(*a):
    p, i, o, f = orig_step(*a); return p, i, o, f + 1 if f else f
def m_flip(self, b, t, ts):
    s = self.word_slot(b, (t // ts) >> 8); self.sstore(s, self.sload(s) ^ 2)
def m_a0(pa, pb, l, r): return orig_a0(pa, pb, l, r) + (1 if r else 0)
def m_tick(p): return orig_tick(p) + (1 if p % 7 == 0 else 0)
MUT = {'none': {}, 'swap amountOut +1': {'step': m_step}, 'swap fee +1': {'step': m_stepfee}, 'flipTick wrong bit': {'flip': m_flip},
       'getAmount0Delta round-up +1': {'a0': m_a0}, 'getTickAtSqrtPrice +1 on 1/7 of prices': {'tick': m_tick}}
res = {}
for name, pat in MUT.items():
    V.compute_swap_step = pat.get('step', orig_step); M.Model.flip = pat.get('flip', orig_flip); V.amount0_delta = pat.get('a0', orig_a0)
    V.get_tick_at_sqrt_price = pat.get('tick', orig_tick)
    hit = 0; kinds = collections.Counter(); relevant = 0
    for raw in raws:
        rec = json.loads(raw)
        pre = next((v for k, v in rec['pre'].items() if k.lower() == PM), {})
        dpre = next((v for k, v in rec['diff']['pre'].items() if k.lower() == PM), {})
        dpost = next((v for k, v in rec['diff']['post'].items() if k.lower() == PM), {})
        m = M.Model(PM, pre.get('storage'), M.I(pre.get('balance')))
        try:
            m.frame(rec['call']); m.finish(dpre, dpost)
        except Exception as e:
            kinds['exception'] += 1; hit += 1; continue
        if m.mm: hit += 1
        for x in m.mm: kinds[x['kind']] += 1
    res[name] = {'txs': len(raws), 'txsWithMismatch': hit, 'kinds': dict(kinds)}
    print(name, res[name], flush=True)
json.dump(res, open('../raw/%d/mutation.json' % cid, 'w'), indent=1)
