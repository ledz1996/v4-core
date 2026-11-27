# Fetch only the index, per-arch manifests and configs of an OCI tag (no layers). Reads only.
import sys, json, os, hashlib, urllib.request
reg, repo, tag, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
tok = json.load(urllib.request.urlopen(f"https://ghcr.io/token?scope=repository:{repo}:pull&service={reg}"))['token']
ACC = ','.join(['application/vnd.oci.image.index.v1+json','application/vnd.docker.distribution.manifest.list.v2+json',
 'application/vnd.oci.image.manifest.v1+json','application/vnd.docker.distribution.manifest.v2+json'])
def get(path, accept=ACC):
    r = urllib.request.Request(f"https://{reg}/v2/{repo}/{path}", headers={'Authorization':'Bearer '+tok,'Accept':accept})
    return urllib.request.urlopen(r).read()
idx = get(f"manifests/{tag}"); open(f"{out}/index.json",'wb').write(idx)
print('index sha256', hashlib.sha256(idx).hexdigest())
for m in json.loads(idx).get('manifests', []):
    arch = m.get('platform',{}).get('architecture')
    mb = get(f"manifests/{m['digest']}"); assert 'sha256:'+hashlib.sha256(mb).hexdigest()==m['digest']
    open(f"{out}/manifest-{arch}.json",'wb').write(mb); mj=json.loads(mb)
    cfg = get(f"blobs/{mj['config']['digest']}", '*/*'); assert 'sha256:'+hashlib.sha256(cfg).hexdigest()==mj['config']['digest']
    open(f"{out}/config-{arch}.json",'wb').write(cfg)
    print(arch, m['digest'], 'config', mj['config']['digest'], [l['digest'][:19] for l in mj['layers']])
