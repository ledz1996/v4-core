"""Debug helper: rerun one transaction in pyevm_tx and print every frame with its outcome, next to the chain's call tree."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '.')
import replay as RP, pyevm_tx as P, scan as S
cid, url, h, lurl = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
orig = P.World._call
log = []
def wrap(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
    i = len(log); log.append([depth, hex(to), bytes(data[:4]).hex(), None, None])
    ok, ret = orig(self, caller, to, value, data, static, depth, code_addr, storage_addr)
    log[i][3] = ok; log[i][4] = ret[:132].hex(); return ok, ret
P.World._call = wrap
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
r = RP.one(cid, url, nets[cid]['poolManager'], h, lurl)
ct = RP.R(url, 'debug_traceTransaction', [h, {'tracer': 'callTracer'}])
fl = []
def walk(n, d):
    fl.append([d, n.get('to'), n.get('input', '')[2:10], n.get('error'), (n.get('output') or '')[:136]])
    for c in n.get('calls', []) or []: walk(c, d + 1)
walk(ct, 0)
for i in range(max(len(log), len(fl))):
    a = log[i] if i < len(log) else None; b = fl[i] if i < len(fl) else None
    print(i, 'REF', a, '\n   CHN', b)
    if i > int(sys.argv[5]) if len(sys.argv) > 5 else 60: break
