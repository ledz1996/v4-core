# Task 4 summary: PoolManager shapes (v0.16.7 emitter) x execution by the PoolManager scenarios (operand classes
# recorded in the interpreter at the same pc) x the micro programs (coarse shape with edge operands).
import json,glob,collections,sys
sys.path.insert(0,'.')
from srcmap import where
CL=['0','1','31','32','255','256','257..2^64-1','>=2^64 top bit clear','2^255','2^256-1','other top bit set','2..254 other']
def names(m): return [CL[i] for i in range(12) if m>>i&1]
sh=json.load(open(sys.argv[1]))
op=collections.defaultdict(lambda:{'n':0,'m':[0,0,0],'j':set()})
for f in glob.glob('opnd/*.txt'):
    for l in open(f):
        x=l.split(); pc=int(x[0]); r=op[pc]; r['n']+=int(x[1])
        for i in range(3): r['m'][i]|=int(x[2+i])
        r['j'].update(x[5:])
micro=json.load(open('micro/shapes.json'))
msig=collections.defaultdict(int)
for k,v in micro.items(): msig[(k.split('-')[0],' > '.join(v))]+=1
out=[];notrun=[]
coarse=collections.defaultdict(list)
for s in sh:
    c=' > '.join(x for x in s['shape'] if ':' not in x)
    coarse[(s['op'],c)].append(s)
for (o,c),lst in sorted(coarse.items()):
    pcs=sorted(p for s in lst for p in s['pcs'])
    ex=[p for p in pcs if op[p]['n']>0]
    m=[0,0,0]; j=set()
    for p in ex:
        for i in range(3): m[i]|=op[p]['m'][i]
        j|=op[p]['j']
    rec={'op':o,'shape':c,'fineVariants':len(lst),'pcs':pcs,'source':sorted(set(where(p) for p in pcs)),
         'pcsExecutedByPoolManagerScenarios':len(ex),'executions':sum(op[p]['n'] for p in ex),
         'operandClasses':[names(x) for x in m],'joint':sorted(j),'microPrograms':msig.get((o,c),0)}
    out.append(rec)
    for s in lst:
        if not any(op[p]['n']>0 for p in s['pcs']): notrun.append({'op':o,'shape':c,'variant':s['shape'],'pcs':s['pcs'],'source':[where(p) for p in s['pcs']],'microPrograms':msig.get((o,c),0)})
json.dump({'coarse':out,'fineVariantsNotExecuted':notrun},open(sys.argv[2],'w'),indent=1)
for r in out: print(r['op'],'|',r['shape'],'| pcs',len(r['pcs']),'exec',r['pcsExecutedByPoolManagerScenarios'],'| micro',r['microPrograms'],'|',r['operandClasses'][:2])
print('fine variants not executed by PM scenarios:',len(notrun))
for x in notrun: print(' ',x['op'],x['pcs'],x['source'],x['shape'],'micro',x['microPrograms'])
