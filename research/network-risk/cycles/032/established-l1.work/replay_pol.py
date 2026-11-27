"""Run tools/opdiff/replay.py for the Polygon samples only, reading parent-block state from
QuikNode's public Polygon endpoint (publicnode refuses archive reads). Read-only.
Usage: python3 replay_pol.py <swaps.json> <out.json>"""
import sys, json, runpy
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
src = json.load(open(sys.argv[1]))
src['results'] = [r for r in src['results'] if r['chainId'] == 137]
tmp = sys.argv[2] + '.src.json'; json.dump(src, open(tmp, 'w'))
import replay
replay.__dict__  # loaded
code = open('/home/user/v4-core/research/network-risk/tools/opdiff/replay.py').read()
code = code.replace("STATE_RPC = {", "STATE_RPC = {137: 'https://rpc-mainnet.matic.quiknode.pro', ")
sys.argv = ['replay.py', tmp, sys.argv[2]]
exec(compile(code, '/home/user/v4-core/research/network-risk/tools/opdiff/replay.py', 'exec'), {'__name__': '__main__', '__file__': '/home/user/v4-core/research/network-risk/tools/opdiff/replay.py'})
