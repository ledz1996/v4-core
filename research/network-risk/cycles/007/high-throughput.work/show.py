import sys,pickle,collections
res=pickle.load(open(sys.argv[1],'rb'))
names={l.split()[0].lower():l.split()[1] for l in open(sys.argv[2]) if l.strip()}
V=10**12
# summarise per target: for each (frame,kind) the set of outcomes over shapes
by=collections.OrderedDict()
errs=0
for t,frame,kind,shape,p in res:
    if 'err' in p: errs+=1; o='ERR:'+p['err'][:60]
    elif 'pm_call_ok' in p: o='PMFAIL'
    elif 'short' in p: o='SHORT'
    else:
        ret=p['ret']
        o=('ok' if p['ok'] else 'rev')+f"/rds{p['rds']}"
        if p['ok'] and p['rds']: o+=':'+ret[:64]
        if not p['ok'] and p['rds']: o+=':'+ret[:8]
        # balance effects
        if p['tbal'] and frame=='inh' and 'value' not in kind: pass
        o+=f" cv={p['cv']} self={p['selfbal'] if frame=='inh' else 'pm'}"
    by.setdefault(t,collections.OrderedDict()).setdefault((frame,kind),[]).append((shape,o))
print('errors',errs)
for t,d in by.items():
    print('==',t,names.get(t.lower(),''))
    for (frame,kind),lst in d.items():
        groups=collections.OrderedDict()
        for shape,o in lst: groups.setdefault(o,[]).append(shape)
        for o,shs in groups.items():
            print(f'   {frame:6} {kind:20} {o[:150]:150} <- {",".join(shs) if len(shs)<6 else str(len(shs))+" shapes: "+",".join(shs[:3])+"..."}')
