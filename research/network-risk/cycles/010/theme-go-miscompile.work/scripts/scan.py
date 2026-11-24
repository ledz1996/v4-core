# Heuristic scan for the Go issue 81863 shape: a pointer (or slice) variable that holds
# the address of a local and is reassigned on a branch to the address of another value.
import re,sys,glob,collections
rx_func=re.compile(r'^func\s')
rx_assign=re.compile(r'^\s*(?:var\s+)?([A-Za-z_]\w*)\s*(:?=)\s*(.+)$')
def addrlike(rhs):
    rhs=rhs.strip()
    return rhs.startswith('&') or rhs.startswith('new(') or re.match(r'^[A-Za-z_]\w*\[[^\]]*:[^\]]*\]$',rhs) is not None
for path in sys.argv[1:]:
    lines=open(path,errors='replace').read().split('\n')
    fstart=None; fname=None
    funcs=[]
    for i,l in enumerate(lines):
        if rx_func.match(l):
            if fstart is not None: funcs.append((fname,fstart,i))
            fstart=i; fname=l.strip()[:90]
    if fstart is not None: funcs.append((fname,fstart,len(lines)))
    for fname,a,b in funcs:
        defs=collections.defaultdict(list)
        for i in range(a,b):
            l=lines[i].split('//')[0]
            m=rx_assign.match(l)
            if not m: continue
            name,op,rhs=m.groups()
            # multi-assign skipped
            if ',' in name: continue
            defs[name].append((i+1,op,rhs.strip(),len(l)-len(l.lstrip('\t'))))
        for name,ds in defs.items():
            if len(ds)<2: continue
            if not any(addrlike(r) for _,_,r,_ in ds): continue
            if not any(op=='=' for _,op,_,_ in ds): continue
            print(f'{path}:{fname}\n   var {name}: '+'; '.join(f'L{n} {op} {r[:50]} (indent {ind})' for n,op,r,ind in ds))
