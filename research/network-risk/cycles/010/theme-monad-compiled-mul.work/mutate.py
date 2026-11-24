"""Mutation checks: each change below breaks one emitted instruction; the run must then fail.
Usage: python3 -I mutate.py <workdir>"""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import muljit as J, run as R
out = {}
def trial(name, path, n=4000):
    rng = random.Random(7); random.seed(8); st = {}; fl = []
    for i in range(n):
        if path == 'mm96': R.mul_mod2(rng, 96, R.operand(rng), R.operand(rng), False, st, fl, 'm')
        elif path == 'mm128': R.mul_mod2(rng, 128, R.operand(rng), R.operand(rng), False, st, fl, 'm')
        elif path == 'tick':
            c = R.SITE_MUL_LITERALS[i % len(R.SITE_MUL_LITERALS)]; R.mul_optimized(rng, c, R.operand(rng), st, fl, 't')
        elif path == 'mullit':
            c = rng.getrandbits(32) | (1 << 31) | 3
            R.mul_optimized(rng, c, R.operand(rng), st, fl, 'l')
        elif path == 'rt': R.rt_mul(rng, R.operand(rng), R.operand(rng), st, fl, 'r')
    out[name] = {'path': path, 'n': st.get('n'), 'fail': st.get('fail', 0) + st.get('assert', 0)}
    print(name, out[name])
trial('baseline-mm96', 'mm96'); trial('baseline-mm128', 'mm128'); trial('baseline-tick', 'tick'); trial('baseline-rt', 'rt'); trial('baseline-mullit', 'mullit')
orig_adc = J.CPU.adc
J.CPU.adc = lambda self, d, s: J.CPU.add(self, d, s)          # carry dropped in every adc
trial('adc-as-add-mm128', 'mm128'); trial('adc-as-add-tick', 'tick'); trial('adc-as-add-rt', 'rt')
J.CPU.adc = orig_adc
orig_wr = J.CPU.wr
def wr64(self, o, v, w=64):
    if isinstance(o, J.R32): self.reg[o.r] = (self.reg[o.r] & ~J.M32 | (v & J.M32)) & J.M64  # 32 bit write keeps the upper half
    else: orig_wr(self, o, v, w)
J.CPU.wr = wr64
trial('r32-no-zero-extend-mm96', 'mm96')
J.CPU.wr = orig_wr
orig = J.Emitter.__dict__['bounded']
J.Emitter.bounded = staticmethod(lambda x: x <= J.M32)          # unsigned 32 bit bound instead of signed
trial('bound-unsigned-tick', 'tick'); trial('bound-unsigned-mullit', 'mullit')
J.Emitter.bounded = orig
orig_mx = J.CPU.mulx
J.CPU.mulx = lambda self, hi, lo, s: (orig_mx(self, hi, lo, s), self.__setattr__('cf', 0))[0]   # mulx that clears CF
trial('mulx-clears-cf-tick', 'tick'); trial('mulx-clears-cf-rt', 'rt')
J.CPU.mulx = orig_mx
J.CPU.mulx = lambda self, hi, lo, s: (orig_mx(self, hi, lo, s), self.wr(hi, 0))[0]   # high half lost
trial('mulx-hi-lost-mm128', 'mm128'); trial('mulx-hi-lost-mm96', 'mm96')
J.CPU.mulx = orig_mx
json.dump(out, open(os.path.join(sys.argv[1], 'mutate.json'), 'w'), indent=1)
