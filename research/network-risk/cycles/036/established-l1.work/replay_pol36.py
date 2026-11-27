"""Run tools/opdiff/replay.py with Polygon state read from the Tenderly public gateway
(publicnode refuses parent-block reads). Optional third argument keeps one chain id.
Read-only. Usage: python3 replay_pol36.py <swaps.json> <out.json> [chainId]"""
import sys, json
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
src = json.load(open(sys.argv[1]))
if len(sys.argv) > 3:
    src['results'] = [r for r in src['results'] if r['chainId'] == int(sys.argv[3])]
tmp = sys.argv[2] + '.src.json'; json.dump(src, open(tmp, 'w'))
code = open(T + '/replay.py').read()
code = code.replace("STATE_RPC = {", "STATE_RPC = {137: 'https://polygon.gateway.tenderly.co', ")
sys.argv = ['replay.py', tmp, sys.argv[2]]
exec(compile(code, T + '/replay.py', 'exec'), {'__name__': '__main__', '__file__': T + '/replay.py'})
