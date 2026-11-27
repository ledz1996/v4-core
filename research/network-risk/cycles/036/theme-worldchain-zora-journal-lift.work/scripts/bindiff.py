# Count differing bytes between two ELF files and map them to sections. Reads only.
import sys, subprocess
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
assert len(a)==len(b)
diffs=[i for i in range(len(a)) if a[i]!=b[i]] if False else None
import itertools
# fast diff in chunks
d=[]; CH=1<<16
for o in range(0,len(a),CH):
    if a[o:o+CH]!=b[o:o+CH]:
        for i in range(o,min(o+CH,len(a))):
            if a[i]!=b[i]: d.append(i)
secs=[]
for l in subprocess.run(['readelf','-SW',sys.argv[1]],capture_output=True,text=True).stdout.splitlines():
    p=l.replace('[ ','[').split()
    if len(p)>6 and p[0].startswith('[') and p[0]!='[Nr]':
        try: secs.append((p[1],int(p[4],16),int(p[5],16)))
        except: pass
from collections import Counter
c=Counter()
for i in d:
    s=[n for n,off,sz in secs if off<=i<off+sz]; c[s[0] if s else '?']+=1
print('differing bytes',len(d)); print(dict(c))
runs=[]; 
for i in d:
    if runs and i-runs[-1][1]<=8: runs[-1][1]=i
    else: runs.append([i,i])
print('runs',len(runs))
for r in runs[:20]: print(hex(r[0]),r[1]-r[0]+1, a[r[0]:r[1]+1][:40], b[r[0]:r[1]+1][:40])
