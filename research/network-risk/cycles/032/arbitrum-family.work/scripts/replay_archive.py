# Cycle 32: rerun replay.py's samples for Arbitrum One against the Pocket archive gateway, which serves historical state.
import sys, json, runpy
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import replay
src, out = sys.argv[1], sys.argv[2]
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
res = []
for r in json.load(open(src))['results']:
    if r['chainId'] != 42161: continue
    ch = replay.Chain('https://arb-one.api.pocket.network', nets[42161]['poolManager'])
    for kind in ('otherSamples', 'multiSamples'):
        for smp in r.get(kind, []):
            try: x = replay.replay(ch, smp)
            except Exception as e: x = {'ok': False, 'why': str(e)[:100]}
            res.append({'kind': kind[:-7], 'tx': smp['tx'], **x}); print(kind, smp['tx'][:12], x.get('ok'), x.get('steps'), x.get('why', '')[:60], flush=True)
json.dump({'url': 'https://arb-one.api.pocket.network', 'results': res}, open(out, 'w'), indent=1)
