"""Cycle 37, L-1318 live complement: reruns cycle 31's live_credit_shapes.py (zero crossing writes of PoolManager
slots, and a helper that writes and then reverts inside the same unlock) on the live Tempo binary with the
PoolManager's TIP-1060 credit word in 0x1060000000000000000000000000000000000000 replaced by state override, so
the credit branch of SSTORE runs with other host data than the real 20 credits. Read-only eth_call / eth_simulateV1.
usage: python3 -I credit_override.py <out.json> [credits ...]   (env TIME_OVERRIDE for T14 rules)"""
import sys, json, importlib.util
sys.argv = [sys.argv[0]] + sys.argv[1:]
OUT = sys.argv[1]; CREDITS = [int(x, 0) for x in sys.argv[2:]] or [0, 1, 20, 2**64 - 1]
src = '/home/user/v4-core/research/network-risk/cycles/031/theme-tempo-binary-call-rollback.work/scripts/live_credit_shapes.py'
spec = importlib.util.spec_from_file_location('lcs', src); L = importlib.util.module_from_spec(spec)
sys.argv = [src, '/dev/null']; spec.loader.exec_module(L)
CS = '0x1060000000000000000000000000000000000000'
PMSLOT = '0x%064x' % L.PM
orig = L.state_override
allres = {}
for c in CREDITS:
    def so(codes, c=c):
        s = orig(codes); s[CS] = {'stateDiff': {PMSLOT: '0x%064x' % c}}; return s
    L.state_override = so
    out = OUT + '.credits_%d.json' % c
    L.OUT = out
    L.main()
    r = json.load(open(out))
    allres[str(c)] = {k: {'equal': v['equal'], 'nodeOk': v['node']['ok'], 'refOk': v['ref']['ok'], 'nodeErr': v['node'].get('error')} for k, v in r['variants'].items()}
    allres[str(c)]['client'] = [r['clientBefore'].get('result'), r['clientAfter'].get('result')]; allres[str(c)]['block'] = r['block']
    allres[str(c)]['simTimestamps'] = r.get('simulatedTimestamps')
json.dump(allres, open(OUT, 'w'), indent=1)
print(json.dumps(allres, indent=1))
