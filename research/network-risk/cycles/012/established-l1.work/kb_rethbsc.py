"""Run the cycle 11 keccak bucket test (theme-keccak-cache.work/keccak_buckets.py) against chosen endpoints.
Usage: python3 kb_rethbsc.py <out.json>"""
import sys, os, json, runpy
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, '..', '..', '011', 'theme-keccak-cache.work', 'keccak_buckets.py')
m = runpy.run_path(src, run_name='kb')
EP = [(56, 'https://bsc-rpc.publicnode.com'), (56, 'https://bsc-dataseed1.bnbchain.org'), (43114, 'https://api.avax.network/ext/bc/C/rpc')]
recs, meta = m['build'](); code = m['contract']()
for g in recs:
    for d in g: m['kc'](d)
out = {'meta': meta, 'networks': []}
for cid, url in EP:
    r = m['run_net'](cid, url, recs, code); r['rpc'] = url; out['networks'].append(r)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
