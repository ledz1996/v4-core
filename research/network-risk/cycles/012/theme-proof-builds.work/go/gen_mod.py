# Translate the straight-line bits.* statements of holiman/uint256 v1.3.2 mod.go into Python.
# Lines that are not pure bits.* calls are emitted as '#MANUAL: <go text>' for hand translation.
import re,sys
src=open(sys.argv[1]).read().split('\n')
out=[]
call=re.compile(r'^\s*([\w\[\]_, ]+?)\s*:?=\s*bits\.(Mul64|Add64|Sub64)\((.*)\)\s*$')
for ln,line in enumerate(src,1):
    s=line.split("//")[0].strip()
    if not s or s.startswith('//'): continue
    for part in [p.strip() for p in s.split(';') if p.strip()]:
        m=call.match(part)
        if m:
            lhs,fn,args=m.groups()
            args=args.replace('uint64(1) << 62','(1<<62)')
            out.append(f'{lhs} = {fn}({args})  # mod.go:{ln}')
        else:
            out.append(f'#MANUAL mod.go:{ln}: {part}')
open(sys.argv[2],'w').write('\n'.join(out)+'\n')
