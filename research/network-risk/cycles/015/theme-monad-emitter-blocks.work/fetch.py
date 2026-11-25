import json,sys,os,urllib.request,concurrent.futures as cf
lst,repo,ver,out=sys.argv[1:5]; BASE=os.environ.get("BASE") or f"https://cdn.jsdelivr.net/gh/{repo}@{ver}"; prefixes=sys.argv[5:]
d=json.load(open(lst))
fs=[f['name'] for f in d['files'] if any(f['name'].startswith(p) for p in prefixes)]
def get(f):
    p=out+f
    if os.path.exists(p): return
    os.makedirs(os.path.dirname(p),exist_ok=True)
    for i in range(3):
        try:
            data=urllib.request.urlopen(f'{BASE}{f}',timeout=60).read(); open(p,'wb').write(data); return
        except Exception as e: err=e
    print('FAIL',f,err)
with cf.ThreadPoolExecutor(16) as ex: list(ex.map(get,fs))
print(len(fs))
