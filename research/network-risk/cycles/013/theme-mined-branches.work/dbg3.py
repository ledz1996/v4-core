"""First non-PoolManager frame whose return data differs between the rerun and the trace."""
import sys, json
import rerun as R, pyevm2
from common import *
orig = pyevm2.World.__init__
def init(self, *a, **k):
    orig(self, *a, **k); self.calllog = []; self.prelog = []; DB.append(self)
pyevm2.World.__init__ = init; DB = []
oc = pyevm2.World.call
def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
    i = len(self.prelog); self.prelog.append(None)
    ok, ret = oc(self, caller, to, value, data, static, depth, code_addr, storage_addr)
    self.prelog[i] = ('0x%040x' % (code_addr if code_addr is not None else to), '0x' + bytes(data).hex(), ok, '0x' + ret.hex())
    return ok, ret
pyevm2.World.call = call
cid, h = int(sys.argv[1]), sys.argv[2]
r = R.rerun(cid, h)
t = rpc(TRACE[cid], 'debug_traceTransaction', [h, {'tracer': 'callTracer'}])
tl = []
def walk(n):
    tl.append(((n.get('to') or '').lower(), (n.get('input') or '0x').lower(), 'error' not in n, (n.get('output') or '0x').lower(), n.get('type')))
    for c in n.get('calls', []) or []: walk(c)
walk(t)
pl = DB[0].prelog
print(len(tl), len(pl))
j = 0
for i, a in enumerate(tl):
    if j >= len(pl): print('rerun ended at', i); break
    b = pl[j]
    if a[0] != b[0] or a[1] != b[1]:
        # precompile frames may be missing on one side
        print('align break at', i, j, a[:2], b[:2]); break
    if a[2] != b[2] or (a[2] and a[3] != b[3]):
        print('differing frame', i, a[4], a[0], a[1][:138], '\n trace', a[2], a[3][:140], '\n rerun', b[2], b[3][:140])
    j += 1
