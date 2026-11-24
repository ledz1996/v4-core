import re,sys
auto=[l for l in open('mod_auto.txt').read().split('\n') if l and not l.startswith('#MANUAL')]
def seg(a,b,ind):
    out=[]
    for l in auto:
        n=int(re.search(r'mod\.go:(\d+)',l).group(1))
        if a<=n<=b: out.append(' '*ind+l)
    return '\n'.join(out)
t=open('u256_template.py').read()
t=re.sub(r'@@SEG (\d+) (\d+) (\d+)@@',lambda m:seg(int(m.group(1)),int(m.group(2)),int(m.group(3))),t)
open('u256py.py','w').write(t)
