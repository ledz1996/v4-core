import json,glob
R={}
for f in glob.glob('raw/sweep_*.json'):
    if f.endswith('_all.json'): continue
    d=json.load(open(f)); R.update(d)
eth=R['1']['sweep']
def H(x): return '0x'+('%x'%x).rjust(40,'0')
out={}
for cid,r in sorted(R.items(),key=lambda x:int(x[0])):
    s=r['sweep']; diffs=[]
    for i in range(1,0x200):
        a=H(i)
        if s[a]!=eth[a]: diffs.append((hex(i),s[a]['ok'],s[a]['rds'],s[a]['used']))
    pmrow=None
    other={a:v for a,v in s.items() if int(a,16)>=0x200}
    out[cid]=diffs
    print('==',cid,r['clientVersionBefore'][:40],'diffs in 0x01-0x1ff:',len(diffs))
    print('   ',diffs[:40])
    for a,v in other.items(): print('    ',a,v)
