"""Fetch Monad execution source files at two tags from raw.githubusercontent.com and report which differ.
Usage: python3 fetch_monad.py <outdir> <tagA> <tagB> <file> [file ...]"""
import sys, os, urllib.request, hashlib
out, a, b = sys.argv[1:4]
for f in sys.argv[4:]:
    res = {}
    for v in (a, b):
        url = f"https://raw.githubusercontent.com/category-labs/monad/{v}/{f}"
        try:
            data = urllib.request.urlopen(url, timeout=40).read()
        except Exception as e:
            res[v] = None; continue
        d = os.path.join(out, v); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, f.replace('/', '_')), 'wb').write(data)
        res[v] = hashlib.sha256(data).hexdigest()[:12]
    st = '404' if res[a] is None and res[b] is None else ('same' if res[a] == res[b] else 'DIFF')
    print(st, f, res[a], res[b], flush=True)
