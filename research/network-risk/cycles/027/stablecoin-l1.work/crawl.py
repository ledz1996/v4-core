"""Crawl a Rust crate's module tree from raw.githubusercontent.com at one commit, starting at src/lib.rs.
Usage: python3 -I crawl.py <repo> <commit> <crate dir> <outdir>"""
import sys, os, re, urllib.request, ssl
repo, rev, crate, out = sys.argv[1:5]
ctx = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt')
def get(p):
    u = f'https://raw.githubusercontent.com/{repo}/{rev}/{crate}/{p}'
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={'user-agent': 'curl/8'}), timeout=60, context=ctx) as r:
            return r.read()
    except Exception:
        return None
seen = {}
todo = [('src/lib.rs', 'src')]
while todo:
    p, d = todo.pop()
    if p in seen: continue
    b = get(p); seen[p] = b is not None
    if b is None: continue
    dst = os.path.join(out, p); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(b)
    txt = b.decode('utf8', 'replace')
    txt = re.sub(r'//[^\n]*', '', txt)
    pending_path = None
    for m in re.finditer(r'(#\[path\s*=\s*"([^"]+)"\]\s*)?(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;', txt):
        name = m.group(3)
        if m.group(2):
            todo.append((os.path.normpath(os.path.join(os.path.dirname(p), m.group(2))), None)); continue
        base = os.path.dirname(p) if os.path.basename(p) in ('lib.rs', 'mod.rs') else p[:-3]
        a = f'{base}/{name}.rs'; c = f'{base}/{name}/mod.rs'
        if get(a) is not None: todo.append((a, None))
        else: todo.append((c, None))
for k, v in sorted(seen.items()): print(('ok  ' if v else 'MISS') + ' ' + k)
