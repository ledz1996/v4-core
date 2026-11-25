# Compile each micro program with the instrumented emitter and record the shape the target instruction got.
import subprocess,json,sys,os,tempfile,re,collections
sys.path.insert(0,'shapes')
lmap={int(k):v for k,v in json.load(open('shapes/emitter.lmap.json')).items()}
SPEC=re.compile(r'shift|^shl$|^shr$|^sar$|byte|signextend|calldataload|mulmod|mul_mod|modop|mul_with_bit_size|sdiv|smod|div_optimized|mod_optimized|mcopy|tload|tstore|call_runtime|is_bounded_by_bits|bounded_rax|test_high_bits|bswap|^exp|addmod|add_mod|mstore8|negate|sar_by|smod_by|and_')
OPS={'SHL','SHR','SAR','BYTE','SIGNEXTEND','SDIV','SMOD','MULMOD','ADDMOD','CALLDATALOAD'}
td=tempfile.mkdtemp(dir='micro')
res={}
lines=open(sys.argv[1]).read().split('\n')
for l in lines:
    if not l: continue
    name,addr,code=l.split()
    op=name.split('-')[0]
    hx=os.path.join(td,'p.hex'); open(hx,'w').write(code)
    mk=os.path.join(td,'m.txt')
    subprocess.run(['./shapes/asmlog',hx,os.path.join(td,'a.asm')],env={**os.environ,'HX_MARKS':mk},stdout=subprocess.DEVNULL)
    cur=None;sig=[];folded=True
    for m in open(mk).read().split('\n'):
        if m.startswith('@I '):
            cur=m.split()[2]; 
            if cur==op: sig=[]; take=True
            else: take=False
            continue
        if cur!=op or not take: continue
        if m.startswith('@F'):
            f=m[2:].split(' ',1)[1]
            if f=='estimate_size': take=False; continue
            if SPEC.search(f) and f not in sig: sig.append(f)
    res[name]=sig
json.dump(res,open(sys.argv[2],'w'))
c=collections.Counter((k.split('-')[0],tuple(v)) for k,v in res.items())
for (op,s),n in sorted(c.items()): print(op,n,' > '.join(s))
