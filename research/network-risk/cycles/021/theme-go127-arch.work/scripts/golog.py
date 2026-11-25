import json,sys
for f in sys.argv[1:]:
    d=json.loads(open(f).read()[4:])
    print('#####',f,len(d['log']),'commits', 'next' in d and 'MORE' or '')
    for c in d['log']:
        m=c['message']; first=m.split('\n')[0]
        print('*',c['commit'][:12],c['committer']['time'],first)
