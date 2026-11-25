# Follows `mod x;` declarations from crate roots and fetches each file from raw.githubusercontent.com
import re, os, sys, urllib.request, subprocess
rev, out = sys.argv[1], sys.argv[2]
B = f"https://raw.githubusercontent.com/DaniPopes/evm2/{rev}/"
def get(p):
    r = subprocess.run(["curl","-s","-f",B+p],capture_output=True)
    return r.stdout.decode() if r.returncode==0 else None
seen=set()
def save(p,t):
    fp=os.path.join(out,p); os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,"w").write(t)
def crawl(p, moddir):
    if p in seen: return
    seen.add(p); t=get(p)
    if t is None: print("MISS",p); return
    save(p,t)
    for m in re.finditer(r'(?m)^\s*(?:#\[[^\]]*\]\s*)*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;', t):
        name=m.group(1)
        # path attribute
        pre=t[max(0,m.start()-200):m.start()]
        pa=re.findall(r'#\[path\s*=\s*"([^"]+)"\]', t[max(0,m.start()-100):m.end()])
        if pa:
            crawl(os.path.normpath(os.path.join(os.path.dirname(p),pa[-1])), None); continue
        c1=moddir+name+".rs"; c2=moddir+name+"/mod.rs"
        if get(c1) is not None: crawl(c1, moddir+name+"/")
        else: crawl(c2, moddir+name+"/")
    for m in re.finditer(r'include_str!\("([^"]+)"\)|include!\(concat!\(env!\("OUT_DIR"\)', t): pass
for crate in sys.argv[3:]:
    for root in ["src/lib.rs","build.rs","Cargo.toml"]:
        p=f"{crate}/{root}"
        if root=="src/lib.rs": crawl(p, f"{crate}/src/")
        else:
            t=get(p)
            if t: save(p,t)
print(len(seen))
