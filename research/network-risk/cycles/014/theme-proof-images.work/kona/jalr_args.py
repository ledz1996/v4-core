# For each indirect call that the CFG scan reached with a 0-or-64 value still in an argument register, list which
# argument registers ($4-$11) the caller writes in the basic block before the call (back to the previous branch,
# jump or label-free stop of 40 instructions) plus the delay slot, and where $25 comes from.
import os,sys,json,struct
os.environ['TEXT']=sys.argv[1]; sys.argv=[sys.argv[0]]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import cfg_scan as C
d=json.load(open('cfg_scan.json'))
seen={}
for s in d['sites']:
    for f in s['flags']:
        if 'indirect call' not in f['role']: continue
        pc=int(f['pc'],16); key=(pc,tuple(f['tainted']))
        if key in seen: continue
        writes=set(); src25=None
        k,u,df,e=C.dec(C.word(pc+4)); writes|=set(df)&C.ARGS
        p=pc-4
        for i in range(40):
            k,u,df,e=C.dec(C.word(p))
            if k in ('branch','j','jal','jalr','jr'): break
            writes|=set(df)&C.ARGS
            if 25 in df and src25 is None: src25='%08x'%C.word(p)
            p-=4
        seen[key]={'jalr':hex(pc),'site':s['site'],'taintedArgReg':f['tainted'],'argRegsWrittenBeforeCall':sorted(writes),'blockStart':hex(p+4),'t9From':src25}
for v in seen.values(): print(v)
json.dump(list(seen.values()),open('jalr_args.json','w'),indent=1)
