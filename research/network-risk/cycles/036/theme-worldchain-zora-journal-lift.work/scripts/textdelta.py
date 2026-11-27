# For each differing run in .text of two same-size ELF files, read the 4-byte little-endian word that ends at the
# run's last byte (run length <= 4) and report b-a. Displacement-only changes give small constant deltas. Reads only.
import sys, subprocess, collections, json
A,B=sys.argv[1],sys.argv[2]; a=open(A,'rb').read(); b=open(B,'rb').read()
sec={}
for l in subprocess.run(['readelf','-SW',A],capture_output=True,text=True).stdout.splitlines():
    p=l.replace('[ ','[').split()
    if len(p)>6 and p[0].startswith('['):
        try: sec[p[1]]=(int(p[3],16),int(p[4],16),int(p[5],16))
        except: pass
va,off,sz=sec['.text']
runs=[]
for o in range(off,off+sz,1<<16):
    e=min(o+(1<<16),off+sz)
    if a[o:e]!=b[o:e]:
        for i in range(o,e):
            if a[i]!=b[i]:
                if runs and i-runs[-1][1]==1: runs[-1][1]=i
                else: runs.append([i,i])
c=collections.Counter(); odd=[]
for s,e in runs:
    best=None
    for start in range(e-3, s+1):  # windows of 4 covering whole run
        if start<=s and start+3>=e:
            d=(int.from_bytes(b[start:start+4],'little',signed=True)-int.from_bytes(a[start:start+4],'little',signed=True))
            if best is None or abs(d)<abs(best[0]): best=(d,start)
    if best is None: odd.append((hex(s-off+va),e-s+1)); continue
    c[best[0]]+=1
print(json.dumps({'runs':len(runs),'delta_hist':dict(c.most_common(20)),'long_runs':odd[:20],'n_long':len(odd)}))
