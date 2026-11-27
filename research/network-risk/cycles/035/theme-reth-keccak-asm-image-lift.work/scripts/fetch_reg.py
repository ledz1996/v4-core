"""Fetch one platform of a Docker Hub image (manifest, config, layers) into a new dl/ directory, checking every digest.
Reads only; nothing is run. usage: python3 -I fetch_hub.py <repo> <tag> <arch> <outdir>"""
import sys, json, os, hashlib, urllib.request
repo, tag, arch, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
REG = os.environ.get("REG", "registry-1.docker.io")
TOKURL = os.environ.get("TOKURL", "https://auth.docker.io/token?service=registry.docker.io&")
_t = json.load(urllib.request.urlopen(f"{TOKURL}scope=repository:{repo}:pull"))
tok = _t.get("token") or _t.get("access_token")
ACC = ','.join(['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.list.v2+json',
                'application/vnd.oci.image.manifest.v1+json', 'application/vnd.docker.distribution.manifest.v2+json'])
def get(path, accept=ACC):
    r = urllib.request.Request(f"https://{REG}/v2/{repo}/{path}", headers={'Authorization': 'Bearer ' + tok, 'Accept': accept})
    return urllib.request.urlopen(r).read()
idxb = get(f"manifests/{tag}"); open(f"{out}/index.json", 'wb').write(idxb)
idx = json.loads(idxb)
top = 'sha256:' + hashlib.sha256(idxb).hexdigest()
if 'manifests' in idx:
    m = [x for x in idx['manifests'] if x.get('platform', {}).get('architecture') == arch][0]
    mb = get(f"manifests/{m['digest']}")
    assert 'sha256:' + hashlib.sha256(mb).hexdigest() == m['digest']
    md = m['digest']
else:
    mb = idxb; md = top
open(f"{out}/manifest-{arch}.json", 'wb').write(mb)
mj = json.loads(mb)
cfg = get(f"blobs/{mj['config']['digest']}", '*/*')
assert 'sha256:' + hashlib.sha256(cfg).hexdigest() == mj['config']['digest']
open(f"{out}/config-{arch}.json", 'wb').write(cfg)
log = []
for i, l in enumerate(mj['layers']):
    b = get(f"blobs/{l['digest']}", '*/*')
    assert 'sha256:' + hashlib.sha256(b).hexdigest() == l['digest'], 'digest mismatch'
    open(f"{out}/{arch}-layer{i}.tgz", 'wb').write(b)
    log.append((arch, i, l['digest'], l['size']))
json.dump({'reg': REG, 'repo': repo, 'tag': tag, 'top': top, 'manifest': md, 'layers': log}, open(f"{out}/fetch-log.json", 'w'), indent=1)
print(top, md); print(json.dumps(log))
