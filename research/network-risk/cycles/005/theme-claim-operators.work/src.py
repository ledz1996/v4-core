# Fetch verified source from Sourcify (v2 API) and save it under raw/src/.
import sys, json, os, requests
def fetch(cid, addr):
    d = os.path.join('raw', 'src'); os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, '%d_%s.json' % (cid, addr.lower()))
    if os.path.exists(fn): return json.load(open(fn))
    r = requests.get('https://sourcify.dev/server/v2/contract/%d/%s?fields=sources,compilation,abi' % (cid, addr), timeout=60)
    j = r.json() if r.status_code == 200 else {'status': r.status_code, 'text': r.text[:200]}
    json.dump(j, open(fn, 'w'))
    return j
if __name__ == '__main__':
    j = fetch(int(sys.argv[1]), sys.argv[2])
    if 'sources' not in j: print(j); sys.exit()
    print(j.get('compilation', {}).get('name'), j.get('compilation', {}).get('compilerVersion'), list(j['sources'].keys())[:20])
    pat = sys.argv[3] if len(sys.argv) > 3 else None
    if pat:
        import re
        for name, s in j['sources'].items():
            lines = s['content'].split('\n')
            for i, l in enumerate(lines):
                if re.search(pat, l): print('%s:%d: %s' % (name.split('/')[-1], i + 1, l.rstrip()[:220]))
