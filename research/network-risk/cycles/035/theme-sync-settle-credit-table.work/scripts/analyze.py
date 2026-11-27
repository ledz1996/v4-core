import json, sys
r = json.load(open(sys.argv[1]))
def iv(h): return int(h, 16) if h else None
for cid, n in r.items():
    print('==', cid, n['name'], n['blockNumber'], (n['before'].get('web3_clientVersion') or {}).get('result'), '|', (n['after'].get('web3_clientVersion') or {}).get('result'))
    for c in n['cases']:
        if 'steps' not in c:
            print('  ', c['case'], 'NOT RUN', str(c.get('skipped') or c.get('raw'))[:150]); continue
        st = c['steps']; L = {s['label']: s for s in st}
        def val(l):
            s = L.get(l); 
            if s is None: return None
            return s['ok'] if s['ret'] == '' else iv(s['ret'][:64])
        line = []
        for s in st:
            v = s['ret']
            line.append(f"{s['label']}={s['ok']}:{(str(iv(v[:64])) if v and len(v)<=64 else (v[:10]+'..'+str(len(v)//2)+'B') if v else '')}")
        print('  ', c['case'], c.get('x', ''))
        print('      ', ' | '.join(line))
