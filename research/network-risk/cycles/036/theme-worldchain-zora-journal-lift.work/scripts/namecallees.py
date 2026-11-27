"""Annotate a callees.py listing with shortened symbol names. usage: namecallees.py <nm output> <listing>"""
import re, sys
syms={}
for l in open(sys.argv[1]):
    p=l.split(None,2)
    if len(p)==3 and re.match(r'^[0-9a-f]+$',p[0]): syms.setdefault(int(p[0],16),p[2].strip())
def short(s):
    while re.search(r'<[^<>]*>',s): s=re.sub(r'<[^<>]*>','',s)
    return s[:120]
for l in open(sys.argv[2]):
    m=re.match(r'(\s*)([0-9a-f]+) \((\d+)\)',l)
    print(m.group(1)+m.group(2)+" "+m.group(3)+" "+short(syms.get(int(m.group(2),16),"?")) if m else l.rstrip())
