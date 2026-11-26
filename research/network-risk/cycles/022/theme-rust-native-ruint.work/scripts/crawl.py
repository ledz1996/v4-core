# Fetch a Rust crate's module tree from raw.githubusercontent.com by following `mod x;` declarations.
import sys, os, re, urllib.request, json
repo, ref, root, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
base = f"https://raw.githubusercontent.com/{repo}/{ref}/"
log = open(os.path.join(out, "fetchlog.txt"), "a")
def get(p):
    dst = os.path.join(out, repo.replace('/', '_') + '@' + ref, p)
    if os.path.exists(dst):
        return open(dst, encoding='utf-8', errors='replace').read()
    try:
        d = urllib.request.urlopen(base + p, timeout=60).read()
    except Exception as e:
        log.write(f"MISS {base+p} {e}\n"); return None
    os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(d)
    log.write(f"OK {base+p} {len(d)}\n"); return d.decode('utf-8', 'replace')
seen = set()
def walk(p, is_modroot):
    if p in seen: return
    seen.add(p)
    s = get(p)
    if s is None: return False
    d = os.path.dirname(p)
    if not is_modroot:
        d = os.path.join(d, os.path.basename(p)[:-3])
    s2 = re.sub(r'//[^\n]*', '', s)
    for m in re.finditer(r'(#\[path\s*=\s*"([^"]+)"\]\s*)?(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;', s2):
        if m.group(2):
            walk(os.path.normpath(os.path.join(d, m.group(2))), True); continue
        n = m.group(3)
        a = os.path.join(d, n + '.rs')
        if get(a) is not None: walk(a, False)
        else: walk(os.path.join(d, n, 'mod.rs'), True)
    return True
walk(root, True)
print(len(seen), "files")
