# Fetch one blob by digest and check its sha256. Reads only.
import sys, json, hashlib, urllib.request
reg, repo, dig, out = sys.argv[1:5]
tok = json.load(urllib.request.urlopen(f"https://ghcr.io/token?scope=repository:{repo}:pull&service={reg}"))['token']
r = urllib.request.Request(f"https://{reg}/v2/{repo}/blobs/{dig}", headers={'Authorization':'Bearer '+tok})
b = urllib.request.urlopen(r).read()
assert 'sha256:'+hashlib.sha256(b).hexdigest()==dig, 'digest mismatch'
open(out,'wb').write(b); print('ok', dig, len(b))
