"""Fetch one platform of an OCI image (manifest, config, layers) into a new dl/ directory, checking every digest.
Reads only; nothing is run. usage: python3 -I fetch_one.py <registry> <repo> <tag> <arch> <outdir>"""
import sys, json, os, hashlib, urllib.request
reg, repo, tag, arch, out = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
tokurl = {'ghcr.io': 'https://ghcr.io/token', 'us-docker.pkg.dev': 'https://us-docker.pkg.dev/v2/token'}[reg]
tok = json.load(urllib.request.urlopen(f"{tokurl}?scope=repository:{repo}:pull&service={reg}"))
tok = tok.get('token') or tok.get('access_token')
ACC = ','.join(['application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.list.v2+json',
                'application/vnd.oci.image.manifest.v1+json', 'application/vnd.docker.distribution.manifest.v2+json'])
def get(path, accept=ACC):
    r = urllib.request.Request(f"https://{reg}/v2/{repo}/{path}", headers={'Authorization': 'Bearer ' + tok, 'Accept': accept})
    return urllib.request.urlopen(r).read()
idx = get(f"manifests/{tag}"); open(f"{out}/index.json", 'wb').write(idx)
idx = json.loads(idx)
m = [x for x in idx['manifests'] if x.get('platform', {}).get('architecture') == arch][0]
mb = get(f"manifests/{m['digest']}")
assert 'sha256:' + hashlib.sha256(mb).hexdigest() == m['digest']
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
json.dump({'reg': reg, 'repo': repo, 'tag': tag, 'manifest': m['digest'], 'layers': log}, open(f"{out}/fetch-log.json", 'w'), indent=1)
print(json.dumps(log))
