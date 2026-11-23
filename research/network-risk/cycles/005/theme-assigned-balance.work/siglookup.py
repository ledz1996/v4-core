# Look up every PUSH4 operand found in pooled token code in the public signature database.
import json, gzip, glob, os, time, requests, collections
from concurrent.futures import ThreadPoolExecutor
RAW = 'raw'
fn = os.path.join(RAW, 'signatures.json.gz')
known = json.load(gzip.open(fn)) if os.path.exists(fn) else {}
allsel = set()
for f in glob.glob('raw/selectors_*.json.gz'):
    d = json.load(gzip.open(f))
    for h, p in d.items(): allsel.update(p['sels'])
for f in glob.glob('raw/proxies_*.json.gz'):
    d = json.load(gzip.open(f))
    for a, p in d['code'].items(): allsel.update(p['sels'])
todo = sorted(s for s in allsel if s not in known)
print('todo', len(todo), flush=True)
S = requests.Session()
def job(i):
    ch = todo[i:i + 150]
    for k in range(6):
        host = ['https://api.4byte.sourcify.dev', 'https://api.openchain.xyz'][k % 2]
        try:
            r = S.get(host + '/signature-database/v1/lookup?filter=false&function=' + ','.join('0x' + s for s in ch), timeout=60)
            j = r.json()
            if j.get('ok'):
                return {s: [x['name'] for x in (j['result']['function'].get('0x' + s) or [])] for s in ch}
        except Exception as e:
            pass
        time.sleep(1 + k)
    print('fail', i, flush=True); return {}
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(job, range(0, len(todo), 150)): known.update(res)
json.dump(known, gzip.open(fn, 'wt'))
print('known', len(known), 'named', sum(1 for v in known.values() if v))
