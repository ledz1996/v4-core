# Names for selectors found in discover_*.json.gz that the cycle 5 signature file does not hold (public signature database).
import json, gzip, glob, os, time, requests
from concurrent.futures import ThreadPoolExecutor
from base import *
fn5 = os.path.join(RAW5, 'signatures.json.gz'); fn6 = os.path.join(RAW6, 'signatures_more.json.gz')
known = jz(fn5); more = jz(fn6) if os.path.exists(fn6) else {}
allsel = set()
for f in glob.glob(os.path.join(RAW6, 'discover_*.json.gz')):
    for t, o in jz(f).items():
        allsel.update(o.get('sels') or [])
        for a, r in (o.get('rel') or {}).items(): allsel.update(r['sels'])
todo = sorted(s for s in allsel if s not in known and s not in more)
print('selectors', len(allsel), 'todo', len(todo), flush=True)
S = requests.Session()
def job(i):
    ch = todo[i:i + 150]
    for k in range(6):
        host = ['https://api.4byte.sourcify.dev', 'https://api.openchain.xyz'][k % 2]
        try:
            j = S.get(host + '/signature-database/v1/lookup?filter=false&function=' + ','.join('0x' + s for s in ch), timeout=60).json()
            if j.get('ok'): return {s: [x['name'] for x in (j['result']['function'].get('0x' + s) or [])] for s in ch}
        except Exception as e: pass
        time.sleep(1 + k)
    print('fail', i, flush=True); return {}
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(job, range(0, len(todo), 150)): more.update(res)
json.dump(more, gzip.open(fn6, 'wt'))
print('more', len(more), 'named', sum(1 for v in more.values() if v))
