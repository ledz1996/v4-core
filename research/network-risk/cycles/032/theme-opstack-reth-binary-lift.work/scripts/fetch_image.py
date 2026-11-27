# Fetch an OCI image's manifests and layers into a dl/ directory. Reads only; nothing is run.
import sys, json, os, hashlib, urllib.request
reg, repo, tag, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
tokurl = {'ghcr.io':'https://ghcr.io/token','us-docker.pkg.dev':'https://us-docker.pkg.dev/v2/token'}[reg]
tok = json.load(urllib.request.urlopen(f"{tokurl}?scope=repository:{repo}:pull&service={reg}"))
tok = tok.get('token') or tok.get('access_token')
ACC = ','.join(['application/vnd.oci.image.index.v1+json','application/vnd.docker.distribution.manifest.list.v2+json',
 'application/vnd.oci.image.manifest.v1+json','application/vnd.docker.distribution.manifest.v2+json'])
def get(path, accept=ACC):
    r = urllib.request.Request(f"https://{reg}/v2/{repo}/{path}", headers={'Authorization':'Bearer '+tok,'Accept':accept})
    return urllib.request.urlopen(r).read()
idx = get(f"manifests/{tag}"); open(f"{out}/index.json",'wb').write(idx)
idx = json.loads(idx)
mans = idx.get('manifests') or [{'digest':None,'platform':{'architecture':'single'}}]
log = []
for m in mans:
    p = m.get('platform',{}); arch = p.get('architecture'); 
    if arch in ('unknown',): continue
    mb = get(f"manifests/{m['digest']}") if m['digest'] else json.dumps(idx).encode()
    assert m['digest'] is None or 'sha256:'+hashlib.sha256(mb).hexdigest()==m['digest']
    mj = json.loads(mb); open(f"{out}/manifest-{arch}.json",'wb').write(mb)
    cfg = get(f"blobs/{mj['config']['digest']}", '*/*'); open(f"{out}/config-{arch}.json",'wb').write(cfg)
    for i,l in enumerate(mj['layers']):
        fn = f"{out}/{arch}-layer{i}.tgz"
        if not os.path.exists(fn):
            b = get(f"blobs/{l['digest']}", '*/*')
            assert 'sha256:'+hashlib.sha256(b).hexdigest()==l['digest'], 'digest mismatch'
            open(fn,'wb').write(b)
        log.append((arch, i, l['digest'], l['size']))
json.dump({'reg':reg,'repo':repo,'tag':tag,'layers':log}, open(f"{out}/fetch-log.json",'w'), indent=1)
print(json.dumps(log, indent=0))
