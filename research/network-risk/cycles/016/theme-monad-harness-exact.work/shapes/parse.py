# Group the emitter markers by EVM instruction (pc) and give each target instruction a shape signature:
# the ordered emitter functions and branch arms (lines of the unmodified emitter.cpp) that are specific to
# the instruction, taken while the emitter handled that instruction (up to its post-instruction size check).
import json,sys,collections,re
T={'MULMOD','ADDMOD','SDIV','SMOD','SIGNEXTEND','SAR','BYTE','SHL','SHR','EXP','CALLDATALOAD','MSTORE8','MCOPY','TLOAD','TSTORE'}
SPEC=re.compile(r'shift|^shl$|^shr$|^sar$|byte|signextend|calldataload|mulmod|mul_mod|modop|mul_with_bit_size|sdiv|smod|div_optimized|mod_optimized|mcopy|tload|tstore|call_runtime|is_bounded_by_bits|bounded_rax|test_high_bits|bswap|^exp|addmod|mstore8|touch_memory|mstore')
lmap={int(k):v for k,v in json.load(open(sys.argv[2])).items()}
recs=[];cur=None
for l in open(sys.argv[1]).read().split('\n'):
    if l.startswith('@I '):
        _,pc,op=l.split(' ',2); cur={'pc':int(pc),'op':op.split()[0],'marks':[],'done':False}; recs.append(cur); continue
    if cur is None or cur['done']: continue
    if l.startswith('@F'):
        a,name=l[2:].split(' ',1)
        if name=='estimate_size': cur['done']=True; continue
        cur['marks'].append(name)
    elif l.startswith('@L'):
        n=int(l[2:]); cur['marks'].append(f'{lmap.get(n,"?")}:{n}')
sig=collections.defaultdict(list)
for r in recs:
    if r['op'] not in T: continue
    s=[];seen=set()
    for m in r['marks']:
        f=m.split(':')[0]
        if not SPEC.search(f) or m in seen: continue
        seen.add(m); s.append(m)
    sig[(r['op'],tuple(s))].append(r['pc'])
res=[{'op':op,'shape':list(s),'pcs':pcs} for (op,s),pcs in sorted(sig.items())]
json.dump(res,open(sys.argv[3],'w'),indent=1)
c=collections.Counter(x['op'] for x in res)
for op in sorted(c): print(op,c[op],'shapes,', sum(len(x['pcs']) for x in res if x['op']==op),'instructions')
