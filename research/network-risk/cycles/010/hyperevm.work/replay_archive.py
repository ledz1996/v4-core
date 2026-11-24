"""Replay the newest multi-step HyperEVM swaps of out/swaps_all.json with tools/opdiff/replay.py, reading pool state
at the block of each swap from the archive endpoint rpc.purroofgroup.com, because the official endpoint answers every
block tag with latest state (hyperliquid-dex/node issue 158). Read only. Usage: python3 replay_archive.py <in.json> <out.json>"""
import sys, json, os, runpy
sys.path.insert(0, __file__.rsplit('/', 4)[0] + '/tools/opdiff')
src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src)); tmp = out + '.in.json'
json.dump({'results': [d]}, open(tmp, 'w'))
code = open(__file__.rsplit('/', 4)[0] + '/tools/opdiff/replay.py').read().replace(
    "56: 'https://bsc-rpc.publicnode.com'}", "56: 'https://bsc-rpc.publicnode.com', 999: 'https://rpc.purroofgroup.com'}")
sys.argv = ['replay.py', tmp, out]
g = {'__name__': '__main__', '__file__': __file__.rsplit('/', 4)[0] + '/tools/opdiff/replay.py'}
exec(compile(code, 'replay.py', 'exec'), g)
