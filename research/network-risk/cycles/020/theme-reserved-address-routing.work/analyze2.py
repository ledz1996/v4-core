import json,glob
R={}
for f in glob.glob('raw/sweep_*.json'):
    if f.endswith('_all.json') or 'summary' in f: continue
    R.update(json.load(open(f)))
NETS=json.load(open('../../../state/networks.json')); NETS=NETS if isinstance(NETS,list) else NETS['networks']
PMS={str(n['chainId']):n['poolManager'].lower() for n in NETS}
eth=R['1']['sweep']
def H(x): return '0x'+('%x'%x).rjust(40,'0')
summary={}
for cid in [str(n['chainId']) for n in NETS]:
    r=R[cid]; s=r['sweep']
    cold=s['0x00000000000000000000000000000000c0ffee01']
    diffs=[(hex(i),s[H(i)]['ok'],s[H(i)]['rds'],s[H(i)]['used']) for i in range(1,0x200) if s[H(i)]!=eth[H(i)]]
    odd=[(a,v['ok'],v['rds'],v['used']) for a,v in s.items() if int(a,16)>=0x200 and v!=cold and a not in (PMS[cid],'0x00000000000000000000000000000000000a11ce','0x00000000000000000000000000000000005eeb01')]
    pm=s[PMS[cid]]
    summary[cid]={'client':r['clientVersionBefore'],'clientAfter':r['clientVersionAfter'],'coldEmpty':cold,'pm':pm,'diffsLow':diffs,'oddHigh':odd}
    # compress runs of identical diffs
    runs=[];
    for d in diffs:
        if runs and int(d[0],16)==runs[-1][1]+1 and d[1:]==runs[-1][2]: runs[-1][1]+=1
        else: runs.append([int(d[0],16),int(d[0],16),d[1:]])
    print('==',cid,(r['clientVersionBefore'] or '')[:45],'| cold',(cold['ok'],cold['used']),'| PM',(pm['ok'],pm['rds'],pm['used']))
    print('   low diffs:',[('%#x-%#x'%(a,b) if a!=b else '%#x'%a,v) for a,b,v in runs])
    if odd: print('   other:',odd)
json.dump(summary,open('raw/sweep_summary.json','w'),indent=1)
