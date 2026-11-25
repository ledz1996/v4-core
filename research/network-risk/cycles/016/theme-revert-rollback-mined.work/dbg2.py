"""Debug helper: environment opcodes executed per depth in the reference run of one transaction."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '.')
import replay as RP, pyevm_tx as P
cid, url, h, lurl, d0 = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
oi = P.World.__init__
def init(self, *a, **k):
    oi(self, *a, **k); self.trace = []; self.trace_stack = 3
P.World.__init__ = init
cap = {}
orun = P.World.run
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
import replay
W = []
oc = P.World.call
def c(self, *a, **k):
    W.append(self); return oc(self, *a, **k)
P.World.call = c
r = RP.one(cid, url, nets[cid]['poolManager'], h, lurl)
w = W[0]
seen = 0
for (dp, pc, op, stk) in w.trace:
    if dp == d0 and (0x30 <= op <= 0x4a or op == 0x5a): print(dp, pc, P.NAMES.get(op), stk); seen += 1
    if seen > 40: break
