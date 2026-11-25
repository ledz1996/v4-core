# Convert fetched mined transactions (dl/mined/*.json) into the line format read by replay.cpp
import json,sys,glob
PM='0x188d586ddcf52439676ca21a244753fa19f9ea8e'
def h(x):
    x=(x or '0x')[2:]
    if len(x)%2: x='0'+x
    return x if x else '-'
def num(x): return str(int(x,16)) if x else '0'
out=open(sys.argv[1],'w'); n=0
files=sorted(glob.glob('dl/mined/*.json'))
for p in files:
    try: d=json.load(open(p))
    except Exception: continue
    rc=d['receipt']; tx=d['txobj']; hd=d['header']; ct=d['calltree']
    gp=tx.get('gasPrice') or rc.get('effectiveGasPrice') or '0x0'
    rnd=hd.get('mixHash') or hd.get('prevRandao') or '0x0'
    out.write(f"TX {d['tx']} {int(rc['status'],16)} {int(hd['number'],16)} {int(hd['timestamp'],16)} {h(hd.get('baseFeePerGas'))} {hd['miner'][2:]} {tx['from'][2:]} {h(gp)} {h(rnd)} {int(hd['gasLimit'],16)}\n")
    pre=d['prestate'].get(PM) or {}
    for k,v in (pre.get('storage') or {}).items(): out.write(f"PRE {k[2:]} {v[2:]}\n")
    out.write(f"BAL {h(pre.get('balance','0x0'))}\n")
    for e in tx.get('accessList') or []:
        out.write(f"ACL {e['address'][2:]}\n")
        if e['address'].lower()==PM:
            for s in e.get('storageKeys') or []: out.write(f"ACLS {s[2:]}\n")
    ids=[0]
    def walk(node,parent):
        i=ids[0]; ids[0]+=1
        to=(node.get('to') or '').lower()
        pm=1 if to==PM and node.get('type') in ('CALL','STATICCALL') else 0
        err=node.get('error') or ''
        oog=1 if 'gas' in err.lower() else 0
        out.write(f"N {i} {parent} {pm} {node.get('type')} {to[2:] if to else '-'} {node['from'][2:]} {h(node.get('value','0x0'))} {num(node.get('gas'))} {num(node.get('gasUsed'))} {0 if err else 1} {oog} {h(node.get('input'))} {h(node.get('output'))}\n")
        for c in node.get('calls') or []: walk(c,i)
    walk(ct,-1)
    for l in rc['logs']:
        if l['address'].lower()!=PM: continue
        out.write(f"LOG {len(l['topics'])} {' '.join(t[2:] for t in l['topics'])} {h(l['data'])}\n")
    n+=1
print(n,'transactions')
