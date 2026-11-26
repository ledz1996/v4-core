"""Lead L-1038: rerun replay.py's step-by-step Pool.swap replay for the Arbitrum One samples of a swaps.json
against alternative endpoints that serve historical state. Read-only (eth_getStorageAt / eth_call at past blocks).
usage: altreplay.py <swaps.json> <out.json> <url> [url ...]"""
import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import replay as R
src, out, urls = sys.argv[1], sys.argv[2], sys.argv[3:]
PM = '0x360e68faccca8ca495c1b759fd9eee466db9fb32'
jobs = [(kind[:-7], smp) for r in json.load(open(src))['results'] if r['chainId'] == 42161 for kind in ('otherSamples', 'multiSamples') for smp in r.get(kind, [])]
allres = {}
for url in urls:
    ch = R.Chain(url, PM)
    def work(j):
        kind, smp = j
        try: res = R.replay(ch, smp)
        except Exception as e: res = {'ok': False, 'why': str(e)[:120]}
        return {'kind': kind, 'tx': smp['tx'], **res}
    with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(work, jobs))
    ok = sum(r['ok'] for r in res); why = {}
    for r in res:
        if not r['ok']: why[r['why'][:50]] = why.get(r['why'][:50], 0) + 1
    print(url, 'samples', len(res), 'replayed', ok, 'maxSteps', max([r.get('steps', 0) for r in res] or [0]), 'fail reasons', why, flush=True)
    allres[url] = res
json.dump(allres, open(out, 'w'), indent=1)
