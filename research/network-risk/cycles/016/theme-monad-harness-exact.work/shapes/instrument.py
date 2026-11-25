# Insert compile-time markers into Monad's x86 emitter: one at the entry of every Emitter member
# function ("@F<line> <name>") and one at the head of every if/else/case/loop arm ("@L<line>"),
# where <line> is the line in the unmodified emitter.cpp. The markers are asmjit logger comments
# (checked_debug_comment), which are written only when an asm log is requested and do not change
# the emitted machine code. Usage: instrument.py in.cpp out.cpp
import re,sys
src=open(sys.argv[1]).read().split('\n')
out=[];depth=0;infn=False;fname=None;pending=None;lmap={}
fnre=re.compile(r'Emitter::(~?[A-Za-z_0-9]+)\s*\(')
for i,l in enumerate(src,1):
    s=l.strip()
    out.append(l)
    if not infn:
        m=fnre.search(l)
        if m and not s.endswith(';') and not s.startswith('//') and 'template' not in s.split('Emitter::')[0][-1:]:
            pending=m.group(1)
        if pending and l.startswith('    {') and s=='{':
            infn=True;depth=1;fname=pending;pending=None
            if fname not in ('Emitter','~Emitter','checked_debug_comment','unchecked_debug_comment') and not fname.startswith('RoData') :
                out.append(f'        hx_mark("@F{i} {fname}");')
        elif s.endswith(';') and pending and '{' not in l:
            pass
        continue
    # inside a member function body
    opens=l.count('{')-l.count('}')
    code=s.split('//')[0].strip()
    ins=False
    if code.endswith('{') and depth>=1:
        if re.match(r'^(\}\s*)?(else\b|if\b|if constexpr\b|else if\b|for\b|while\b|case\b.*:|default:)',code) or code in ('{',') {') or code.endswith(') {'):
            if not re.search(r'\[[^\]]*\]\s*(\(|\{|mutable)|->\s*[\w:<>]+\s*\{$|=\s*\{$|return\s*\{|^switch\b|\bswitch\s*\(|struct\b|class\b|union\b|^do\b',code) and not code.startswith('switch'):
                ins=True
    if ins:
        ind=len(l)-len(l.lstrip())+4
        out.append(' '*ind+f'hx_mark("@L{i}");'); lmap[i]=fname
    depth+=opens
    if depth<=0:
        infn=False;depth=0;fname=None
import json; json.dump(lmap,open(sys.argv[2]+'.lmap.json','w'))
out.insert(0,'extern "C" void hx_mark(char const *);')
open(sys.argv[2],'w').write('\n'.join(out))
