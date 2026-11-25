# Per-frame gas of the replay (interpreter run) against gasUsed in the block's call tree, classified
import sys,subprocess,collections,json
tot=collections.Counter()
for part in sys.argv[1:]:
    s=open(part).read()
    out=subprocess.run(['./rp','monad-pm-runtime.hex',part,'-v'],capture_output=True,text=True).stdout
    rec={};cur=None
    for l in s.split('\n'):
        if l.startswith('TX '): cur=l.split()[1]; rec[cur]=[]
        elif l.startswith('N '):
            f=l.split()
            if f[3]=='1': rec[cur].append((int(f[9]),int(f[8]),f[2]=='-1'))
    cur=None;mode=None
    for l in out.split('\n'):
        if l.startswith(('SAME','DIFF')): cur=l.split()[1]; i=0
        elif l.startswith('--- '): mode=l[4:]; i=0
        elif l.startswith('  frame ') and mode=='interp':
            f=l.split()
            if f[3]=='forced-oog': tot['forced out of gas (not run)']+=1
            else:
                gu,gas,top=rec[cur][i]; d=int(f[3])-gu
                if d==0: tot['equal']+=1
                elif top and gu==gas: tot['top-level frame, block reports the whole gas limit']+=1
                elif d>0 and d%10000==0: tot['higher by a multiple of 10,000 (cold account access warmed earlier by another contract)']+=1
                elif d<0 and (-d)%10100==0: tot['lower by a multiple of 10,100']+=1
                else: tot['other: %d'%d]+=1
            i+=1
print(json.dumps(tot,indent=1))
